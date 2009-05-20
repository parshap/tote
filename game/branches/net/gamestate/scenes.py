import gamestate

class Scene(object):
    pass
    
class TestScene(Scene):
    def __init__(self, world):
        self.world = world
        
        # Add stationary NPC ninja...
        npc = gamestate.objects.Player(self.world)
        self.world.add_object(npc)
        npc.position = (45, 45)
        npc.isPassable = False
        
        # Add boundary lines for map walls.
        
        # north wall
        boundary1 = gamestate.objects.GameObject(self.world)
        boundary1.position = (-90, -90)
        boundary1.isPassable = False
        boundary1.bounding_shape = gamestate.collision.BoundingLineSegment((-90, -90),
                                                                           (90, -90),
                                                                           (0, 1))
        # south wall
        boundary2 = gamestate.objects.GameObject(self.world)
        boundary2.position = (-90, 90)
        boundary2.isPassable = False
        boundary2.bounding_shape = gamestate.collision.BoundingLineSegment((-90, 90),
                                                                           (90, 90),
                                                                           (0, -1))
        # east wall
        boundary3 = gamestate.objects.GameObject(self.world)
        boundary3.position = (90, -90)
        boundary3.isPassable = False
        boundary3.bounding_shape = gamestate.collision.BoundingLineSegment((90, -90),
                                                                           (90, 90),
                                                                           (-1, 0))
        # west wall
        boundary4 = gamestate.objects.GameObject(self.world)
        boundary4.position = (-90, -90)
        boundary4.isPassable = False
        boundary4.bounding_shape = gamestate.collision.BoundingLineSegment((-90, -90),
                                                                           (-90, 90),
                                                                           (1, 0))

        self.world.add_object(boundary1)
        self.world.add_object(boundary2)
        self.world.add_object(boundary3)
        self.world.add_object(boundary4)