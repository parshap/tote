from __future__ import division
import ogre.renderer.OGRE as ogre
from gamestate.event import Event

class Element(object):
    def __init__(self, overlay_name):
        self.name = overlay_name
        self.overlay = ogre.OverlayManager.getSingleton().getOverlayElement(overlay_name)
        
        self.updated = Event()
        
    def show(self): self.overlay.show()
    def hide(self): self.overlay.hide()
    
    def update(self, dt):
        self.updated(self, dt)


class IClickable(object):
    def __init__(self, bounding_rectangle):
        self.bounding_rectangle = bounding_rectangle

    def inject_mouse_press(self, button, x, y):
        if self.overlay.isVisible() and self.bounding_rectangle.inside(x, y):
            self.on_click(button)
            
    def inject_mouse_release(self, mouse_button, x, y):
        pass
        
            
    def on_click(self, mouse_button):
        pass


class Button(Element, IClickable):
    def __init__(self, overlay_name, bounding_rectangle):
        Element.__init__(self, overlay_name)
        IClickable.__init__(self, bounding_rectangle)
        self.clicked = Event()
    
    def on_click(self, mouse_button):
        self.clicked(self, mouse_button)
        
    def update(self, dt):
        Element.update(self, dt)

class StatusBar(Element):
    def __init__(self, overlay_name, bounding_rectangle, max_value):
        Element.__init__(self, overlay_name)
        self.value = max_value
        self.max_value = max_value
        self.name = ""
        self.type = "StatusBar"
        self.container = ogre.OverlayManager.getSingleton().getOverlayElement("UI/StatusBars")
        self.on_value_changed(self.max_value)
    
    def on_value_changed(self, new_value):
        self.value = new_value
        if self.value > self.max_value:
            self.value = self.max_value
        if self.value < 0:
            self.value = 0
        
        # update the visual element
        bar_total_width = self.container.getWidth()
        full_proportion = self.value / self.max_value
        bar_width = bar_total_width * full_proportion
        self.overlay.setWidth(bar_width)

class AbilityCooldownDisplay(Element):
    def __init__(self, overlay_name, bounding_rectangle, ability_index, cooldown_time):
        Element.__init__(self, overlay_name)
        self.type = "AbilityCooldownDisplay"
        self.cooldown_time = cooldown_time
        self.time_till_enable = 0
        self.ability_index = ability_index
        self.cooldown_container = self.overlay.getChild(overlay_name+"/CooldownContainer")
        self.text_area = self.cooldown_container.getChild(overlay_name+"/Cooldown")
        self.cooldown_container.hide()
        print "should be true if found container: " + str(self.cooldown_container is not None)
        
        
    def on_ability_used(self, player, index, ability):
        if index == self.ability_index:
            self.begin_cooldown()
        
    def update(self, dt):
        Element.update(self, dt)
        if self.time_till_enable > 0:
            self.time_till_enable -= dt
            if self.time_till_enable < 0:
                self.end_cooldown()
            display_caption = "%d" %(self.time_till_enable + 1)
            self.text_area.setCaption(display_caption)
            
    def begin_cooldown(self):
        # udpate display
        self.cooldown_container.show()
        
        # set cooldown time
        self.time_till_enable = self.cooldown_time
    
    def end_cooldown(self):
        # update display
        self.cooldown_container.hide()
        
    def set_player_listener(self, player):
        player.ability_used += self.on_ability_used


class Label(Element):
    def __init__(self, overlay_name):
        Element.__init__(self, overlay_name)
        self.textarea = self.overlay.getChild(overlay_name + "/Text")
        self._text = self.textarea.getCaption()
        
    def _get_text(self):
        """ Gets or sets the label's text caption. """
        return self._text
    def _set_text(self, value):
        self.textarea.setCaption(value)
        self._text = value
    text = property(_get_text, _set_text)


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
            fps = int(self.frames_passed/self.time_passed)
            self.time_passed = 0
            self.frames_passed = 0
            self.target_window += 1
            if(self.target_window == 6):
                self.target_window = 1
                ogre.OverlayManager.getSingleton().getOverlayElement("UI/FPS/Meter").setCaption(str(fps))
            else:
                ogre.OverlayManager.getSingleton().getOverlayElement("UI/FPS/Meter"+str(self.target_window)).setCaption(str(fps))