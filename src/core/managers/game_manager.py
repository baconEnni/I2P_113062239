from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport
from src.utils.definition import Monster
import json, os
import pygame as pg
from typing import TYPE_CHECKING
from src.entities.shop_npc import ShopNPC

if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.data.bag import Bag

class GameManager:
    # Entities
    player: Player | None
    enemy_trainers: dict[str, list[EnemyTrainer]] 
    bag: "Bag"
    
    # Map properties
    current_map_key: str
    maps: dict[str, Map]
    
    # Changing Scene properties
    should_change_scene: bool
    next_map: str
    
    # collide with enemy trainers
    collide_enemy_trainer: EnemyTrainer
    collide_enemy_trainers: bool
    enemy_monster: dict | None
    enemy_trainer_pos: Position | None
    
    # bush collision
    collide_bush: bool
    
    # record last leave position
    entry_pos: Position | None = None
    last_positions: dict[str, Position]
    
    # save old data
    _original_data: dict[str, object]
    
    # shop
    collide_shops: bool #shop collision
    collide_shop_npc: ShopNPC
    #open_shop_flag: bool
    shops: dict[str, list[ShopNPC]] # dict: map_name → list of ShopNPC
    
    # overlay open player don't move
    overlay_open: bool
    
    # chosen monster for battle
    monster_idx: int
    # after battle end
    win_message: bool
    player_monster: dict
    
    def __init__(self, maps: dict[str, Map], start_map: str, 
                 player: Player | None,
                 enemy_trainers: dict[str, list[EnemyTrainer]], 
                 bag: Bag | None = None):
                     
        from src.data.bag import Bag
        # Game Properties
        self.maps = maps
        self.current_map_key = start_map
        self.player = player
        self.enemy_trainers = enemy_trainers
        self.bag = bag if bag is not None else Bag([], [])
        
        # Check If you should change scene
        self.should_change_scene = False
        self.next_map = ""
        
        self.collide_enemy_trainer = None
        self.collide_enemy_trainers = False
        self.enemy_monster = None
        self.enemy_MONSTER = None
        self.enemy_trainer_pos = None
        
        self.collide_bush = False
        
        self.last_positions = {map_name: Position(self.maps[map_name].spawn.x, self.maps[map_name].spawn.y)
                               for map_name in maps.keys()}
        
        # for shops
        self.collide_shops = False
        self.collide_shop_npc = None
        #self.open_shop_flag = False
        self.shops = {}
        
        self.overlay_open = False
        
        self.monster_idx = 0
        self.win_message = False
        
        self.account_name = ""
        player_monster = None
        
    @property
    def current_map(self) -> Map:
        return self.maps[self.current_map_key]
        
    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        return self.enemy_trainers[self.current_map_key]
        
    @property
    def current_teleporter(self) -> list[Teleport]:
        return self.maps[self.current_map_key].teleporters
    
    def switch_map(self, target: str) -> None:
        if target not in self.maps:
            Logger.warning(f"Map '{target}' not loaded; cannot switch.")
            return
        
        if self.player:
            self.last_positions[self.current_map_key] = Position(
                self.player.position.x,
                self.player.position.y
            )
        
        self.next_map = target
        self.should_change_scene = True
            
    def try_switch_map(self) -> None:
        if self.should_change_scene:
            self.current_map_key = self.next_map
            self.next_map = ""
            self.should_change_scene = False
            if self.player:
                if self.entry_pos is not None:
                    # first time enter
                    if self.current_map_key == "gym.tmx":
                        self.player.position = Position(self.entry_pos.x, self.entry_pos.y - 2*GameSettings.TILE_SIZE)
                    else:
                        self.player.position = Position(self.entry_pos.x, self.entry_pos.y + 2*GameSettings.TILE_SIZE)
                    self.entry_pos = None
                else:
                    # entered before
                    lp = self.last_positions[self.current_map_key]
                    self.player.position = Position(lp.x, lp.y+ 2*GameSettings.TILE_SIZE)
            
    def check_collision(self, rect: pg.Rect) -> bool:
        if self.maps[self.current_map_key].check_collision(rect):
            return True
        for entity in self.enemy_trainers[self.current_map_key]:
            if rect.colliderect(entity.animation.rect) and not self.overlay_open:
                # chackpoint2-05: collide with enemy_trainers
                self.enemy_trainer_pos = Position(entity.animation.rect.x, entity.animation.rect.y)
                self.enemy_monster = entity.monster
                self.collide_enemy_trainers = True
                #Logger.info(f"Collided with enemy trainer (pos: {self.enemy_trainer_pos.x}, {self.enemy_trainer_pos.y})")
                #Logger.info(f"player pos: ({rect.x}, {rect.y})")
                self.collide_enemy_trainer = entity
                return True
        for entity in self.shops.get(self.current_map_key, []):
            if rect.colliderect(entity.animation.rect) and not self.overlay_open:
                self.collide_shops = True
                self.collide_shop_npc = entity
                return True
        return False
        
    def save(self, path: str) -> None:
        try:
            with open(path, "w") as f:
                json.dump(self.to_dict(), f, indent=2)
            Logger.info(f"Game saved to {path}")
        except Exception as e:
            Logger.warning(f"Failed to save game: {e}")
             
    @classmethod
    def load(cls, path: str) -> "GameManager | None":
        if not os.path.exists(path):
            Logger.error(f"No file found: {path}, ignoring load function")
            return None

        with open(path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    def to_dict(self) -> dict[str, object]:
        map_blocks: list[dict[str, object]] = []
        for key, m in self.maps.items():
            block = m.to_dict()
            block["enemy_trainers"] = [t.to_dict() for t in self.enemy_trainers.get(key, [])]
            
            block["shops"] = []
            for npc in self.shops.get(key, []):

                # monsters-only(without items, only monsters)
                monsters_only = []
                for item_or_monster, price in npc.shop_items:
                    # dict -> monster
                    if isinstance(item_or_monster, dict):
                        monster = item_or_monster.copy()
                        monster["price"] = price
                        monsters_only.append(monster)

                block["shops"].append({
                    "x": int(npc.position.x // GameSettings.TILE_SIZE),
                    "y": int(npc.position.y // GameSettings.TILE_SIZE),
                    "monsters": monsters_only
                })
            
            map_blocks.append(block)
            
        # player, map in .json don't update
        original_player = self._original_data.get("player", None)
        original_map = self._original_data.get("current_map", None)
        
        return {
            "map": map_blocks,
            "current_map": original_map,
            "player": original_player,
            "bag": self.bag.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GameManager":
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer
        from src.data.bag import Bag
        
        Logger.info("Loading maps")
        maps_data = data["map"]
        maps: dict[str, Map] = {}
        player_spawns: dict[str, Position] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}

        for entry in maps_data:
            path = entry["path"]
            maps[path] = Map.from_dict(entry)
            sp = entry.get("player")
            if sp:
                player_spawns[path] = Position(
                    sp["x"] * GameSettings.TILE_SIZE,
                    sp["y"] * GameSettings.TILE_SIZE
                )
        current_map = data["current_map"]
        gm = cls(
            maps, current_map,
            None, # Player
            trainers,
            bag=None
        )
        gm.current_map_key = current_map
        
        gm._original_data = data #save old data
        
        Logger.info("Loading enemy trainers")
        for m in data["map"]:
            raw_data = m["enemy_trainers"]
            gm.enemy_trainers[m["path"]] = [EnemyTrainer.from_dict(t, gm) for t in raw_data]
                 
        for m in data["map"]:
            shops_raw = m.get("shops", [])
            gm.shops[m["path"]] = []
            for s in shops_raw:
                sx = s["x"] * GameSettings.TILE_SIZE
                sy = s["y"] * GameSettings.TILE_SIZE
                
                monsters = s.get("monsters", [])  
                # [ {"name":"Pikachu",....., "price":200}, ... ]
                monster_list = [({k: v for k, v in m.items() if k != "price"}, m["price"]) for m in monsters]
                gm.shops[m["path"]].append(
                    ShopNPC(sx, sy, gm, monsters_for_sale=monster_list)
                )
        
        Logger.info("Loading Player")
        if data.get("player"):
            gm.player = Player.from_dict(data["player"], gm)
        
        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag
        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag( [], [])

        return gm