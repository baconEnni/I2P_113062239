from __future__ import annotations
import pygame
from src.entities.entity import Entity
from src.core.services import input_manager
from src.utils import GameSettings
from src.sprites import Sprite, Animation

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.managers.game_manager import GameManager

'''[TODO] items(different ShopNPC sell different items)'''
class ShopNPC(Entity):
    shop_items: list[tuple[dict | str, int]]
    
    def __init__(self, x: float, y: float, game_manager: "GameManager",
                 monsters_for_sale: list[tuple[dict, int]] | None = None):
        super().__init__(x, y, game_manager)
        self.animation = Animation(
            "character/ow2.png", ["down", "left", "right", "up"], 4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )
        
        ## shop items
        self.shop_items = [
            ("Heal Potion", 50),
            ("Strength Potion", 50),
            ("Defense Potion", 50),
            ("Max Potion", 100),
            ("Pokeball", 150)
        ]
        # monsters for the ShopNPC
        if monsters_for_sale:
            self.shop_items += monsters_for_sale
        
        self.interact_radius = GameSettings.TILE_SIZE

    def is_player_near(self):
        player = self.game_manager.player
        if player is None:
            return False
        dx = abs(self.position.x - player.position.x)
        dy = abs(self.position.y - player.position.y)
        return dx < self.interact_radius and dy < self.interact_radius

    def update(self, dt: float):
        self.animation.update_pos(self.position)

    def draw(self, screen, camera):
        super().draw(screen, camera)
