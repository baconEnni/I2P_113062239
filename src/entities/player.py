from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager, resource_manager #resource_manager for warning image
from src.utils import Position, PositionCamera, GameSettings, Logger, Direction
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.managers.game_manager import GameManager
import math
from typing import override

class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)
        self._set_direction("DOWN")
        
    def _set_direction(self, direction: str) -> None:
        self.direction = direction
        if direction == "RIGHT":
            self.animation.switch("right")
        elif direction == "LEFT":
            self.animation.switch("left")
        elif direction == "DOWN":
            self.animation.switch("down")
        else:
            self.animation.switch("up")
        self.los_direction = self.direction

    @override
    def update(self, dt: float) -> None:
        dis = Position(0, 0)
        '''
        [TODO HACKATHON 2]
        Calculate the distance change, and then normalize the distance
        
        [TODO HACKATHON 4]
        Check if there is collision, if so try to make the movement smooth
        Hint #1 : use entity.py _snap_to_grid function or create a similar function
        Hint #2 : Beware of glitchy teleportation, you must do
                    1. Update X
                    2. If collide, snap to grid
                    3. Update Y
                    4. If collide, snap to grid
                  instead of update both x, y, then snap to grid
        
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= ...
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += ...
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= ...
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += ...
        
        self.position = ...
        '''
        
        '''
        def _snap_to_grid(value: float) -> int:
        return round(value / GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE
        '''
    
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            self.game_manager.collide_enemy_trainers = False
            dis.x -= 1
            self._set_direction("LEFT")
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            self.game_manager.collide_enemy_trainers = False
            dis.x += 1
            self._set_direction("RIGHT")
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            self.game_manager.collide_enemy_trainers = False
            dis.y -= 1
            self._set_direction("UP")
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            self.game_manager.collide_enemy_trainers = False
            dis.y += 1
            self._set_direction("DOWN")
        
        if not (dis.x == 0 and dis.y == 0):
            length = (dis.x**2 + dis.y**2)**0.5
            dx = dis.x/length*self.speed /GameSettings.TILE_SIZE
            dy = dis.y/length*self.speed /GameSettings.TILE_SIZE
            future_x = self.position.x + dx
            future_y = self.position.y + dy
            
            # Check teleportation
            tp = self.game_manager.current_map.check_teleport(Position(future_x+2, 
                                                                       future_y+2))
            if tp:
                map_to = tp.destination
                
                dest_map = self.game_manager.maps[map_to]
                entry = dest_map.get_teleport_entry(self.game_manager.current_map_key)
                self.game_manager.entry_pos = entry
                
                self.game_manager.switch_map(map_to)

            if not self.game_manager.check_collision(pg.Rect(future_x+2, self.position.y+2,
                    GameSettings.TILE_SIZE-2, GameSettings.TILE_SIZE-2)) and not self.game_manager.overlay_open:
                self.position.x = future_x
                #Logger.info(f"player: ({self.position.x/GameSettings.TILE_SIZE}, {self.position.y/GameSettings.TILE_SIZE})")
        
            if not self.game_manager.check_collision(pg.Rect(self.position.x+2, future_y+2,
                    GameSettings.TILE_SIZE-2, GameSettings.TILE_SIZE-2)) and not self.game_manager.overlay_open:
                self.position.y = future_y
                #Logger.info(f"player: ({self.position.x/GameSettings.TILE_SIZE}, {self.position.y/GameSettings.TILE_SIZE})")
        
        # chackpoint2-06: check collision    
        player_rect = pg.Rect(
            self.position.x+2,
            self.position.y+2,
            GameSettings.TILE_SIZE-4,
            GameSettings.TILE_SIZE-4
        )

        if self.game_manager.current_map.check_bush_collision(player_rect):
            self.game_manager.collide_bush = True
        else:
            self.game_manager.collide_bush = False
                
        super().update(dt)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @property
    @override
    def camera(self) -> PositionCamera:
        return PositionCamera(int(self.position.x) - GameSettings.SCREEN_WIDTH // 2, int(self.position.y) - GameSettings.SCREEN_HEIGHT // 2)
            
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)

