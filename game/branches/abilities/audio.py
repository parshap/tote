import pyglet.media as media


"""
GameAudioPlayer is a complete interface for playing sounds and music using pyglet.media.
It currently only supports .wav media files.
"""
_sources = { }
_bg_music_player = None
_bg_music_source = None

_bg_music_volume = 1.0
_sound_volume = 1.0
    
def play_sound(name, volume = 1.0):
    """
    Plays the sound with the registered name once.
    """ 
    
    global _sources
    global _sound_volume
    
    # Get the StaticSource from our source dict
    source = _sources[name]
    if source is not None:
        # Create a ManagedPlayer to play the sound by calling source.play()
        # Upon completion of playing, the ManagedPlayer will destroy it
        player = source.play()
        player.volume = volume * _sound_volume
        
    else:
        print "Source " + name + " could not be found!"
        
def load_source(name, path):
    """
    Registers a new sound with the name "name" from the source specified by "path".
    Once a source has been loaded, you can play it by calling AudioPlayer.play("name")
    """
    global _sources
    
    # Use pyglet.media to load the Source
    source = media.load(path)
    
    if source is not None:
        # Convert our source to a static source to allow for 
        # overlapping playback
        static_source = media.StaticSource(source)
        _sources[name] = static_source
    else:
        print "Unable to load " + path + ", check path."
        
def set_background_music(path, looping = True):
    """
    Sets the background music to the file specified by "path"
    Once background music has been set, you can play it by calling AudioPlayer.play_background_music()
    """
    
    # Background music is handled a bit differently than other sounds
    # Since it must stream and loop, we cannot use StaticSource.play() to create a ManagedPlayer
    # Instead, load create a Source object from file, and a Player() from this Source
    # This will be our background music Player
    global _bg_music_source
    global _bg_music_player
    
    _bg_music_source = media.load(path, None, looping)
    _bg_music_player = media.Player()
    _bg_music_player.queue(_bg_music_source)
    _bg_music_player.pause()
    print "set music"

def test(player):
    player.pause()
    print "EOS"
    
def play_background_music(volume = 0.5):
    """
    Plays the background music track.
    """
    
    global _bg_music_player
    global _bg_music_volume
    
    if _bg_music_player is not None:
        _bg_music_player.volume = volume * _bg_music_volume
        _bg_music_player.play()
    else:
        print "No background music source loaded!"

def update(dt):
    """
    Necessary for Player objects to throw EOS events when sounds end. The handlers
    for these events determine the Player's behavior on completion of the sound (destroy, loop, etc)
    """
    global _bg_music_player
    
    if _bg_music_player is not None:
        _bg_music_player.dispatch_events()
    
    for player in media.managed_players:
        player.dispatch_events()