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
    
    def is_requestable(self, index):
        return self.is_oncooldown(self.ability_keys[index])
        
    def is_oncooldown(self, ability_name):
        cooldown = self.ability_cooldowns[ability_name]
        lastuse = self.last_ability_times[ability_name]
        return lastuse > 0 and self.player.world.time <= (lastuse + cooldown)


class EarthElement(Element):
    ability_cooldowns = {
        "Primary": 1,
        "Hook": 2,
        "Earthquake": 2,
        "PowerSwing": 2,
    }
    ability_keys = {
        1: "Primary",
        2: "Hook",
        3: "Earthquake",
        4: "PowerSwing",
    }
    ability_ids = {
        1: 101,
        2: 102,
        3: 103,
        4: 104,    
    }
    
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
        if self.is_oncooldown("Primary"):
            return False
        ability = abilities.EarthPrimaryInstance(self.player)
        ability.run()
        self.last_ability_times["Primary"] = self.player.world.time
        return ability
    
    def use_ability_Hook(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown("Hook"):
            return False
        ability = abilities.EarthHookInstance(self.player)
        ability.run()
        self.last_ability_times["Hook"] = self.player.world.time
        return ability
    
    def use_ability_Earthquake(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown("Earthquake"):
            return False
        ability = abilities.EarthEarthquakeInstance(self.player)
        ability.run()
        self.last_ability_times["Earthquake"] = self.player.world.time
        return ability
    
    def use_ability_PowerSwing(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown("PowerSwing"):
            return False
        ability = abilities.EarthPowerSwingInstance(self.player)
        ability.run()
        self.last_ability_times["PowerSwing"] = self.player.world.time
        return ability


class FireElement(Element):
    ability_cooldowns = {
        "Primary": 1,
        "FlameRush": 2,
        "LavaSplash": 2,
        "RingOfFire": 2,
    }
    ability_keys = {
        1: "Primary",
        2: "FlameRush",
        3: "LavaSplash",
        4: "RingOfFire",
    }
    ability_ids = {
        1: 201,
        2: 202,
        3: 203,
        4: 204,    
    }
    
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
        if self.is_oncooldown("Primary"):
            return False
        ability = abilities.FirePrimaryInstance(self.player)
        ability.run()
        self.last_ability_times["Primary"] = self.player.world.time
        return ability
        
    def use_ability_FlameRush(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown("FlameRush"):
            return False
        ability = abilities.FireFlameRushInstance(self.player)
        ability.run()
        self.last_ability_times["FlameRush"] = self.player.world.time
        return ability
    
    def use_ability_LavaSplash(self):
        if(self.player.is_ongcd()):
            return False
        if self.is_oncooldown("LavaSplash"):
            return False
        ability = abilities.FireLavaSplashInstance(self.player)
        ability.run()
        self.last_ability_times["LavaSplash"] = self.player.world.time
        return ability
    
    def use_ability_RingOfFire(self):
        if(self.player.is_ongcd()):
            return False
        if self.is_oncooldown("RingOfFire"):
            return False
        ability = abilities.FireRingOfFireInstance(self.player)
        ability.run()
        self.last_ability_times["RingOfFire"] = self.player.world.time
        return ability


class AirElement(Element):
    ability_cooldowns = {
        "Primary": 1,
        "GustOfWind": 2,
        "WindWhisk": 2,
        "LightningBolt": 2,
    }
    ability_keys = {
        1: "Primary",
        2: "GustOfWind",
        3: "WindWhisk",
        4: "LightningBolt",
    }
    ability_ids = {
        1: 301,
        2: 302,
        3: 303,
        4: 304,    
    }
    def __init__(self, player):
        Element.__init__(self, player, "air")
        
    def use_ability(self, index):
        """ Use an ability by index. """
        if index == 1:
            return self.use_ability_Primary()
        elif index == 2:
            return self.use_ability_GustOfWind()
        elif index == 3:
            return self.use_ability_WindWhisk()
        elif index == 4:
            return self.use_ability_LightningBolt()
        
    def use_ability_Primary(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown("Primary"):
            return False
        ability = abilities.AirPrimaryInstance(self.player)
        ability.run()
        self.last_ability_times["Primary"] = self.player.world.time
        return ability
        
    def use_ability_GustOfWind(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown("GustOfWind"):
            return False
        ability = abilities.AirGustOfWindInstance(self.player)
        ability.run()
        self.last_ability_times["GustOfWind"] = self.player.world.time
        return ability
    
    def use_ability_WindWhisk(self):
        if(self.player.is_ongcd()):
            return False
        if self.is_oncooldown("WindWhisk"):
            return False
        ability = abilities.AirWindWhiskInstance(self.player)
        ability.run()
        self.last_ability_times["WindWhisk"] = self.player.world.time
        return ability
    
    def use_ability_LightningBolt(self):
        if(self.player.is_ongcd()):
            return False
        if self.is_oncooldown("LightningBolt"):
            return False
        ability = abilities.AirLightningBoltInstance(self.player)
        ability.run()
        self.last_ability_times["LightningBolt"] = self.player.world.time
        return ability    


class WaterElement(Element):
    ability_cooldowns = {
        "Primary": 1,
        "WaterGush": 2,
        "TidalWave": 2,
        "IceBurst": 2,
    }
    ability_keys = {
        1: "Primary",
        2: "WaterGush",
        3: "TidalWave",
        4: "IceBurst",
    }
    ability_ids = {
        1: 401,
        2: 402,
        3: 403,
        4: 404,    
    }
    
    def __init__(self, player):
        Element.__init__(self, player, "water")
        
    def use_ability(self, index):
        """ Use an ability by index. """
        if index == 1:
            return self.use_ability_Primary()
        elif index == 2:
            return self.use_ability_WaterGush()
        elif index == 3:
            return self.use_ability_TidalWave()
        elif index == 4:
            return self.use_ability_IceBurst()
        
    def use_ability_Primary(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown("Primary"):
            return False
        ability = abilities.WaterPrimaryInstance(self.player)
        ability.run()
        self.last_ability_times["Primary"] = self.player.world.time
        return ability
        
    def use_ability_WaterGush(self):
        if self.player.is_ongcd():
            return False
        if self.is_oncooldown("WaterGush"):
            return False
        ability = abilities.WaterWaterGushInstance(self.player)
        ability.run()
        self.last_ability_times["WaterGush"] = self.player.world.time
        return ability
    
    def use_ability_TidalWave(self):
        if(self.player.is_ongcd()):
            return False
        if self.is_oncooldown("TidalWave"):
            return False
        ability = abilities.WaterTidalWaveInstance(self.player)
        ability.run()
        self.last_ability_times["TidalWave"] = self.player.world.time
        return ability
    
    def use_ability_IceBurst(self):
        if(self.player.is_ongcd()):
            return False
        if self.is_oncooldown("IceBurst"):
            return False
        ability = abilities.WaterIceBurstInstance(self.player)
        ability.run()
        self.last_ability_times["IceBurst"] = self.player.world.time
        return ability    