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
    def __init__(self, soundManager):
        self.soundManager = soundManager
        self.active_sounds = { }
        self.sound_id = 0 # for unique IDs
        print "creating soundplayer"
    
    def get_unique_id(self, name):
        self.sound_id += 1
        return name + str(self.sound_id)   
        
    def play(self, sound_name, looping = False, streaming = False):
        """
        Plays the soundfile soundname.
        """
        unique_name = self.get_unique_id(sound_name)
        sound = self.soundManager.createSound(unique_name, 
                                              sound_name, 
                                              looping, 
                                              streaming)
        self.active_sounds[unique_name] = sound
        
        sound.play()
    
    def update(self, dt):
        remove_list = []
        for key in self.active_sounds:
            sound = self.active_sounds[key]
            if sound.isStopped():
                print "removing " + key
                remove_list.append(key)
        for key in remove_list:
            self.soundManager.destroySound(key)
            del self.active_sounds[key]
    
       