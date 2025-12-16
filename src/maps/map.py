import pygame as pg
import pytmx

from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport
from src.utils import Logger

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.managers.game_manager import GameManager
import src.core.managers.game_manager as gm_module
from src.core import services

class Map:
    # Map Properties
    path_name: str
    tmxdata: pytmx.TiledMap
    # Position Argument
    spawn: Position
    teleporters: list[Teleport]
    # Rendering Properties
    _surface: pg.Surface
    _collision_map: list[pg.Rect]

    _bush_map: list[pg.Rect]

    def __init__(self, path: str, tp: list[Teleport], spawn: Position):
        
        self.path_name = path
        self.tmxdata = load_tmx(path)
        self.spawn = spawn
        self.teleporters = tp

        pixel_w = self.tmxdata.width * GameSettings.TILE_SIZE
        pixel_h = self.tmxdata.height * GameSettings.TILE_SIZE

        # prebake the map
        self._surface = pg.Surface((pixel_w, pixel_h), pg.SRCALPHA)
        self._render_all_layers(self._surface)
        # prebake the collision map
        self._collision_map = self._create_collision_map()
        
        self._bush_map = self._create_bush_map()
        
        # for minimap
        w, h = self._surface.get_size()
        s = 300 / max(w, h)
        self.minimap_surface = pg.transform.scale(self._surface, (int(w * s), int(h * s)))
        
    # checkpoint2-06: bush map & check collision
    def _create_bush_map(self) -> list[pg.Rect]:
        rects = []
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and ("PokemonBush" in layer.name):
                for x, y, gid in layer:
                    if gid != 0:
                        rects.append(pg.Rect(
                            x * GameSettings.TILE_SIZE,
                            y * GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE
                        ))
        return rects
    def check_bush_collision(self, rect: pg.Rect) -> bool:
        return any(rect.colliderect(r) for r in self._bush_map)

    def update(self, dt: float):
        return

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        screen.blit(self._surface, camera.transform_position(Position(0, 0)))
        # Draw the hitboxes collision map(%%%deleted)
        '''
        if GameSettings.DRAW_HITBOXES:
            for rect in self._collision_map:
                pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(rect), 1)
        '''
        
    def check_collision(self, rect: pg.Rect) -> bool:
        '''
        [TODO HACKATHON 4]
        Return True if collide if rect param collide with self._collision_map
        Hint: use API colliderect and iterate each rectangle to check
        '''
        return any(rect.colliderect(r) for r in self._collision_map)
        
    def get_teleport_entry(self, from_map: str) -> Position:
        # find from_map teleporter
        for t in self.teleporters:
            if t.destination == from_map:
                return Position(t.pos.x, t.pos.y)
        # can't find the teleporter -> use spawn
        return Position(self.spawn.x, self.spawn.y)
        
    def check_teleport(self, pos: Position) -> Teleport | None:
        '''TODO: Teleportation'''
        for teleport in self.teleporters:
            #Logger.info(f"player:{pos.x/GameSettings.TILE_SIZE}, {pos.y/GameSettings.TILE_SIZE}")
            #Logger.info(f"teleport:{teleport.to_dict()["x"]}, {teleport.to_dict()["y"]}")
            if pg.Rect(pos.x, pos.y, 
                       GameSettings.TILE_SIZE-2, GameSettings.TILE_SIZE-2).colliderect(
               pg.Rect(teleport.to_dict()["x"]*GameSettings.TILE_SIZE, teleport.to_dict()["y"]*GameSettings.TILE_SIZE,
                       GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)):
                         
                Logger.info(f"encountered teleport!")
                return teleport
        else:
            return None

    def _render_all_layers(self, target: pg.Surface) -> None:
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                self._render_tile_layer(target, layer)
            # elif isinstance(layer, pytmx.TiledImageLayer) and layer.image:
            #     target.blit(layer.image, (layer.x or 0, layer.y or 0))
 
    def _render_tile_layer(self, target: pg.Surface, layer: pytmx.TiledTileLayer) -> None:
        for x, y, gid in layer:
            if gid == 0:
                continue
            image = self.tmxdata.get_tile_image_by_gid(gid)
            if image is None:
                continue

            image = pg.transform.scale(image, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
            target.blit(image, (x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE))
    
    def _create_collision_map(self) -> list[pg.Rect]:
        rects = []
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer) and ("collision" in layer.name.lower() or "house" in layer.name.lower() or "shop" in layer.name.lower()):
                for x, y, gid in layer:
                    if gid != 0:
                        '''
                        [TODO HACKATHON 4]
                        rects.append(pg.Rect(...))
                        Append the collision rectangle to the rects[] array
                        Remember scale the rectangle with the TILE_SIZE from settings
                        '''
                        rects.append(pg.Rect(x*GameSettings.TILE_SIZE, y*GameSettings.TILE_SIZE, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        return rects

    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        tp = [Teleport.from_dict(t) for t in data["teleport"]]
        pos = Position(data["player"]["x"] * GameSettings.TILE_SIZE, data["player"]["y"] * GameSettings.TILE_SIZE)
        return cls(data["path"], tp, pos)

    def to_dict(self):
        return {
            "path": self.path_name,
            "teleport": [t.to_dict() for t in self.teleporters],
            "player": {
                "x": self.spawn.x // GameSettings.TILE_SIZE,
                "y": self.spawn.y // GameSettings.TILE_SIZE,
            }
        }
