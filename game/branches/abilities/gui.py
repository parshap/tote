import ogre.renderer.OGRE as ogre
from gamestate.event import Event


class Element(object):
    def __init__(self, overlay_name, bounding_rectangle):
        self.overlay = ogre.OverlayManager.getSingleton().getOverlayElement(overlay_name)
        self.bounding_rectangle = bounding_rectangle
        
    def show(self): self.overlay.show()
    def hide(self): self.overlay.hide()


class IClickable(object):
    def inject_mouse_press(self, button, x, y):
        if self.overlay.isVisible() and self.bounding_rectangle.inside(x, y):
            self.on_click(button)
            
    def inject_mouse_release(self, mouse_button, x, y):
        pass
        
            
    def on_click(self, mouse_button):
        pass


class Button(Element, IClickable):
    def __init__(self, overlay_name, bounding_rectangle):
        Element.__init__(self, overlay_name, bounding_rectangle)
        IClickable.__init__(self)
        self.clicked = Event()
    
    def on_click(self, mouse_button):
        self.clicked(self, mouse_button)
        
class FPSCounter():
    def __init__(self, overlay_name):
        self.textArea = ogre.OverlayManager.getSingleton().getOverlayElement(overlay_name)
        self.time_passed = 0
        self.frames_passed = 0
        self.target_window = 1
        
    def update(self, dt, df=1):
        """
        Update normally takes the amount of time since the last frame.
        The use of df allows for flexibility if update is not called
        every frame.
        """
        self.time_passed += dt
        self.frames_passed += df
        if(self.time_passed >= .1):
            fps = int(df/dt)
            self.time_passed = 0
            self.frames_passed = 0
            self.target_window += 1
            if(self.target_window == 6):
                self.target_window = 1
                ogre.OverlayManager.getSingleton().getOverlayElement("UI/FPS/Meter").setCaption(str(fps))
            else:
                ogre.OverlayManager.getSingleton().getOverlayElement("UI/FPS/Meter"+str(self.target_window)).setCaption(str(fps))

        