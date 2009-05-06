from event import Event
import abilities

class Element(object):
    def __init__(self, player):
        # Hold a reference to the player that is "using" this element.
        self.player = player
        self.type = ""
        
    def useAbility(self, index):
        """
        This method is intended to be overridden by deriving classes that
        define the element's ability usage.
        The useAbility() method should return True if the ability use was
        successful or False if it was not (e.g., on cooldown or gcd).
        """
        raise NotImplementedError("Base Element class does not implement useAbility.")


class EarthElement(Element):
    def __init__(self, player):
        Element.__init__(self, player)
        self.type = "earth"
        
    def useAbility(self, index):
        """ Use an ability by index. """
        if index == 1:
            return self.useAbilityPrimary()
        elif index == 2:
            # ...
            pass
        
    def useAbilityPrimary(self):
        # @todo: check gcd and ability cooldown.
        ability = abilities.EarthPrimaryInstance(self.player)
        ability.run()
        return True
