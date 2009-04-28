from __future__ import division

from event import Event

class World(object):
    """
    This class represents the game world, including the map and all objects
    contained within it.
    """
    def __init__(self):
        self.objects = []
        self.object_added = Event()

    def add_object(self, gameObject):
        # Add the object and fire the object_added event.
        self.objects.append(gameObject)
        self.object_added(gameObject)
        
    def update(self, dt):
        for gameObject in self.objects:
            gameObject.update(dt)