from __future__ import division
import math

import collision
from collision import CollisionDetector
import elements
from event import Event

class GameObject(object):
    def __init__(self, world):
        self.world = world
        self.object_id = None
        self._rotation = 0
        self.rotation_changed = Event()
        self._position = (0, 0)
        self.isPassable = True
        self.bounding_shape = None
        self.type = ""
        self.is_active = False

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
        self.move_speed = 0
        self.move_direction = 0
        
        self.position_changed = Event()
        self.collided = Event()
        
        self.force_vector = (0, 0)
        self.force_strength = 0
        self.force_applied = False
        self.force_duration = 0

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
    
    def apply_force(self, vector, strength, acceleration_factor = 1, duration = False):
        self.force_vector = CollisionDetector.normalise_vector(vector)
        self.force_strength = strength
        self.force_duration = duration
        self.force_acceleration = acceleration_factor
        self.force_applied = True
        
    def remove_force(self):
        self.force_applied = False

    def update(self, dt):
        GameObject.update(self, dt)

        # if a force is applied to this mobileobject
        if self.force_applied:
            # if there is time remaining for the force, or if no duration was set
            if self.force_duration > 0 or not self.force_duration:
                # move this object based on the force
                self._move((self.force_vector[0] * self.force_strength * dt, 
                            self.force_vector[1] * self.force_strength * dt))
                # update duration if duration is set
                if self.force_duration is not False:
                    self.force_duration -= dt
                
                # apply force acceleration
                self.force_vector = (self.force_vector[0] + self.force_acceleration * self.force_vector[0] * dt,
                                     self.force_vector[1] + self.force_acceleration * self.force_vector[1] * dt)
            else:
                # duration expired
                print "force expired"
                self.force_duration = 0
                self.force_applied = False

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
        
        # Create a BoundingLineSegment that represents the player's move vector
        # We do this here so that we only have to do it ONCE to check against all
        # objects in the world.
        move_segment = collision.BoundingLineSegment(self.position, new_pos)
        
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
            rayResult = CollisionDetector.is_between(object.bounding_shape, object.position, move_segment)
            
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
                    print "DENIED MOVEMENT!!"
                    
                    # must collide these two objects to throw the proper events
                    self.collide(object)
                    object.collide(self)
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
            self.collide(object)
            object.collide(self)

    def collide(self, object):
        GameObject.collide(self, object)
        self.collided(object)


class Player(MobileObject):
    """
    This class a game-world representation of a player. This class is
    responsible for things such as containing state information (e.g., health,
    power, action state) and performing deterministic calculations (e.g., new
    position based on velocity) on every update() (once per frame).
    """
    gcd = 1.0
    
    def __init__(self, world):
        MobileObject.__init__(self, world)
        self.move_speed = 100
        self._health = 100
        self._power = 100
        self.max_power = 100
        self.max_health = 100
        self.health_regen = 1
        self.power_regen = 10
        self.dead = False
        self.died = Event()
        self.bounding_shape = collision.BoundingCircle(6)
        self.type = "player"
        
        self._is_charging = False
        self._is_hooked = False
        self.hooked_position = (0, 0)
        self.is_charging_changed = Event()
        self.is_hooked_changed = Event()
        self.hooked_by_player = None
        self.is_invulnerable = False
        self.is_immobilized = False
        
        # Create an Element and pass it a reference to this player make it our
        # current active element.
        # @todo: don't hardcode this
        self.element = elements.EarthElement(self)
        self.element_changed = Event()
        
        self.active_abilities = []
        self.last_ability_time = 0
        self.ability_used = Event()
        self.ability_instance_created = Event()
        
        self.health_changed = Event()
        self.power_changed = Event()
        self.ability_requested = Event()
        
    def _get_health(self):
        return self._health
    def _set_health(self, value):
        if value < 0:
            value = 0
        elif value > self.max_health:
            value = self.max_health
        if value != self.health:
            self._health = value
            if value <= 0 and not self.dead:
                self.dead = True
                print "player died"
                self.died()
            self.health_changed(self._health)
    
    health = property(_get_health, _set_health) 
        
    def _get_power(self):
        return self._power
    def _set_power(self, value):
        if value < 0:
            value = 0
        elif value > self.max_power:
            value = self.max_power
        if value != self.power:
            self._power = value
            self.power_changed(self._power)
    
    power = property(_get_power, _set_power)
        
    def apply_damage(self, amount):
        if not self.is_invulnerable:
            self.health = self.health - amount
                
    def use_power(self, amount):
        self.power = self.power - amount
        
    def _get_is_charging(self):
        """ Gets or sets the object's current charging state """
        return self._is_charging
    def _set_is_charging(self, value):
        if value is not self._is_charging:
            self._is_charging = value
            self.is_charging_changed(self, value)
    is_charging = property(_get_is_charging, _set_is_charging)
    
    def _get_is_hooked(self):
            return self._is_hooked
    def _set_is_hooked(self, value):
        if value is not self._is_hooked:
            self._is_hooked = value
            self.is_hooked_changed(self, value)
    is_hooked = property(_get_is_hooked, _set_is_hooked)
    
    
    # We will override the MobileObject.rotation property to redefine the
    # setter used so that we can deny a rotation change while charging.
    def _set_rotation(self, value):
        # Update the value and fire the changed event.
        if self.is_charging:
            # Prevent changing direction while in the middle of a charge.
            return
        self._rotation = value
        self.rotation_changed(self, value)
    rotation = property(MobileObject._get_rotation, _set_rotation)

    def update(self, dt):
        # Regen health & power.
        self.health += self.health_regen * dt
        self.power += self.power_regen * dt
        if self.is_charging:
            # If the player is charging then force movement.
            self.is_moving = True
        if self.is_hooked:
            if collision.CollisionDetector.check_collision(collision.BoundingCircle(8), self.hooked_by_player.position,
                                                           self.bounding_shape, self.position):
                self.is_hooked = False
                self.hooked_by_player = None
            else:
                self.is_moving = False
                distance = 200 * dt
                dx = self.hooked_by_player.position[0] - self.position[0]
                dz = self.hooked_by_player.position[1] - self.position[1]
                move_direction = math.atan2(dz, dx)              
                
                move_vector = (distance * math.cos(move_direction),
                               distance * math.sin(move_direction))
                self._move(move_vector)
        if self.is_immobilized:
            self.is_moving = False
        MobileObject.update(self, dt)

        for ability in self.active_abilities:
            ability.update(dt)
            
    def change_element(self, element_type):
        if self.element.type == element_type:
            return
        if element_type == "earth":
            self.element = elements.EarthElement(self)
        elif element_type == "fire":
            self.element = elements.FireElement(self)
        elif element_type == "water":
            self.element = elements.WaterElement(self)
        elif element_type == "air":
            self.element = elements.AirElement(self)
        else:
            return
        self.element_changed(self)
        
    def is_ongcd(self):
        """
        Return wether or not the player is currently on the global ability
        cooldown.
        """
        return self.last_ability_time > 0 and \
               self.world.time <= (self.last_ability_time + self.gcd)
    
    def request_ability(self, index):
        """ Requests use of an ability from the server. """
        if(not self.element.is_requestable(index)):
            ability_id = self.element.ability_ids[index]
            self.ability_requested(self, ability_id)
        
    def use_ability(self, ability_id):
        """
        Attempts to use an ability by ability_id. Returns True if sucessful,
        False otherwise.
        """
        # Try to use the ability.
        ability = self.element.use_ability(ability_id)
        if ability is not False:
            # Ability use was successful - do some updates.
            self.last_ability_time = self.world.time
            self.active_abilities.append(ability)
            ability.expired += self.on_ability_expired
            # @todo: find a more elegant way to pass the mobileobject/projectile than passing the entire ability
            # this won't be an easy design issue to fix, but luckily doing it this way will work and be easy to
            # implement and understand (even if it's a tad sloppy)
            self.ability_used(self, ability_id, ability)
            
            self.ability_instance_created(ability, self.world.time)
            return True
        return False
            
    def on_ability_expired(self, ability):
        self.active_abilities.remove(ability)
        return False
        
class ProjectileObject(MobileObject):
    def __init__(self, player, projectile_radius, duration):
        MobileObject.__init__(self, player.world)
        self.time_to_live = duration
        self.owner = player
        self.bounding_shape = collision.BoundingCircle(projectile_radius)
        self.duration = duration
        self.expired = Event()
        self.type = "projectile"
        player.world.add_object(self)
    
    def update(self, dt):
        # @todo fix double call bug and remove is_active
        if not self.is_active:
            return
        MobileObject.update(self, dt)
        self.time_to_live -= dt
        if self.time_to_live <= 0:
            self.expire()
            
    def collide(self, object):
        # @todo fix double call bug and remove is_active
        if not self.is_active:
            return
        if object == self.owner:
            return
        if object.type == "projectile":
            return
        MobileObject.collide(self, object)
        self.expire()
        
    def expire(self):
        self.expired(self)
        self.world.remove_object(self)
