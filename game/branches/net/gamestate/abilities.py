#from event import Event
import collision
from collision import CollisionDetector

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
        colliders = self.player.world.get_colliders(collision.BoundingCircle(10),
                                                    self.player.position,
                                                    [self.player])
        print "Earth Primary ability collided with %s game objects." % (len(colliders))