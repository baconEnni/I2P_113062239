import pygame as pg

from .sprite import Sprite
from src.utils import GameSettings

# DONE highlight'-01: add w, h, x, y for overlay
class BackgroundSprite(Sprite):
    def __init__(self, image_path: str, w = GameSettings.SCREEN_WIDTH, h = GameSettings.SCREEN_HEIGHT):
        super().__init__(image_path, (w, h))
        
    def draw(self, screen: pg.Surface, x=0, y=0):
        screen.blit(self.image, (x, y))
        
