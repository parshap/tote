import ogre.renderer.OGRE as ogre
import ogre.io.OIS as OIS
import ogre.gui.CEGUI as CEGUI
import SceneLoader
 
class ExitListener(ogre.FrameListener):
 
    def __init__(self, keyboard):
        ogre.FrameListener.__init__(self)
        self.keyboard = keyboard
 
    def frameStarted(self, evt):
        self.keyboard.capture()
        return not self.keyboard.isKeyDown(OIS.KC_ESCAPE)
 
class Application(object):
 
    def go(self):
        self.createRoot()
        self.defineResources()
        self.setupRenderSystem()
        self.createRenderWindow()
        self.initializeResourceGroups()
        self.setupScene()
        self.setupInputSystem()
        self.setupCEGUI()
        self.createFrameListener()
        self.startRenderLoop()
        self.cleanUp()
 
    def createRoot(self):
        self.root = ogre.Root()
 
    def defineResources(self):
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
        if not self.root.showConfigDialog(): # not self.root.restoreConfig() and
           raise Exception("User canceled the config dialog! -> Application.setupRenderSystem()")

 
    def createRenderWindow(self):
        self.root.initialise(True, "Tides of the Elements Demo - Lava Map")
 
    def initializeResourceGroups(self):
        ogre.TextureManager.getSingleton().setDefaultNumMipmaps(5)
        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()

 
    def setupScene(self):
        # LOAD SCENE HERE
        sceneManager = self.root.createSceneManager(ogre.ST_GENERIC, "Default SceneManager")
        sceneLoader = SceneLoader.DotSceneLoader("testtilescene.scene", sceneManager)
        sceneLoader.parseDotScene()
        
		#setup camera
		playerCamera = sceneManager.createCamera("PlayerCamera1")
        playerCamera.nearClipDistance = 1
        playerCamera.farClipDistance = 500
        playerCamera.setProjectionType(ogre.PT_ORTHOGRAPHIC)
		
		# THIS SPECIFIES THE HEIGHT OF THE ORTHOGRAPHIC WINDOW
		# the width will be recalculated based on the aspect ratio
		# in ortho projection mode, decreasing the size of the window
		# is equivalent to zooming in, increasing is the equivalent of
		# zooming out
        playerCamera.setOrthoWindowHeight(200)
        
        # setup camera node
        cameraNode = sceneManager.getRootSceneNode().createChildSceneNode('cameraNode1')
        cameraNode.position = (0, 1, 1)
        cameraNode.pitch(ogre.Degree(-45))
        cameraNode.attachObject(playerCamera)
        
        #setup viewport
        vp = self.root.getAutoCreatedWindow().addViewport(playerCamera)
        vp.backGroundColor = (0, 0, 1)
        playerCamera.aspectRatio = float (vp.actualWidth) / float (vp.actualHeight)

 
    def setupInputSystem(self):
        windowHandle = 0
        renderWindow = self.root.getAutoCreatedWindow()
        windowHandle = renderWindow.getCustomAttributeInt("WINDOW")
        paramList = [("WINDOW", str(windowHandle))]
        self.inputManager = OIS.createPythonInputSystem(paramList)
        try:
           self.keyboard = self.inputManager.createInputObjectKeyboard(OIS.OISKeyboard, False)
           self.mouse = self.inputManager.createInputObjectMouse(OIS.OISMouse, False)
           # self.joystick = self.inputManager.createInputObjectJoyStick(OIS.OISJoyStick, False)
        except Exception, e:
           raise e


 
    def setupCEGUI(self):
        sceneManager = self.root.getSceneManager("Default SceneManager")
        renderWindow = self.root.getAutoCreatedWindow()
       
        # CEGUI setup
        self.renderer = CEGUI.OgreCEGUIRenderer(renderWindow, ogre.RENDER_QUEUE_OVERLAY, False, 3000, sceneManager)
        self.system = CEGUI.System(self.renderer)

 
    def createFrameListener(self):
        self.exitListener = ExitListener(self.keyboard)
        self.root.addFrameListener(self.exitListener)

 
    def startRenderLoop(self):
        self.root.startRendering()
 
    def cleanUp(self):
        self.inputManager.destroyInputObjectKeyboard(self.keyboard)
        # self.inputManager.destroyInputObjectMouse(self.mouse)
        # self.inputManager.destroyInputObjectJoyStick(self.joystick)
        OIS.InputManager.destroyInputSystem(self.inputManager)
        self.inputManager = None
        
        del self.renderer
        del self.system
        
        del self.exitListener
        del self.root


 
 
if __name__ == '__main__':
    try:
        ta = Application()
        ta.go()
    except ogre.OgreException, e:
        print e