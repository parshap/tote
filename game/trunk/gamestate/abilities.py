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


class FirePrimaryInstance(AbilityInstance):
    def __init__(self, player):
        AbilityInstance.__init__(self, player)

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
    charge_speed_multiplier = 2

    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.scheduler = Scheduler(2)
        self.scheduler.on_fire += self.expire

    def run(self):
        AbilityInstance.run(self)
        self.player.is_charging = True
        self.player.move_speed *= self.charge_speed_multiplier
        self.player.collided += self.on_player_collided
        
    def on_player_collided(self, player, object):
        if object.type == "player":
            # @todo: do damage...
            print "Flame Rush collided with another player!"
            self.expire()
            return False

        if not object.isPassable:
            # @todo: stun? damage? etc...
            print "Flame Rush collided with some other object!"
            self.expire()
            return False

    def update(self, dt):
        print "Flame Rush is updating."
        AbilityInstance.update(self, dt)
        self.scheduler.addtime(dt)

    def expire(self):
        AbilityInstance.expire(self)
        self.player.is_charging = False
        self.player.move_speed /= self.charge_speed_multiplier