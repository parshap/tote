from __future__ import division
import math

from event import Event

class GameObject(object):
    def __init__(self, world):
        self.world = world
        self._rotation = 0
        self.rotation_changed = Event()
        self._position = (0, 0)

    def _get_rotation(self):
        """ Gets or sets the object's current orientation angle in radians. """
        return self._rotation
    def _set_rotation(self, value):
        # Update the value and fire the changed event.
        self._rotation = value
        self.rotation_changed(self, value)
    rotation = property(_get_rotation, _set_rotation)

    def rotate(self, angle):
        self.rotation += angle


    def _get_position(self):
        """ Gets or sets the object's current (x, z) position as a tuple """
        return self._position
    def _set_position(self, value):
        self._position = value
    position = property(_get_position, _set_position)

    def update(self, dt):
        pass


class MobileObject(GameObject):
    def __init__(self, world):
        GameObject.__init__(self, world)
        self._isRunning = False
        self.isRunning_changed = Event()
        self.runSpeed = 100
        self.runDirection = 0
        self.position_changed = Event()

    def _get_isRunning(self):
        """ Gets or sets the object's current running state """
        return self._isRunning
    def _set_isRunning(self, value):
        # Update the value and fire the changed event if the value has changed.
        if value != self._isRunning:
            self._isRunning = value
            self.isRunning_changed(self, value)
    isRunning = property(_get_isRunning, _set_isRunning)

    def _get_position(self):
        """ Gets or sets the object's current (x, z) position as a tuple """
        return self._position
    def _set_position(self, value):
        # Update the value and fire the changed event.
        self._position = value
        self.position_changed(self, value)
    position = property(_get_position, _set_position)

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
    def __init__(self, world):
        MobileObject.__init__(self, world)
        self.power = 100
        self.health = 100

    def update(self, dt):
        MobileObject.update(self, dt)
