import pygame as pg

from src.utils import GameSettings, load_font, Logger
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager
from typing import override

from src.core.services import game_manager
import os
import shutil

class MenuScene(Scene):
    # Background Image
    background: BackgroundSprite
    # Buttons
    play_button: Button
    setting_button: Button
    
    # input account
    account_name: str
    input_active: bool
    # cursor
    cursor_timer: float
    cursor_visible: bool
    # message
    error_message: str
    error_message_timer: int
    
    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background1.png")
        
        ## account name input
        self.account_name = ""
        self.input_active = False
        # input field image & area
        self.input_bg = resource_manager.get_image("UI/raw/UI_Flat_InputField01a.png")
        self.input_bg = pg.transform.scale(self.input_bg, (300, 50))
        self.input_rect = pg.Rect(GameSettings.SCREEN_WIDTH // 2 - 150, GameSettings.SCREEN_HEIGHT // 2, 300, 50)
        # input font
        self.font = load_font("Minecraft.ttf", 22)

        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3//4
        self.play_button = Button(
            "UI/button_play.png", "UI/button_play_hover.png",
            px + 100, py, 80, 80,
            lambda: self.start_game()
        )
        self.setting_button = Button(
            "UI/button_setting.png", "UI/button_setting_hover.png",
            px - 140, py, 80, 80,
            lambda: scene_manager.change_scene("setting")
        )
        
        # cursor
        self.cursor_timer = 0.0
        self.cursor_visible = True
        
        # message
        self.error_message = ""
        self.error_message_timer = 0
        
    def start_game(self):
        name = self.account_name
        # entered nothing
        if not name:
            self.error_message = "please enter player name"
            self.error_message_timer = 80
            return
        for char in name:
            c = ord(char)
            if not ( ord('0') <= c <= ord('9') or
                     ord('a') <= c <= ord('z') or
                     ord('A') <= c <= ord('Z')):
                self.error_message = "invalid player name! (should only have numbers or characters)"
                self.error_message_timer = 80
                return
        # path name
        save_path = f"saves/game_{name}.json"
        backup_path = "saves/game0.json"
        
        # save_path doesn't exsist
        if not os.path.exists(save_path):
            os.makedirs("saves", exist_ok=True)
            shutil.copyfile(backup_path, save_path) # copy saves/game0.json to make new .json
            Logger.info(f"Created new save: {save_path} from {backup_path}")
        scene_manager.account_name = self.account_name
        scene_manager.change_scene("game")
        
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        self.account_name = ""
        pass

    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
        # click input field
        if input_manager.mouse_pressed(1):
            if self.input_rect.collidepoint(input_manager.mouse_pos):
                self.input_active = True
            else:
                self.input_active = False

        # keyboard text input
        if self.input_active:
            # backspace
            if input_manager.key_pressed(pg.K_BACKSPACE) and self.account_name:
                self.account_name = self.account_name[:-1]

            # normal characters
            for ch in input_manager.get_text():
                if len(self.account_name) < 12:
                    self.account_name += ch

        # cursor blink
        if self.input_active:
            self.cursor_timer += dt
            if self.cursor_timer >= 0.5:
                self.cursor_visible = not self.cursor_visible
                self.cursor_timer = 0
        else:
            self.cursor_visible = False
            self.cursor_timer = 0

        # buttons
        self.play_button.update(dt)
        self.setting_button.update(dt)

        # error message
        if self.error_message_timer > 0:
            self.error_message_timer -= 1
            if self.error_message_timer <= 0:
                self.error_message = ""

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        
        if self.error_message:
            message_text = self.font.render(self.error_message, True, (255, 0, 0))
            screen.blit(message_text, (self.input_rect.x, self.input_rect.y - 30))
        
        ### input field
        # input field
        screen.blit(self.input_bg, self.input_rect)
        # text
        display_text = self.account_name
        if self.input_active and self.cursor_visible:
            display_text += "|"
        if self.input_active:
            text_surf = self.font.render(display_text or "", True, (0, 0, 0))
        else:
            text_surf = self.font.render(display_text or "Enter name", True, (0, 0, 0) if display_text else (200, 200, 200))
        screen.blit(text_surf, (self.input_rect.x + 10, self.input_rect.y + 12))

        # active outline
        if self.input_active or self.input_rect.collidepoint(input_manager.mouse_pos):
            pg.draw.rect(screen, (255, 200, 0), self.input_rect, 2)
        ###
        
        self.play_button.draw(screen)
        self.setting_button.draw(screen)
