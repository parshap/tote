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
import math

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
        
        # Create an empty list of nodes
        self.nodes = []
        
        # Set up the scene.
        self.setupScene()

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
        # @todo: move this out of here!
        
        # north wall
        boundary1 = gamestate.objects.GameObject(self.world)
        boundary1.position = (-640, -640)
        boundary1.isPassable = False
        boundary1.bounding_shape = gamestate.collision.BoundingLineSegment((-640, -640),
                                                                           (640, -640),
                                                                           (0, 1))
        # south wall
        boundary2 = gamestate.objects.GameObject(self.world)
        boundary2.position = (-640, 640)
        boundary2.isPassable = False
        boundary2.bounding_shape = gamestate.collision.BoundingLineSegment((-640, 640),
                                                                           (640, 640),
                                                                           (0, -1))
        # east wall
        boundary3 = gamestate.objects.GameObject(self.world)
        boundary3.position = (640, -640)
        boundary3.isPassable = False
        boundary3.bounding_shape = gamestate.collision.BoundingLineSegment((640, -640),
                                                                           (640, 640),
                                                                           (-1, 0))
        # west wall
        boundary4 = gamestate.objects.GameObject(self.world)
        boundary4.position = (-640, -640)
        boundary4.isPassable = False
        boundary4.bounding_shape = gamestate.collision.BoundingLineSegment((-640, -640),
                                                                           (-640, 640),
                                                                           (1, 0))

        self.world.add_object(boundary1)
        self.world.add_object(boundary2)
        self.world.add_object(boundary3)
        self.world.add_object(boundary4)
        
        # Listen to the player's position change event so we can mvoe the
        # camera with the player.
        self.player.position_changed += self.on_player_position_changed

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
        
    def on_static_node_expired(self, static_node):
        print static_node.unique_scene_node_name
        self.sceneManager.destroySceneNode(static_node.unique_scene_node_name)

    ## Window event listener callbacks

    def windowResized(self, renderWindow):
        self.mouse.getMouseState().width = renderWindow.width
        self.mouse.getMouseState().height = renderWindow.height
        vp = self.camera.getViewport()
        self.camera.aspectRatio = vp.actualWidth / vp.actualHeight
        # @todo: Scale the image so viewable area remains the same.

    def windowClosed(self, renderWindow):
        # Only close for window that created OIS
        if(renderWindow == self.renderWindow):
            del self