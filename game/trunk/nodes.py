"""
This module defines several the Node class and several subclasses that are used
as Ogre (3d-world) representations of game-world objects (such as players or
static map objects like trees and rocks, generally represented by a mesh).
These classes uses the adapter pattern to implement Ogre's SceneNode
functionality. This class is responsible for things such as mapping game-world
coordinates to 3d-world coordinates and displaying animations.

These classes listen to events fired by their game-world object counterparts to
perform actions (such as starting an animation) and make updates (such as
moving the mesh in the 3d-world to objcet the player moving in the game-world).

*NOTE: The following is strongly recommended as best use of these classes:
 - The interaction between the game state and these classes should be one way
   (from the game state to these classes). Do not directly interact with the
   game state (e.g., the node's game state counterpart) in any way.
 - Any information needed about the game state should be obtained via event
   handler parameters and the game state should not be directly referenced.
"""

from __future__ import division

class Node(object):
    
    _countEntity = 0
    
    def __init__(self, sceneManager, gameObject):
        self._countEntity += 1
        self.entity = sceneManager.createEntity("Entity" + str(self._countEntity), "ninja.mesh")
        self.sceneNode = sceneManager.getRootSceneNode().createChildSceneNode()
        self.sceneNode.attachObject(self.entity)
        self.sceneNode.setScale(.1, .1, .1)
        
        # Create a dict of our available animations. The animations are stored
        # as a tuple of the animation state and the speed at which the
        # animation should be played.
        self.animations = { }
        self.animations["idle"] = (self.entity.getAnimationState("Idle2"), 1)
        self.animations["run"] = (self.entity.getAnimationState("Walk"), 3)
        
        # Create a set of current active animations.
        self.animations_active = set()
        
        # Start the idle animation
        self.animation_start("idle")
        
        self.rotation = 0
        
        # Listen to the events we care about.
        gameObject.rotation_changed += self.on_rotation_changed
        
    def animation_start(self, name):
        anim, speed = self.animations[name]
        anim.setLoop(True)
        anim.setEnabled(True)
        self.animations_active.add((anim, speed))
        
    def animation_stop(self, name):
        anim, speed = self.animations[name]
        anim.setEnabled(False)
        self.animations_active.remove((anim, speed))
        
    def animations_stopall(self):
        for anim, speed in self.animations_active:
            anim.setEnabled(False)
        self.animations_active.clear()
        
    def animations_addtime(self, time):
        for (anim, speed) in self.animations_active:
            anim.addTime(time*speed)
    
    ## Game state event listeners
    
    def on_rotation_changed(self, gameObject, rotation):
        self.sceneNode.rotate((0, 1, 0), rotation - self.rotation)
        self.rotation = rotation


class MobileNode(Node):
    def __init__(self, sceneManager, mobileObject):
        Node.__init__(self, sceneManager, mobileObject)
        
        # Listen to the events we care about.
        mobileObject.position_changed += self.on_position_changed
        mobileObject.isRunning_changed += self.on_isRunning_changed
        
    ## Game state event listeners
    
    def on_position_changed(self, mobileObject, position):
        self.sceneNode.position = (position[0], 0, position[1])
        
    def on_isRunning_changed(self, gameObject, isRunning):
        if isRunning:
            self.animation_stop("idle")
            self.animation_start("run")
        else:
            self.animation_stop("run")
            self.animation_start("idle")


class PlayerNode(MobileNode):
    def __init__(self, sceneManager, playerObject):
        MobileNode.__init__(self, sceneManager, playerObject)
        
        # Listen to the events we care about.
