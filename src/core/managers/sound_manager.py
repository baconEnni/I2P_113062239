import pygame as pg
from src.utils import load_sound, GameSettings

class SoundManager:
    def __init__(self):
        pg.mixer.init()
        pg.mixer.set_num_channels(GameSettings.MAX_CHANNELS)
        self.current_bgm = None
        
    def play_bgm(self, filepath: str):
        if self.current_bgm:
            self.current_bgm.stop()
        audio = load_sound(filepath)
        if(GameSettings.MUTE == "ON"): # checkpoint2-03: mute
            audio.set_volume(0)
        else:
            audio.set_volume(GameSettings.AUDIO_VOLUME)
        audio.play(-1)
        self.current_bgm = audio
        
    # checkpoint2-03: set new volume to current_bgm (class: Sound)
    def set_volume(self, volume: float):
        if self.current_bgm:
            self.current_bgm.set_volume(volume)
        
    def pause_all(self):
        pg.mixer.pause()

    def resume_all(self):
        pg.mixer.unpause()
        
    def play_sound(self, filepath, volume=0.7):
        sound = load_sound(filepath)
        sound.set_volume(volume)
        sound.play()

    def stop_all_sounds(self):
        pg.mixer.stop()
        self.current_bgm = None