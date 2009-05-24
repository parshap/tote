#from event import Event
import collision
from collision import CollisionDetector
import objects
import math
from event import Event, Scheduler
from collections import defaultdict


class AbilityInstance(object):
    def __init__(self, player):
        self.player = player
        self.expired = Event()
        self.is_active = False
        self.type = ""

    def run(self):
        self.is_active = True

    def update(self, dt):
        pass

    def expire(self):
        self.is_active = False
        self.expired(self)


class EarthPrimaryInstance(AbilityInstance):
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "EarthPrimaryInstance"
        
        self.hit_angle = math.pi/2
        self.range = self.player.bounding_shape.radius + 8

    def run(self):
        AbilityInstance.run(self)
        # @todo: have swing delay
        bounding_shape = collision.BoundingCone(
            self.range,
            self.player.rotation, self.hit_angle)
        colliders = self.player.world.get_colliders(
            bounding_shape, self.player.position,
            [self.player], objects.Player)
        print "Earth Primary ability collided with %s players." % (len(colliders))
        self.expire()
        
class EarthHookInstance(AbilityInstance):
    projectile_velocity = 200
    projectile_radius = 12
    projectile_duration = 0.5
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "EarthHookInstance"
        self.hook_projectile_created = Event()
        self.start_position = player.position
        self.start_rotation = player.rotation

    def run(self):
        AbilityInstance.run(self)
        
        #make the projectile's projectileobject
        self.hook_projectile = objects.ProjectileObject(self.player, self.projectile_radius,
                                                        self.projectile_duration)
        self.hook_projectile.position = self.start_position
        self.hook_projectile.bounding_shape = collision.BoundingCircle(self.projectile_radius)
        self.hook_projectile.rotation = self.start_rotation
        self.hook_projectile.move_speed = self.projectile_velocity
        self.hook_projectile.is_moving = True
        self.player.world.add_object(self.hook_projectile)
        self.hook_projectile.collided += self.on_collided
        
        # throw event
        self.hook_projectile_created(self.hook_projectile)
    
    def on_collided(self, object_collided_with):
        # @todo: do damage
        if object_collided_with.type == "player":
            print "hook collided with player"
            if not object_collided_with.is_hooked:
                object_collided_with.is_hooked = True
                object_collided_with.hooked_position = self.start_position
                object_collided_with.hooked_by_player = self.player
                self.expire()

class EarthEarthquakeInstance(AbilityInstance):
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "EarthEarthQuakeInstance"
        self.hitRadius = 30
        
    def run(self):
        AbilityInstance.run(self)
        
        # get a list of players that were hit by the earthquake
        self.bounding_circle = collision.BoundingCircle(self.hitRadius)
        
        colliders = self.player.world.get_colliders(self.bounding_circle, self.player.position,
                                                    [self.player], objects.Player)
        
        # apply effects
        for player in colliders:
            # @todo: apply slow effects, etc
            print "Earthquake collided with another player!"
            
        self.expire()
        
class EarthPowerSwingInstance(AbilityInstance):
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "EarthPowerSwingInstance"
        self.hit_angle = math.pi/2
        self.range = 10
        
    def run(self):
        AbilityInstance.run(self)
        # @todo: have swing delay
        bounding_shape = collision.BoundingCone(
            self.range,
            self.player.rotation, self.hit_angle)
        colliders = self.player.world.get_colliders(
            bounding_shape, self.player.position,
            [self.player], objects.Player)
        print "Earth Power Swing ability collided with %s players." % (len(colliders))
        self.expire()
        
        

class FirePrimaryInstance(AbilityInstance):
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "FirePrimaryInstance"

    def run(self):
        AbilityInstance.run(self)
        bounding_shape = collision.BoundingCone(
            self.player.bounding_shape.radius + 8,
            self.player.rotation, math.pi/2)
        colliders = self.player.world.get_colliders(
            bounding_shape, self.player.position,
            [self.player], objects.Player)
        print "Fire Primary ability collided with %s game objects." % (len(colliders))
        self.expire()


class FireFlameRushInstance(AbilityInstance):
    charge_speed_multiplier = 3
    damage_dealt = 1 
    duration = 2
    radius = 12

    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.scheduler = Scheduler(self.duration)
        self.scheduler.on_fire += self.expire
        self.type = "FireFlameRushInstance"
        self.collided = Event()
        

    def run(self):
        AbilityInstance.run(self)
        self.player.is_charging = True
        self.player.move_speed *= self.charge_speed_multiplier
        self.player.collided += self.on_player_collided
        
    def on_player_collided(self, object):
        if not object.isPassable:
            self.collided(self.player)
            # create the bounding circle to check collision against
            bounding_circle = collision.BoundingCircle(self.radius) 
            
            # get a list of colliding players
            colliders = self.player.world.get_colliders(bounding_circle, self.player.position,
                                                        [self.player], objects.Player)
            
            # for each player, apply effects
            for player in colliders:
                # @todo: apply damage
                print "Flame Rush collided with some other object!"
                
            self.expire()
            return False

    def update(self, dt):
        AbilityInstance.update(self, dt)
        self.scheduler.addtime(dt)

    def expire(self):
        AbilityInstance.expire(self)
        self.player.is_charging = False
        self.player.move_speed /= self.charge_speed_multiplier
        
class FireLavaSplashInstance(AbilityInstance):
    damage_dealt = 1
    radius = 18
        
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "FireLavaSplashInstance"
    
    def run(self):
        AbilityInstance.run(self)
        # create the bounding circle to check collision against
        bounding_circle = collision.BoundingCircle(self.radius) 
        
        # get a list of colliding players
        colliders = self.player.world.get_colliders(bounding_circle, self.player.position,
                                                    [self.player], objects.Player)
        
        # for each player, apply effects
        for player in colliders:
            # @todo: apply damage
            print "Lava Splash collided with another player!"
                
        # end the effect
        self.expire()
            
    def update(self, dt):
        AbilityInstance.update(self, dt)
    
    def expire(self):
        AbilityInstance.expire(self)
        
class FireRingOfFireInstance(AbilityInstance):
    damage_per_tick = 10
    duration = 3
    radius = 40
    tick_time = 1
    last_player_hit_times = defaultdict(int)
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "FireRingOfFireInstance"
        self.time_to_live = self.duration
        self.ring_of_fire = objects.ProjectileObject(self.player, self.radius,
                                                     self.duration)
        self.ring_of_fire.position = self.player.position
        self.ring_of_fire.bounding_shape = collision.BoundingCircle(self.radius, True)
        self.ring_of_fire.outer_bounding_circle = collision.BoundingCircle(self.radius + 10, True)
        self.ring_of_fire.inner_bounding_circle = collision.BoundingCircle(self.radius - 10, True)
        self.ring_of_fire.move_speed = 0
        self.ring_of_fire.is_moving = False
        
    def run(self):
        AbilityInstance.run(self)
        # nothing to do here really
  
    def update(self, dt):
        AbilityInstance.update(self, dt)
                
        # if the ability has expired...
        self.duration -= dt
        if self.duration <= 0:
            self.player.world.remove_object(self.ring_of_fire)
            print "effect destroyed"
            self.expire()
            return
        
        # otherwise do our updates
        colliders = self.player.world.get_colliders(self.ring_of_fire.bounding_shape, self.ring_of_fire.position,
                                                    [self.player], objects.Player)
        inner_colliders = self.player.world.get_colliders(self.ring_of_fire.inner_bounding_circle, self.ring_of_fire.position,
                                                    [self.player], objects.Player)
        outer_colliders = self.player.world.get_colliders(self.ring_of_fire.outer_bounding_circle, self.ring_of_fire.position,
                                                          [self.player], objects.Player)
        for collider in inner_colliders:
            colliders.append(collider)
        for collider in outer_colliders:
            colliders.append(collider)
        
        for collider in colliders:
            # if this player has already been hit
            if self.last_player_hit_times.has_key(collider):
                if collider == self.player:
                    print "player collided"
                    continue
                # check to see if the player was hit long ago enough to hit him again
                dt = self.player.world.time - self.last_player_hit_times[collider]
                if dt >= self.tick_time:
                    print "Another player was hit by Ring of Fire!"
                    self.last_player_hit_times[collider] = self.player.world.time
                    # @todo: apply damage etc etc etc
            # if the player has not already been hit
            else:
                self.last_player_hit_times[collider] = self.player.world.time
                print "Another player was hit by Ring of Fire!"
                # @todo: : apply damage etc etc etc
    
                