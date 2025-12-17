import pygame as pg
import random

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

class BattleScene(Scene):
    game_manager: "GameManager"
    # Background Image
    background: BackgroundSprite
    # Buttons
    fight_button: Button
    item_button: Button
    switch_button: Button
    run_button: Button
    
    is_attack: bool #is the effecting button "attack"?
    button_effecting: bool
    
    player_monster: dict | None
    player_MONSTER: MonsterObj | None
    enemy_monster: dict | None
    enemy_MONSTER: MonsterObj | None
    
    # save original HP -> next time enter able to use
    enemy_MONSTER_originalHP: int
    
    ## font
    title_font: pg.font.Font
    content_font: pg.font.Font
    note_font: pg.font.Font
    name_font: pg.font.Font
    hp_font: pg.font.Font
    message_font: pg.font.Font
    
    ## battle turn
    turn: str  #player/enemy
    timer: int
    
    # message
    warning_message: str
    warning_message_timer: int
    
    # items
    show_items: bool
    items_selected: bool
    items_buttons: list[Button]
    player_extra_damage: int
    enemy_extra_damage: int
    defend: bool
    item_message: str
    
    hp_deduction: int
    
    element_list: list[list[str]]
    
    # animation
    jumping_timer: int
    jumping_idx: int
    
    all_monster: list[list[dict]]
    
    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")

        px, py = GameSettings.SCREEN_WIDTH // 4 - 10, GameSettings.SCREEN_HEIGHT * 5/6
        self.fight_button = Button(
            "UI/raw/UI_Flat_Button01a_1.png", "UI/raw/UI_Flat_Button01a_3.png",
            px, py+40, 150, 50,
            lambda: self.attack(self.player_MONSTER.level)
        )
        self.item_button = Button(
            "UI/raw/UI_Flat_Button01a_1.png", "UI/raw/UI_Flat_Button01a_3.png",
            px+170, py+40, 150, 50,
            lambda: self.item_onclick()
        )
        self.switch_button = Button(
            "UI/raw/UI_Flat_Button01a_1.png", "UI/raw/UI_Flat_Button01a_3.png",
            px+340, py+40, 150, 50,
            lambda: self.switch_monster()
        )
        self.run_button = Button(
            "UI/raw/UI_Flat_Button01a_1.png", "UI/raw/UI_Flat_Button01a_3.png",
            px+510, py+40, 150, 50,
            lambda: scene_manager.change_scene("game")
        )
        
        self.player_monster = None
        self.player_MONSTER = None
        self.enemy_monster = None
        self.enemy_MONSTER = None
        
        ## fonts
        self.title_font = load_font("Minecraft.ttf", 32) #path, size
        self.content_font = load_font("Minecraft.ttf", 28)
        self.message_font = load_font("Minecraft.ttf", 20)
        self.note_font = load_font("Minecraft.ttf", 16)
        self.name_font = load_font("Minecraft.ttf", 12)
        self.hp_font = load_font("Minecraft.ttf", 8)
        
        self.message = None
        
        self.turn = "player"
        self.timer = 0
        
        self.warning_message = None
        self.warning_message_timer = 0
        
        self.button_effecting = False
        self.is_attack = False
        
        self.show_items = False
        self.items_selected = False
        self.player_extra_damage = None
        self.enemy_extra_damage = None
        self.defend = False
        self.item_message = ""
        
        self.game_manager = services.game_manager
        self.items_buttons = []
        
        self.hp_deduction = None
        
        self.element_list = [
            ["Pikachu", "Ewolee", "Dragonite", "Piculakus", "Pigodicha"],
            ["Venusaur", "Gengar", "Flamanite"],
            ["Ifocy", "raiite", "docitiz"]
        ]
        
        self.jumping_timer = 0
        self.jumping_dx = 1
        
        self.all_monster = [
            [
                {
                    "name": "Pikachu",
                    "hp": 50,
                    "max_hp": 100,
                    "sprite_path": "menu_sprites/menusprite1.png",
                },
                {
                    "name": "Piculakus",
                    "hp": 60,
                    "max_hp": 120,
                    "sprite_path": "menu_sprites/menusprite2.png",
                },
                {
                    "name": "Pigodicha",
                    "hp": 70,
                    "max_hp": 140,
                    "sprite_path": "menu_sprites/menusprite3.png",
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
        self.switching = False
        
    def attack(self, level: int) -> None:
        self.button_effecting = True
        damage = level
        if self.turn == "player":
            damage += self.player_extra_damage
        else:
            damage += self.enemy_extra_damage
        if self.is_attack == False:
            if self.turn == "player":
                self.hp_deduction = self.enemy_MONSTER.hp - damage
            else:
                self.hp_deduction = self.player_MONSTER.hp - damage
        self.is_attack = True
        
        if self.turn == "player":
            damage += self.player_extra_damage
            if self.timer == 0:
                self.timer = 70
            else:
                self.enemy_MONSTER.hp = max(0, max(self.hp_deduction, self.enemy_MONSTER.hp - damage/70))
        else:
            if not self.defend:
                self.player_MONSTER.hp = max(0, max(self.hp_deduction, self.player_MONSTER.hp - damage/70))
           
    def item_onclick(self):
        self.button_effecting = True
        Logger.info("battle ***item***")
        self.show_items = True
        self.items_selected = False
            
    def use_item(self, idx: int):
        self.item_idx = idx
        self.items_selected = True
        if self.timer <= 0:
            self.timer = 80
            self.game_manager.bag._items_data[idx]["count"] -= 1
            if idx == 1:
                self.player_extra_damage += 10
            elif idx == 2:
                self.defend = True
            elif idx == 5:
                self.hp_before_maxpotion = self.player_MONSTER.hp
        else:
            if idx == 0:
                self.player_MONSTER.hp = min(self.player_MONSTER.max_hp, self.player_MONSTER.hp + 40/80)
            elif idx == 5:
                self.player_MONSTER.hp = min(self.player_MONSTER.max_hp, self.player_MONSTER.hp + (self.player_MONSTER.max_hp-self.hp_before_maxpotion)/80)

    def switch_monster(self):
        if self.game_manager.bag._items_data[3]["count"] < 5:
            self.warning_message = "no enough coins!"
            self.warning_message_timer = 70
            return
        self.button_effecting = True
        self.switching = True
        self.timer = 80
            
    def random_monster_by_map(self, map_idx: int, original_monster_name: int) -> dict:
        monsters = self.all_monster[map_idx]

        # possibilities: 1/4, 1/2, 1/8, 1/16, 1/32 (the medium)
        weights = [8, 2, 1, 16, 4]
        chosen = random.choices(monsters, weights=weights, k=1)[0]
        while chosen["name"] == original_monster_name:
            chosen = random.choices(monsters, weights=weights, k=1)[0]
        idx = monsters.index(chosen)
        
        if chosen["name"] == "Piculakus":
            lvl = random.randint(60, 90)
        elif chosen["name"] == "Pigodicha":
            lvl = random.randint(100, 120)
        else:
            lvl = random.randint(10*(idx+1), 15*(idx+1))

        # create monster
        return {
            "name": chosen["name"],
            "hp": random.randint(40, 70),
            "max_hp": chosen["max_hp"],
            "level": lvl,
            "sprite_path": chosen["sprite_path"]
        }
    
    def end_battle(self):
        if self.player_MONSTER.hp <= 0:
            self.game_manager.bag._monsters_data.remove(self.player_monster)
        elif self.enemy_MONSTER.hp <= 0:
            # add new monster
            hp_ratio = self.player_MONSTER.hp / self.player_MONSTER.max_hp #new monster's hp -> refer to player monster's hp ratio
            new_monster = { **self.enemy_monster, "hp": int(hp_ratio * self.enemy_MONSTER.max_hp)}
            self.game_manager.bag._monsters_data.append(new_monster)
            # save hp of player monster
            idx = self.game_manager.bag._monsters_data.index(self.player_monster)
            self.game_manager.bag._monsters_data[idx]["hp"] = self.player_MONSTER.hp
            
            # win message
            self.game_manager.win_message = True
            
        # count again
        # reset countdown for the actual trainer on the map
        enemy = self.game_manager.collide_enemy_trainer
        if enemy:
            enemy.countdown = 540 
        # del countdown (no need)
        if self.game_manager.enemy_monster and "countdown" in self.game_manager.enemy_monster:
            del self.game_manager.enemy_monster["countdown"]
            
        scene_manager.change_scene("game")
        self.show_items = False
        
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 107 Battle! (Trainer).ogg")
        self.game_manager = services.game_manager
        self.player_monster = self.game_manager.bag._monsters_data[self.game_manager.monster_idx]
        self.player_MONSTER = MonsterObj(self.player_monster)
        self.enemy_monster = self.game_manager.enemy_monster
        self.enemy_MONSTER = MonsterObj(self.enemy_monster)

        self.enemy_MONSTER_originalHP = self.game_manager.collide_enemy_trainer.original_hp
        
        player_element_idx = None
        enemy_element_idx = None
        # elements belongings
        for idx, name_list in enumerate(self.element_list):
            if self.player_MONSTER.name in name_list:
                player_element_idx = idx
            if self.enemy_MONSTER.name in name_list:
                enemy_element_idx = idx
        self.player_extra_damage = 0
        self.enemy_extra_damage = 0
        if player_element_idx < enemy_element_idx or (player_element_idx == 2 and enemy_element_idx == 0):
            self.enemy_extra_damage = 10 
        elif player_element_idx != enemy_element_idx:
            self.player_extra_damage = 10
        
        self.turn = "player"
        self.timer = 0
        self.switching = False
        
        self.items_buttons = []
        x = GameSettings.SCREEN_WIDTH*2/7 + 270
        for index, dic in enumerate(self.game_manager.bag._items_data[:3]):
            hover = dic["sprite_path"]
            hover = ( hover[:-5] + str(int(hover[-5]) + 4) + hover[-4:])
            btn = Button(
                dic["sprite_path"],
                hover,
                x, 
                GameSettings.SCREEN_HEIGHT- 100,
                50, 50,
                lambda idx=index: self.use_item(idx)   # '''change'''
            )
            self.items_buttons.append(btn)
            x += 100
        
        btn = Button(
            "ingame_ui/potion.png",
            "ingame_ui/potion_hover.png",
            x, 
            GameSettings.SCREEN_HEIGHT- 100,
            50, 50,
            lambda idx=5: self.use_item(idx)   # '''change'''
        )
        self.items_buttons.append(btn)
        
        self.game_manager.win_message = False

    @override
    def exit(self) -> None:
        self.enemy_MONSTER.hp = int(self.enemy_MONSTER.hp)
        self.player_MONSTER.hp = int(self.player_MONSTER.hp)
        if self.enemy_MONSTER.hp>0:
            self.game_manager.enemy_monster["hp"] = self.enemy_MONSTER.hp
        else: # revive
            self.game_manager.enemy_monster["hp"] = self.enemy_MONSTER_originalHP
        self.game_manager.player_monster = self.player_monster

    @override
    def update(self, dt: float) -> None:
        if self.jumping_timer <= -29 or self.jumping_timer >= 29:
            self.jumping_dx = -self.jumping_dx
        self.jumping_timer += self.jumping_dx
        if input_manager.key_pressed(pg.K_ESCAPE):
            scene_manager.change_scene("game")
            return
        if self.button_effecting == False:
            self.fight_button.update(dt)
            self.item_button.update(dt)
            self.switch_button.update(dt)
            self.run_button.update(dt)
        if self.button_effecting and self.timer <= 0 and not(self.show_items): 
            self.button_effecting = False
            self.is_attack = False
        if self.show_items and self.items_selected:
            if self.timer > 0:
                self.use_item(self.item_idx)
            else:
                self.show_items = False
        if self.switching:
            if self.timer == 40:
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
                self.enemy_monster = self.random_monster_by_map(map_idx, self.enemy_MONSTER.name)
                self.enemy_MONSTER = MonsterObj(self.enemy_monster)
                self.enemy_MONSTER_originalHP = self.enemy_MONSTER.hp
        
        if self.timer < 0:
            if self.turn == "player":
                self.turn = "enemy"
                self.timer = 130
            else:
                self.turn = "player"
                self.timer = 0
                self.defend = False
        
        ### [player's turn]
        if self.turn == "player":
            #attack when press button(start from full timer)
            if self.timer == 79 and self.switching:
                if self.game_manager.bag._items_data[3]["count"] < 5:
                    self.warning_message = "drop 5 coins!"
                    self.warning_message_timer = 70
                self.game_manager.bag.pay(5)
                self.warning_message = "drop 5 coins!"
                self.warning_message_timer = 70
            if self.timer > 0:
                if self.is_attack:
                    self.attack(self.player_MONSTER.level)
                    self.message = f"My {self.player_MONSTER.name} is attacking {self.enemy_MONSTER.name}!"
                if self.timer == 1:
                    self.timer -= 2 #countdown
                else:
                    self.timer -= 1 #
                if self.show_items:
                    if self.item_idx == 0:
                        self.message = f"add HP to my {self.player_MONSTER.name}"
                        self.item_message = "+40"
                    elif self.item_idx == 1:
                        self.message = f"{self.player_MONSTER.name} ATTACK power UP!!!"
                        self.item_message = "+10"
                    elif self.item_idx == 2:
                        self.message = f"got a SHIELD"
                    else:
                        self.message = f"drink MAX POTION"
            # choose items
            elif self.show_items:
                self.message = f"pick a tool"
            #not attacking
            else:
                self.message = f"What does {self.player_MONSTER.name} do?"
                
            ## items
            if self.show_items:
                for idx, btn in enumerate(self.items_buttons):
                    if idx == 3:
                        idx = 5
                    if (self.game_manager.bag._items_data[idx]["count"] > 0 and self.timer == 0) or (self.game_manager.bag._items_data[idx]["count"] == 0 and self.timer == 1):
                        btn.update(dt)
            if self.timer == 69 and self.is_attack:
                self.game_manager.bag.pay(-5)
                self.warning_message = "attack! earn 5 coins!"
                self.warning_message_timer = 70
        ###
        
        ### [enemy's turn]
        elif self.turn == "enemy":
            self.switching = False
            if self.timer > 0:
                self.timer -= 1 #countdown
                if self.timer <= 70:
                    self.attack(self.enemy_MONSTER.level) # loose hp when end attacking
                    self.message = f"{self.enemy_MONSTER.name} is attacking!"
                else:
                    self.message = "rest"
            else:
                self.timer -= 1
        ###
        
        ### battle end
        if self.player_MONSTER.hp <= 0 or self.enemy_MONSTER.hp <= 0:
            self.end_battle()
    
    # red on image        
    def make_red(self, sprite: pg.Surface, intensity=150):
        img = sprite.copy()
        img.fill((intensity, 0, 0), special_flags=pg.BLEND_RGB_ADD)
        return img
                
    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        # overlay
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, 200), pg.SRCALPHA)
        if self.turn == "enemy" and self.timer <= 70:
            overlay.fill((180, 0, 0, 100))   # (R,G,B,A)
        else:
            overlay.fill((0, 0, 0, 100))   # (R,G,B,A)
        screen.blit(overlay, (0, GameSettings.SCREEN_HEIGHT * 5/6))
        
        ### [player's turn]
        if self.turn == "player":
            # buttons
            self.fight_button.draw(screen)
            self.item_button.draw(screen)
            self.switch_button.draw(screen)
            self.run_button.draw(screen)
            
            px, py = GameSettings.SCREEN_WIDTH // 4-5, GameSettings.SCREEN_HEIGHT * 5/6 +30
            fight_text = self.content_font.render("FIGHT", True, (0, 0, 0))
            screen.blit(fight_text, (px+15, py+24))
            item_text = self.content_font.render("ITEM", True, (0, 0, 0))
            screen.blit(item_text, (px+170+15, py+24))
            switch_text = self.content_font.render("SWITCH", True, (0, 0, 0))
            coin_image = resource_manager.get_image("ingame_ui/coin.png")
            coin_image = pg.transform.scale(coin_image, (25, 25))
            screen.blit(coin_image, pg.Rect(px+340+15+30, py+24+35-70, 25, 25))
            minus_text = self.content_font.render("(     -5)", True, (0, 0, 0))
            screen.blit(switch_text, (px+340+15, py+24))
            screen.blit(minus_text, (px+340+15+50-40, py+24+40-75))
            run_text = self.content_font.render("RUN", True, (0, 0, 0))
            screen.blit(run_text, (px+510+15, py+24))
            
            ## items
            if self.show_items:
                # darken background
                background = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
                background.fill((0, 0, 0, 150))  # (R,G,B,transparency)
                screen.blit(background, (0, 0))
                
                x = GameSettings.SCREEN_WIDTH*2/7 + 270
                for idx, btn in enumerate(self.items_buttons):
                    btn.draw(screen)
                    if idx == 3:
                        idx = 5
                    item_count_text = self.content_font.render(f"{self.game_manager.bag._items_data[idx]["count"]}", True, (255, 255, 255))
                    screen.blit(item_count_text, (x + 40, GameSettings.SCREEN_HEIGHT- 100))
                    x += 100
        ###
        
        # monster info.
        block_image = resource_manager.get_image("UI/raw/UI_Flat_Banner03a.png")
        block_image = pg.transform.scale(block_image, ((GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
        ## player monster
        # block
        screen.blit(block_image, pg.Rect(35, GameSettings.SCREEN_HEIGHT-200, (GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
        # image
        monster_image = resource_manager.get_image(self.player_MONSTER.sprite_path)
        monster_image_sprite = pg.transform.scale(monster_image, (200, 200))
        monster_image_sprite = pg.transform.flip(monster_image_sprite, True, False)  # True->horizontal, False->vertical
        attack_image = resource_manager.get_image("attack/attack1.png")
        attack_image_sprite = pg.transform.scale(attack_image, (200, 200))
        attack_image_sprite = pg.transform.flip(attack_image_sprite, True, False)  # True->horizontal, False->vertical
        if self.turn == "enemy" and self.timer > 0 and self.timer <= 70:
            monster_image_sprite = self.make_red(monster_image_sprite) # red when attacked
        monster_image = pg.transform.scale(monster_image, (35, 35))
        screen.blit(monster_image, pg.Rect(50, GameSettings.SCREEN_HEIGHT-195, 35, 35))
        ###
        target_dx, target_dy = (900-100-(50 +200))*1/4, (GameSettings.SCREEN_HEIGHT-495-(GameSettings.SCREEN_HEIGHT-195-200))*1/4
        if self.turn == "player" and self.timer > 0 and self.is_attack:
            screen.blit(monster_image_sprite, pg.Rect(50 +200 +target_dx*(70-self.timer)/70, GameSettings.SCREEN_HEIGHT-195-200+target_dy*(70-self.timer)/70, 200, 200))
            screen.blit(attack_image_sprite, pg.Rect(50 +200 +4*target_dx*(70-self.timer)/70, GameSettings.SCREEN_HEIGHT-195-200+4*target_dy*(70-self.timer)/70, 200, 200))
        else:
            screen.blit(monster_image_sprite, pg.Rect(50 +200, GameSettings.SCREEN_HEIGHT-195-200 +self.jumping_timer, 200, 200))
        ###
        # name
        name_text = self.name_font.render(self.player_MONSTER.name, True, (0, 0, 0))
        screen.blit(name_text, (95, GameSettings.SCREEN_HEIGHT-193))
        # hp bar
        bar_w = (GameSettings.SCREEN_WIDTH*3/7)//3-80
        pg.draw.rect(screen, (200, 200, 200), (95, GameSettings.SCREEN_HEIGHT-180, bar_w, 12))
        player_hp_ratio = self.player_MONSTER.hp/self.player_MONSTER.max_hp
        if player_hp_ratio < 0.2:
            hp_bar_image = resource_manager.get_image("UI/raw/UI_Flat_BarFill01c.png")
        else:
            hp_bar_image = resource_manager.get_image("UI/raw/UI_Flat_BarFill01a.png")
        player_hp_image = pg.transform.scale(hp_bar_image, (int(player_hp_ratio*bar_w), 10))
        screen.blit(player_hp_image, pg.Rect(96, GameSettings.SCREEN_HEIGHT-179, int(player_hp_ratio*bar_w), 10))
        # hp
        hp_text = self.hp_font.render(f"{int(self.player_MONSTER.hp)}/{self.player_MONSTER.max_hp}", True, (0, 0, 0))
        screen.blit(hp_text, (95, GameSettings.SCREEN_HEIGHT-165))
        # level
        name_text = self.name_font.render(f"Lv{self.player_MONSTER.level}", True, (0, 0, 0))
        screen.blit(name_text, (95+bar_w+5, GameSettings.SCREEN_HEIGHT-180))
        
        
        ## enemy monster
        dx_blocks = 1000
        dy_blocks = -400
        # block
        screen.blit(block_image, pg.Rect(35 +dx_blocks, GameSettings.SCREEN_HEIGHT-200 +dy_blocks, (GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
        # image
        monster_image = resource_manager.get_image(self.enemy_MONSTER.sprite_path)
        if self.switching:
            monster_image_sprite = pg.transform.scale(monster_image, (200*abs((self.timer-40)/40), 200*abs((self.timer-40)/40)))
        else:
            monster_image_sprite = pg.transform.scale(monster_image, (200, 200))
        attack_image_sprite = pg.transform.flip(attack_image_sprite, True, False)  # True->horizontal, False->vertical
        if self.turn == "player" and self.timer > 0 and self.is_attack:
            monster_image_sprite = self.make_red(monster_image_sprite) # red when attacked
        monster_image = pg.transform.scale(monster_image, (35, 35))
        screen.blit(monster_image, pg.Rect(50 +dx_blocks, GameSettings.SCREEN_HEIGHT-195 +dy_blocks, 35, 35))
        ###
        if self.switching:
            screen.blit(monster_image_sprite, pg.Rect(50 +dx_blocks-150, GameSettings.SCREEN_HEIGHT-195+100 +dy_blocks, 200*abs((self.timer-40)/40), 200*abs((self.timer-40)/40)))
        else:
            if self.turn == "enemy" and self.timer > 0 and self.timer <= 70: # enemy delay 5s to attack
                screen.blit(monster_image_sprite, pg.Rect(50 +dx_blocks-150 -target_dx*(70-self.timer)/70, GameSettings.SCREEN_HEIGHT-195+100 +dy_blocks -target_dy*(70-self.timer)/70, 200, 200))
                screen.blit(attack_image_sprite, pg.Rect(50 +dx_blocks-150 -4*target_dx*(70-self.timer)/70, GameSettings.SCREEN_HEIGHT-195+100 +dy_blocks -4*target_dy*(70-self.timer)/70, 200, 200))
            else:
                screen.blit(monster_image_sprite, pg.Rect(50 +dx_blocks-150, GameSettings.SCREEN_HEIGHT-195+100 +dy_blocks +self.jumping_timer, 200, 200))
        ###
        # name
        name_text = self.name_font.render(self.enemy_MONSTER.name, True, (0, 0, 0))
        screen.blit(name_text, (95 +dx_blocks, GameSettings.SCREEN_HEIGHT-193 +dy_blocks))
        # hp bar
        pg.draw.rect(screen, (200, 200, 200), (95 + dx_blocks, GameSettings.SCREEN_HEIGHT-180 + dy_blocks, bar_w, 12))
        enemy_hp_ratio = self.enemy_MONSTER.hp/self.enemy_MONSTER.max_hp
        if enemy_hp_ratio < 0.2:
            hp_bar_image = resource_manager.get_image("UI/raw/UI_Flat_BarFill01c.png")
        else:
            hp_bar_image = resource_manager.get_image("UI/raw/UI_Flat_BarFill01a.png")
        enemy_hp_image = pg.transform.scale(hp_bar_image, (int(enemy_hp_ratio*bar_w), 10))
        screen.blit(enemy_hp_image, pg.Rect(96 + dx_blocks, GameSettings.SCREEN_HEIGHT-179 + dy_blocks, int(enemy_hp_ratio*bar_w), 10))
        # hp
        hp_text = self.hp_font.render(f"{int(self.enemy_MONSTER.hp)}/{self.enemy_MONSTER.max_hp}", True, (0, 0, 0))
        screen.blit(hp_text, (95 +dx_blocks, GameSettings.SCREEN_HEIGHT-165 +dy_blocks))
        # level
        name_text = self.name_font.render(f"Lv{self.enemy_MONSTER.level}", True, (0, 0, 0))
        screen.blit(name_text, (95+bar_w+5 +dx_blocks, GameSettings.SCREEN_HEIGHT-180 +dy_blocks))
                
        ## attack power
        # [player]
        if self.player_extra_damage > 0:
            # white overlay
            text_pos = (120, GameSettings.SCREEN_HEIGHT * 2 / 3 - 10)
            bg = pg.Surface((120, 24), pg.SRCALPHA)
            bg.fill((255, 255, 255, 120))
            screen.blit(bg, (text_pos[0] - 5, text_pos[1] - 2))
            # image & text
            power_image = resource_manager.get_image("ingame_ui/baricon7.png")
            power_image = pg.transform.scale(power_image, (35, 35))
            screen.blit(power_image, pg.Rect(80, GameSettings.SCREEN_HEIGHT*2/3 - 10, 50, 50))
            extra_power_text = self.message_font.render(f"extra {self.player_extra_damage}", True, (0, 120, 0))
            screen.blit(extra_power_text, (120, GameSettings.SCREEN_HEIGHT * 2 / 3 - 10))
        # [enemy]
        if self.enemy_extra_damage > 0:
            # white overlay
            text_pos = (120 +950, GameSettings.SCREEN_HEIGHT * 2 / 3 - 10 -400)
            bg = pg.Surface((120, 24), pg.SRCALPHA)
            bg.fill((255, 255, 255, 120))
            screen.blit(bg, (text_pos[0] - 5, text_pos[1] - 2))
            # image & text
            power_image = resource_manager.get_image("ingame_ui/baricon7.png")
            power_image = pg.transform.scale(power_image, (35, 35))
            screen.blit(power_image, pg.Rect(80 +950, GameSettings.SCREEN_HEIGHT*2/3 - 10 -400, 50, 50))
            extra_power_text = self.message_font.render(f"extra {self.enemy_extra_damage}", True, (0, 120, 0))
            screen.blit(extra_power_text, (120 +950, GameSettings.SCREEN_HEIGHT * 2 / 3 - 10 -400))
        
        # warning message
        overlay_x, overlay_y = GameSettings.SCREEN_WIDTH*2/7, GameSettings.SCREEN_HEIGHT//5
        if self.warning_message_timer > 0 and self.warning_message and (self.is_attack or self.switching or self.warning_message == "no enough coins!"):  
            # overlay
            overlay = pg.Surface((230, 40), pg.SRCALPHA)
            overlay.fill((255, 0, 0, 100))   # (R,G,B,A)
            screen.blit(overlay, (overlay_x+150, overlay_y-45))
            
            self.warning_message_timer -= 1
            
            title = self.message_font.render(self.warning_message, True, (255, 255, 255))
            screen.blit(title, (overlay_x+170, overlay_y-35))
        
        # messages
        message = self.message
        message_text = self.message_font.render(message, True, (255, 255, 255))
        screen.blit(message_text, (35, GameSettings.SCREEN_HEIGHT * 5/6 + 15))
        
        if self.show_items and self.timer > 0:
            # item messages
            item_message_text = self.title_font.render(self.item_message, True, (255, 0, 0))
            if self.item_idx == 0:
                screen.blit(item_message_text, (250, GameSettings.SCREEN_HEIGHT * 2/3 + 50 - 20* (80-self.timer)/80))
            elif self.item_idx == 1:
                screen.blit(item_message_text, (120, GameSettings.SCREEN_HEIGHT * 2/3 - 10 - 20* (80-self.timer)/80))
        
        # shield
        if self.defend:
            if self.show_items and self.timer > 0:
                s = pg.Surface((260, 260), pg.SRCALPHA)
                pg.draw.circle(s, (80, 160, 255, 60), (130, 130), 120*(80-self.timer)/80)
                screen.blit(s, (50 + 200 + 100 - 130, GameSettings.SCREEN_HEIGHT - 195 - 200 + 100 - 130))
            else:
                s = pg.Surface((260, 260), pg.SRCALPHA)
                pg.draw.circle(s, (80, 160, 255, 60), (130, 130), 120)
                screen.blit(s, (50 + 200 + 100 - 130, GameSettings.SCREEN_HEIGHT - 195 - 200 + 100 - 130))
