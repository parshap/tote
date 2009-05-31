import ogre.renderer.OGRE as ogre
from gamestate.event import Event


class Element(object):
    def __init__(self, overlay_name, bounding_rectangle):
        self.name = overlay_name
        self.overlay = ogre.OverlayManager.getSingleton().getOverlayElement(overlay_name)
        self.bounding_rectangle = bounding_rectangle
        self.updated = Event()
        
    def show(self): self.overlay.show()
    def hide(self): self.overlay.hide()
    
    def update(self, dt):
        self.updated(self, dt)


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
        
    def update(self, dt):
        Element.update(self, dt)
        
class AbilityCooldownDisplay(Element):
    def __init__(self, overlay_name, bounding_rectangle, ability_index, cooldown_time):
        Element.__init__(self, overlay_name, bounding_rectangle)
        self.type = "AbilityCooldownDisplay"
        self.cooldown_time = cooldown_time
        self.time_till_enable = 0
        self.ability_index = ability_index
        self.text_area = self.overlay.getChild(overlay_name+"/Cooldown")
        print "should be true: " + str(self.text_area is not None)
        
    def on_ability_used(self, player, index, ability):
        if index == self.ability_index:
            self.begin_cooldown()
        print "beginning cooldown"
        
    def update(self, dt):
        Element.update(self, dt)
        if self.time_till_enable > 0:
            self.time_till_enable -= dt
            if self.time_till_enable < 0:
                self.end_cooldown()
            display_caption = "%d" %(self.time_till_enable + 1)
            self.overlay.setCaption(display_caption)
            
    def begin_cooldown(self):
        # udpate display
        
        # set cooldown time
        self.time_till_enable = self.cooldown_time
    
    def end_cooldown(self):
        # update display
        self.overlay.setCaption("")
        
    def set_player_listener(self, player):
        print "setting player listener"
        player.ability_used += self.on_ability_used
        
        
        
        
        