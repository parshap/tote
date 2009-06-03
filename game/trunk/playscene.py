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
import nodes
import gui

# Import other python modules
import math

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
        
        self.renderWindow = ogre.Root.getSingleton().getAutoCreatedWindow()
        self.sceneManager = sceneManager
        self.camera = self.sceneManager.getCamera("PrimaryCamera")
        self.cameraNode = self.sceneManager.getSceneNode("PrimaryCamera")
        
        self.viewport = self.camera.getViewport()
        
        # Create an empty list of nodes
        self.nodes = { }
        
        # Create an empty list of GUI elements.
        self.gui_elements = [] 
        
        # Set up the overlay for the GUI.
        self.setupOverlay()
        
        # Set up the scene.
        self.setupScene()
        
        # Init attributes.
        self.player = None
        self.last_update = None

        # Set up the GUI.
        self.setupGUI()
        
        # Show a welcome message.
        self.message.notice("Tides of the Elements")
        
        # Set up the input devices.
        self.setupInput()

        # Set up initial window size.
        self.windowResized(self.renderWindow)

        # Set this to True when we get an event to exit the application
        self.quit = False

        # Listen for any events directed to the window manager's close button
        ogre.WindowEventUtilities.addWindowEventListener(self.renderWindow, self)

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
        
    def setupGUI(self):
        # Create an FPS label.
        fpslabel = gui.FPSLabel("UI/FPSLabel")
        self.gui_elements.append(fpslabel)
        
        # Create the message label.
        self.message = gui.Message("UI/MessageLabel")
        self.gui_elements.append(self.message)
        
    def setupGUIPlayer(self):
        """ Sets up player-related GUI that requires a player before setting up. """
        # Set up health and power bars
        health_bar_rect = ogre.Rectangle()
        health_bar_rect.left = self.viewport.actualWidth / 2 - 128
        health_bar_rect.top = self.viewport.actualHeight - 84
        health_bar_rect.right = health_bar_rect.left + 256
        health_bar_rect.bottom = health_bar_rect.top + 10
        health_bar = gui.StatusBar("UI/StatusBars/Health", health_bar_rect, self.player.max_health)
        health_bar.name = "Health"
        
        power_bar_rect = ogre.Rectangle()
        power_bar_rect.left = health_bar_rect.left
        power_bar_rect.top = health_bar_rect.bottom
        power_bar_rect.right = health_bar_rect.right
        power_bar_rect.bottom = power_bar_rect.top + 10
        power_bar = gui.StatusBar("UI/StatusBars/Power", power_bar_rect, self.player.max_power)
        power_bar.name = "Power"
        
        # Add the gui elements to the element list.
        self.gui_elements.append(health_bar)
        self.gui_elements.append(power_bar)
        
        # Add listeners to player's health and power changed events.
        self.player.health_changed += health_bar.on_value_changed
        self.player.power_changed += power_bar.on_value_changed
        
        # Set up the ability bar.
        self.setupGUIAbilityBar()
    
    def setupGUIAbilityBar(self):
        player = self.player
        
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
        self.gui_elements.append(ability1_cooldown_display)
        self.gui_elements.append(ability2_cooldown_display)
        self.gui_elements.append(ability3_cooldown_display)
        self.gui_elements.append(ability4_cooldown_display)
        
        # Listen to player events (why isn't this the same as how
        # StatusBar listens to its events?):
        ability1_cooldown_display.set_player_listener(self.player)
        ability2_cooldown_display.set_player_listener(self.player)
        ability3_cooldown_display.set_player_listener(self.player)
        ability4_cooldown_display.set_player_listener(self.player)
        
    def setupOverlay(self):
        pOver = ogre.OverlayManager.getSingleton().getByName("UI")
        pOver.show()
        
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
        for element in self.gui_elements:
            element.update(dt)
        
        # Update the game state world.
        self.world.update(dt)
        
        # Send an PlayerUpdate packet to the server if appropriate.
        self._send_update()
        
        # Send buffered output to server.
        reactor.callFromThread(self.client.send)
        
        # Add time to animations.
        for object in self.nodes:
            self.nodes[object].animations_addtime(dt)

        # Neatly close our FrameListener if our renderWindow has been shut down
        # or we are quitting.
        if self.renderWindow.isClosed() or self.quit:
            return False
        
        return True
        
    ## Net event callbacks & helpers
    def _send_update(self, check_time=True):
        """ Sends a PlayerUpdate packet to the server if appropriate. """
        if self.player is None:
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
            self.world.add_object(self.player, packet.player_id)
            
            # Set up the player's GUI.
            self.setupGUIPlayer()
            
            # Listen to the player's position change event so we can mvoe the
            # camera with the player.
            self.player.position_changed += self.on_player_position_changed
            self.player.element_changed += self.on_player_element_changed
            self.player.ability_requested += self.on_player_ability_requested
        
        # ObjectInit
        elif ptype is packets.ObjectInit:
            if packet.object_type == "player":
                object = gamestate.objects.Player(self.world)
            else:
                raise Exception("Invalid object_type")
            # @todo: implement name, owner_id, ttl

            self.world.add_object(object, packet.object_id)
        
        # ObjectUpdate
        elif ptype is packets.ObjectUpdate:
            if not self.world.objects_hash.has_key(packet.object_id):
                return
            object = self.world.objects_hash[packet.object_id]
            print "Updating object id=%s." % object.object_id
            object.rotation = packet.rotation
            try:
                if packet.move_speed > 0:
                    diff_vector = ogre.Vector3(packet.x - object.position[0], 0, packet.z - object.position[1])
                    move_vector = ogre.Vector3(packet.move_speed * math.cos(packet.rotation), 0,
                                               packet.move_speed * math.sin(packet.rotation))
                    resultant = diff_vector + move_vector
                    angle = math.atan2(resultant.z, resultant.x)
                    object.move_speed = packet.move_speed
                    object.rotation = angle
                    object.move_direction = 0
                    object.is_moving = True
                else:
                    object.position = (packet.x, packet.z)
                    object.is_moving = False
            except:
                object.position = (packet.x, packet.z)
        
        # AbilityUsed
        elif ptype is packets.AbilityUsed:
            player = self.world.objects_hash[packet.object_id]
            player.use_ability(packet.ability_id)
    
    def on_client_connected(self):
        packet = packets.JoinRequest()
        # @todo: Get player_name from somewhere.
        packet.player_name = "Player1"
        self.client.output.put_nowait(packet)
        
    ## Game event callbacks
    def on_world_object_added(self, object):
        if object.type == "player":
            node = nodes.PlayerNode(self.sceneManager, object, "ninja.mesh")
            node.set_scale(.1)
            self.nodes[object] = node
            
    def on_world_object_removed(self, object):
        if object.type == "player":
            node = self.nodes[object]
            node.getParent().removeAndDestroyChild(node.node_name)
            del self.nodes[object]
        
    def on_player_position_changed(self, mobileObject, position):
        self.cameraNode.position = (position[0], 100, position[1] + 100)
        
    def on_player_element_changed(self, player):
        # Remove all current gui.AbilityCooldownDisplay from the current gui.
        self.gui_elements = [element for element in self.gui_elements
            if type(element) is not gui.AbilityCooldownDisplay]
        # Recreate the ability bar GUI.
        self.setupGUIAbilityBar()
        
    def on_player_ability_requested(self, player, ability_id):
        ar = packets.AbilityRequest()
        ar.object_id = player.object_id
        ar.ability_id = ability_id
        # Send a PlayerUpdate so the server has the most recent information
        # about us when using the ability.
        self._send_update(check_time=False)
        self.client.output.put_nowait(ar)
        
     # Is this being used anywhere? @todo: remove if not, uncomment if exception
#    def on_static_node_expired(self, static_node):
#        print static_node.unique_scene_node_name
#        self.sceneManager.destroySceneNode(static_node.node_name)

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