#from event import Event
from __future__ import division
import collision
from collision import CollisionDetector
import objects
import math
from event import Event, Scheduler
from collections import defaultdict


class AbilityInstance(object):
    power_cost = 0
    def __init__(self, player):
        self.player = player
        self.expired = Event()
        self.is_active = False
        self.type = ""

    def run(self):
        self.is_active = True
        if self.player.world.is_master:
            self.player.use_power(self.power_cost)

    def update(self, dt):
        pass

    def expire(self):
        self.is_active = False
        self.expired(self)


class EarthPrimaryInstance(AbilityInstance):
    power_cost = 20
    hit_angle = math.pi/2
    damage = 25
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "EarthPrimaryInstance"
        self.range = self.player.bounding_shape.radius + 8

    def run(self):
        AbilityInstance.run(self)
        # @todo: have swing delay
        bounding_shape = collision.BoundingCone(self.range,
            self.player.rotation, self.hit_angle)
        colliders = self.player.world.get_colliders(bounding_shape,
            self.player.position, [self.player], objects.Player)
        if self.player.world.is_master:
            self.master(colliders)
        self.expire()
        
    def master(self, colliders):
        print "Earth Primary ability collided with %s players." % (len(colliders))
        for player in colliders:
            player.apply_damage(self.damage, self.player, 101)
        
class EarthHookInstance(AbilityInstance):
    power_cost = 50
    damage = 10
    projectile_velocity = 200
    projectile_radius = 12
    projectile_duration = 0.5
    retraction_speed = 200
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "EarthHookInstance"
        self.hook_projectile_created = Event()
        self.start_position = player.position
        self.start_rotation = player.rotation
        self.player_hooked = None

    def run(self):
        AbilityInstance.run(self)
        
        #make the projectile's projectileobject
        self.hook_projectile = objects.ProjectileObject(self.player,
            self.projectile_radius, self.projectile_duration)
        self.hook_projectile.position = self.start_position
        self.hook_projectile.bounding_shape = collision.BoundingCircle(self.projectile_radius)
        self.hook_projectile.rotation = self.start_rotation
        self.hook_projectile.move_speed = self.projectile_velocity
        self.hook_projectile.is_moving = True
        self.player.world.add_object(self.hook_projectile)
        self.hook_projectile.collided += self.on_collided
        
        # throw event
        self.hook_projectile_created(self.hook_projectile)
        
    def update(self, dt):
        AbilityInstance.update(self, dt)
        if self.player.world.is_master:
            if self.player_hooked is None:
                return
            if collision.CollisionDetector.check_collision(collision.BoundingCircle(8), 
                                                           self.player_hooked.position,
                                                           self.player.bounding_shape, 
                                                           self.player.position):
                self.player_hooked.is_hooked = False
                self.player_hooked.force_vector = (0, 0)
                self.expire()
            else:
                fv = (self.player.position[0] - self.player_hooked.position[0],
                      self.player.position[1] - self.player_hooked.position[1])
                fv = CollisionDetector.normalise_vector(fv)
                fv = (fv[0] * self.retraction_speed, fv[1] * self.retraction_speed)
                self.player_hooked.force_vector = fv
        
    
    def on_collided(self, object_collided_with):
        if object_collided_with.type == "player":
            if self.player.world.is_master:
                print "hook collided with player"
                if not object_collided_with.is_hooked:
                    self.player_hooked = object_collided_with
                    object_collided_with.is_hooked = True
                    object_collided_with.apply_damage(self.damage, self.player, 102)

class EarthEarthquakeInstance(AbilityInstance):
    power_cost = 50
    damage_per_tick = 7
    duration = 2
    tick_time = .5
    radius = 50
    slow_speed_multiplier = .5
    slow_time = 1.5
    
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "EarthEarthQuakeInstance"
        self.position = self.player.position
        self.bounding_circle = collision.BoundingCircle(self.radius)
        self.time_lived = 0
        self.ticks_done = 0
        self.slowed_players = []
        self.player.world.world_updated += self.update_slowed_players
        
    def run(self):
        AbilityInstance.run(self)
            
    def update(self, dt):
        AbilityInstance.update(self, dt)
#        self.update_slowed_players(dt)        
        # if the ability has expired...
        self.time_lived += dt
        if self.time_lived >= self.duration:
            print "Earthquake effect destroyed"
            self.expire()
            return
        if self.player.world.is_master:
            #otherwise each teach
            if self.time_lived >= self.ticks_done * self.tick_time:
                self.ticks_done += 1
                # get a list of players that were hit by the earthquake
                colliders = self.player.world.get_colliders(self.bounding_circle, self.position,
                                                            [self.player], objects.Player)
                self.master(colliders)

                
    class EarthQuakeScheduler(Scheduler):
        def __init__(self, player, delay):
            Scheduler.__init__(self, delay)
            self.player = player
        
        def addtime(self, time):
            self._clock += time
            if self._clock >= self._delay:
                self.is_fired = True
                self.fired(self)
            
    def on_fired(self, slow_scheduler):
        player = slow_scheduler.player
        self.slowed_players.remove(slow_scheduler)
        if not self.player_already_slowed(player):
            player.move_speed /= self.slow_speed_multiplier
            print "Run speed returned to normal."
            
    def player_already_slowed(self, player):
        still_in_list = False
        for scheduler in self.slowed_players:
            still_in_list = still_in_list or scheduler.player == player
        return still_in_list
        
    def update_slowed_players(self, dt):
        for scheduler in self.slowed_players:
            scheduler.addtime(dt)
        if len(self.slowed_players) == 0:
            return self.is_active
    
    def master(self, colliders):
        print "Earthquake collided with another player!"
        for player in colliders:
            player.apply_damage(self.damage_per_tick, self.player, 103)
            if not self.player_already_slowed(player):
                player.move_speed *= self.slow_speed_multiplier
            slow_scheduler = self.EarthQuakeScheduler(player, self.slow_time)
            slow_scheduler.fired += self.on_fired
            self.slowed_players.append(slow_scheduler)
        
class EarthPowerSwingInstance(AbilityInstance):
    power_cost = 30
    damage = 50
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "EarthPowerSwingInstance"
        self.hit_angle = math.pi/2
        self.range = 10
        
    def run(self):
        AbilityInstance.run(self)
        # @todo: have swing delay
        bounding_shape = collision.BoundingCone(
            self.range,
            self.player.rotation, self.hit_angle)
        colliders = self.player.world.get_colliders(
            bounding_shape, self.player.position,
            [self.player], objects.Player)
        if self.player.world.is_master:
            self.master(colliders)
        self.expire()
        
    def master(self, colliders):
        print "Earth Power Swing ability collided with %s players." % (len(colliders))
        for player in colliders:
            player.apply_damage(self.damage, self.player, 104)

        
class FirePrimaryInstance(AbilityInstance):
    power_cost = 20
    damage = 18
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
        if self.player.world.is_master:
            self.master(colliders)
        self.expire()
    
    def master(self, colliders):
        print "Fire Primary ability collided with %s game objects." % (len(colliders))
        for player in colliders:
            player.apply_damage(self.damage, self.player, 201)
        

class FireFlameRushInstance(AbilityInstance):
    power_cost = 30
    charge_speed_multiplier = 3
    damage = 20 
    duration = .5
    radius = 12

    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.scheduler = Scheduler(self.duration)
        self.scheduler.fired += self.expire
        self.type = "FireFlameRushInstance"
        self.collided = Event()
        

    def run(self):
        AbilityInstance.run(self)
        self.player.is_charging = True
        if self.player.world.is_master:
            self.player.move_speed *= self.charge_speed_multiplier
        self.player.collided += self.on_player_collided
        
    def on_player_collided(self, object):
        if not self.is_active:
            return False
        if not object.isPassable or object.type == "player":
            self.collided(self.player)
            # create the bounding circle to check collision against
            bounding_circle = collision.BoundingCircle(self.radius) 
            
            # get a list of colliding players
            colliders = self.player.world.get_colliders(bounding_circle, self.player.position,
                                                        [self.player], objects.Player)
            
            # for each player, apply effects
            if self.player.world.is_master:
                    self.master(colliders)
                
            self.expire()
            return False
    def master(self, colliders):
         for player in colliders:
            player.apply_damage(self.damage, self.player, 202)
            print "Flame Rush collided with some other object!"

    def update(self, dt):
        AbilityInstance.update(self, dt)
        self.scheduler.addtime(dt)

    def expire(self):
        AbilityInstance.expire(self)     
        self.player.is_charging = False
        if self.player.world.is_master:
            self.player.move_speed /= self.charge_speed_multiplier
        
class FireLavaSplashInstance(AbilityInstance):
    power_cost = 30
    damage = 25
    radius = 30
        
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
        if self.player.world.is_master:
            self.master(colliders)
                
        # end the effect
        self.expire()
    
    def master(self, colliders):
        for player in colliders:
            player.apply_damage(self.damage, self.player, 203)
            print "Lava Splash collided with another player!"
        
class FireRingOfFireInstance(AbilityInstance):
    power_cost = 50
    damage_per_tick = 25
    duration = 3
    radius = 96
    ring_thickness = 8
    tick_time = 1
    last_player_hit_times = defaultdict(int)
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "FireRingOfFireInstance"
        self.time_to_live = self.duration
        self.ring_of_fire = objects.ProjectileObject(self.player, self.radius,
                                                     self.duration)
        self.ring_of_fire.position = self.player.position
        self.ring_of_fire.bounding_shape = collision.BoundingCircle(self.radius, True)
        self.ring_of_fire.outer_bounding_circle = collision.BoundingCircle(self.radius + self.ring_thickness, True)
        self.ring_of_fire.inner_bounding_circle = collision.BoundingCircle(self.radius - self.ring_thickness, True)
        self.ring_of_fire.move_speed = 0
        self.ring_of_fire.is_moving = False
        
    def run(self):
        AbilityInstance.run(self)
        # nothing to do here really
  
    def update(self, dt):
        AbilityInstance.update(self, dt)
                
        # if the ability has expired...
        self.duration -= dt
        if self.duration <= 0:
            self.expire()
            return
        
        # otherwise do our updates
        colliders = self.player.world.get_colliders(self.ring_of_fire.bounding_shape, self.ring_of_fire.position,
                                                    [self.player], objects.Player)
        inner_colliders = self.player.world.get_colliders(self.ring_of_fire.inner_bounding_circle, self.ring_of_fire.position,
                                                    [self.player], objects.Player)
        outer_colliders = self.player.world.get_colliders(self.ring_of_fire.outer_bounding_circle, self.ring_of_fire.position,
                                                          [self.player], objects.Player)
        for collider in inner_colliders:
            colliders.append(collider)
        for collider in outer_colliders:
            colliders.append(collider)
            
        if self.player.world.is_master:
            self.master(colliders)
     
    def master(self, colliders):   
        for collider in colliders:
            # if this player has already been hit
            if self.last_player_hit_times.has_key(collider):
                if collider == self.player:
                    continue
                # check to see if the player was hit long ago enough to hit him again
                dt = self.player.world.time - self.last_player_hit_times[collider]
                if dt >= self.tick_time:
                    print "A player was hit by Ring of Fire again!"
                    self.last_player_hit_times[collider] = self.player.world.time
                    collider.apply_damage(self.damage_per_tick, self.player, 204)
                    
            # if the player has not already been hit
            else:
                self.last_player_hit_times[collider] = self.player.world.time
                print "A new player was hit by Ring of Fire!"
                collider.apply_damage(self.damage_per_tick, self.player, 204)
    
class AirPrimaryInstance(AbilityInstance):
    power_cost = 20
    start_velocity = 100
    damage_divisor = 10
    acceleration = 500
    projectile_radius = 10
    duration = 10
    collided = Event()
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "AirPrimaryInstance"
        self.projectile = objects.ProjectileObject(self.player, self.projectile_radius, self.duration)
        self.projectile.position = self.player.position
        self.projectile.collided += self.on_collided
        self.projectile.rotate(player.rotation)
                
    def run(self):
        AbilityInstance.run(self)
        self.projectile.move_speed = self.start_velocity
        self.projectile.is_moving = True
  
    def update(self, dt):
        AbilityInstance.update(self, dt)
        self.projectile.move_speed += self.acceleration * dt
        
    def on_collided(self, object_collided_with):
        if not object_collided_with == self.player:
            self.collided()
        if object_collided_with.type == "player":
            if self.player.world.is_master:
                self.master(object_collided_with)
    
    def master(self, player):
        damage = int(self.projectile.move_speed / self.damage_divisor)
        player.apply_damage(damage, self.player, 301)
        print "Air Shot collided with another player for " + str(damage) + " damage!"
        
class AirGustOfWindInstance(AbilityInstance):
    power_cost = 30
    starting_strength = 300
    acceleration_factor = 1
    hit_radius = 60
    hit_angle = math.pi * 2 / 3
    duration = 0.5
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "AirGustOfWindInstance"
        self.targets = []
    
    def run(self):
        AbilityInstance.run(self)
        if self.player.world.is_master:
            # create the bounding circle to check collision against
            bounding_cone = collision.BoundingCone(self.hit_radius, self.player.rotation, self.hit_angle) 
            
            # get a list of colliding players
            self.targets = self.player.world.get_colliders(bounding_cone, self.player.position,
                                                        [self.player], objects.Player)
            
            # for each player, apply effects
            for player in self.targets:
                # get force vector for other player
                force_vector = ((player.position[0] - self.player.position[0],
                                 player.position[1] - self.player.position[1]))
                force_vector = CollisionDetector.normalise_vector(force_vector)
                player.force_vector = (force_vector[0] * self.starting_strength,
                    force_vector[1] * self.starting_strength)
                print "Gust of wind collided with another player!"
                
        # end the effect
        self.expire()
        
    def update(self, dt):
        self.duration -= dt
        if self.player.world.is_master:
            if self.duration <= 0:
                self.duration = 0
                for player in self.targets:
                    player.force_vector = (0, 0)
                self.expire()
                
            for player in self.targets:
                old_fv = player.force_vector
                
                # calculate new force vector
                fv = (old_fv[0] * ((self.acceleration_factor * dt) + 1),
                      old_fv[1] * ((self.acceleration_factor * dt) + 1))
                
                # apply the new force vector
                player.force_vector = fv
        
class AirWindWhiskInstance(AbilityInstance):
    power_cost = 30
    teleport_distance = 100
    
    # increasing move_samples increases collision detection accuracy (no jumping over stuff etc)
    # at the cost of extra calculation time. Each sample will be tested at intervals of length
    # (teleport_distance / move_samples).
    move_samples = 30 
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "AirGustOfWindInstance"
        self.has_collided = False
        self.player_start_position = player.position
        
    def run(self):
        AbilityInstance.run(self)
        # hackish implementation
        # @todo: make this less hackish
        if self.player.world.is_master:    
            i = 0
            while i < self.move_samples:
                sample_position = (self.player.position[0] + (self.teleport_distance /  self.move_samples) * math.cos(self.player.rotation),
                                   self.player.position[1] + (self.teleport_distance /  self.move_samples) * math.sin(self.player.rotation))
                colliders = self.player.world.get_colliders(self.player.bounding_shape, sample_position,
                                                       [self.player])
                for collider in colliders:
                    if collider.type == "player" or collider.type == "projectile":
                        continue
                    else:
                        self.has_collided = True
                move_vector = (sample_position[0] - self.player.position[0], sample_position[1] - self.player.position[1])
                self.player._move(move_vector) # <-- this is why it's hackish
                i += 1
            self.player.teleported()
        # end the effect
        self.expire()
        
class AirLightningBoltInstance(AbilityInstance):
    power_cost = 50
    damage = 20
    range = 100
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.target = None
        
    def run(self):
        AbilityInstance.run(self)
        
        bounding_circle = collision.BoundingCircle(self.range) 
        
        # find a target
        colliders = self.player.world.get_colliders(bounding_circle, self.player.position,
                                                    [self.player], objects.Player)
        if len(colliders) == 0:
            # no targets in range
            return
        
        self.target = colliders[0]
        min_distance = self._square_of_distance(self.player, colliders[0])
        
        for collider in colliders:
            distance_to_collider = self._square_of_distance(self.player, collider)
            if distance_to_collider < min_distance:
                min_distance = distance_to_collider
                self.target = collider
                
        # target found, cast spell
        # @todo: apply damage to self.target here 
        if self.player.world.is_master:
            self.master(self.target)
        
    def _square_of_distance(self, player1, player2):
        return (player2.position[0] - player1.position[0]) * (player2.position[0] - player1.position[0]) + (player2.position[1] - player1.position[1]) * (player2.position[1] - player1.position[1])
                
    def master(self, target):
        target.apply_damage(self.damage, self.player, 304)
        print "Another player was hit by lightning bolt!"
        
    def update(self, dt):
        AbilityInstance.update(self, dt)
    
    def expire(self):
        AbilityInstance.expire(self)
        
class WaterPrimaryInstance(AbilityInstance):
    power_cost = 20
    speed = 200
    projectile_radius = 20
    duration = 20
    damage = 15
    collided = Event()
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "WaterPrimaryInstance"
        self.projectile = objects.ProjectileObject(self.player, self.projectile_radius, self.duration)
        self.projectile.position = self.player.position
        self.projectile.collided += self.on_collided
        self.projectile.rotate(player.rotation)
                
    def run(self):
        AbilityInstance.run(self)
        self.projectile.move_speed = self.speed
        self.projectile.is_moving = True
  
    def update(self, dt):
        AbilityInstance.update(self, dt)
        
    def on_collided(self, object_collided_with):
        if not object_collided_with == self.player:
            self.collided()
        if self.player.world.is_master:
            self.master(object_collided_with)
            
            
    def master(self, object_collided_with):
        if object_collided_with.type == "player":
            object_collided_with.apply_damage(self.damage, self.player, 401)
            print "Ice Shot collided with another player!"


class WaterWaterGushInstance(AbilityInstance):  
    power_cost = 30
    damage = 25
    teleport_distance = 100
    
    # increasing move_samples increases collision detection accuracy (no jumping over stuff etc)
    # at the cost of extra calculation time. Each sample will be tested at intervals of length
    # (teleport_distance / move_samples).
    move_samples = 30 
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "WaterWaterGushInstance"
        self.has_collided = False
        self.player_start_position = player.position
        
    
    def run(self):
        AbilityInstance.run(self)
        # hackish implementation
        # @todo: make this less hackish
        if self.player.world.is_master:
            i = 0
            already_collided = defaultdict(int)
            while i < self.move_samples:
                sample_position = (self.player.position[0] + (self.teleport_distance /  self.move_samples) * math.cos(self.player.rotation),
                                   self.player.position[1] + (self.teleport_distance /  self.move_samples) * math.sin(self.player.rotation))
                colliders = self.player.world.get_colliders(self.player.bounding_shape, sample_position,
                                                       [self.player])
                for collider in colliders:
                    if collider.type == "projectile":
                        continue
                    elif collider.type == "player":
                        if not already_collided[collider]:
                            collider.apply_damage(self.damage, self.player, 402)
                            already_collided[collider] = True
                            print "Water Gush collided with another player!"
                    else:
                        self.has_collided = True
                move_vector = (sample_position[0] - self.player.position[0], sample_position[1] - self.player.position[1])
                self.player._move(move_vector) # <-- this is why it's hackish
                i += 1
            self.player.teleported()
        # end the effect
        self.expire()      
        
class WaterTidalWaveInstance(AbilityInstance):
    power_cost = 30
    hit_radius = 90
    hit_angle = math.pi / 2
    damage = 20
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "WaterTidalWaveInstance"
    
    def run(self):
        AbilityInstance.run(self)
        if self.player.world.is_master:
            self.master()
        # end the effect
        self.expire()
    
    def master(self):
        # create the bounding circle to check collision against
        bounding_cone = collision.BoundingCone(self.hit_radius, self.player.rotation, self.hit_angle) 
        # get a list of colliding players
        colliders = self.player.world.get_colliders(bounding_cone, self.player.position,
                                                    [self.player], objects.Player)
        # for each player, apply effects
        for player in colliders:
            player.apply_damage(self.damage, self.player, 403)
            print "Tidal Wave collided with another player!"
        
class WaterIceBurstInstance(AbilityInstance):
    power_cost = 50
    invulnerable_duration = 1
    shard_damage = 35
    shard_radius = 30
    
    def __init__(self, player):
        AbilityInstance.__init__(self, player)
        self.type = "WaterIceBurstInstance"
        
    def run(self):
        AbilityInstance.run(self)        
        self.player.is_invulnerable = True
        self.player.is_immobilized = True
        print "Player invulnerable for 2 seconds!"
            
    def update(self, dt):
        AbilityInstance.update(self, dt)
        self.invulnerable_duration -= dt
        if self.invulnerable_duration <= 0:
            self.player.is_invulnerable = False
            self.player.is_immobilized = False
            self.create_shard_explosion()
            
    def create_shard_explosion(self):        
        if self.player.world.is_master:
            self.master()
                
        # end the effect
        self.expire()
    
    def master(self):
        bounding_circle = collision.BoundingCircle(self.shard_radius) 
        
        # get a list of colliding players
        colliders = self.player.world.get_colliders(bounding_circle, self.player.position,
                                                    [self.player], objects.Player)
        # for each player, apply effects
        for player in colliders:
            player.apply_damage(self.shard_damage, self.player, 404)
            print "Ice Burst collided with another player!"