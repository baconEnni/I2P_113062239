import pygame as pg

from src.utils import GameSettings, load_font, Logger
from src.core import OnlineManager
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.managers.game_manager import GameManager
from src.core import services
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager, game_manager
from src.utils.definition import Monster
from typing import override

import random # for choosing bush monster

class MonsterObj:
    def __init__(self, data: dict):
        self._data = data
    
    @property
    def name(self) -> str:
        return self._data["name"]

    @property
    def hp(self) -> int:
        return self._data["hp"]
    
    @hp.setter
    def hp(self, value: int):
        self._data["hp"] = value
    
    @property
    def max_hp(self) -> int:
        return self._data["max_hp"]

    @property
    def level(self) -> int:
        return self._data["level"]

    @property
    def sprite_path(self) -> str:
        return self._data["sprite_path"]

class BushScene(Scene):
    game_manager: "GameManager"
    # Background Image
    background: BackgroundSprite
    # Buttons
    pokeball_button: Button | None
    pokeball_info: dict | None
    run_button: Button

    new_monster: dict | None
    new_MONSTER: MonsterObj | None
    
    ## font
    title_font: pg.font.Font
    content_font: pg.font.Font
    note_font: pg.font.Font
    name_font: pg.font.Font
    hp_font: pg.font.Font
    message_font: pg.font.Font
    
    # all monster info
    all_monster: list[list[dict]]
    
    # animation
    jumping_timer: int
    jumping_dx: int
    catch_timer = 0
    caught = False
    
    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")

        px, py = GameSettings.SCREEN_WIDTH // 4 - 10, GameSettings.SCREEN_HEIGHT * 5/6
        self.pokeball_button = None
        self.run_button = Button(
            "UI/raw/UI_Flat_Button01a_1.png", "UI/raw/UI_Flat_Button01a_3.png",
            px+510, py+10, 150, 50,
            lambda: scene_manager.change_scene("game")
        )
        
        self.new_monster = None
        self.new_MONSTER = None
        
        ## fonts
        self.title_font = load_font("Minecraft.ttf", 32) #path, size
        self.content_font = load_font("Minecraft.ttf", 28)
        self.message_font = load_font("Minecraft.ttf", 20)
        self.note_font = load_font("Minecraft.ttf", 16)
        self.name_font = load_font("Minecraft.ttf", 12)
        self.hp_font = load_font("Minecraft.ttf", 8)
        
        self.pokeball_info = None
        
        self.all_monster = [
            [
                {
                    "name": "Pikachu",
                    "hp": 50,
                    "max_hp": 100,
                    "sprite_path": "menu_sprites/menusprite1.png",
                },
                {
                    "name": "Ewolee",
                    "hp": 95,
                    "max_hp": 190,
                    "sprite_path": "menu_sprites/menusprite15.png",
                },
                {
                    "name": "Dragonite",
                    "hp": 110,
                    "max_hp": 220,
                    "sprite_path": "menu_sprites/menusprite16.png",
                }
            ],
            [
                {
                    "name": "Venusaur",
                    "hp": 80,
                    "max_hp": 160,
                    "sprite_path": "menu_sprites/menusprite4.png",
                },
                {
                    "name": "Gengar",
                    "hp": 70,
                    "max_hp": 140,
                    "sprite_path": "menu_sprites/menusprite5.png",
                },
                {
                    "name": "Flamanite",
                    "hp": 130,
                    "max_hp": 260,
                    "sprite_path": "menu_sprites/menusprite7.png",
                }
            ],
            [
                {
                    "name": "Ifocy",
                    "hp": 75,
                    "max_hp": 150,
                    "sprite_path": "menu_sprites/menusprite6.png",
                },
                {
                    "name": "raiite",
                    "hp": 85,
                    "max_hp": 170,
                    "sprite_path": "menu_sprites/menusprite10.png",
                },
                {
                    "name": "docitiz",
                    "hp": 135,
                    "max_hp": 270,
                    "sprite_path": "menu_sprites/menusprite12.png",
                }
            ]
        ]
        
        self.jumping_timer = 0
        self.jumping_dx = 1
        
        self.catch_timer = 0
        self.caught = False

    def random_monster_by_map(self, map_idx: int) -> dict:
        monsters = self.all_monster[map_idx]

        # possibilities: 1/2, 1/4, 1/10 (cheap -> rare)
        weights = [4, 2, 1]
        chosen = random.choices(monsters, weights=weights, k=1)[0]

        # create monster
        return {
            "name": chosen["name"],
            "hp": chosen["hp"],
            "max_hp": chosen["max_hp"],
            "level": random.randint(10, 40),
            "sprite_path": chosen["sprite_path"],
        }
        
    def catch(self):
        self.game_manager.bag._monsters_data.append(self.new_monster)
        self.game_manager.bag._items_data[4]["count"] -= 1
        self.catch_timer = 60
        self.caught = True
        
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 107 Battle! (Trainer).ogg")
        self.game_manager = services.game_manager
        
        # current_map_key = "map.tmx", "gym.tmx", "ice.tmx"
        map_key = self.game_manager.current_map_key
        Logger.info(f"map now: {self.game_manager.current_map_key}")

        if "map" in map_key:
            map_idx = 0
        elif "gym" in map_key:
            map_idx = 1
        else:
            map_idx = 2

        # select monster randomly
        self.new_monster = self.random_monster_by_map(map_idx)
        self.new_MONSTER = MonsterObj(self.new_monster)
            
        self.pokeball_info = self.game_manager.bag._items_data[4]
        px, py = GameSettings.SCREEN_WIDTH // 4 - 10, GameSettings.SCREEN_HEIGHT * 5/6 -200
        self.pokeball_button = Button(
            self.pokeball_info["sprite_path"], self.pokeball_info["sprite_path"],
            px+170, py+10, 150, 150,
            lambda: self.catch()
        )
        
        self.catch_timer = 0
        self.caught = False

    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
        if input_manager.key_pressed(pg.K_ESCAPE):
            scene_manager.change_scene("game")
            return
        self.pokeball_button.update(dt)
        self.run_button.update(dt)
        
        if self.jumping_timer <= -29 or self.jumping_timer >= 29:
            self.jumping_dx = -self.jumping_dx
        self.jumping_timer += self.jumping_dx
        
        if self.catch_timer <= 0 and self.caught:
            scene_manager.change_scene("game")
        elif self.catch_timer > 0:
            self.catch_timer -= 1
            
    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        
        # buttons
        self.pokeball_button.draw(screen)
        self.run_button.draw(screen)
            
        px, py = GameSettings.SCREEN_WIDTH // 4-5, GameSettings.SCREEN_HEIGHT * 5/6
        run_text = self.content_font.render("RUN", True, (0, 0, 0))
        screen.blit(run_text, (px+510+15, py+24))
        
        block_image = resource_manager.get_image("UI/raw/UI_Flat_Banner03a.png")
        block_image = pg.transform.scale(block_image, ((GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
        hp_bar_image = resource_manager.get_image("UI/raw/UI_Flat_BarFill01a.png")
        # new monster info.
        dx_blocks = 1000
        dy_blocks = -400
        # block
        screen.blit(block_image, pg.Rect(35 +dx_blocks, GameSettings.SCREEN_HEIGHT-200 +dy_blocks, (GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
        # image
        monster_image = resource_manager.get_image(self.new_MONSTER.sprite_path)
        if (self.catch_timer > 0 and self.caught) or self.caught:
            monster_image_sprite = pg.transform.scale(monster_image, (200*self.catch_timer/60, 200*self.catch_timer/60))
        else:
            monster_image_sprite = pg.transform.scale(monster_image, (200, 200))
        monster_image = pg.transform.scale(monster_image, (35, 35))
        screen.blit(monster_image, pg.Rect(50 +dx_blocks, GameSettings.SCREEN_HEIGHT-195 +dy_blocks, 35, 35))
        dx, dy = px+200-(50 +dx_blocks-150), py-50-(GameSettings.SCREEN_HEIGHT-195+100 +dy_blocks)
        if (self.catch_timer > 0 and self.caught) or self.caught:
            screen.blit(monster_image_sprite, pg.Rect(50 +dx_blocks-150 + dx*(60-self.catch_timer)/60, GameSettings.SCREEN_HEIGHT-195+100 +dy_blocks + dy*(60-self.catch_timer)/60, 200*self.catch_timer/60, 200*self.catch_timer/60))
        else:   
            screen.blit(monster_image_sprite, pg.Rect(50 +dx_blocks-150, GameSettings.SCREEN_HEIGHT-195+100 +dy_blocks + self.jumping_timer, 200, 200))
        # name
        name_text = self.name_font.render(self.new_MONSTER.name, True, (0, 0, 0))
        screen.blit(name_text, (95 +dx_blocks, GameSettings.SCREEN_HEIGHT-193 +dy_blocks))
        # hp bar
        bar_w = (GameSettings.SCREEN_WIDTH*3/7)//3-80
        pg.draw.rect(screen, (200, 200, 200), (95 + dx_blocks, GameSettings.SCREEN_HEIGHT-180 + dy_blocks, bar_w, 12))
        enemy_hp_ratio = self.new_MONSTER.hp/self.new_MONSTER.max_hp
        enemy_hp_image = pg.transform.scale(hp_bar_image, (int(enemy_hp_ratio*bar_w), 10))
        screen.blit(enemy_hp_image, pg.Rect(96 + dx_blocks, GameSettings.SCREEN_HEIGHT-179 + dy_blocks, int(enemy_hp_ratio*bar_w), 10))
        # hp
        hp_text = self.hp_font.render(f"{self.new_MONSTER.hp}/{self.new_MONSTER.max_hp}", True, (0, 0, 0))
        screen.blit(hp_text, (95 +dx_blocks, GameSettings.SCREEN_HEIGHT-165 +dy_blocks))
        # level
        name_text = self.name_font.render(f"Lv{self.new_MONSTER.level}", True, (0, 0, 0))
        screen.blit(name_text, (95+bar_w+5 +dx_blocks, GameSettings.SCREEN_HEIGHT-180 +dy_blocks))
        
        # pokeball info print
        pokeball_text = self.title_font.render(f"{self.pokeball_info["count"]} pokeballs left", True, (0, 0, 0))
        screen.blit(pokeball_text, (GameSettings.SCREEN_WIDTH // 4 + 120, GameSettings.SCREEN_HEIGHT * 5/6 -200 + 180))
        
