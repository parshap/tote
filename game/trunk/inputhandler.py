import ogre.io.OIS as OIS
import ogre.gui.CEGUI as CEGUI

class InputHandler(OIS.MouseListener, OIS.KeyListener):
    """
    This class handles all user device input event handlers with the defined
    callback functions. This class modifies the game state directly with a
    reference to a player object that represents the current playing player.
    This class also has a reference to the scene object to get information from
    and make changes to the camera, window, and viewport.
    """
    def __init__(self, mouse, keyboard, scene):
        OIS.MouseListener.__init__(self)
        OIS.KeyListener.__init__(self)
        self.mouse = mouse
        self.keyboard = keyboard
        self.scene = scene

    def capture(self):
        self.mouse.capture()
        self.keyboard.capture()

    def mouseMoved(self, event):
        # Pass the location of the mouse pointer over to CEGUI
        CEGUI.System.getSingleton().injectMouseMove(event.get_state().X.rel, event.get_state().Y.rel)
        return True

    def mousePressed(self, event, id):
        # Handle any CEGUI mouseButton events
        CEGUI.System.getSingleton().injectMouseButtonDown(self.convertOISButtonToCEGUI(id))
        return True

    def mouseReleased(self, event, id):
        # Handle any CEGUI mouseButton events
        CEGUI.System.getSingleton().injectMouseButtonUp(self.convertOISButtonToCEGUI(id))
        return True

    def convertOISButtonToCEGUI(self, oisID):
        """ Converts an OIS mouse button ID to a CEGUI mouse button ID """
        if oisID == OIS.MB_Left:
            return CEGUI.LeftButton
        elif oisID == OIS.MB_Right:
            return CEGUI.RightButton
        elif oisID == OIS.MB_Middle:
            return CEGUI.MiddleButton
        else:
            return CEGUI.LeftButton

    def keyPressed(self, event):
        # Quit the application if we hit the escape button
        if event.key == OIS.KC_ESCAPE:
            self.scene.quit = True
        return True

    def keyReleased(self, event):
        return True