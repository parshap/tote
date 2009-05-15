from __future__ import division
import math

import collision
from collision import CollisionDetector
import elements
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
        pass


class MobileObject(GameObject):
    def __init__(self, world):
        GameObject.__init__(self, world)
        self.type = "mobile"
        
        self._is_moving = False
        self.is_moving_changed = Event()
        self.move_speed = 100
        self.move_direction = 0
        
        self.position_changed = Event()
        self.type = "mobile"

    def _get_is_moving(self):
        """ Gets or sets the object's current moving state """
        return self._is_moving
    def _set_is_moving(self, value):
        # Update the value and fire the changed event if the value has changed.
        if value != self._is_moving:
            self._is_moving = value
            self.is_moving_changed(self, value)
    is_moving = property(_get_is_moving, _set_is_moving)

    # Override the GameObject._set_position so we can fire the event.
    def _set_position(self, value):
        # Update the value and fire the changed event.
        GameObject._set_position(self, value)
        self.position_changed(self, value)
    position = property(GameObject._get_position, _set_position)

    def update(self, dt):
        GameObject.update(self, dt)

        if self.is_moving:
            movespd = self.move_speed * dt
            movedir = self.rotation + self.move_direction
            self._move_towards(movespd, movedir)

    def _move_towards(self, distance, direction, already_collided=None):
        """
        Moves the object by distance amount in the given direction (radians)
        and performs collision detection and resolution.
        
        Arguments:
        distance -- The distance (as distance units) to move the object.
        direction -- The direction (as radians where 0 is north) to move in.
        already_collided -- A set of objects previously collided with in this
            gamestate update that need to persist through _move() calls.
        """

        # If the distance we are moving is 0, we don't have to do anything.
        if distance == 0:
            return

        # Calculate the movement vector for this move.
        move_vector = (distance * math.cos(direction),
                       distance * math.sin(direction))

        # And call _move to perform the move with the calculated vector.
        self._move(move_vector, already_collided)
    
    def _move(self, move_vector, already_collided=None):
        """
        Moves the object by the given movement vector (relative to the current
        position and performs collision detection and resolution.
        
        Arguments:
        move_vector -- The vector containing the x and z components to move the
            object in (relative to the current position).
        already_collided -- A set of objects previously collided with in this
            gamestate update that need to persist through _move() calls.
        """
        
        # If the movement vector is 0, we don't have to do anything.
        if move_vector == (0, 0):
            return

        # Calculate the new position we want to move to.
        new_pos = (self._position[0] + move_vector[0],
                   self._position[1] + move_vector[1])
        
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
        
        # Initialize the set of objects we collide with in this object's
        # update (for later use in collision resolution).
        if already_collided is None:
            # If already_collided (a function argument) was not pased then no
            # objects have already collided with this object during this
            # object's update, so initialize it to an empty set.
            collided_objects = set()
        else:
            # Otherwise we already have some objects we have collided with (but
            # not performed resolution on), so initialize our set to those
            # previously collided with objects.
            collided_objects = already_collided
        
        # Loop over all objects in the world to test against.
        for object in self.world.objects:
            if self == object:
                # Can't collide with ourself.
                continue
                
            if object.bounding_shape is None:
                # Can't collide with an object that has no bounding shape.
                continue

            # Cast a ray from where we are to where we are moving to and check
            # if this ray collides with the object. This is to look for any
            # objects that may be between our old position and our new
            # position. This result will be True if the ray collides with the
            # object and False if not.
            rayResult = CollisionDetector.is_between(object.bounding_shape, object.position, self.position, new_pos)
            
            # Check if our bounding shape at our new position would overlap
            # with the object's bounding shape. The result will be None if
            # there is no overlap, or if there is a collision it will be the
            # position we should reset to if the object is not passable as a
            # part of collision resolution.
            shapeResult = CollisionDetector.check_collision_and_resolve(self.bounding_shape, new_pos, self.position, 
                                                                        object.bounding_shape, object.position)
            
            if rayResult is not False and shapeResult is False:
                # The object collided with our ray, but not with our shape,
                # so we must have jumped over it.
                
                # If the object is not passable, then this is a critical error
                # and we will completely deny the move by returning.
                if not object.isPassable:
                    return
                    
                # Otherwise add the object to our set of collided objects.
                collided_objects.add(object)
                
            if shapeResult is not False:
                # Our new bounding shape will be overlapping with another
                # object's bounding shape.
                
                # Add the object to our set of collided objects.
                collided_objects.add(object)
                
                # If the object is not passable, then we need to move to the
                # new position that is provided by the result and redo the
                # collision detection based on that new position. Call
                # self._move() to do this and then return.
                
                if not object.isPassable:
                    # We will use the shapeResult value (a corrected movement
                    # vector) returned from check_collision to move ourself
                    # flush against the object we collided with.
                    move_mm = (move_vector[0] + shapeResult[0],move_vector[1] + shapeResult[1])
                    self._move((move_vector[0] + shapeResult[0],
                                move_vector[1] + shapeResult[1]),
                               set([object]))
                    return

        # Now that collision detection is complete, update our position to the
        # previously calculated new position.
        self.position = new_pos
        
        # We now have a set of objects that we have collided with. Call
        # .collide() on each of those objects to perform collision resolution.
        for object in collided_objects:
            object.collide(self)


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
        
        # Create an EarthElement and pass it a reference to this player and
        # and make it our current active element.
        # @todo: don't hardcode this
        self.element = elements.EarthElement(self)
        
        # @todo: Last use time wasn't *really* at world.time=0, it was never.
        #        Perhaps initialize to some other value (False or None or -1).
        self.lastAbilityUseTime = 0
        self.gcd = 1
        
        self.ability_used = Event()

    def update(self, dt):
        MobileObject.update(self, dt)
        
    def ongcd(self):
        return self.world.time <= (self.lastAbilityUseTime + self.gcd)
        
    def useAbility(self, index):
        # Try to use the ability.
        if self.element.useAbility(index):
            # Ability use was successful. Update the last ability use time.
            self.lastAbilityUseTime = self.world.time
            self.ability_used(self, index)
        else:
            # @todo: Notify player of error?
            pass
