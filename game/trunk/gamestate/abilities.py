#from event import Event
import collision
from collision import CollisionDetector
import objects
import math

class AbilityInstance(object):
    def __init__(self, player):
        self.player = player
    
    def run(self):
        raise NotImplementedError("BaseAbilityInstance class does not implement run.")


class EarthPrimaryInstance(AbilityInstance):
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        
    def run(self):
        # Temporary implementation: detect collision using a circle slightly
        # bigger than the player's ignoring the player that is using the ability.
        # @todo: use real collision using cone(?)
        # @todo: have swing delay
        print self.player.rotation/math.pi
        colliders = self.player.world.get_colliders(collision.BoundingCone(self.player.bounding_shape.radius + 4,
                                                                           self.player.rotation,
                                                                           math.pi/2),
                                                    self.player.position,
                                                    [self.player],
                                                    objects.Player)
        print "Earth Primary ability collided with %s game objects." % (len(colliders))