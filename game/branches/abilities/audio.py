from __future__ import division
import gamestate.abilities
import gamestate.event
import ogre.sound.OgreAL._ogreal_ as OgreAL

class SoundPlayer:
    """
    SoundPlayer is our OgreAL soundwrapper. It has a very simple interface.
    Step 1: Make sure the sound resource is loaded
    Step 2: Call play() and pass it <soundname>.<extension> NO DIR PATHS
    """
    def __init__(self):
        self.soundManager = OgreAL.SoundManager()
        self.active_sounds = { }
        self.sound_id = 0 # for unique IDs
        
    def play(self, sound_name):
        """
        Plays the soundfile soundname.
        """
        self.sound_id += 1
        print str(self.sound_id)
        unique_name = sound_name + "%d"%self.sound_id
        sound = self.soundManager.createSound(unique_name, 
                                              sound_name, 
                                              False, 
                                              False)
        self.active_sounds[unique_name] = sound
        print "playing sound: " + unique_name
        sound.play()
        self.destroy_inactive_sounds()
        
    def destroy_inactive_sounds(self):
        remove_list = []
        for key in self.active_sounds:
            if not self.active_sounds[key].isPlaying():
                remove_list.append(key)
        for item_to_remove in remove_list:
            self.soundManager.destroySound(item_to_remove)
            del self.active_sounds[item_to_remove]
        
    
       