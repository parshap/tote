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