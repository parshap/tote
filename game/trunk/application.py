from __future__ import division

# Import OGRE-specific (and other UI-Client) external packages and modules.
import ogre.renderer.OGRE as ogre
from twisted.internet import reactor

# Import other external packages and modules.
import threading, time

# Import internal packages and modules modules.
from playscene import PlayScene
import gamestate, net
from net import packets
from event import Event, Scheduler

class ClientApplication(object):
    app_title = "MyApplication"
    
    def __init__(self, address, port=8981):
        self.address = address
        self.port = port

    def go(self):
        # See Basic Tutorial 6 for details
        self.createRoot()
        self.defineResources()
        self.setupRenderSystem()
        self.createRenderWindow()
        self.initializeResourceGroups()
        self.setupScene()
        self.createFrameListener()
        self.startRenderLoop()
        self.cleanUp()

    def createRoot(self):
        self.root = ogre.Root()

    def defineResources(self):
        # Read the resources.cfg file and add all resource locations in it
        cf = ogre.ConfigFile()
        cf.load("resources.cfg")
        seci = cf.getSectionIterator()
        while seci.hasMoreElements():
            secName = seci.peekNextKey()
            settings = seci.getNext()

            for item in settings:
                typeName = item.key
                archName = item.value
                ogre.ResourceGroupManager.getSingleton().addResourceLocation(archName, typeName, secName)

    def setupRenderSystem(self):
        # Show the config dialog if we don't yet have an ogre.cfg file
        if not self.root.restoreConfig() and not self.root.showConfigDialog():
            raise Exception("User canceled config dialog! (setupRenderSystem)")

    def createRenderWindow(self):
        self.root.initialise(True, self.app_title)
        self.renderWindow = self.root.getAutoCreatedWindow()
        self.renderWindow.setDeactivateOnFocusChange(False)

    def initializeResourceGroups(self):
        ogre.TextureManager.getSingleton().setDefaultNumMipmaps(5)
        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()

    def setupScene(self):
        self.sceneManager = self.root.createSceneManager(ogre.ST_GENERIC, "PrimarySceneManager")
        
        # Create the camera and attach it to a scene node.
        camera = self.sceneManager.createCamera("PrimaryCamera")
        cameraNode = self.sceneManager.getRootSceneNode().createChildSceneNode('PrimaryCamera')
        cameraNode.attachObject(camera)

        # setup viewport
        vp = self.renderWindow.addViewport(camera)
        vp.backGroundColor = (0, 0, 0)

    def createFrameListener(self):
        self.playScene = PlayScene(self.sceneManager, self.address, self.port)
        self.root.addFrameListener(self.playScene)

    def startRenderLoop(self):
        self.root.startRendering()

    def cleanUp(self):
        # @todo: move this somewhere else
        self.playScene.client.stop()
        pass


class ServerApplication(object):
    def __init__(self, port=8981):
        self.port = port
        self.schedulers = []
        self.is_round_active = False
        
    def go(self):
        self.world = gamestate.world.World(master=True)
        self.world.object_added += self.on_world_object_added
        self.world.object_removed += self.on_world_object_removed
        
        self.server = net.server.GameServer(self.world, self.port)
        self.server.client_connected += self.on_client_connected
        self.server.client_disconnected += self.on_client_disconnected
        self.server_thread = threading.Thread(target=self.server.go)
        self.server_thread.start()
        
        self.last_updates = { }
        
        # A set of players who's status updates need to be sent out.
        self.status_updates = set()
        
        self.scene = gamestate.scenes.TestScene(self.world)
        
        self.is_round_active = True
        self.run = True
        
        last = time.clock()
        while self.run:
            new = time.clock()
            dt = new - last
            self.update(dt)
            last = new
    
    def stop(self):
        self.run = False
        self.server.stop()
        
    def update(self, dt):
        # Add time to schedulers.
        for scheduler in self.schedulers:
            scheduler.addtime(dt)
        
        # Get buffered input from clients and process it.
        while not self.server.input.empty():
            (client, packet) = self.server.input.get_nowait()
            self.process_packet(client, packet)
        
        # Update the game state world.
        self.world.update(dt)
        
        # Send necessary ObjectUpdate packets.
        for object in self.world.objects:
            if object.type == "player":
                self._send_update(object)
            
        # Send necessary ObjectStatusUpdate packets.
        for object in self.status_updates:
            update = packets.ObjectStatusUpdate()
            update.object_id = object.object_id
            update.health, update.power = object.health, object.power
            self.server.output_broadcast.put_nowait((update, None))
        self.status_updates.clear()
        
        # Send buffered output to clients.
        reactor.callFromThread(self.server.send)
        
        # Sleep some if we're updating too fast.
        extra = 0.01 - dt
        if extra >= 0.001:
            time.sleep(extra)
            
    def schedule(self, in_time, callback, *params):
        s = Scheduler(in_time, *params)
        s.fired += lambda *_: self.schedulers.remove(s)
        s.fired += callback
        self.schedulers.append(s)
        
    def round_start(self):
        self.is_round_active = True
        # Reset everyone's score to 0.
        for client in self.server.clients:
            if client.player is not None:
                client.player.score = 0
        # Tell everyone that the round is starting.
        start = packets.RoundStart()
        self.server.output_broadcast.put_nowait((start, None))
    
    def round_end(self, winner_player):
        self.is_round_active = False
        # Send RoundEnd packet.
        end = packets.RoundEnd()
        self.server.output_broadcast.put_nowait((end, None))
        # Send a message to everyone.
        m = packets.Message()
        m.message = "%s has won the round." % winner_player.name
        m.type = "success"
        self.server.output_broadcast.put_nowait((m, None))
        # Kill everyone.
        for client in self.server.clients:
            if client.player is not None:
                client.player.is_dead = True
        # Schedule a round to start in 5 seconds.
        self.schedule(5, self.round_start)

    ## World event handlers
    def on_world_object_added(self, object):
        if object.type == "player":
            # Sent a ObjectInit for the new player obeject to everyone but the player.
            init = packets.ObjectInit()
            init.object_id = object.object_id
            init.object_type = object.type
            init.element_type = object.element.type
            init.name = object.name
            self.server.output_broadcast.put_nowait((init, object))
            # Send a ObjectUpdate for the new player object to everyone.
            self._send_update(object)

    def on_world_object_removed(self, object):
        if object.type == "player":
            remove = packets.ObjectRemove()
            remove.object_id = object.object_id
            self.server.output_broadcast.put_nowait((remove, None))
            
    def on_player_status_changed(self, player, value):
        self.status_updates.add(player)
    
    def on_player_is_dead_changed(self, player):
        self._send_update(player, check_time=False)
        if player.is_dead:
            if self.is_round_active:
                if player.last_damage_code == 1:
                    # Player died to a suicide.
                    m = "%s has committed suicide." % player.name
                elif player.last_damage_player is not None:
                    # Player died to an ability and we know the source player.
                    player.last_damage_player.score += 1
                    m = "%s has killed %s." % (player.last_damage_player.name, player.name)
                else:
                    # Player died, but we don't know by who.
                    m = "%s has died." % player.name
                message = packets.Message()
                message.message = m
                message.type = "death"
                self.server.output_broadcast.put_nowait((message, None))
            self.world.remove_object(player)
        else:
            self.world.add_object(player)
    
    def on_player_teleported(self, player):
        self._send_update(player, time_check=False, forced=True)
    
    def on_player_score_changed(self, player):
        update = packets.ScoreUpdate()
        update.player_id = player.object_id
        update.score = player.score
        self.server.output_broadcast.put_nowait((update, None))
        if player.score >= 10:
            # Schedule the round end to happen on the next frame. We need to do
            # this because otherwise there is some conflict with the order of
            # packets being processed (player is killed before ability_used is
            # sent.)
            self.schedule(0, self.round_end, player)
    
    ## Network event handlers & helpers
    def on_client_connected(self, client):
        pass
    
    def on_client_disconnected(self, client):
        if client.player is not None and client.player.is_active:
            self.world.remove_object(client.player)
            client.player = None

    def process_packet(self, client, packet):
        ptype = type(packet)
        print "Processing packet=%s: %s from client=%s." % (packet.id, ptype.__name__, client.client_id)
        
        # JoinRequest
        if ptype is packets.JoinRequest:
            # @todo: deny conditions
            # Create the player in the world.
            player = gamestate.objects.Player(self.world)
            player.name = packet.player_name
            player.object_id = self.world.generate_id()
            player.is_dead = True
            # Listen to events.
            player.health_changed += self.on_player_status_changed
            player.power_changed += self.on_player_status_changed
            player.is_dead_changed += self.on_player_is_dead_changed
            player.score_changed += self.on_player_score_changed
            client.player = player
            print "Creating player in world with id=%s for client id=%s." % \
                (player.object_id, client.client_id)
                
            # Send the JoinResponse.
            response = packets.JoinResponse()
            response.player_id = player.object_id
            self.server.output.put_nowait((client, response))
            
            # Send ObjectUpdate and ObjectInit to the player for each object.
            for object in self.world.objects:
                if object.type != "player":
                    continue
                if object == player:
                    continue
                init = packets.ObjectInit()
                init.object_id = object.object_id                    
                init.object_type = object.type
                init.element_type = object.element.type
                init.name = object.name
                self.server.output.put_nowait((client, init))
                update = self._get_update(object)
                self.server.output.put_nowait((client, update))
                score = packets.ScoreUpdate()
                score.player_id = object.object_id
                score.score = object.score
                self.server.output.put_nowait((client, score))
        
        # SpawnRequest
        elif ptype is packets.SpawnRequest:
            if self.is_round_active:
                # @todo: more deny conditions
                client.player.change_element(packet.element_type)
                client.player.position = self.scene.generate_spawn_position()
                client.player.rotation = 1.5707963267948966
                client.player.health = client.player.max_health
                client.player.health = client.player.max_power
                client.player.is_dead = False
                response = packets.SpawnResponse()
                response.element_type = packet.element_type
                response.x, response.z = client.player.position
                self.server.output.put_nowait((client, response))
                self._send_update(client.player, check_time=False)

        # PlayerUpdate
        elif ptype is packets.PlayerUpdate:
            client.player.position = (packet.x, packet.z)
            client.player.rotation = packet.rotation
            if packet.move_speed > 0:
                client.player.is_moving = True
                #client.player.move_speed = packet.move_speed
                client.player.move_direction = packet.move_direction
            else:
                client.player.is_moving = False
        
        # AbilityRequest
        elif ptype is packets.AbilityRequest:
            # @todo: deny conditions
            if client.player.use_ability(packet.ability_id):
                used = packets.AbilityUsed()
                used.object_id = client.player.object_id
                used.ability_id = packet.ability_id
                # Send an ObjectUpdate for this player so clients have most recent
                # data when using the ability.
                self._send_update(client.player, ignore=client.player, check_time=False)
                self.server.output_broadcast.put_nowait((used, None))
    
    def _send_update(self, object, ignore=None, check_time=True, check_data=True, forced=False):
        # Only send updates for MobileObjects.
        if not isinstance(object, gamestate.objects.MobileObject):
            return
        
        update = self._get_update(object)
        update.force = forced

        if self.last_updates.has_key(object):
            last_update_time, last_update = self.last_updates[object]
            
            # Only send if update threshold has expired.
            if check_time and last_update_time + 0.05 > self.world.time:
                return
            
            # Only send if there is new information to be sent.
            if check_data and update.object_id == last_update.object_id and \
                update.x == last_update.x and update.z == last_update.z and \
                update.rotation == last_update.rotation and \
                update.move_speed == last_update.move_speed and \
                update.move_direction == last_update.move_direction and \
                update.is_dead == last_update.is_dead:
                return
        
        print "Broadcasting update for object id=%s." % object.object_id
        self.server.output_broadcast.put_nowait((update, ignore))
        self.last_updates[object] = (self.world.time, update)

    def _get_update(self, object):
        """ Helper method to create an ObjectUpdate packet from a game object. """
        update = packets.ObjectUpdate()
        update.object_id = object.object_id
        update.x = object.position[0]
        update.z = object.position[1]
        update.rotation = object.rotation
        try:
            if object.is_moving:
                update.move_speed = object.move_speed
                update.move_direction = object.move_direction
            else:
                update.move_speed = 0
                update.move_direction = 0
        except:
            update.move_speed = 0
            update.move_direction = 0
        if object.type == "player":
            update.is_dead = object.is_dead
        else:
            update.is_dead = False
        return update