from __future__ import division

import ogre.io.OIS as OIS
import ogre.gui.CEGUI as CEGUI

import math

KEYBOARD_CONTROLS = {

}

MOUSE_CONTROLS = {
    # The player will face towards the mouse cursor while this button is
    # pressed.
    "FACE": OIS.MB_Right,
    
    # The player will move forward while this button is pressed.
    "MOUSEMOVE": OIS.MB_Right,
}

class InputHandler(OIS.MouseListener, OIS.KeyListener):
    """
    This class handles all user device input event handlers with the defined
    callback functions. This class modifies the game state directly with a
    reference to a player object that represents the current playing player.
    This class also has a reference to the scene object to get information from
    and make changes to the camera, window, and viewport.
    
    The *Pressed() and *Released() event handlers should handle state changes
    that occur only on the pressed and released events, whereas process()
    should handle state changes that occur continuously while the key is kept
    pressed down.
    """
    
    def __init__(self, mouse, keyboard, scene, player):
        OIS.MouseListener.__init__(self)
        OIS.KeyListener.__init__(self)
        self.mouse = mouse
        self.keyboard = keyboard
        self.scene = scene
        self.viewport = vp = self.scene.camera.getViewport()
        self.player = player
        
    def capture(self):
        self.mouse.capture()
        self.keyboard.capture()
        self.process()
        
    def process(self):
        mouseState = self.mouse.getMouseState()
        
        if mouseState.buttonDown(MOUSE_CONTROLS["FACE"]):
            mousex = mouseState.X.abs
            mousey = mouseState.Y.abs
            angle = self._get_angle_from_vector(mousex - self.viewport.actualWidth/2,
                                                mousey - self.viewport.actualHeight/2)
            self.player.rotation = angle

    def mouseMoved(self, event):
        state = event.get_state()
        
        # Pass the location of the mouse pointer over to CEGUI
        CEGUI.System.getSingleton().injectMouseMove(state.X.rel, state.Y.rel)
        return True

    def mousePressed(self, event, id):
        if id == MOUSE_CONTROLS["MOUSEMOVE"]:
            self.player.isRunning = True
        
        # Handle any CEGUI mouseButton events
        CEGUI.System.getSingleton().injectMouseButtonDown(self._convertOISToCEGUI(id))
        return True

    def mouseReleased(self, event, id):
        if id == MOUSE_CONTROLS["MOUSEMOVE"]:
            self.player.isRunning = False
            
        # Handle any CEGUI mouseButton events
        CEGUI.System.getSingleton().injectMouseButtonUp(self._convertOISToCEGUI(id))
        return True

    def _convertOISToCEGUI(self, oisID):
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
        
        
    # Internal helper methods to help input handling.
    def _get_angle_from_vector(self, x, y):
        """
        Returns the ccw rotation angle (in radians) from north of the given
        screen vector. The true south vector is <0, -1> and true east is
        <1, 0>. 
        """
        if x == 0:
            if y <= 0:
                angle = 0
            else:
                angle = math.pi
        else:
            if x >= 0:
                angle = math.atan(-y / x) - math.pi/2
            else:
                angle = math.atan(-y / x) + math.pi/2
        return angle
