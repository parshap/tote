from __future__ import division
import math

from event import Event

class GameObject(object):
    def __init__(self, node=None):
        self._rotation = 0
        self.rotation_changed = Event()
        self._position = (0, 0)
        
    @property
    def rotation(self):
        """ Gets or sets the object's current orientation angle in radians. """
        return self._rotation
    @rotation.setter
    def rotation(self, value):
        # Update the value and fire the changed event.
        self._rotation = value
        self.rotation_changed(self, value)

    def rotate(self, angle):
        self.rotation += angle
        
        
    @property
    def position(self):
        """ Gets or sets the object's current (x, z) position as a tuple """
        return self._position
    @position.setter
    def position(self, value):
        self._position = value

    def update(self, dt):
        pass


class MobileObject(GameObject):
    def __init__(self):
        GameObject.__init__(self)
        self._isRunning = False
        self.isRunning_changed = Event()
        self.runSpeed = 100
        self.runDirection = 0
        self.position_changed = Event()
    
    @property
    def isRunning(self):
        """ Gets or sets the object's current running state """
        return self._isRunning
    @isRunning.setter
    def isRunning(self, value):
        # Update the value and fire the changed event if the value has changed.
        if value != self._isRunning:
            self._isRunning = value
            self.isRunning_changed(self, value)
        
    @property
    def position(self):
        """ Gets or sets the object's current (x, z) position as a tuple """
        return self._position
    @position.setter
    def position(self, value):
        # Update the value and fire the changed event.
        self._position = value
        self.position_changed(self, value)

    def update(self, dt):
        GameObject.update(self, dt)
        
        if self.isRunning:
            runSpd = self.runSpeed * dt
            runDir = self.rotation + self.runDirection
            self._move(runSpd, runDir)

    def _move(self, delta, direction):
        """
        Moves the object by delta amount in the given direction (radians) and
        performs collision detection.
        """
        # @todo: do collision detection...
        # if new position collides with object o:
        #     o.collide(self)
        #     if o is not passible:
        #         move as close as possible
        #         return
        # move normally
        self.position = (self._position[0] + delta * -math.sin(direction),
                         self._position[1] + delta * -math.cos(direction))

class Player(MobileObject):
    """
    This class a game-world representation of a player. This class is
    responsible for things such as containing state information (e.g., health,
    power, action state) and performing deterministic calculations (e.g., new
    position based on velocity) on every update() (once per frame).
    """
    def __init__(self):
        MobileObject.__init__(self)
        self.power = 100
        self.health = 100

    def update(self, dt):
        MobileObject.update(self, dt)
