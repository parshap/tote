from __future__ import division
import threading, time, math

# Import OGRE-specific (and other UI-Client) external packages and modules.
import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS
from twisted.internet import reactor

# Import internal packages and modules modules.
import gamestate, net
from net import packets
import SceneLoader
from inputhandler import InputHandler
from event import Event
import nodes
import gui
import audio

# Import other python modules
import math

class PlaySceneGUI(object):
    def __init__(self, playscene):
        self.playscene = playscene
        self.viewport = playscene.viewport
        self._setup_overlay()
        self.elements = []
        
        # Create an FPS label.
        fpslabel = gui.FPSLabel("UI/FPSLabel")
        self.elements.append(fpslabel)
        
        # Create quick scores labels.
        self.qscores_1_name = gui.Label("UI/QuickScores/1/Name")
        self.qscores_1_score = gui.Label("UI/QuickScores/1/Score")
        self.qscores_2_name = gui.Label("UI/QuickScores/2/Name")
        self.qscores_2_score = gui.Label("UI/QuickScores/2/Score")
        playscene.scores_changed += self.on_scores_changed
        
        # Create the message label.
        self.message = gui.Message("UI/MessageLabel")
        self.elements.append(self.message)
        
        # Create the element selection panel
        self.element_selection = gui.Element("UI/ElementSelection")
        self.element_selection.hide()
        self.elements.append(self.element_selection)
        
        # Add buttons for each of the 4 element buttons.
        left = self.viewport.actualWidth / 2 - 300
        top = self.viewport.actualHeight / 2 - 300
        
        earth_rect = ogre.Rectangle()
        earth_rect.left = left + 40
        earth_rect.top = top + 40
        earth_rect.right = earth_rect.left + 212
        earth_rect.bottom = earth_rect.top + 212
        
        fire_rect = ogre.Rectangle()
        fire_rect.left = left + 40
        fire_rect.top = top + 600 - 212 - 40
        fire_rect.right = fire_rect.left + 212
        fire_rect.bottom = fire_rect.top + 212
        
        water_rect = ogre.Rectangle()
        water_rect.left = left + 600 - 212 - 40
        water_rect.top = top + 40
        water_rect.right = water_rect.left + 212
        water_rect.bottom = water_rect.top + 212
        
        air_rect = ogre.Rectangle()
        air_rect.left = left + 600 - 212 - 40
        air_rect.top = top + 600 - 212 - 40
        air_rect.right = air_rect.left + 212
        air_rect.bottom = air_rect.top + 212
        
        self.element_selected = Event()

        def on_element_clicked_earth(button, mouse_button):
            self.element_selected("earth")
        def on_element_clicked_fire(button, mouse_button):
            self.element_selected("fire")
        def on_element_clicked_water(button, mouse_button):
            self.element_selected("water")
        def on_element_clicked_air(button, mouse_button):
            self.element_selected("air")
            
        earth_button = gui.Button("UI/ElementSelection/Earth", earth_rect)
        earth_button.clicked += on_element_clicked_earth
        fire_button = gui.Button("UI/ElementSelection/Fire", fire_rect)
        fire_button.clicked += on_element_clicked_fire
        water_button = gui.Button("UI/ElementSelection/Water", water_rect)
        water_button.clicked += on_element_clicked_water
        air_button = gui.Button("UI/ElementSelection/Air", air_rect)
        air_button.clicked += on_element_clicked_air
        
        self.elements.append(earth_button)
        self.elements.append(fire_button)
        self.elements.append(water_button)
        self.elements.append(air_button)
    
    def _setup_overlay(self):
        pOver = ogre.OverlayManager.getSingleton().getByName("UI")
        pOver.show()
        
    def setup_player_gui(self, player):
        """ Sets up player-related GUI that requires a player before setting up. """
        # Set up health and power bars
        health_bar_rect = ogre.Rectangle()
        health_bar_rect.left = self.viewport.actualWidth / 2 - 128
        health_bar_rect.top = self.viewport.actualHeight - 84
        health_bar_rect.right = health_bar_rect.left + 256
        health_bar_rect.bottom = health_bar_rect.top + 10
        health_bar = gui.StatusBar("UI/StatusBars/Health", health_bar_rect, player.max_health)
        health_bar.name = "Health"
        
        power_bar_rect = ogre.Rectangle()
        power_bar_rect.left = health_bar_rect.left
        power_bar_rect.top = health_bar_rect.bottom
        power_bar_rect.right = health_bar_rect.right
        power_bar_rect.bottom = power_bar_rect.top + 10
        power_bar = gui.StatusBar("UI/StatusBars/Power", power_bar_rect, player.max_power)
        power_bar.name = "Power"
        
        # Add the gui elements to the element list.
        self.elements.append(health_bar)
        self.elements.append(power_bar)
        
        # Add listeners to player's health and power changed events.
        player.health_changed += health_bar.on_value_changed
        player.power_changed += power_bar.on_value_changed
        
        self.setup_ability_bar(player)

    def setup_ability_bar(self, player):
        # Remove all current gui.AbilityCooldownDisplay from the current gui.
        self.elements = [element for element in self.elements
            if type(element) is not gui.AbilityCooldownDisplay]
        # Set up ability cooldown displays
        ability_keys = player.element.ability_keys
        ability_cooldowns = player.element.ability_cooldowns
        ability1_cooldown = ability_cooldowns[ability_keys[1]]
        ability2_cooldown = ability_cooldowns[ability_keys[2]]
        ability3_cooldown = ability_cooldowns[ability_keys[3]]
        ability4_cooldown = ability_cooldowns[ability_keys[4]]
        
        # Set up ability icons.
        if player.element.type == "fire":
            # Fire
            ability1_icon_mat = "FireIconAbility1"
            ability2_icon_mat = "FireIconAbility2"
            ability3_icon_mat = "FireIconAbility3"
            ability4_icon_mat = "FireIconAbility4"
        elif player.element.type == "earth":
            # Earth
            ability1_icon_mat = "EarthIconAbility1"
            ability2_icon_mat = "EarthIconAbility2"
            ability3_icon_mat = "EarthIconAbility3"
            ability4_icon_mat = "EarthIconAbility4"
        elif player.element.type == "air":
            # Air
            ability1_icon_mat = "AirIconAbility1"
            ability2_icon_mat = "AirIconAbility2"
            ability3_icon_mat = "AirIconAbility3"
            ability4_icon_mat = "AirIconAbility4"
        elif player.element.type == "water":
            # Water
            ability1_icon_mat = "WaterIconAbility1"
            ability2_icon_mat = "WaterIconAbility2"
            ability3_icon_mat = "WaterIconAbility3"
            ability4_icon_mat = "WaterIconAbility4"
        
        # Create UI Elements      
        ability1_cdd_rect = ogre.Rectangle()
        ability1_cdd_rect.left = self.viewport.actualWidth / 2 - 128
        ability1_cdd_rect.top = self.viewport.actualHeight - 64
        ability1_cdd_rect.right = ability1_cdd_rect.left + 64
        ability1_cdd_rect.bottom = ability1_cdd_rect.top + 64
        ability1_cooldown_display = gui.AbilityCooldownDisplay("UI/AbilityBar/Ability1", ability1_cdd_rect, 1, ability1_cooldown)
        ability1_cooldown_display.overlay.setMaterialName(ability1_icon_mat)
        
        ability2_cdd_rect = ogre.Rectangle()
        ability2_cdd_rect.left = ability1_cdd_rect.right
        ability2_cdd_rect.top = ability1_cdd_rect.top
        ability2_cdd_rect.right = ability2_cdd_rect.left + 64
        ability2_cdd_rect.bottom = ability2_cdd_rect.top + 64
        ability2_cooldown_display = gui.AbilityCooldownDisplay("UI/AbilityBar/Ability2", ability2_cdd_rect, 2, ability2_cooldown)
        ability2_cooldown_display.overlay.setMaterialName(ability2_icon_mat)
        
        ability3_cdd_rect = ogre.Rectangle()
        ability3_cdd_rect.left = ability2_cdd_rect.right
        ability3_cdd_rect.top = ability2_cdd_rect.top
        ability3_cdd_rect.right = ability3_cdd_rect.left + 64
        ability3_cdd_rect.bottom = ability3_cdd_rect.top + 64
        ability3_cooldown_display = gui.AbilityCooldownDisplay("UI/AbilityBar/Ability3", ability3_cdd_rect, 3, ability3_cooldown)
        ability3_cooldown_display.overlay.setMaterialName(ability3_icon_mat)
        
        ability4_cdd_rect = ogre.Rectangle()
        ability4_cdd_rect.left = ability3_cdd_rect.right
        ability4_cdd_rect.top = ability3_cdd_rect.top
        ability4_cdd_rect.right = ability4_cdd_rect.left + 64
        ability4_cdd_rect.bottom = ability4_cdd_rect.top + 64
        ability4_cooldown_display = gui.AbilityCooldownDisplay("UI/AbilityBar/Ability4", ability4_cdd_rect, 4, ability4_cooldown)
        ability4_cooldown_display.overlay.setMaterialName(ability4_icon_mat)
        
        # Add the gui elements to the element list.
        self.elements.append(ability1_cooldown_display)
        self.elements.append(ability2_cooldown_display)
        self.elements.append(ability3_cooldown_display)
        self.elements.append(ability4_cooldown_display)
        
        # Listen to player events (why isn't this the same as how
        # StatusBar listens to its events?):
        ability1_cooldown_display.set_player_listener(player)
        ability2_cooldown_display.set_player_listener(player)
        ability3_cooldown_display.set_player_listener(player)
        ability4_cooldown_display.set_player_listener(player)
        
    def update(self, dt):
        for element in self.elements:
            element.update(dt)
    
    def inject_mouse_press(self, id, x, y):
        for element in self.elements:
            if isinstance(element, gui.IClickable):
                element.inject_mouse_press(id, x, y)
    
    def inject_mouse_release(self, id, x, y):
        for element in self.elements:
            if isinstance(element, gui.IClickable):
                element.inject_mouse_release(id, x, y)
    
    def on_scores_changed(self, scores):
        slist = scores.items()
        slist.sort(key=lambda x: x[1])
        slist.reverse()
        
        first_name = self.playscene.players[slist[0][0]].name
        first_score = str(slist[0][1])
        
        if slist[0][0] == self.playscene.player.object_id:
            if len(slist) > 1:
                second_name = self.playscene.players[slist[1][0]].name
                second_score = str(slist[1][1])
            else:
                second_name, second_score = "", ""
        else:
            second_name = self.playscene.player.name
            second_score = str(self.playscene.player.score)
        
        self.qscores_1_name.text = "1. " + first_name
        self.qscores_1_score.text = first_score
        
        self.qscores_2_name.text = "2. " + second_name if len(second_name) > 0 else ""
        self.qscores_2_score.text = second_score


class PlayScene(ogre.FrameListener, ogre.WindowEventListener):
    """
    This class represents the game's main scene - the play scene. This class
    sets up the initial scene and acts as the main game loop (via
    frameStarted()).
    """

    def __init__(self, sceneManager, address, port):
        # Initialize the various listener classes we are a subclass from
        ogre.FrameListener.__init__(self)
        ogre.WindowEventListener.__init__(self)
        
        self.address = address
        self.port = port
        self.player_name = "Player1"
        self.is_round_active = False
        
        self.renderWindow = ogre.Root.getSingleton().getAutoCreatedWindow()
        self.sceneManager = sceneManager
        self.camera = self.sceneManager.getCamera("PrimaryCamera")
        self.cameraNode = self.sceneManager.getSceneNode("PrimaryCamera")
        
        self.viewport = self.camera.getViewport()
        
        self.player = None
        self.last_update = None
        self.scores = { }
        self.scores_changed = Event()
        self.nodes = { }
        self.players = { }
        
        # Set up the scene.
        self.setupScene()
        
        # Load sounds.
        self.loadSceneSounds()
        
        # Set up the GUI.
        self.gui = PlaySceneGUI(self)
        self.gui.element_selected += self.on_gui_element_selected
        
        # Show a welcome message.
        self.gui.message.notice("Tides of the Elements")
        
        # Load scene music
        audio.set_background_music("media/sounds/Dispatches+Of+Humanity.wav")
        
        # Set up the input devices.
        self.setupInput()

        # Set up initial window size.
        self.windowResized(self.renderWindow)

        # Set this to True when we get an event to exit the application
        self.quit = False

        # Listen for any events directed to the window manager's close button
        ogre.WindowEventUtilities.addWindowEventListener(self.renderWindow, self)
        
        # Begin scene music
        audio.play_background_music()

    def __del__ (self ):
        # Clean up OIS 
        self.inputManager.destroyInputObjectKeyboard(self.keyboard)
        self.inputManager.destroyInputObjectMouse(self.mouse)
        OIS.InputManager.destroyInputSystem(self.inputManager)
        self.inputManager = None

        ogre.WindowEventUtilities.removeWindowEventListener(self.renderWindow, self)
        self.windowClosed(self.renderWindow)
        
    def setupScene(self):
        ## Load the level.

        # Create the world.
        self.world = gamestate.world.World()
        
        # Load the scene into the Ogre world.
        # @todo: Remove .scene dependancy and move to external file (format?).
        sceneLoader = SceneLoader.DotSceneLoader("media/testtilescene.scene", self.sceneManager)
        sceneLoader.parseDotScene()
        
        # Load the scene into the game state.
        self.scene = gamestate.scenes.TestScene(self.world)
        
        # Create the client and set listeners.
        self.client = net.client.GameClient(self.world, self.address, self.port)
        self.client.connected += self.on_client_connected
        
        # Start the netclient and connect.
        self.client_thread = threading.Thread(target=self.client.go)
        self.client_thread.start()
        
        # Attach a handler to world.object_added and removed
        self.world.object_added += self.on_world_object_added
        self.world.object_removed += self.on_world_object_removed

        # Setup camera
        self.camera.nearClipDistance = 1
        self.camera.farClipDistance = 500
        self.camera.setProjectionType(ogre.PT_ORTHOGRAPHIC)

        # THIS SPECIFIES THE HEIGHT OF THE ORTHOGRAPHIC WINDOW
        # the width will be recalculated based on the aspect ratio
        # in ortho projection mode, decreasing the size of the window
        # is equivalent to zooming in, increasing is the equivalent of
        # zooming out.
        self.camera.setOrthoWindowHeight(200)

        # Setup camera node
        self.cameraNode.position = (0, 100, 100)
        self.cameraNode.pitch(ogre.Degree(-45))
        
    def loadSceneSounds(self):
        # Air Sounds
        audio.load_source("airshot",        "media/sounds/airshot.wav")
        audio.load_source("gustofwind",     "media/sounds/gustofwind.wav")
        audio.load_source("windwhisk",      "media/sounds/windwhisk.wav")
        audio.load_source("lightningbolt",  "media/sounds/lightningbolt.wav")
        
        # Earth Sounds
        audio.load_source("earthquake",     "media/sounds/earthquake.wav")
        audio.load_source("hook",           "media/sounds/hook.wav")
       
        # Fire Sounds
        audio.load_source("flamerush",      "media/sounds/flamerush.wav") 
        audio.load_source("lavasplash",     "media/sounds/lavasplash.wav")
        audio.load_source("ringoffire",     "media/sounds/ringoffire.wav")
        
        # Water Sounds
        audio.load_source("iceshot",        "media/sounds/iceshot.wav")
        audio.load_source("iceburst",       "media/sounds/iceburst.wav")
        audio.load_source("tidalwave",      "media/sounds/tidalwave.wav")
        audio.load_source("watergush",      "media/sounds/watergush.wav")
        
        # General Sounds
        audio.load_source("weaponswing",    "media/sounds/weaponswing.wav")
        audio.load_source("weaponswingmiss","media/sounds/weaponswingmiss.wav")
        audio.load_source("whiff",          "media/sounds/whiff.wav")
        audio.load_source("impact",         "media/sounds/impact.wav")
    
    def setupInput(self):
        # Create the inputManager using the supplied renderWindow
        windowHnd = self.renderWindow.getCustomAttributeInt("WINDOW")
        paramList = [("WINDOW", str(windowHnd)), \
                     ("w32_mouse", "DISCL_FOREGROUND"), \
                     ("w32_mouse", "DISCL_NONEXCLUSIVE"), \
                     ("w32_keyboard", "DISCL_FOREGROUND"), \
                     ("w32_keyboard", "DISCL_NONEXCLUSIVE"),]
                     # @todo: add mac/linux parameters
        self.inputManager = OIS.createPythonInputSystem(paramList)

        # Attempt to get the mouse/keyboard input device objects.
        try:
            self.mouse = self.inputManager.createInputObjectMouse(OIS.OISMouse, True)
            self.keyboard = self.inputManager.createInputObjectKeyboard(OIS.OISKeyboard, True)
        except Exception: # Unable to obtain mouse/keyboard input
            raise

        # Use an InputHandler object to handle the callback functions.
        self.inputHandler = InputHandler(self.mouse, self.keyboard, self)
        self.mouse.setEventCallback(self.inputHandler)
        self.keyboard.setEventCallback(self.inputHandler)

    def frameStarted(self, event):
        """ 
        Called before a frame is displayed, handles events
        (also those via callback functions, as you need to call capture()
        on the input objects)

        Returning False here exits the application (render loop stops)
        """
        
        dt = event.timeSinceLastFrame
        
        # Get buffered input from server and process it.
        while not self.client.input.empty():
            packet = self.client.input.get_nowait()
            self.process_packet(packet)

        # Capture any buffered events (and fire any callbacks).
        self.inputHandler.capture()
        
        # Update our UI Elements
        self.gui.update(dt)
        
        # Update the game state world.
        self.world.update(dt)
        
        # Update the audio module so it can throw its events
        audio.update(dt)
        
        # Send an PlayerUpdate packet to the server if appropriate.
        self._send_update()
        
        # Send buffered output to server.
        reactor.callFromThread(self.client.send)
        
        # Add time to animations.
        for object_id in self.nodes:
            self.nodes[object_id].animations_addtime(dt)

        # Neatly close our FrameListener if our renderWindow has been shut down
        # or we are quitting.
        if self.renderWindow.isClosed() or self.quit:
            return False
        
        return True
        
    ## Net event callbacks & helpers
    def _send_update(self, check_time=True):
        """ Sends a PlayerUpdate packet to the server if appropriate. """
        if self.player is None or self.player.is_dead:
            return

        update = self._get_update()
        if self.last_update is not None:
            update_time, last_update = self.last_update
            
            # Don't send if we've sent in the last 0.1s.
            if check_time and update_time + 0.05 > self.world.time:
                return
                
            # Don't send if info hasn't changed since the last update.
            if last_update.x == update.x and last_update.z == update.z and \
                last_update.rotation == update.rotation and \
                last_update.move_speed == update.move_speed and \
                last_update.move_direction == update.move_direction:
                return
        
        print "Sending player update to server."
        self.client.output.put_nowait(update)
        self.last_update = (self.world.time, update)
    
    def _get_update(self):
        """ Returns a PlayerUpdate packet based on the current player state. """
        update = packets.PlayerUpdate()
        update.x, update.z = self.player.position
        update.rotation = self.player.rotation
        if self.player.is_moving:
            update.move_speed = self.player.move_speed
            update.move_direction = self.player.move_direction
        else:
            update.move_speed = 0
            update.move_direction = 0
        return update

    def process_packet(self, packet):
        ptype = type(packet)
        print "Processing packet=%s: %s from server." % (packet.id, ptype.__name__)
        
        # JoinResponse
        if ptype is packets.JoinResponse:
            # @todo: handle deny
            # Add a player to the world and set it as our active player.
            print "Creating player in world with id=%s." % packet.player_id
            self.player = gamestate.objects.Player(self.world)
            self.player.object_id = packet.player_id
            self.player.is_dead = True
            self.player.name = self.player_name
            self.players[self.player.object_id] = self.player
            self.scores[self.player.object_id] = 0
            self.scores_changed(self.scores)
            
            # Listen to the player's position change event so we can mvoe the
            # camera with the player.
            self.player.position_changed += self.on_player_position_changed
            self.player.element_changed += self.on_player_element_changed
            self.player.ability_requested += self.on_player_ability_requested
            self.player.is_dead_changed += self.on_player_is_dead_changed
            
            self.gui.element_selection.show()
            
        # SpawnResponse
        if ptype is packets.SpawnResponse:
            self.player.change_element(packet.element_type)
            self.player.position = (packet.x, packet.z)
            self.world.add_object(self.player, self.player.object_id)
            self.gui.setup_player_gui(self.player)
            self.is_round_active = True
        
        # ObjectInit
        elif ptype is packets.ObjectInit:
            if packet.object_type == "player":
                object = gamestate.objects.Player(self.world)
                object.name = packet.name
                object.change_element(packet.element_type)
                # @todo: implement owner_id, ttl
                self.world.add_object(object, packet.object_id)
                self.players[packet.object_id] = object
                if not self.scores.has_key(packet.object_id):
                    self.scores[packet.object_id] = 0
                    self.scores_changed(self.scores)
            else:
                raise Exception("Invalid object_type")

        # ObjectUpdate
        elif ptype is packets.ObjectUpdate:
            if not self.world.objects_hash.has_key(packet.object_id):
                # We don't know about this object yet, so we can't update it.
                print "Received ObjectUpdate for unnkown object id=%s" % packet.object_id
            else:
                object = self.world.objects_hash[packet.object_id]
                print "Updating object id=%s." % object.object_id
                print "Update force vector: (%.2f, %.2f)" % (packet.force_x, packet.force_z)
                if packet.forced:
                    object.position = (packet.x, packet.z)
                    object.rotation = packet.rotation
                    object.move_speed = packet.move_speed
                    object.move_direction = packet.move_direction
                    object.force_vector = (packet.force_x, packet.force_z)
                    object.is_dead = packet.is_dead
                else:
                    object.rotation = packet.rotation
                    object.force_vector = (packet.force_x, packet.force_z)
                    if object == self.player:
                        # This is an update about the player. We want to deal with
                        # this case differently so we don't overwrite some client
                        # states such as position.
                        object.is_dead = packet.is_dead
                        if packet.move_speed > 0:
                            object.move_speed = packet.move_speed
                        diff_vector = ogre.Vector2(packet.x - object.position[0],
                                                   packet.z - object.position[1])
                        if diff_vector.squaredLength() > 500:
                            # If the server tells us we're far from where we think
                            # we are, then warp to the server's location.
                            object.position = (packet.x, packet.z)
                    else:
                        # This is an update for another game object.
                        if packet.move_speed > 0:
                            object.is_moving = True
                            object.move_direction = packet.move_direction
                            object.move_speed = packet.move_speed
                            
                            diff_vector = ogre.Vector3(packet.x - object.position[0], 0, packet.z - object.position[1])
                            if diff_vector.squaredLength() > 500:
                                # If the server's location is far from where we
                                # thinkt his player is, then, then don't smooth.
                                object.position = (packet.x, packet.z)
                                object.rotation = packet.rotation
                            else:
                                # Smooth the difference in locations.
                                move_vector = ogre.Vector3(packet.move_speed * math.cos(packet.rotation + packet.move_direction), 0,
                                                           packet.move_speed * math.sin(packet.rotation + packet.move_direction))
                                resultant = diff_vector + move_vector
                                angle = math.atan2(resultant.z, resultant.x)
                                object.rotation = angle - packet.move_direction
                        else:
                            object.position = (packet.x, packet.z)
                            object.is_moving = False
                    if object.type == "player":
                        if object.is_dead:
                            print 'setting player to dead'
                        object.is_dead = packet.is_dead
        
        # ObjectStatusUpdate
        elif ptype is packets.ObjectStatusUpdate:
            if self.world.objects_hash.has_key(packet.object_id):
                object = self.world.objects_hash[packet.object_id]
                object.health = packet.health
                object.power = packet.power
            else:
                print "Ignoring ObjectStatusUpdate because player is not in world."
        
        # ObjectRemove
        elif ptype is packets.ObjectRemove:
            object = self.world.objects_hash[packet.object_id]
            self.world.remove_object(object)
        
        # AbilityUsed
        elif ptype is packets.AbilityUsed:
            print "Using ability id=%s on player_id=%s" % (packet.object_id, packet.ability_id)
            player = self.world.objects_hash[packet.object_id]
            player.use_ability(packet.ability_id)
            
        # Message
        elif ptype is packets.Message:
            if packet.type == "error": self.gui.message.error(packet.message)
            elif packet.type == "notice": self.gui.message.notice(packet.message)
            elif packet.type == "death": self.gui.message.death(packet.message)
            elif packet.type == "success": self.gui.message.success(packet.message)
            elif packet.type == "system": self.gui.message.system(packet.message)
            else: self.gui.message.system(packet.message)
            
        # ScoreUpdate
        elif ptype is packets.ScoreUpdate:
            # @todo: Delete these at some point.
            player = self.players[packet.player_id]
            player.score = packet.score
            self.scores[player.object_id] = player.score
            self.scores_changed(self.scores)
            
        # RoundEnd
        elif ptype is packets.RoundEnd:
            self.is_round_active = False
            self.player.is_dead = True
            self.gui.element_selection.hide()
            
        # RoundStart
        elif ptype is packets.RoundStart:
            self.is_round_active = True
            self.gui.element_selection.show()
            
        # ClientDisconnect
        elif ptype is packets.ClientDisconnect:
            if self.nodes.has_key(packet.player_id):
                node = self.nodes[packet.player_id]
                del self.nodes[packet.player_id]
                node.destroy()
            if self.players.has_key(packet.player_id):
                del self.players[packet.player_id]
            
    
    def on_client_connected(self):
        packet = packets.JoinRequest()
        # @todo: Get player_name from somewhere.
        packet.player_name = self.player_name
        self.client.output.put_nowait(packet)
        
    ## Game event callbacks
    def on_world_object_added(self, object):
        if object.type == "player":
            if self.nodes.has_key(object.object_id):
                # We already have a node for this game object, but it may be
                # represented by another object in memory.
                node = self.nodes[object.object_id]
                if node.object == object:
                    # If it's the same object, we don't need a new node.
                    if node.corpse is not None:
                        node.corpse.destroy()
                        node.corpse = None
                    return
                # Otherwise, destroy the current node and create a new one.
                node.destroy()
            node = nodes.PlayerNode(self.sceneManager, object, "ninja.mesh")
            node.set_scale(.1)
            node.rotation -= math.pi/2
            self.nodes[object.object_id] = node
            
    def on_world_object_removed(self, object):
        # @todo: Remove nodes at some point for players no longer here.
        pass
        
    def on_player_position_changed(self, mobileObject, position):
        self.cameraNode.position = (position[0], 100, position[1] + 100)
        
    def on_player_element_changed(self, player):
        # Recreate the ability bar GUI.
        self.gui.setup_ability_bar(self.player)
        
    def on_player_ability_requested(self, player, ability_id):
        ar = packets.AbilityRequest()
        ar.object_id = player.object_id
        ar.ability_id = ability_id
        # Send a PlayerUpdate so the server has the most recent information
        # about us when using the ability.
        self._send_update(check_time=False)
        self.client.output.put_nowait(ar)
        
    def on_player_is_dead_changed(self, player):
        if self.player.is_dead and self.is_round_active:
            self.gui.element_selection.show()
        
        
     # Is this being used anywhere? @todo: remove if not, uncomment if exception
#    def on_static_node_expired(self, static_node):
#        print static_node.unique_scene_node_name
#        self.sceneManager.destroySceneNode(static_node.node_name)

    ## GUI event handlers
    def on_gui_element_selected(self, element_type):
        print "selected:", element_type
        request = packets.SpawnRequest()
        request.element_type = element_type
        self.client.output.put_nowait(request)
        self.gui.element_selection.hide()

    ## Window event listener callbacks
    def windowResized(self, renderWindow):
        self.mouse.getMouseState().width = renderWindow.width
        self.mouse.getMouseState().height = renderWindow.height
        vp = self.viewport
        self.camera.aspectRatio = vp.actualWidth / vp.actualHeight
        # @todo: Scale the image so viewable area remains the same.

    def windowClosed(self, renderWindow):
        # Only close for window that created OIS
        if(renderWindow == self.renderWindow):
            del self