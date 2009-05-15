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
import math

class Node(object):
    _unique_count = 0
    @staticmethod
    def _unique(prefix=""):
        """ Return a unique name prefixed with the optional parameter. """
        Node._unique_count += 1
        return "%s%s" % (prefix, Node._unique_count)
    
    def __init__(self, sceneManager, gameObject):
        self.entity = sceneManager.createEntity(Node._unique("EntityNinja"), "ninja.mesh")
        self.sceneNode = sceneManager.getRootSceneNode().createChildSceneNode()
        self.sceneNode.attachObject(self.entity)
        self.sceneNode.setScale(.1, .1, .1)
        self.rotation_offset = 3*math.pi/2
        
        # Set the scenenode's position to the GameObject's current position.
        self.sceneNode.position = (gameObject.position[0], 0, gameObject.position[1])
        
        # Create a dict of our available animations. The animations are stored
        # as a tuple of the animation state and the speed at which the
        # animation should be played.
        self.animations = { }
        self.animations["idle"] = (self.entity.getAnimationState("Idle2"), 1)
        self.animations["run"] = (self.entity.getAnimationState("Walk"), 3)
        self.animations["ability_1"] = (self.entity.getAnimationState("Attack3"), 1)
        
        # Start the idle animation
        self.animation_start("idle")
        
        self.rotation = self.rotation_offset
        
        # Listen to the events we care about.
        gameObject.rotation_changed += self.on_rotation_changed
        
    def animation_start(self, name):
        anim, speed = self.animations[name]
        anim.setLoop(True)
        anim.setEnabled(True)
        
    def animation_playonce(self, name, weight=1):
        anim, speed = self.animations[name]
        anim.setLoop(False)
        anim.setEnabled(True)
        anim.setWeight(weight)
        anim.setTimePosition(0)
        
    def animation_stop(self, name):
        anim, speed = self.animations[name]
        anim.setEnabled(False)
        
    def animations_stopall(self):
        for name in self.animations:
            anim, speed = self.animations[name]
            anim.setEnabled(False)
        
    def animations_addtime(self, time):
        for name in self.animations:
            anim, speed = self.animations[name]
            if anim.getEnabled():
                anim.addTime(time*speed)
                if anim.hasEnded():
                    anim.setEnabled(False)
    
    ## Game state event listeners
    
    def on_rotation_changed(self, gameObject, rotation):
        delta = rotation - self.rotation
        self.sceneNode.rotate((0, -1, 0), delta)
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
    def __init__(self, sceneManager, player):
        MobileNode.__init__(self, sceneManager, player)
        
        # Listen to the events we care about.
        player.ability_used += self.on_ability_used
        
    def on_ability_used(self, player, index):
        if index == 1:
            # Play the animation with weight 100 so that it basically ovverides
            # any other animations currently playing.
            # @todo: use an actual solution instead of weight hack.
            self.animation_playonce("ability_1", 100)
