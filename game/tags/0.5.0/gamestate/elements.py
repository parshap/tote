from event import Event
import abilities
from collections import defaultdict

class Element(object):
    def __init__(self, player, type):
        self.player = player
        self.type = type
        self.last_ability_times = defaultdict(int)
        
    def use_ability(self, ability_id):
        """
        This method is intended to be overridden by deriving classes that
        define the element's ability usage.
        The use_ability() method should return True if the ability use was
        successful or False if it was not (e.g., on cooldown or gcd).
        """
        raise NotImplementedError("Base Element class does not implement use_ability.")
    
    def is_requestable(self, index):
        if self.is_oncooldown(self.ability_keys[index]):
            return False
        power = abilities.abilityinstances[self.ability_ids[index]].power_cost
        if power > self.player.power:
            return False
        return True
        
    def is_oncooldown(self, ability_name):
        cooldown = self.ability_cooldowns[ability_name]
        lastuse = self.last_ability_times[ability_name]
        return lastuse > 0 and self.player.world.time <= (lastuse + cooldown)


class EarthElement(Element):
    ability_cooldowns = {
        "Primary": 1,
        "Hook": 4,
        "Earthquake": 6,
        "PowerSwing": 4,
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
    ability_indexes = {
        101: 1,
        102: 2,
        103: 3,
        104: 4,
    }
    
    def __init__(self, player):
        Element.__init__(self, player, "earth")
        
    def use_ability(self, ability_id):
        """ Use an ability by index. """
        if ability_id == 101:
            return self.use_ability_Primary()
        elif ability_id == 102:
            return self.use_ability_Hook()
        elif ability_id == 103:
            return self.use_ability_Earthquake()
        elif ability_id == 104:
            return self.use_ability_PowerSwing()
        else:
            return False
    
    def use_ability_Primary(self):
#        if self.player.is_ongcd():
#            return False
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
        "FlameRush": 6,
        "LavaSplash": 6,
        "RingOfFire": 10,
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
    ability_indexes = {
        201: 1,
        202: 2,
        203: 3,
        204: 4,
    }
    
    def __init__(self, player):
        Element.__init__(self, player, "fire")
        
    def use_ability(self, ability_id):
        """ Use an ability by index. """
        if ability_id == 201:
            return self.use_ability_Primary()
        elif ability_id == 202:
            return self.use_ability_FlameRush()
        elif ability_id == 203:
            return self.use_ability_LavaSplash()
        elif ability_id == 204:
            return self.use_ability_RingOfFire()
        else:
            return False
        
    def use_ability_Primary(self):
#        if self.player.is_ongcd():
#            return False
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
        "Primary": 1.5,
        "GustOfWind": 4,
        "WindWhisk": 6,
        "LightningBolt": 6,
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
    ability_indexes = {
        301: 1,
        302: 2,
        303: 3,
        304: 4,
    }
    def __init__(self, player):
        Element.__init__(self, player, "air")
        
    def use_ability(self, ability_id):
        """ Use an ability by index. """
        if ability_id == 301:
            return self.use_ability_Primary()
        elif ability_id == 302:
            return self.use_ability_GustOfWind()
        elif ability_id == 303:
            return self.use_ability_WindWhisk()
        elif ability_id == 304:
            return self.use_ability_LightningBolt()
        else:
            return False
        
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
        "WaterGush": 6,
        "TidalWave": 5,
        "IceBurst": 15,
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
    ability_indexes = {
        401: 1,
        402: 2,
        403: 3,
        404: 4,
    }
    
    def __init__(self, player):
        Element.__init__(self, player, "water")
        
    def use_ability(self, ability_id):
        """ Use an ability by index. """
        if ability_id == 401:
            return self.use_ability_Primary()
        elif ability_id == 402:
            return self.use_ability_WaterGush()
        elif ability_id == 403:
            return self.use_ability_TidalWave()
        elif ability_id == 404:
            return self.use_ability_IceBurst()
        else:
            return False
        
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