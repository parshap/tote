from __future__ import division

# Import OGRE-specific (and other UI-Client) external packages and modules.
import ogre.renderer.OGRE as ogre
import ogre.gui.CEGUI as CEGUI
from twisted.internet import reactor

# Import other external packages and modules.
import threading, time

# Import internal packages and modules modules.
from playscene import PlayScene
import gamestate, net
from net import packets

class ClientApplication(object):

    app_title = "MyApplication"

    def go(self):
        # See Basic Tutorial 6 for details
        self.createRoot()
        self.defineResources()
        self.setupRenderSystem()
        self.createRenderWindow()
        self.initializeResourceGroups()
        self.setupScene()
        self.createFrameListener()
        self.setupCEGUI()
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
        self.playScene = PlayScene(self.sceneManager)
        self.root.addFrameListener(self.playScene)

    def setupCEGUI(self):
        sceneManager = self.sceneManager

        # CEGUI
        self.renderer = CEGUI.OgreCEGUIRenderer(self.renderWindow, ogre.RENDER_QUEUE_OVERLAY, False, 3000, sceneManager)
        self.system = CEGUI.System(self.renderer)

        # CEGUI.SchemeManager.getSingleton().loadScheme("TaharezLookSkin.scheme")
        # self.system.setDefaultMouseCursor("TaharezLook", "MouseArrow")
        # self.system.setDefaultFont("BlueHighway-12")

        # Uncomment the following to read in a CEGUI sheet (from CELayoutEditor)
        # 
        # self.mainSheet = CEGUI.WindowManager.getSingleton().loadWindowLayout("myapplication.layout")
        # self.system.setGUISheet(self.mainSheet)

    def startRenderLoop(self):
        self.root.startRendering()

    def cleanUp(self):
        # @todo: move this somewhere else
        self.playScene.client.stop()
        pass


class ServerApplication(object):
    def __init__(self, port=8981):
        self.port = port
        
    def go(self):
        self.world = gamestate.world.World()
        self.scene = gamestate.scenes.TestScene(self.world)
        
        self.server = net.server.GameServer(self.world, self.port)
        self.server_thread = threading.Thread(target=self.server.go)
        self.server_thread.start()
        
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
        # Get buffered input from clients and process it.
        while not self.server.input.empty():
            (client, packet) = self.server.input.get_nowait()
            self.process_packet(client, packet)
            
        # Send buffered output to clients.
        reactor.callFromThread(self.server.send)
        
        # Update the game state world.
        self.world.update(dt)
        
        # Sleep some if we're updating too fast.
        extra = 0.01 - dt
        if extra >= 0.001:
            time.sleep(extra)
    
    def process_packet(self, client, packet):
        ptype = type(packet)
        print "Processing packet=%s: %s from client=%s." % (packet.id, ptype.__name__, client.client_id)
        
        if ptype is packets.JoinRequest:
            # @todo: deny conditions
            response = packets.JoinResponse()
            response.player_id = 1
            self.server.output.put_nowait((client, response))