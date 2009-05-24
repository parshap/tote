from event import Event
import abilities
from collections import defaultdict

class Element(object):
    def __init__(self, player, type):
        self.player = player
        self.type = type
        self.last_ability_times = defaultdict(int)
        
    def use_ability(self, index):
        """
        This method is intended to be overridden by deriving classes that
        define the element's ability usage.
        The use_ability() method should return True if the ability use was
        successful or False if it was not (e.g., on cooldown or gcd).
        """
        raise NotImplementedError("Base Element class does not implement use_ability.")
        
    def is_oncooldown(self, cooldown, lastuse):
        return lastuse > 0 and self.player.world.time <= (lastuse + cooldown)


class EarthElement(Element):
    def __init__(self, player):
        Element.__init__(self, player, "earth")
        
    def use_ability(self, index):
        """ Use an ability by index. """
        if index == 1:
            return self.use_ability_Primary()
        elif index == 2:
            return self.use_ability_Hook()
        elif index == 3:
            return self.use_ability_Earthquake()
        elif index == 4:
            return self.use_ability_PowerSwing()
        
    def use_ability_Primary(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown(2, self.last_ability_times["Primary"]):
            return False
        ability = abilities.EarthPrimaryInstance(self.player)
        ability.run()
        self.last_ability_times["Primary"] = self.player.world.time
        return ability
    
    def use_ability_Hook(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown(1, self.last_ability_times["Hook"]):
            return False
        ability = abilities.EarthHookInstance(self.player)
        ability.run()
        self.last_ability_times["Hook"] = self.player.world.time
        return ability
    
    def use_ability_Earthquake(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown(1, self.last_ability_times["Earthquake"]):
            return False
        ability = abilities.EarthEarthquakeInstance(self.player)
        ability.run()
        print "Used ability: Earthquake"
        self.last_ability_times["Earthquake"] = self.player.world.time
        return ability
    
    def use_ability_PowerSwing(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown(1, self.last_ability_times["PowerSwing"]):
            return False
        ability = abilities.EarthPowerSwingInstance(self.player)
        ability.run()
        print "Used ability: PowerSwing"
        self.last_ability_times["PowerSwing"] = self.player.world.time
        return ability


class FireElement(Element):
    def __init__(self, player):
        Element.__init__(self, player, "fire")
        
    def use_ability(self, index):
        """ Use an ability by index. """
        if index == 1:
            return self.use_ability_Primary()
        elif index == 2:
            return self.use_ability_FlameRush()
        elif index == 3:
            return self.use_ability_LavaSplash()
        elif index == 4:
            return self.use_ability_RingOfFire()
        
    def use_ability_Primary(self):
        if self.player.is_ongcd():
            return False
        ability = abilities.FirePrimaryInstance(self.player)
        ability.run()
        self.last_ability_times["Primary"] = self.player.world.time
        return ability
        
    def use_ability_FlameRush(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown(2, self.last_ability_times["FlameRush"]):
            return False
        ability = abilities.FireFlameRushInstance(self.player)
        ability.run()
        self.last_ability_times["FlameRush"] = self.player.world.time
        return ability
    
    def use_ability_LavaSplash(self):
        cooldown = 2
        if(self.player.is_ongcd()):
            return False
        if self.is_oncooldown(cooldown, self.last_ability_times["LavaSplash"]):
            return False
        ability = abilities.FireLavaSplashInstance(self.player)
        ability.run()
        self.last_ability_times["LavaSplash"] = self.player.world.time
        return ability
    
    def use_ability_RingOfFire(self):
        cooldown = 2
        if(self.player.is_ongcd()):
            return False
        if self.is_oncooldown(cooldown, self.last_ability_times["RingOfFire"]):
            return False
        ability = abilities.FireRingOfFireInstance(self.player)
        ability.run()
        self.last_ability_times["RingOfFire"] = self.player.world.time
        return ability

    