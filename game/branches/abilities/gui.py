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
        self._textarea = self.overlay.getChild(overlay_name + "/Text")
        self._opacity_target = None
        self._opacity_step = 1
        self._fade_callback = None
        
    def _get_text(self):
        """ Gets or sets the label's text caption. """
        return self._textarea.getCaption()
    def _set_text(self, value):
        self._textarea.setCaption(value)
    text = property(_get_text, _set_text)
    
    def _get_opacity(self):
        """ Gets or sets the label's opacity. """
        return self._textarea.getColour().a
    def _set_opacity(self, value):
        if value > 1: value = 1
        elif value < 0: value = 0
        c = self._textarea.getColour()
        c.a = value
        self._textarea.setColour(c)
    opacity = property(_get_opacity, _set_opacity)
    
    def _get_color(self):
        """ Gets or sets the label's color as an RGBA tuple. """
        c = self._textarea.getColour()
        return (c.r, c.g, c.b, c.a)
    def _set_color(self, value):
        c = self._textarea.getColour()
        if len(value) == 3:
            r, g, b = value
            a = None
        elif len(value) == 4:
            r, g, b, a = value
        else:
            raise Exception("Invalid color value, must be RGB or RGBA tuple.")
        c.r = r
        c.g = g
        c.b = b
        if a is not None: c.a = a
        self._textarea.setColour(c)
    color = property(_get_color, _set_color)
    
    def _get_is_fading(self):
        """ Gets whether or not the label is currently fading. """
        return self._opacity_target is not None and \
               self.opacity != self._opacity_target
    is_fading = property(_get_is_fading)
    
    def _get_is_visible(self):
        """ Gets whether or not the label is currently visible. """
        return self.opacity > 0 and self.overlay.isVisible() and self._textarea.isVisible()
    is_visible = property(_get_is_visible)
    
    def update(self, dt):
        Element.update(self, dt)
        if self._opacity_target is not None and \
           self.opacity != self._opacity_target:
            newval = self.opacity + (self._opacity_step * dt)
            if self._opacity_step > 0 and newval > self._opacity_target or \
               self._opacity_step < 0 and newval < self._opacity_target:
                newval = self._opacity_target
                self._opacity_target = None
                if self._fade_callback is not None:
                    self._fade_callback(self)
            self.opacity = newval
    
                
    def fade(self, start=None, end=None, duration=0.2, callback=None):
        """
        Linearly fade the label from the start opacity to the end opacity over
        duration seconds. The opacity will be set to the start opacity and
        fading will begin immediately. If no start or end parameters are given
        the current opacity is used.
        The callback is called with this label passed as the only parameter
        when the fading is complete. If fading is interrupted before it is
        complete, the callback will never be called.
        """
        if start is None: start = self.opacity
        if end is None: end = self.opacity
        self._opacity_target = end
        self._opacity_step = (end - start)
        if duration != 0:
            self._opacity_step /= duration
        self.opacity = start
        self._fade_callback = callback
    

class FPSLabel(Label):
    def __init__(self, overlay_name, update_frequency=.5):
        Label.__init__(self, overlay_name)
        self.update_frequency = update_frequency
        self.time_passed = 0
        self.frames_passed = 0
        self.opacity = 0.5
    
    def update(self, dt):
        Label.update(self, dt)
        self.time_passed += dt
        self.frames_passed += 1
        if(self.time_passed >= self.update_frequency):
            fps = self.frames_passed / self.time_passed
            self.text = "%d" % fps
            self.time_passed = 0
            self.frames_passed = 0


class Message(Label):
    def __init__(self, overlay_name):
        Label.__init__(self, overlay_name)
        self._show_time = 0
    
    def _set_text(self, value):
        raise Exception("Setting text directly is not supported in Message.")
    text = property(Label._get_text, _set_text)
    
    def update(self, dt):
        Label.update(self, dt)
        if not self.is_fading and self.is_visible:
            self._show_time -= dt
            if self._show_time <= 0:
                self.fade(end=0, duration=self._fade_duration)
    
    def show(self, text, color, fade_duration=.5, show_duration=None):
        """
        Temporarily displays the text.
        
        Parameters:
        text - The text to display.
        color - The color to display the text.
        fade_duration - The duration for the fade in and fade out. Default is
            0.5.
        show_duration - The duration to display the text for after fade in is
            complete before starting fade out. Default is a duration calculated
            based on the length of the text string with a minimum display of 1
            second and maximum display fo 5 seconds.
        """
        if show_duration is None: show_duration = min(max(len(text) * .05, 1), 5)
        Label._set_text(self, text)
        self.color = color
        self.fade(start=0, end=1, duration=fade_duration)
        self._show_time = show_duration
        self._fade_duration = fade_duration
    
    def error(self, text):
        # Used for game errors (e.g., not enough power)
        self.show(text, (.8, .1, .1))
        
    def notice(self, text):
        # Used for game notices (e.g., player won the game, you died)
        self.show(text, (.9, .9, .6))

    def success(self, text):
        # Used for game success messages (e.g., you killed a player)
        self.show(text, (.1, .8, .1))
        
    def system(self, text):
        # Used for system messages (e.g., connected to server, player joined)
        self.show(text, (1, 1, 1))