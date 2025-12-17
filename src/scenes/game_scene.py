import pygame as pg
import threading
import time
import random

from src.scenes.scene import Scene
from src.core import OnlineManager
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core.managers.game_manager import GameManager
import src.core.managers.game_manager as gm_module
from src.core import services
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager, resource_manager, input_manager, scene_manager # resource_manager: for mute moving UI, input_manager: for volume slider moving UI, scene_manager: for back button in setting
from src.sprites import Sprite
from typing import override
from src.interface.components import Button
from src.entities.shop_npc import ShopNPC

from src.sprites import BackgroundSprite # for overlay
from src.utils import load_font, GameSettings #for font(def load_font in loader.py)

class GameScene(Scene):
    game_manager: "GameManager"
    online_manager: OnlineManager | None
    sprite_online: Sprite
    ## Buttons
    backpack_button: Button
    setting_button: Button
    # setting buttons
    save_button: Button
    load_button: Button
    back_button: Button
    x_button: Button
    mute_button: Button
    # switch to battle scene
    battle_button: Button
    # switch to bush scene
    catch_button: Button
    ## overlay
    show_backpack: None
    show_setting: None
    ## font
    title_font: pg.font.Font
    content_font: pg.font.Font
    note_font: pg.font.Font
    name_font: pg.font.Font
    hp_font: pg.font.Font
    medium_font: pg.font.Font

    ## shop
    show_shop: bool
    shop_selected: int
    page: int
    # buttons
    shop_buy_buttons: list[Button]
    choose_monster_buttons: list[Button]
    next_page_button: Button
    last_page_button: Button
    
    # warning massage
    warning_message: str
    warning_message_timer: int
    
    # choose monster before battle
    show_monsters: bool
    
    first_collide_bush: bool
    can_catch: bool
    
    def __init__(self):
        super().__init__()
        # Game Manager
        manager = gm_module.GameManager.load(f"saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        services.game_manager = manager
        self.game_manager = manager
        
        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.sprite_online = Sprite("ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        
        ## Buttons
        px, py = GameSettings.SCREEN_WIDTH - 150, 25
        self.backpack_button = Button(
            "UI/button_backpack.png", "UI/button_backpack_hover.png",
            px, py, 50, 50,
            lambda: self.draw_backpack_overlay()
        )
        self.setting_button = Button(
            "UI/button_setting.png", "UI/button_setting_hover.png",
            px+70, py, 50, 50,
            lambda: self.draw_setting_overlay()
        )
        # DONE checkpoint2-02: setting components
        #setting buttons
        px_, py_= GameSettings.SCREEN_WIDTH*2/7+30, GameSettings.SCREEN_HEIGHT*3/5
        self.save_button = Button(
            "UI/button_save.png", "UI/button_save_hover.png",
            px_, py_, 70, 70,
            lambda: self.game_manager.save(f"saves/game_{scene_manager.account_name}.json")
        )
        self.load_button = Button(
            "UI/button_load.png", "UI/button_load_hover.png",
            px_+90, py_, 70, 70,
            lambda: self.load_game()
        )
        self.back_button = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            px_+180, py_, 70, 70,
            lambda: self.back_to_menu()
        )
        self.x_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            GameSettings.SCREEN_WIDTH*5/7-60, GameSettings.SCREEN_HEIGHT//5+30, 30, 30,
            lambda: self.close_overlay()
        )
        # mute button changes color(red/ green)
        self.mute_button = Button(
            ("UI/raw/UI_Flat_BarFill01c.png" if GameSettings.MUTE == "OFF" else "UI/raw/UI_Flat_BarFill01a.png"), ("UI/raw/UI_Flat_BarFill01d.png" if GameSettings.MUTE == "OFF" else "UI/raw/UI_Flat_BarFill01b.png"),
            GameSettings.SCREEN_WIDTH*2/7 +185, GameSettings.SCREEN_HEIGHT//5 +200, 30, 20,
            lambda: self.mute_button_onclick() # mute: ON->OFF / OFF->ON
        )
        # battle button (when warning)
        self.battle_button = Button(
            "UI/raw/UI_Flat_Bar01a.png", "UI/raw/UI_Flat_Bar10a.png",
            GameSettings.SCREEN_WIDTH-180, GameSettings.SCREEN_HEIGHT-90, 165, 70,
            lambda: self.before_battle()
        )
        self.catch_button = Button(
            "UI/raw/UI_Flat_Bar01a.png", "UI/raw/UI_Flat_Bar10a.png",
            GameSettings.SCREEN_WIDTH-180, GameSettings.SCREEN_HEIGHT-90, 165, 70,
            lambda: scene_manager.change_scene("bush")
        )
        self.next_page_button = Button(
            "UI/raw/UI_Flat_ButtonArrow01a.png", "UI/raw/UI_Flat_ButtonArrow01b.png",
            GameSettings.SCREEN_WIDTH*5/7-70, GameSettings.SCREEN_HEIGHT//5+370, 40, 40,
            lambda: self.next_page(1)
        )
        self.last_page_button = Button(
            "UI/raw/UI_Flat_ButtonArrow01a_back.png", "UI/raw/UI_Flat_ButtonArrow01b_back.png",
            GameSettings.SCREEN_WIDTH*5/7-525, GameSettings.SCREEN_HEIGHT//5+370, 40, 40,
            lambda: self.next_page(-1)
        )
        self.buy_or_sell_button = Button(
            "UI/raw/UI_Flat_ToggleRightOff01a.png", "UI/raw/UI_Flat_ToggleRightOn01a.png",
            GameSettings.SCREEN_WIDTH//2+50, 170, 35, 35,
            lambda: self.change_buy_sell()
        )
        self.buy_or_sell = "buy"
        
        ## fonts
        self.title_font = load_font("Minecraft.ttf", 32) #path, size
        self.content_font = load_font("Minecraft.ttf", 28)
        self.medium_font = load_font("Minecraft.ttf", 20)
        self.note_font = load_font("Minecraft.ttf", 16)
        self.name_font = load_font("Minecraft.ttf", 12)
        self.hp_font = load_font("Minecraft.ttf", 8)
        
        ## setting & backpack
        self.show_backpack = False
        self.show_setting = False
        
        ## slider dragging
        self.slider_dragging = False
        
        # shop overlay
        self.page = 1
        self.show_shop = False
        self.shop_selected = 0
        self.shop_buy_buttons = []
        self.choose_monster_buttons = []
        
        self.warning_message = None
        self.warning_message_timer = 0
        
        self.show_monsters = False
        
        self.first_collide_bush = True
        self.can_catch = None
        
        # evolution / level up
        self.level_timer = 0
        self.level_up = False
        self.future_info = None
    # but/sell
    def change_buy_sell(self):
        if self.buy_or_sell == "buy":
            self.buy_or_sell = "sell"
        else:
            self.buy_or_sell = "buy"
        self.page = 1
    # minimap
    def draw_minimap(self, screen: pg.Surface):
        m = self.game_manager.current_map
        mw, mh = m._surface.get_size()
        mini = m.minimap_surface
        sw, sh = mini.get_size()
        pos = (35, 35)
        
        # frame
        pg.draw.rect( screen, (0, 0, 0), (pos[0]-2, pos[1]-2, sw+5, sh+5), 3)
        # draw minimap
        screen.blit(mini, pos)

        p = self.game_manager.player
        if not p:
            return
        # red dot
        pg.draw.circle(screen, (255, 0, 0),
            (pos[0] + int(p.position.x * sw / mw), pos[1] + int(p.position.y * sh / mh),), 4)
        
    # back to menu -> may have different player login
    def back_to_menu(self):
        scene_manager.change_scene("menu")
        scene_manager.first_enter = True
    # change page in shop
    def next_page(self, add: int):
        self.page += add
        Logger.info(f"now at page {self.page}")

    # backpack/setting button clicked (open overlay)
    def draw_backpack_overlay(self):
        self.show_backpack = True
        self.game_manager.overlay_open = True
        self.show_setting = False
        self.page = 1
    def draw_setting_overlay(self):
        self.show_backpack = False
        self.show_setting = True
        self.game_manager.overlay_open = True
    # backpack/setting x_button clicked (close overlay)
    def close_overlay(self):
        self.game_manager.overlay_open = False
        if self.show_backpack:
            self.show_backpack = False
        elif self.show_setting:
            self.show_setting = False
        elif self.show_shop:
            self.shop_shop = 0
            self.show_shop = False
            self.game_manager.collide_shops = False
            self.collide_shop_npc = None
            self.page = 1
    # load game -> game_manager
    def load_game(self):
        ### keep player position and map
        player_pos = self.game_manager.player.position
        current_map = self.game_manager.current_map
        ###
        gm = gm_module.GameManager.load(f"saves/game_{scene_manager.account_name}.json")
        if gm:
            ###
            # restore player pos
            if gm.player:
                gm.player.position = player_pos
            # restore current map
            gm.current_map_key = current_map.path_name
            ###
            services.game_manager = gm
            self.game_manager = gm

    # mute button clicked
    def mute_button_onclick(self):
        if(GameSettings.MUTE == "ON"):
            GameSettings.MUTE = "OFF"
            sound_manager.set_volume(GameSettings.AUDIO_VOLUME)
        else:
            GameSettings.MUTE = "ON"
            sound_manager.set_volume(0)
    
    # for shop
    def buy_item(self, index):
        shop_items = self.game_manager.collide_shop_npc.shop_items
        item_or_monster, price = shop_items[index]
        Logger.info(f"price: {price}")

        if self.game_manager.bag.coins < price:
            self.warning_message = "No enough coins!"
            self.warning_message_timer = 70
            return
        self.game_manager.bag.coins -= price
        self.game_manager.bag._items_data[3]["count"] -= price

        # add item
        if type(item_or_monster) == str:
            # find item -> add one
            for item in self.game_manager.bag._items_data:
                if item["name"] == item_or_monster:
                    item["count"] += 1
                    break
        # add monster
        else:
            # new monster
            self.game_manager.bag._monsters_data.append(item_or_monster)
        Logger.info(f"Bought: {item_or_monster}")
        
    def sell_monster(self, index: int):
        monsters = self.game_manager.bag._monsters_data

        if index < 0 or index >= len(monsters):
            return

        monster = monsters[index]
        # price related to level
        price = monster["level"] * 5
        # keep at least 1
        if len(monsters) <= 1:
            self.warning_message = "Must keep at least one monster!"
            self.warning_message_timer = 70
            return
        # add coins
        self.game_manager.bag.coins += price
        self.game_manager.bag.sync_coins_item()

        # del monster
        monsters.pop(index)

        self.warning_message = f"Sold {monster['name']} +${price}"
        self.warning_message_timer = 70
        
    def before_battle(self):
        self.game_manager.overlay_open = True
        self.show_monsters = True
    def before_change_scene_battle(self, idx: int):
        self.game_manager.monster_idx = idx
        self.show_monsters = False
        self.game_manager.overlay_open = False
        scene_manager.change_scene("battle")
        
    @override
    def enter(self) -> None:
        if scene_manager.first_enter:
            Logger.info(f"account_name: {scene_manager.account_name}")

            ### Game Manager again
            manager = gm_module.GameManager.load(f"saves/game_{scene_manager.account_name}.json")
            if manager is None:
                Logger.error("Failed to load game manager")
                exit(1)
            services.game_manager = manager
            self.game_manager = manager
            
            # Online Manager
            if GameSettings.IS_ONLINE:
                self.online_manager = OnlineManager()
            else:
                self.online_manager = None
            self.sprite_online = Sprite("ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
            ###
            scene_manager.first_enter = False
        
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()
            
        # reset overlays
        self.show_backpack = False
        self.show_setting = False
        self.slider_dragging = False
        
        self.first_collide_bush = True
        
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):
        # Check if there is assigned next scene
        self.game_manager.try_switch_map()
        
        # Update player and other data
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
            
        # Update others
        self.game_manager.bag.update(dt)
        
        if self.game_manager.player is not None and self.online_manager is not None:
            _ = self.online_manager.update(
                self.game_manager.player.position.x, 
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name
            )
        
        ## Update buttons
        if not(self.game_manager.overlay_open or self.show_shop):
            self.backpack_button.update(dt)
            self.setting_button.update(dt)
        # setting buttons
        if self.show_setting:
            self.save_button.update(dt)
            self.load_button.update(dt)
            self.back_button.update(dt)
            self.x_button.update(dt)
            self.mute_button.update(dt)
        # backpack buttons
        if self.show_backpack:
            self.x_button.update(dt)
            if self.page > 1:
                self.last_page_button.update(dt)
            if self.page * 5 < len(self.game_manager.bag._monsters_data):
                self.next_page_button.update(dt)
        # battle button
        if self.game_manager.collide_enemy_trainers:
            self.battle_button.update(dt)

        # slider UI move
        mouse_x, mouse_y = input_manager.mouse_pos
        slider_x, slider_y = GameSettings.SCREEN_WIDTH*2/7+35, GameSettings.SCREEN_HEIGHT//5+145
        slider_w = GameSettings.SCREEN_WIDTH*3/7-70
        
        if input_manager.mouse_pressed(1):
            if pg.Rect(slider_x, slider_y, slider_w, 25).collidepoint(mouse_x, mouse_y):
                self.slider_dragging = True
        if input_manager.mouse_released(1):
            self.slider_dragging = False
            
        if self.slider_dragging:
            # 0～slider_width
            pos = max(0, min(mouse_x-slider_x, slider_w))
            GameSettings.AUDIO_VOLUME = pos / slider_w
            if GameSettings.MUTE == "OFF": #%%%add
                sound_manager.set_volume(GameSettings.AUDIO_VOLUME)
        
        # press esc to close overlay
        if input_manager.key_down(pg.K_ESCAPE):
            self.close_overlay()
            
        if self.game_manager.collide_bush:
            self.catch_button.update(dt)
            
        if (self.game_manager.collide_shops or (
            self.show_shop and not(input_manager.key_down(pg.K_UP) or 
                                   input_manager.key_down(pg.K_DOWN) or 
                                   input_manager.key_down(pg.K_RIGHT) or 
                                   input_manager.key_down(pg.K_LEFT)))) and not (self.show_backpack or self.show_setting):
            if self.page == 0:
                self.page = 1
            self.show_shop = True
            self.game_manager.collide_shops = False
        elif self.show_shop:
            self.close_overlay()
            
        # shop NPC update
        for npc in self.game_manager.shops.get(self.game_manager.current_map_key, []):
            npc.update(dt)

        # shop UI control
        if self.show_shop:
            self.buy_or_sell_button.update(dt)
            # rebuild buy buttons each frame based on current shop items
            self.shop_buy_buttons = []
            y = GameSettings.SCREEN_HEIGHT//5 + 100

            if self.buy_or_sell == "buy":
                # BUY
                for index, (info, price) in enumerate(self.game_manager.collide_shop_npc.shop_items):
                    if index%5 == 0:
                        y = GameSettings.SCREEN_HEIGHT//5 + 100
                    btn = Button(
                        "UI/raw/UI_Flat_Button02a_3.png",
                        "UI/raw/UI_Flat_Button02a_1.png",
                        GameSettings.SCREEN_WIDTH*2/7 + 262,
                        y - 10,
                        65, 50,
                        lambda idx=index: self.buy_item(idx)
                    )
                    self.shop_buy_buttons.append(btn)
                    y += 60

            else:
                # SELL
                for index, monster in enumerate(self.game_manager.bag._monsters_data):
                    btn = Button(
                        "UI/raw/UI_Flat_Button02a_3.png",
                        "UI/raw/UI_Flat_Button02a_1.png",
                        GameSettings.SCREEN_WIDTH*2/7 + 262,
                        y - 10,
                        65, 50,
                        lambda idx=index: self.sell_monster(idx)
                    )
                    self.shop_buy_buttons.append(btn)
                    y += 60

            
            # shop button
            if self.show_shop:
                self.next_page_button.update(dt)
                self.last_page_button.update(dt)
                # buy buttons update needed
                if self.page*5 >= len(self.shop_buy_buttons):
                    end_of_page = len(self.shop_buy_buttons)
                else:
                    end_of_page = self.page*5
                for btn in self.shop_buy_buttons[(self.page-1)*5:end_of_page]:
                    btn.update(dt)
                
        # countdown for battle trigger
        for enemy in self.game_manager.current_enemy_trainers:
            if enemy.countdown > 0:
                enemy.countdown -= 1
                    
        # buttons for choose monster before battle
        if self.show_monsters == True:
            # rebuild buy buttons each frame based on current shop items
            self.choose_monster_buttons = []
            y = GameSettings.SCREEN_HEIGHT//5 + 420 - len(self.game_manager.bag._monsters_data)*60

            for index, dic in enumerate(self.game_manager.bag._monsters_data):
                btn = Button(
                    "UI/raw/UI_Flat_Button02a_3.png",
                    "UI/raw/UI_Flat_Button02a_1.png",
                    GameSettings.SCREEN_WIDTH*2/7 + 712, 
                    y - 15,
                    50, 50,
                    lambda idx=index: self.before_change_scene_battle(idx)   # '''change'''
                )
                self.choose_monster_buttons.append(btn)
                btn.update(dt)
                y += 60
                
        # === evolution countdown ===
        if self.level_up:
            self.level_timer -= 1

            if self.level_timer <= 0 and self.future_info:
                # change info
                self.game_manager.player_monster["name"] = self.future_info["name"]
                self.game_manager.player_monster["sprite_path"] = self.future_info["sprite_path"]
                # full hp & add max_hp
                self.game_manager.player_monster["max_hp"] += 20
                self.game_manager.player_monster["hp"] = self.game_manager.player_monster["max_hp"]

                # reset flags
                self.level_up = False
                self.future_info = None
                
    @override
    def draw(self, screen: pg.Surface):        
        if self.game_manager.player:
            '''
            [TODO HACKATHON 3]
            Implement the camera algorithm logic here
            Right now it's hard coded, you need to follow the player's positions
            you may use the below example, but the function still incorrect, you may trace the entity.py
            
            camera = self.game_manager.player.camera
            '''
            camera = self.game_manager.player.camera
            #camera = PositionCamera(16 * GameSettings.TILE_SIZE, 30 * GameSettings.TILE_SIZE)
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)
        for npc in self.game_manager.shops.get(self.game_manager.current_map_key, []):
            npc.draw(screen, camera)

        self.game_manager.bag.draw(screen)
        
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for player in list_online:
                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.draw(screen)
        # draw minimap
        self.draw_minimap(screen)
        
        # draw coins
        # image
        item_image = resource_manager.get_image(self.game_manager.bag._items_data[3]["sprite_path"])
        item_image = pg.transform.scale(item_image, (35, 35))
        screen.blit(item_image, pg.Rect(GameSettings.SCREEN_WIDTH-130, 110, 40, 40))
        # amount
        count_text = self.content_font.render(str(self.game_manager.bag._items_data[3]["count"]), True, (0, 0, 0))
        screen.blit(count_text, (GameSettings.SCREEN_WIDTH-70, 115))
        # draw monsters
        # image
        item_image = resource_manager.get_image("ingame_ui/baricon7.png")
        item_image = pg.transform.scale(item_image, (35, 35))
        screen.blit(item_image, pg.Rect(GameSettings.SCREEN_WIDTH-130, 160, 40, 40))
        # amount
        count_text = self.content_font.render(str(len(self.game_manager.bag._monsters_data)), True, (0, 0, 0))
        screen.blit(count_text, (GameSettings.SCREEN_WIDTH-70, 165))
        
        ## draw buttons
        self.backpack_button.draw(screen)
        self.setting_button.draw(screen)
        
        # DONE checkpoint2-05: collide with enemy trainers draw
        if self.game_manager.collide_enemy_trainers and not self.game_manager.overlay_open:
            # "!"
            warning_image = resource_manager.get_image("exclamation.png")
            warning_image = pg.transform.scale(warning_image, (35, 35))
            screen.blit(warning_image, pg.Rect((self.game_manager.enemy_trainer_pos.x)-camera.x-10, (self.game_manager.enemy_trainer_pos.y-5)-camera.y-10, 35, 35))
            
            enemy = None
            for e in self.game_manager.current_enemy_trainers:
                if e is self.game_manager.collide_enemy_trainer:
                    enemy = e
                    break
            # countdown display
            if enemy:
                seconds_left = max(0, enemy.countdown // 50)
                if seconds_left > 0:
                    timer_text = self.content_font.render(f"{seconds_left}", True, (255, 255, 255))
                    screen.blit(timer_text, (
                        (self.game_manager.enemy_trainer_pos.x - camera.x),
                        (self.game_manager.enemy_trainer_pos.y - camera.y - 40)
                    ))
            
            enemy = None
            for e in self.game_manager.current_enemy_trainers:
                if e.animation.rect.colliderect(pg.Rect(self.game_manager.enemy_trainer_pos.x,
                                                        self.game_manager.enemy_trainer_pos.y, 1, 1)):
                    enemy = e
                    break
            if len(self.game_manager.bag._monsters_data) <= 1 and not self.show_shop:
                self.warning_message = "only one monster left! Go find bush"
                self.warning_message_timer = 1
            if len(self.game_manager.bag._monsters_data) > 1 and enemy and self.game_manager.collide_enemy_trainers and enemy.countdown < 30:  # countdown 0~30 show battle button
                self.battle_button.draw(screen)
                battle_text = self.content_font.render("Battle!", True, (0,0,0))
                screen.blit(battle_text, (GameSettings.SCREEN_WIDTH-145, GameSettings.SCREEN_HEIGHT-65))
            
        
        # DONE checkpoint2-01: show overlay(setting/backpack button clinked)
        overlay_x, overlay_y = GameSettings.SCREEN_WIDTH*2/7, GameSettings.SCREEN_HEIGHT//5
        if self.show_setting or self.show_backpack or self.show_shop or self.show_monsters:
            # darken background
            background = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
            background.fill((0, 0, 0, 150))  # (R,G,B,transparency)
            screen.blit(background, (0, 0))

            if self.show_shop:
                overlay = BackgroundSprite("UI/raw/UI_Flat_Frame02a.png", GameSettings.SCREEN_WIDTH*3/7, GameSettings.SCREEN_HEIGHT*3/5)
            else:
                overlay = BackgroundSprite("UI/raw/UI_Flat_Frame03a.png", GameSettings.SCREEN_WIDTH*3/7, GameSettings.SCREEN_HEIGHT*3/5)
            
            if not self.show_monsters:
                overlay.draw(screen, overlay_x, overlay_y)
            
        if self.show_setting:
            # draw buttons
            self.save_button.draw(screen)
            self.load_button.draw(screen)
            self.back_button.draw(screen)
            self.x_button.draw(screen)
            
            # text
            title = self.title_font.render("SETTINGS", True, (255, 255, 255))
            screen.blit(title, (overlay_x+35, overlay_y+35))
            volume_text = self.content_font.render(f"Volume: {int(GameSettings.AUDIO_VOLUME*100)}%", True, (255, 255, 255))
            screen.blit(volume_text, (overlay_x+35, overlay_y+110))
            mute_text = self.content_font.render(f"Mute: {GameSettings.MUTE}", True, (255, 255, 255))
            screen.blit(mute_text, (overlay_x+35, overlay_y+200))
            esc_text = self.note_font.render(f"press ESC to quit", True, (255, 255, 255))
            screen.blit(esc_text, (overlay_x+35, overlay_y+GameSettings.SCREEN_HEIGHT*3/5-40))
            
            ## volume slider
            # bar
            pg.draw.rect(screen, (210, 210, 210), (overlay_x+35, overlay_y+150, GameSettings.SCREEN_WIDTH*3/7-70, 20)) #(x, y, width, height)
            # moving UI
            handle_x = overlay_x+35 + int(GameSettings.AUDIO_VOLUME * (GameSettings.SCREEN_WIDTH*3/7-70 - 15))
            handle_y = overlay_y+145
            volume_move_UI_image = resource_manager.get_image("UI/raw/UI_Flat_Button02a_1.png")
            volume_move_UI_image = pg.transform.scale(volume_move_UI_image, (15, 25))
            screen.blit(volume_move_UI_image, pg.Rect(handle_x, handle_y, 15, 25))
            
            ## mute button
            # change color
            self.mute_button.img_button_default = Sprite(("UI/raw/UI_Flat_BarFill01c.png" if GameSettings.MUTE == "OFF" else "UI/raw/UI_Flat_BarFill01a.png"), (30, 20))
            self.mute_button.img_button_hover = Sprite(("UI/raw/UI_Flat_BarFill01d.png" if GameSettings.MUTE == "OFF" else "UI/raw/UI_Flat_BarFill01b.png"), (30, 20))
            self.mute_button.draw(screen)

            # moving UI
            mute_move_UI_image = resource_manager.get_image("UI/raw/UI_Flat_Button02a_1.png")
            mute_move_UI_image = pg.transform.scale(mute_move_UI_image, (15, 25))
            screen.blit(mute_move_UI_image, pg.Rect(overlay_x+ (185 if GameSettings.MUTE == "OFF" else 200), overlay_y+195, 15, 25))
            
        if self.show_backpack:
            # draw buttons
            self.x_button.draw(screen)
            
            # text
            title = self.title_font.render("BAG", True, (255, 255, 255))
            screen.blit(title, (overlay_x+35, overlay_y+35))
            
            # monsters
            i = 0
            block_x, block_y_top = overlay_x+55, overlay_y+75
            block_dis = 57
            block_image = resource_manager.get_image("UI/raw/UI_Flat_Banner03a.png")
            block_image = pg.transform.scale(block_image, ((GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
            hp_bar_image = resource_manager.get_image("UI/raw/UI_Flat_BarFill01a.png")
            
            # next page button
            if self.page > 1:
                self.last_page_button.draw(screen)
            if self.page*5 < len(self.game_manager.bag._monsters_data):
                self.next_page_button.draw(screen)
            # determine monsters shown in page
            if self.page*5 >= len(self.game_manager.bag._monsters_data):
                end_of_page = len(self.game_manager.bag._monsters_data)
            else:
                end_of_page = self.page*5
            
            for monster in self.game_manager.bag._monsters_data[(self.page-1)*5:end_of_page]:
                # block
                screen.blit(block_image, pg.Rect(block_x-5, block_y_top+block_dis*i, (GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
                # image
                monster_image = resource_manager.get_image(monster["sprite_path"])
                monster_image = pg.transform.scale(monster_image, (35, 35))
                screen.blit(monster_image, pg.Rect(block_x+10, block_y_top+block_dis*i+5, 35, 35))
                # name
                name_text = self.name_font.render(monster["name"], True, (0, 0, 0))
                screen.blit(name_text, (block_x+55, block_y_top+block_dis*i+7))
                # hp bar
                bar_w = (GameSettings.SCREEN_WIDTH*3/7)//3-80
                pg.draw.rect(screen, (200, 200, 200), (block_x+55, block_y_top+block_dis*i+20, bar_w, 12))
                hp_bar_image = pg.transform.scale(hp_bar_image, ((monster["hp"]/monster["max_hp"])*bar_w, 10))
                screen.blit(hp_bar_image, pg.Rect(block_x+56, block_y_top+block_dis*i+21, (monster["hp"]/monster["max_hp"])*bar_w, 10))
                # hp
                hp_text = self.hp_font.render(f"{monster["hp"]}/{monster["max_hp"]}", True, (0, 0, 0))
                screen.blit(hp_text, (block_x+55, block_y_top+block_dis*i+35))
                # level
                name_text = self.name_font.render(f"Lv{monster["level"]}", True, (0, 0, 0))
                screen.blit(name_text, (block_x+55+bar_w+5, block_y_top+block_dis*i+20))
                
                i += 1
            
            block_x, block_y_top = overlay_x+(GameSettings.SCREEN_WIDTH*3/7)//2+10, overlay_y+75
            block_dis = 57
            i = 0  
            for item in self.game_manager.bag._items_data:
                if item["name"] == "Coins":
                    continue
                # image
                item_image = resource_manager.get_image(item["sprite_path"])
                item_image = pg.transform.scale(item_image, (35, 35))
                screen.blit(item_image, pg.Rect(block_x+10, block_y_top+block_dis*i+5, 40, 40))
                # name
                name_text = self.name_font.render(item["name"], True, (0, 0, 0))
                screen.blit(name_text, (block_x+55, block_y_top+block_dis*i+17))
                # amount
                count_text = self.name_font.render(str(item["count"]), True, (0, 0, 0))
                screen.blit(count_text, (block_x+200, block_y_top+block_dis*i+17))
                
                i += 1
            
        if self.game_manager.collide_bush == False:
            self.first_collide_bush = True
        if self.game_manager.collide_bush and not self.game_manager.overlay_open and (self.first_collide_bush or self.can_catch):
            if self.first_collide_bush:
                self.can_catch = 1 if random.random() < 1/4 else 0 # bush_has monster with possibility 1/5
                self.first_collide_bush = False
            
            if self.can_catch:
                self.catch_button.draw(screen)
                catch_text = self.content_font.render("Catch!", True, (0, 0, 0))
                screen.blit(catch_text, (GameSettings.SCREEN_WIDTH-145, GameSettings.SCREEN_HEIGHT-65))
            
        # shop overlay
        if self.show_shop:
            # next page button
            if self.page > 1:
                self.last_page_button.draw(screen)
            if self.page*5 < len(self.shop_buy_buttons):
                self.next_page_button.draw(screen)
            # sell or buy
            self.buy_or_sell_button.draw(screen)
            mode_text = self.medium_font.render( f"Mode: {self.buy_or_sell.upper()}", True, (255, 255, 255))
            screen.blit(mode_text, (overlay_x + 200, overlay_y + 35))
            # title
            title = self.title_font.render("SHOP", True, (255, 255, 255))
            screen.blit(title, (overlay_x + 35, overlay_y + 35))
            
            '''[TODO] list out items-> which NPC'''
            y = overlay_y + 100

            # collided npc's items + monsters
            # draw buy buttons
            if self.page*5 >= len(self.shop_buy_buttons):
                end_of_page = len(self.shop_buy_buttons)
            else:
                end_of_page = self.page*5
            
            for btn in self.shop_buy_buttons[(self.page-1)*5:end_of_page]:
                btn.draw(screen)
                
            if self.buy_or_sell == "buy":
                items = self.game_manager.collide_shop_npc.shop_items
            else:
                items = []
                for monster in self.game_manager.bag._monsters_data:
                    price = monster["level"] * 5
                    items.append((monster, price))
            for name_or_monsterInfo, price in items[(self.page-1)*5:end_of_page]:
                if type(name_or_monsterInfo) == str:
                    # block
                    block_image = resource_manager.get_image("UI/raw/UI_Flat_Banner03a.png")
                    block_image = pg.transform.scale(block_image, ((GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
                    screen.blit(block_image, pg.Rect(overlay_x + 35-5, y-12, (GameSettings.SCREEN_WIDTH*3/7)//3+25 , 52))
                    # image
                    item_image = None
                    for item in self.game_manager.bag._items_data:
                        if item["name"] == name_or_monsterInfo:
                            item_image = resource_manager.get_image(item["sprite_path"])
                            break
                    item_image = pg.transform.scale(item_image, (35, 35))
                    screen.blit(item_image, pg.Rect(overlay_x + 40, y-5, 40, 40))
                    # name
                    item_text = self.medium_font.render(name_or_monsterInfo, True, (0, 0, 0))
                    screen.blit(item_text, (overlay_x + 25 +65, y+5))
                else:
                    # block
                    block_image = resource_manager.get_image("UI/raw/UI_Flat_Banner03a.png")
                    block_image = pg.transform.scale(block_image, ((GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
                    screen.blit(block_image, pg.Rect(overlay_x + 35-5, y-12, (GameSettings.SCREEN_WIDTH*3/7)//3+25 , 52))
                    # image
                    monster_image = resource_manager.get_image(name_or_monsterInfo["sprite_path"])
                    monster_image = pg.transform.scale(monster_image, (35, 35))
                    screen.blit(monster_image, pg.Rect(overlay_x + 35+10, y-7, 35, 35))
                    # name
                    name_text = self.name_font.render(name_or_monsterInfo["name"], True, (0, 0, 0))
                    screen.blit(name_text, (overlay_x + 35+55, y-4))
                    # hp bar
                    bar_w = (GameSettings.SCREEN_WIDTH*3/7)//3-80
                    pg.draw.rect(screen, (200, 200, 200), (overlay_x + 35+55, y+8, bar_w, 12))
                    hp_bar_image = resource_manager.get_image("UI/raw/UI_Flat_BarFill01a.png")
                    hp_bar_image = pg.transform.scale(hp_bar_image, ((name_or_monsterInfo["hp"]/name_or_monsterInfo["max_hp"])*bar_w, 10))
                    screen.blit(hp_bar_image, pg.Rect(overlay_x + 35+56, y+9, (name_or_monsterInfo["hp"]/name_or_monsterInfo["max_hp"])*bar_w, 10))
                    # hp
                    hp_text = self.hp_font.render(f"{name_or_monsterInfo["hp"]}/{name_or_monsterInfo["max_hp"]}", True, (0, 0, 0))
                    screen.blit(hp_text, (overlay_x + 35+55, y+23))
                    # level
                    name_text = self.name_font.render(f"Lv{name_or_monsterInfo["level"]}", True, (0, 0, 0))
                    screen.blit(name_text, (overlay_x + 35+55+bar_w+5, y+8))
                    
                # price
                item_text = self.medium_font.render(f"${price}", True, (0, 0, 0))
                screen.blit(item_text, (overlay_x + 275, y+5))
                y += 60

            ## show coins
            # image
            item_image = resource_manager.get_image(self.game_manager.bag._items_data[3]["sprite_path"])
            item_image = pg.transform.scale(item_image, (35, 35))
            screen.blit(item_image, pg.Rect(overlay_x + 400, overlay_y + 35, 40, 40))
            # amount
            count_text = self.content_font.render(str(self.game_manager.bag._items_data[3]["count"]), True, (255, 255, 255))
            screen.blit(count_text, (overlay_x + 450, overlay_y + 40))
     
        if self.warning_message_timer > 0 and self.warning_message:  
            # overlay
            if self.warning_message == "No enough coins!":
                overlay = pg.Surface((220, 40), pg.SRCALPHA)
                overlay.fill((255, 0, 0, 100))   # (R,G,B,A)
                screen.blit(overlay, (overlay_x+150, overlay_y-45))
            elif self.warning_message == "only one monster left! Go find bush":
                overlay = pg.Surface((400, 40), pg.SRCALPHA)
                overlay.fill((255, 0, 0, 100))   # (R,G,B,A)
                screen.blit(overlay, (GameSettings.SCREEN_WIDTH-400 -10, GameSettings.SCREEN_HEIGHT-150 -10))
            elif self.warning_message == "Won! earn 30 coins!": 
                overlay = pg.Surface((230, 40), pg.SRCALPHA)
                overlay.fill((255, 255, 0, 100))   # (R,G,B,A)
                screen.blit(overlay, (overlay_x+150, overlay_y-45))
            elif self.warning_message == "Level up!":
                # big overlay
                overlay = BackgroundSprite("UI/raw/UI_Flat_Banner02a.png", 500, 200)
                overlay.draw(screen, overlay_x+110, overlay_y-80)
                # word highlight
                overlay = pg.Surface((230, 40), pg.SRCALPHA)
                overlay.fill((255, 255, 0, 100))   # (R,G,B,A)
                screen.blit(overlay, (overlay_x+250, overlay_y-55))
            elif self.warning_message == "Must keep at least one monster!":
                overlay = pg.Surface((340, 40), pg.SRCALPHA)
                overlay.fill((255, 0, 0, 120))
                screen.blit(overlay, (overlay_x+120, overlay_y-45))
            
            self.warning_message_timer -= 1
            title = self.medium_font.render(self.warning_message, True, (255, 255, 255))
            if self.warning_message == "No enough coins!":
                screen.blit(title, (overlay_x+175, overlay_y-35))
            elif self.warning_message == "only one monster left! Go find bush":
                screen.blit(title, (GameSettings.SCREEN_WIDTH-400, GameSettings.SCREEN_HEIGHT-150))
            elif self.warning_message == "Won! earn 30 coins!":
                screen.blit(title, (overlay_x+170, overlay_y-35))
            elif self.warning_message == "Level up!":
                title = self.medium_font.render(self.warning_message, True, (0, 0, 0))
                screen.blit(title, (overlay_x+300, overlay_y-45))
                level = self.title_font.render(f"lv. {self.game_manager.player_monster["level"]}", True, (0, 0, 0))
                screen.blit(level, (overlay_x+300, overlay_y))
                self.previous_level = self.game_manager.player_monster["level"]
                if self.warning_message_timer % 10 == 0 and self.warning_message_timer>=50:
                    self.game_manager.player_monster["level"] += 1 # add level by 1 every 4*dt(total add 10)
                    
                    # change info when hitting standard
                    if self.game_manager.player_monster["name"] == "Pikachu":
                        if self.previous_level < 55 and self.game_manager.player_monster["level"] >= 55:
                            self.level_timer = 150
                            self.level_up = True
                            self.future_info = {
                                "sprite_path": "menu_sprites/menusprite2.png",
                                "name": "Piculakus"
                            }

                        elif self.previous_level < 100 and self.game_manager.player_monster["level"] >= 100:
                            self.level_timer = 150
                            self.level_up = True
                            self.future_info = {
                                "sprite_path": "menu_sprites/menusprite3.png",
                                "name": "Pigodicha"
                            }
            elif self.warning_message == "Must keep at least one monster!":
                screen.blit(title, (overlay_x+140, overlay_y-35))
                
        if self.game_manager.win_message == True:
            self.game_manager.bag.pay(-30)
            self.warning_message = "Won! earn 30 coins!"
            self.warning_message_timer = 35
            self.game_manager.win_message = False
        if self.warning_message == "Won! earn 30 coins!" and self.warning_message_timer == 1:
            self.warning_message = "Level up!"
            self.warning_message_timer = 150
            
        if self.show_monsters == True:
            # monsters
            i = 0
            block_x, block_y_top = overlay_x+500, GameSettings.SCREEN_HEIGHT//5 + 400 - len(self.game_manager.bag._monsters_data)*57
            block_dis = 57
            block_image = resource_manager.get_image("UI/raw/UI_Flat_Banner03a.png")
            block_image = pg.transform.scale(block_image, ((GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
            hp_bar_image = resource_manager.get_image("UI/raw/UI_Flat_BarFill01a.png")
            
            for monster in self.game_manager.bag._monsters_data:
                # block
                screen.blit(block_image, pg.Rect(block_x-5, block_y_top+block_dis*i, (GameSettings.SCREEN_WIDTH*3/7)//3+30 , 52))
                # image
                monster_image = resource_manager.get_image(monster["sprite_path"])
                monster_image = pg.transform.scale(monster_image, (35, 35))
                screen.blit(monster_image, pg.Rect(block_x+10, block_y_top+block_dis*i+5, 35, 35))
                # name
                name_text = self.name_font.render(monster["name"], True, (0, 0, 0))
                screen.blit(name_text, (block_x+55, block_y_top+block_dis*i+7))
                # hp bar
                bar_w = (GameSettings.SCREEN_WIDTH*3/7)//3-80
                pg.draw.rect(screen, (200, 200, 200), (block_x+55, block_y_top+block_dis*i+20, bar_w, 12))
                hp_bar_image = pg.transform.scale(hp_bar_image, ((monster["hp"]/monster["max_hp"])*bar_w, 10))
                screen.blit(hp_bar_image, pg.Rect(block_x+56, block_y_top+block_dis*i+21, (monster["hp"]/monster["max_hp"])*bar_w, 10))
                # hp
                hp_text = self.hp_font.render(f"{monster["hp"]}/{monster["max_hp"]}", True, (0, 0, 0))
                screen.blit(hp_text, (block_x+55, block_y_top+block_dis*i+35))
                # level
                name_text = self.name_font.render(f"Lv{monster["level"]}", True, (0, 0, 0))
                screen.blit(name_text, (block_x+55+bar_w+5, block_y_top+block_dis*i+20))
                
                i += 1

            # draw monster buttons
            y = GameSettings.SCREEN_HEIGHT//5 + 420 - len(self.game_manager.bag._monsters_data)*60
            
            for idx, btn in enumerate (self.choose_monster_buttons):
                btn.draw(screen)
                
                # idx on button
                idx_text = self.title_font.render(f"{idx+1}", True, (0, 0, 0))
                screen.blit(idx_text, (GameSettings.SCREEN_WIDTH*2/7 + 732, y-5))
                y += 60
                
        # === evolution display ===
        if self.level_up and self.future_info:
            # black transparent background
            upgrade_background = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT), pg.SRCALPHA)
            upgrade_background.fill((0, 0, 0, 160))
            screen.blit(upgrade_background, (0, 0))

            # new monster image
            upgrade_monster_image = resource_manager.get_image(self.future_info["sprite_path"])
            upgrade_monster_image = pg.transform.scale(upgrade_monster_image, (180, 180))
            screen.blit(upgrade_monster_image, (GameSettings.SCREEN_WIDTH // 2 - 90, GameSettings.SCREEN_HEIGHT // 2 - 120))
            # text
            upgrade_text = self.title_font.render(f"Upgrade to {self.future_info['name']}!", True, (255, 255, 0))
            screen.blit(upgrade_text, (GameSettings.SCREEN_WIDTH // 2 - upgrade_text.get_width() // 2, GameSettings.SCREEN_HEIGHT // 2 + 80))