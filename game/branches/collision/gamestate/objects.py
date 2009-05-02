from __future__ import division
import math

import collision
from collision import CollisionDetector
from event import Event

class GameObject(object):
    def __init__(self, world):
        self.world = world
        self._rotation = 0
        self.rotation_changed = Event()
        self._position = (0, 0)
        self.isPassable = True
        self.bounding_shape = None
        self.type = ""

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
        
    def collide(self, otherObject):
        print "%s collided with %s" % (self, otherObject)


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

    # Override the GameObject._set_position so we can fire the event.
    def _set_position(self, value):
        # Update the value and fire the changed event.
        GameObject._set_position(self, value)
        self.position_changed(self, value)
    position = property(GameObject._get_position, _set_position)

    def update(self, dt):
        GameObject.update(self, dt)

        if self.isRunning:
            runSpd = self.runSpeed * dt
            runDir = self.rotation + self.runDirection
            self._move(runSpd, runDir)

    def _move(self, delta, direction):
        """
        Moves the object by delta amount in the given direction (radians) and
        performs collision detection and resolution.
        """
        
        # If the distance we are moving is 0, then we don't have to do anything.
        if delta == 0:
            return
 
        # Calculate the new position we want to move to.
        new_pos = (self._position[0] + delta * -math.sin(direction),
                   self._position[1] + delta * -math.cos(direction))
                   
        # If the object doesn't have a bounding shape then we don't need to
        # worry about collision detection & resolution and can simply update
        # the position and return.
        if self.bounding_shape is None:
            self.position = new_pos
            return
        
        # Otherwise we need to do collision detection.
        
        # @todo: possible optimizations:
        #   - Check un-passable objects first so we can restart _move sooner (if needed).
        #   - Check only against nearby objects (quadtree?)
        
        # Create an empty list to store objects that we collide with (for later
        # use in collision resolution).
        collided_objects = []
        
        # Change the direction to be what CollisionDetector expects (0 should 
        # be east instead of north).
        # @todo: Change all angles to use the same system.
        direction += math.pi/2
        
        # Loop over all objects in the world to test against.
        for object in self.world.objects:
            if self == object:
                # Can't collide with ourself.
                continue
                
            if object.bounding_shape is None:
                # Can't collide with an object that has no bounding shape.
                continue
        
            # Cast a ray from where we were in the direction we are moving to
            # with the distance of our move. This is to look for any objects
            # that may be between our old position and our new position. This
            # result will be True if the ray collides with the object and False
            # if not.
            rayResult = CollisionDetector.cast_ray(self.position, direction, delta, object.bounding_shape, object.position)
            
            # Check if our bounding shape at our new position would overlap
            # with the object's bounding shape. The result will be None if
            # there is no overlap, or if there is a collision it will be the
            # position we should reset to if the object is not passable as a
            # part of collision resolution.
            shapeResult = CollisionDetector.check_collision(self.bounding_shape, new_pos, object.bounding_shape, object.position)
            
            if rayResult and shapeResult is None:
                # The object collided with our ray, but not with our shape,
                # so we must have jumped over it.
                
                # If the object is not passable, then this is a critical error
                # and we will completely deny the move by returning.
                if not object.isPassable:
                    print "****DENYING MOVEMENT BECAUSE OF RAY!!"
                    return
                    
                # Otherwise append the object to our list of collided objects.
                collided_objects.append(object)
                
            if shapeResult is not None:
                # Our new bounding shape will be overlapping with another
                # object's bounding shape.
                
                # If the object is not passable, then we need to move to the
                # new position that is provided by the result and redo the
                # collision detection based on that new position. Call
                # self._move() to do this and then return.
                if not object.isPassable:
                    change = (shapeResult.x - self.position[0],
                              shapeResult.z - self.position[1])
                    distance = math.sqrt(change[0]*change[0] + change[1]*change[1])
                    x = change[0]
                    y = change[1]
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
                    
                    self._move(distance, angle)
                    return
                    
                # Otherwise append the object to our list of collided objects.
                collided_objects.append(object)
                
        # Collision detection is over and we now have a list of objects that we
        # have collided with. Call .collide() on each of those objects to
        # perform collision resolution.
        for object in collided_objects:
            object.collide(self)
            
        print "<<<< DID MOVE!!"
            
        # Now that collision detection and resolution is complete, update our
        # position to the previously calculated new position.
        self.position = new_pos


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
        self.bounding_shape = collision.BoundingCircle(6)
        self.type = "player"

    def update(self, dt):
        MobileObject.update(self, dt)
