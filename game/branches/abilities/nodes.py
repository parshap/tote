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
import gamestate.abilities
import gamestate.event
import ogre.renderer.OGRE as ogre




class Node(object):
    """Node represents a ogre scene node with a position relative to the root scene node."""
    _unique_count = 0
    @staticmethod
    def _unique(prefix=""):
        """ Return a unique name prefixed with the optional parameter. """
        Node._unique_count += 1
        return "%s%s" % (prefix, Node._unique_count)
    
    def __init__(self, sceneManager):
        # Create a SceneNode for this Node (attached to RootSceneNode).
        self.sceneManager = sceneManager
        self.sceneNode = sceneManager.getRootSceneNode().createChildSceneNode()
        self.unique_scene_node_name = Node._unique("sceneNode")
        
        # Node spatial properties
        self.position = (0,0,0)
        self.rotation = -math.pi/2 #@todo: fix this
        self.scale = 1
        
        # Node renderables
        self.mesh = None
        self.particle_system = None
        
    # spatial properties
    def set_position(self, position_offset):
        self.position = position_offset
        self.sceneNode.setPosition(position_offset[0], position_offset[1], position_offset[2])
        
    def set_rotation(self, rotation):
        delta = rotation - self.rotation
        self.sceneNode.rotate((0, -1, 0), delta)
        self.rotation = rotation
    
    def set_scale(self, scale):
        self.scale = scale
        self.sceneNode.setScale(scale, scale, scale)
    
    ## Particle Effect
    def set_particle_system(self, name, position_offset = (0,0,0), rotation = 0, scale = 1):
        """
        Initialize the particle effect with the given parameters.
        Parameters:
        name - The name for this particle effect.
        position - The position of the SceneNode the ParticleSystem is attached to.
        rotation - The rotation of the SceneNode the ParticleSystem is attached to.
        systemname - The name of the particle_system to use, defaults to the
            name of the particle effect.
        """
        self.particle_system = self.sceneManager.createParticleSystem(Node._unique("PE%s" % name), name)
        if self.particle_system is not None:
            for i in xrange(0, self.particle_system.getNumEmitters()):
                self.particle_system.getEmitter(i).setEnabled(False)
        particleNode = self.sceneNode.createChildSceneNode()
        particleNode.attachObject(self.particle_system)
        particleNode.position = position_offset
        particleNode.rotate((0, -1, 0), rotation)     
    
    def get_particle_system(self):
        return self.particle_system
        
    def particle_effect_start(self):
        """ Enable the particle effect with the given name. """
        print "particle started!"
        if self.particle_system is not None:
            for i in xrange(0, self.particle_system.getNumEmitters()):
                self.particle_system.getEmitter(i).setEnabled(True)
        else:
            raise Exception("Particle system not set for PlayerNode!")
            
    def particle_effect_stop(self):
        """ Disable the particle effect with the given name. """
        if self.particle_system is not None:
            for i in xrange(0, self.particle_system.getNumEmitters()):
                self.particle_system.getEmitter(i).setEnabled(False)
        else:
            raise Exception("Particle system not set for PlayerNode!")
    
    ## Mesh
    def set_mesh(self, name, position_offset = (0,0,0), rotation = 0, scale = 1):
        # Create an Entity (to represent this Node with a 3D mesh) and attach
        # it to the SceneNode. The Entity is configured with a default rotation
        # offset and scale.
        self.mesh = self.sceneManager.createEntity(Node._unique(name), name)
        entityNode = self.sceneNode.createChildSceneNode()
        entityNode.attachObject(self.mesh)
        entityNode.position = ( position_offset[0], 
                                position_offset[1],
                                position_offset[2] )
        entityNode.setScale(scale, scale, scale)
        entityNode.rotate((0, -1, 0), rotation)
    
    def get_mesh(self):
        return self.mesh
        
    ## Animations
    def animation_start(self, name):
        """ Play and loop the animation with the given name. """
        anim, speed = self.animations[name]
        anim.setLoop(True)
        anim.setEnabled(True)
        
    def animation_playonce(self, name, weight=1):
        """ Play the animation witht he given name once and then stop. """
        anim, speed = self.animations[name]
        anim.setLoop(False)
        anim.setEnabled(True)
        anim.setWeight(weight)
        anim.setTimePosition(0)
        
    def animation_stop(self, name):
        """ Stop the animation with the given name. """
        anim, speed = self.animations[name]
        anim.setEnabled(False)
        
    def animations_stopall(self):
        """ Stop all animations. """
        for name in self.animations:
            anim, speed = self.animations[name]
            anim.setEnabled(False)
        
    def animations_addtime(self, time):
        """ Add time to all enabled animations. """
        for name in self.animations:
            anim, speed = self.animations[name]
            if anim.getEnabled():
                anim.addTime(time * speed)
                if anim.hasEnded():
                    anim.setEnabled(False)
        
class GameNode(Node):
    """GameNode represents a Node that is attached to a gameObject."""
    def __init__(self, sceneManager, gameObject):
        Node.__init__(self, sceneManager)  
        
        # Initialize the position and rotation to the GameObject's current values.
        self.sceneNode.position = (gameObject.position[0], 0, gameObject.position[1])
        self.on_rotation_changed(gameObject, gameObject.rotation)
        
        # Listen to the events we care about.
        gameObject.rotation_changed += self.on_rotation_changed
    
    ## Game state event listeners
    def on_rotation_changed(self, gameObject, rotation):
        delta = rotation - self.rotation
        self.sceneNode.rotate((0, -1, 0), delta)
        self.rotation = rotation


class MobileGameNode(GameNode):
    def __init__(self, sceneManager, mobileObject):
        GameNode.__init__(self, sceneManager, mobileObject)
        self.is_active = True
        self.type = mobileObject.type
        
        # Listen to the events we care about.
        mobileObject.position_changed += self.on_position_changed
        if mobileObject.type == "projectile":
            mobileObject.expired += self.on_expired

    ## Game state event listeners
    def on_position_changed(self, mobileObject, position):
        if not self.is_active:
            return False
        self.sceneNode.position = (position[0], 0, position[1])
    
    def on_expired(self, projectileObject):
        if not self.is_active:
            return False
        self.expire(projectileObject)
        self.is_active = False
        
    def expire(self, projectileObject):
        # @todo: if our game is really slow, this might be a memory leak
       self.particle_effect_stop()
       

class ProjectileNode(MobileGameNode):
    def __init__(self, sceneManager, projectileObject):
        MobileGameNode.__init__(self, sceneManager, projectileObject)
        
        self.secondary_particle_system = None
        projectileObject.collided += self.on_collided
        projectileObject.expired -= self.on_expired
    
    def set_secondary_particle_system(self, system_name, position_offset = (0,0,0), rotation = 0, scale = 1):
        self.secondary_particle_system = self.sceneManager.createParticleSystem(Node._unique("PE%s" % system_name), system_name)
        particleNode = self.sceneNode.createChildSceneNode()
        particleNode.attachObject(self.secondary_particle_system)
        particleNode.position = position_offset
        particleNode.rotate((0, -1, 0), rotation)
        self.secondary_particle_node = particleNode
        for i in xrange(0, self.secondary_particle_system.getNumEmitters()):
                self.secondary_particle_system.getEmitter(i).setEnabled(False)
    
    def on_collided(self, object_collided_with):
        if self.particle_system is not None:
            self.particle_effect_stop()
            if self.secondary_particle_system is not None:
                if object_collided_with.type == "player":
                    self.set_position((object_collided_with.position[0],
                                       0,
                                       object_collided_with.position[1]))
                    self.secondary_particle_effect_start()
                else:
                    self.secondary_particle_effect_start()
            
    def secondary_particle_effect_start(self):
        if self.secondary_particle_system is not None:
            for i in xrange(0, self.secondary_particle_system.getNumEmitters()):
                self.secondary_particle_system.getEmitter(i).setEnabled(True)
        else:
            raise Exception("Particle system not set!")
    
    def secondary_particle_effect_stop(self):
        if self.secondary_particle_system is not None:
            for i in xrange(0, self.secondary_particle_system.getNumEmitters()):
                self.secondary_particle_system.getEmitter(i).setEnabled(False)
        else:
            raise Exception("Particle system not set!")
    
    
  
class StaticEffectNode(Node):
    """ Implementation of Node that represents an object that exists ONLY IN OGRE
    and has no corresponding GameObject. A StaticEffectNode allows itself to be destroyed
    a given time offset (time_to_live) after creation. This class will be used for such
    things as PBAoE instant particle effects. time_to_live defaults to False, meaning
    that the object is persistent.
    """
    def __init__(self, sceneManager, world, time_to_live = False, triggerable = False):
        Node.__init__(self, sceneManager)
        self.time_to_live = time_to_live
        self.triggered = False
        self.triggerable = triggerable
        self.world = world
        if time_to_live:
            world.world_updated += self.on_world_updated
            
        self.static_node_expired = gamestate.event.Event()
    
    def on_world_updated(self, dt):
        if not self.triggerable or self.triggered:
            self.time_to_live -= dt
            if self.time_to_live <= 0:
                self.expire()
                return False
    
    def expire(self):      
        # throw expired event
        if self.particle_system is not None:
            print "turning particle effect off"
            self.particle_effect_stop()
        if self.mesh is not None:
            self.sceneNode.setVisible(False)
        self.static_node_expired()
        
    def on_triggered(self):
        self.triggered = True
        if self.particle_system is not None:
            self.particle_effect_start()
        return False
    
class PlayerNode(MobileGameNode):
    def __init__(self, sceneManager, player, mesh_name):
        MobileGameNode.__init__(self, sceneManager, player)
        
        self.set_mesh(mesh_name)
        self.mesh.setMaterialName("Ninja-" + player.element.type)
        
        # Listen to the events we care about.
        player.is_moving_changed += self.on_is_moving_changed
        player.is_charging_changed += self.on_is_charging_changed
        player.is_hooked_changed += self.on_is_hooked_changed
        player.ability_used += self.on_ability_used
        player.ability_instance_created += self.on_ability_instance_created
        player.element_changed += self.on_element_changed
        
        # Create a dict of our available animations. The animations are stored
        # as a tuple of the animation state and the speed at which the
        # animation should be played.
        self.animations = { }
        self.animations["idle"] = (self.mesh.getAnimationState("Idle2"), 1)
        self.animations["run"] = (self.mesh.getAnimationState("Walk"), 3)
        self.animations["ability_1"] = (self.mesh.getAnimationState("Attack3"), 1)
        
        # Start the idle animation
        self.animation_start("idle")
        
    def on_element_changed(self, player):
        self.mesh.setMaterialName("Ninja-" + player.element.type)
        
    def on_is_moving_changed(self, gameObject, is_moving):
        # Play running animations when the player 
        if is_moving:
            self.animation_stop("idle")
            self.animation_start("run")
        else:
            self.animation_stop("run")
            self.animation_start("idle")
            
    def on_is_charging_changed(self, player, is_charging):
        # Start/stop the charging particle effect and set the animation speed.
        multi = gamestate.abilities.FireFlameRushInstance.charge_speed_multiplier
        (anim, speed) = self.animations["run"]
        if is_charging:
            self.set_particle_system("FireTrail")
            self.particle_effect_start()
            self.animations["run"] = (anim, speed * multi)
        else:
            self.particle_effect_stop()
            self.animations["run"] = (anim, speed / multi)
    
    def on_is_hooked_changed(self, player, is_hooked):
        pass
    
    def on_ability_instance_created(self, ability, time):
        if ability.type == "FireFlameRushInstance":
            ability.collided += self.on_flame_rush_collided
        if ability.type == "EarthHookInstance":
            self.create_hook_projectile_node(ability.hook_projectile)       
    
    def on_flame_rush_collided(self, player):
        effect_node = StaticEffectNode(self.sceneManager, player.world, 2)
        effect_node.position = (player.position[0], 0, player.position[1])
        effect_node.set_particle_system("LavaSplash", (player.position[0], 0, player.position[1]))
        effect_node.particle_effect_start()
             
    def create_hook_projectile_node(self, game_object):
        projectile_node = MobileGameNode(self.sceneManager, game_object)
        projectile_node.position = (game_object.position[0], 0, game_object.position[1])
        projectile_node.set_particle_system("DustEruption")
        projectile_node.particle_effect_start() 
    
    def on_ability_used(self, player, index, ability_instance):
        
        #@todo: remove this... this is just here for an easy way to test the UI StatusBars
        player.apply_damage(20)
        
        if player.element.type == "earth":
            if index == 1:
                # Earth : Primary
                # Play the animation with weight 100 so that it basically overrides
                # any other animations currently playing.
                # @todo: use an actual solution instead of weight hack.
                self.animation_playonce("ability_1", 100)
            
            elif index == 2:
                # Earth : Hook
                # handled elsewhere
                pass
            
            elif index == 3:
                # Earth : Earthquake
                # Play the particle animation
                effect_node = StaticEffectNode(self.sceneManager, player.world, 2) 
                effect_node.set_particle_system("Earthquake", (player.position[0],
                                                               0,
                                                               player.position[1]))
                effect_node.particle_effect_start()
            
            elif index == 4:
                # Earth : Power Swing
                # Play the animation
                self.animation_playonce("ability_1", 100)

        elif player.element.type == "fire":
            if index == 1:
                # Fire : Primary
                # Play the animation with weight 100 so that it basically overrides
                # any other animations currently playing.
                # @todo: use an actual solution instead of weight hack.
                self.animation_playonce("ability_1", 100)
            elif index == 2:
                # Fire :  Flame Rush
                # note: this is handle elsewhere
                pass
            elif index == 3:
                # Fire : Lava Splash
                effect_node = StaticEffectNode(self.sceneManager, player.world, 2)
                effect_node.set_particle_system("LavaSplash", (player.position[0],
                                                               0,
                                                               player.position[1]))
                effect_node.particle_effect_start()
            
            elif index == 4:
                # Fire : Ring of Fire
                effect_node = StaticEffectNode(self.sceneManager, player.world, 3)
                effect_node.set_particle_system("RingOfFire", (player.position[0],
                                                               0,
                                                               player.position[1]))
                effect_node.particle_effect_start()
        
        elif player.element.type == "air":
            if index == 1:
                # Air : Primary
                
                # @note: this is why passing the ability_instance to on_ability_used is sloppy
                # but the effect_node that represents the projectile object on the ogre side of
                # things NEEDS a reference to the corresponding ProjectileObject.
                # Find a better way to do this someday. 
                projectile_node = ProjectileNode(self.sceneManager, ability_instance.projectile)
                projectile_node.set_particle_system("AirShot")
                projectile_node.set_secondary_particle_system("LavaSplash")
                projectile_node.particle_effect_start()
                
            if index == 2:
                # Air : Gust of Wind
                effect_node = StaticEffectNode(self.sceneManager, player.world, 0.5)
                effect_node.set_particle_system("GustOfWind", (player.position[0],
                                                               0,
                                                               player.position[1]),
                                                               player.rotation)
               
                effect_node.particle_effect_start()
                
            if index == 3:
                # Air : Wind Whisk
                effect_node1 = StaticEffectNode(self.sceneManager, player.world, 0.3)
                effect_node1.set_particle_system("WindWhisk", (ability_instance.player_start_position[0],
                                                               0,
                                                               ability_instance.player_start_position[1]))
                effect_node1.particle_effect_start()
                
                effect_node2 = StaticEffectNode(self.sceneManager, player.world, 0.3)
                effect_node2.set_particle_system("WindWhisk", (player.position[0],
                                                               0,
                                                               player.position[1]))
                effect_node2.particle_effect_start()
                
            if index == 4:
                # Air : Lightning Bolt
                if ability_instance.target is None:
                    # event was launched because ability was used, but there was no target in range
                    return
                effect_node = StaticEffectNode(self.sceneManager, player.world, 0.2)
                # @todo: come up with a particle effect for this ability
                
                dx = -player.position[0] + ability_instance.target.position[0]
                dz = -player.position[1] + ability_instance.target.position[1]
                distance = math.sqrt( dx * dx + dz * dz)
                rotation = math.atan2(dz, dx)
                x_offset = dx/2
                z_offset = dz/2
                
                effect_node.set_particle_system("Lightning", (player.position[0] + x_offset,
                                                               10,
                                                               player.position[1] + z_offset), rotation)
                
                effect_node.particle_effect_start()
                effect_node.particle_system.getEmitter(0).setParameter("depth", str(distance))
                
        elif player.element.type == "water":
            if index == 1:
                # Water : Primary
 
                # @note: this is why passing the ability_instance to on_ability_used is sloppy
                # but the effect_node that represents the projectile object on the ogre side of
                # things NEEDS a reference to the corresponding ProjectileObject.
                # Find a better way to do this someday. 
                projectile_node = ProjectileNode(self.sceneManager, ability_instance.projectile)
                #@todo: make particle effects for these
                projectile_node.set_particle_system("AirShot")
                projectile_node.set_secondary_particle_system("WaterSplash")
                projectile_node.particle_effect_start()

            elif index == 2:
                # Water : Water Gush
                effect_node = StaticEffectNode(self.sceneManager, player.world, 0.5)
                # @todo: come up with a particle effect for this ability
                
                dx = -player.position[0] + ability_instance.player_start_position[0]
                dz = -player.position[1] + ability_instance.player_start_position[1]
                distance = math.sqrt( dx * dx + dz * dz)
                rotation = math.atan2(dz, dx)
                x_offset = dx/2
                z_offset = dz/2
                
                effect_node.set_particle_system("WaterTrail", (player.position[0] + x_offset,
                                                                  5,
                                                                  player.position[1] + z_offset), rotation)
                
                effect_node.particle_effect_start()
                effect_node.particle_system.getEmitter(0).setParameter("depth", str(distance))
                
                pass
            elif index == 3:
                # Water : Tidal Wave
                effect_node = StaticEffectNode(self.sceneManager, player.world, 1)
                effect_node.set_particle_system("TidalWave", (player.position[0] + 10 * math.cos(player.rotation), 
                                                              15, 
                                                              player.position[1] + 10 * math.sin(player.rotation)), player.rotation)
                effect_node.particle_effect_start()
            elif index == 4:
                # Water : Ice Burst                
                mesh_node = StaticEffectNode(self.sceneManager, player.world, 2)
                mesh_node.set_mesh("iceblock.mesh", (player.position[0], 0, player.position[1] + 10), 0, 15)
                
                explosion_node = StaticEffectNode(self.sceneManager, player.world, 0.5, True)
                explosion_node.set_particle_system("IceBurstExplosion", (player.position[0],
                                                                         0,
                                                                         player.position[1]))
                mesh_node.static_node_expired += explosion_node.on_triggered