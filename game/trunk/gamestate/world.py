from __future__ import division
from collision import CollisionDetector

from event import Event

class World(object):
    """
    This class represents the game world, including the map and all objects
    contained within it.
    """
    def __init__(self, master=False):
        self.is_master = master
        self.objects = []
        self.objects_hash = { }
        self.object_id_pos = 0
        self.object_added = Event()
        self.object_removed = Event()
        self.world_updated = Event()
        self.debug_file = open("world.log", "w")
        self.time = 0

    def add_object(self, object, object_id=None):
        # Add the object and fire the object_added event.
        if object_id is None:
            self.object_id_pos += 1
            object_id = self.object_id_pos
        while self.objects_hash.has_key(object_id):
            object_id += 1
        if object_id > self.object_id_pos:
            self.object_id_pos = object_id + 1
        object.object_id = object_id
        self.objects.append(object)
        self.objects_hash[object.object_id] = object
        object.is_active = True
        self.object_added(object)
    
    def remove_object(self, object):
        # Remove the object
        self.objects.remove(object)
        del self.objects_hash[object.object_id]
        object.is_active = False
        self.object_removed(object)
        
    def update(self, dt):
        self.world_updated(dt)
        
        self.time += dt
        for gameObject in self.objects:
            gameObject.update(dt)
            
    def log(self, text):
        self.debug_file.write(text)
        self.debug_file.write("\n")
        
    def get_colliders(self, bounding_shape, position, ignored=[], typefilter=None):
        """
        Returns a list of game objects in the world that are currently
        colliding with the given bounding_shape at the given position. This
        method performs no collision resolution.
        
        This method is useful for collision between game objects in the world
        and some bounding shape that may not be "in" the world (e.g., a
        temporary bounding shape used for abilities).
        
        Arguments:
        bounding_shape -- The shape to check objects against.
        position -- The position of the shape to check objects against.
        ignored -- A list of game objects to ignore collision with.
        typefilter -- A class type that the colliding object must an instance
            (or derived instance) of.
        """
        colliders = []
        for object in self.objects:
            if object.bounding_shape is None:
                # Can't collide with an object that has no bounding shape.
                continue
            if typefilter is not None and not isinstance(object, typefilter):
                # Only collide with filtered objects.
                continue
            
            result = CollisionDetector.check_collision(bounding_shape, position, object.bounding_shape, object.position)
            if result is not False and object not in ignored:
                colliders.append(object)
                
        return colliders