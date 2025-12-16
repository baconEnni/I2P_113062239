import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item


class Bag:
    _monsters_data: list[Monster]
    _items_data: list[Item]
    coins: int

    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None):
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        
        self.coins = 0
        for item in self._items_data:
            if item["name"].lower() == "coins":
                self.coins = item["count"]

    def update(self, dt: float):
        pass

    def draw(self, screen: pg.Surface):
        pass
    
    ### for shop
    # coins & coins syncronize
    def sync_coins_item(self):
        found = False
        for item in self._items_data:
            if item["name"].lower() == "coins":
                item["count"] = self.coins
                found = True
                break
        if not found:
            # (default) no coins add one
            self._items_data.append({
                "name": "Coins",
                "count": self.coins,
                "sprite_path": "ingame_ui/coin.png",
            })

    def can_afford(self, price: int) -> bool:
        return self.coins >= price

    def pay(self, price: int) -> bool:
        # enough coins -> pay -> True
        if self.coins >= price:
            self.coins -= price
            self.sync_coins_item()
            return True
        return False
            
    def add_item(self, name: str, sprite_path: str, count: int = 1):
        # potion & pokeball
        for item in self._items_data:
            if item["name"] == name:
                item["count"] += count
                return
        self._items_data.append({
            "name": name,
            "count": count,
            "sprite_path": sprite_path,
        })

    def add_monster(self, monster_data: dict):
        self._monsters_data.append(monster_data)
    ###

    def to_dict(self) -> dict[str, object]:
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data)
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        monsters = data.get("monsters") or []
        for m in monsters:
            if "countdown" not in m:
                m["countdown"] = 540
        items = data.get("items") or []
        bag = cls(monsters, items)
        return bag