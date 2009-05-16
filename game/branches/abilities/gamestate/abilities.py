#from event import Event
import collision
from collision import CollisionDetector
import objects
import math
from event import Event, Scheduler


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

    def run(self):
        AbilityInstance.run(self)
        # @todo: have swing delay
        bounding_shape = collision.BoundingCone(
            self.player.bounding_shape.radius + 8,
            self.player.rotation, math.pi/2)
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