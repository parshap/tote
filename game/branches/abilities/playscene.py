from __future__ import division
import gc

# Import OGRE-specific (and other UI-Client) external packages and modules.
import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS

# Import internal packages and modules modules.
import gamestate
import SceneLoader
from inputhandler import InputHandler
import nodes
import gui

# Import other python modules
import math
from xml.dom import minidom, Node

class PlayScene(ogre.FrameListener, ogre.WindowEventListener):
    """
    This class represents the game's main scene - the play scene. This class
    sets up the initial scene and acts as the main game loop (via
    frameStarted()).
    """

    def __init__(self, sceneManager):
        # Initialize the various listener classes we are a subclass from
        ogre.FrameListener.__init__(self)
        ogre.WindowEventListener.__init__(self)

        
        self.renderWindow = ogre.Root.getSingleton().getAutoCreatedWindow()
        self.sceneManager = sceneManager
        self.camera = self.sceneManager.getCamera("PrimaryCamera")
        self.cameraNode = self.sceneManager.getSceneNode("PrimaryCamera")
        
        self.viewport = self.camera.getViewport()
        
        # Create an empty list of nodes
        self.nodes = []
        
        # Create an empty list of GUI elements.
        self.gui_elements = [] 
        
        # Set up the overlay for the GUI.
        self.setupOverlay()
        
        # Set up the scene.
        self.setupScene()
        
        # Set up the GUI.
        self.setupGUI()
        
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
        self.inputHandler = InputHandler(mouse=self.mouse, keyboard=self.keyboard,
                                         scene=self, player=self.player)
        self.mouse.setEventCallback(self.inputHandler)
        self.keyboard.setEventCallback(self.inputHandler)

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
        # @todo: Remove .scene dependancy and move to external file (format?).
        
        # Load some data from the .scene file
        sceneLoader = SceneLoader.DotSceneLoader("media/testtilescene.scene", self.sceneManager)
        sceneLoader.parseDotScene()
        
        # Create the world.
        self.world = gamestate.world.World()
        
        # Attach a handler to world.object_added
        self.world.object_added += self.on_world_object_added
        
        # Add a player to the world and set it as our active player.
        self.player = gamestate.objects.Player(self.world)
        self.world.add_object(self.player)
        
        # Add stationary NPC ninja...
        npc = gamestate.objects.Player(self.world)
        self.world.add_object(npc)
        npc.position = (128, 128)
        npc.isPassable = False
        
        # Add boundary lines for map walls.       
        self.setup_level_boundaries("media/levelbounds.bounds")
        
        # Listen to player events.
        self.player.position_changed += self.on_player_position_changed
        self.player.element_changed += self.on_player_element_changed

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
        
        # Create an FPS label.
        fpslabel = gui.FPSLabel("UI/FPSLabel")
        self.gui_elements.append(fpslabel)
        
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
        
    def setup_level_boundaries(self, filepath):
        """
        Takes an xml-style file that specifies all of the level's static boundinglinesegments, and creates those
        bounds in the world.
        """
        xml_data = minidom.parse(filepath)
        docRoot = xml_data.getElementsByTagName('segments')[0].childNodes
        for segmentNode in docRoot:
            if segmentNode.nodeType == Node.ELEMENT_NODE and segmentNode.nodeName == 'segment':
                point1_data = self.getXMLNode(segmentNode, "point1").attributes
                point2_data = self.getXMLNode(segmentNode, "point2").attributes
                normal_data = self.getXMLNode(segmentNode, "normal").attributes
                
                point1 = (float(point1_data["x"].nodeValue),  -float(point1_data["z"].nodeValue))
                point2 = (float(point2_data["x"].nodeValue),  -float(point2_data["z"].nodeValue))
                normal = (float(normal_data["x"].nodeValue),  float(normal_data["z"].nodeValue))
                
                boundary_wall = gamestate.objects.GameObject(self.world)
                boundary_wall.isPassable = False
                boundary_wall.position = point1
                
                boundary_wall.bounding_shape = gamestate.collision.BoundingLineSegment(point1, point2, normal)
                
                self.world.add_object(boundary_wall)
                
    def getXMLNode(self, base, name):
        """
        This function basically doubles as both a test for element 
        existence and a getter for that element node... used with setup_level_boundaries()
        """
        if base.hasChildNodes:
            baseChildNodes = base.childNodes
            
            for node in baseChildNodes:
                if node.nodeType == Node.ELEMENT_NODE and node.nodeName == name:
                    return node
            
            return False

    def frameStarted(self, event):
        """ 
        Called before a frame is displayed, handles events
        (also those via callback functions, as you need to call capture()
        on the input objects)

        Returning False here exits the application (render loop stops)
        """
        
        dt = event.timeSinceLastFrame
        
        # Capture any buffered events (and fire any callbacks).
        self.inputHandler.capture()
        
        # Update our UI Elements
        for element in self.gui_elements:
            element.update(dt)
        
        # Update the game state world.
        self.world.update(dt)
        
        # Add time to animations.
        for node in self.nodes:
            node.animations_addtime(dt)

        # Neatly close our FrameListener if our renderWindow has been shut down
        # or we are quitting.
        if self.renderWindow.isClosed() or self.quit:
            return False
        
        return True
 
    ## Game event callbacks
    def on_world_object_added(self, gameObject):
        if gameObject.type == "player":
            newPlayerNode = nodes.PlayerNode(self.sceneManager, gameObject, "ninja.mesh")
            newPlayerNode.set_scale(.1)
            self.nodes.append(newPlayerNode)
        
    def on_player_position_changed(self, mobileObject, position):
        self.cameraNode.position = (position[0], 100, position[1] + 100)
        
    def on_player_element_changed(self, player):
        # Remove all current gui.AbilityCooldownDisplay from the current gui.
        print len(self.gui_elements)
        self.gui_elements = [element for element in self.gui_elements
            if type(element) is not gui.AbilityCooldownDisplay]
        print len(self.gui_elements)
        # Recreate the ability bar GUI.
        self.setupGUIAbilityBar()
        print len(self.gui_elements)
        
    def on_static_node_expired(self, static_node):
        print static_node.unique_scene_node_name
        self.sceneManager.destroySceneNode(static_node.unique_scene_node_name)

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