'''
[TODO HACKATHON 5]
Try to mimic the menu_scene.py or game_scene.py to create this new scene
'''
import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from src.sprites import Sprite
from src.core.services import scene_manager, sound_manager, input_manager, resource_manager
from typing import override
from src.utils import load_font

class SettingScene(Scene):
    # Background Image
    background: BackgroundSprite
    # Buttons
    back_button: Button
    mute_button: Button
    
    ## font
    title_font: pg.font.Font
    content_font: pg.font.Font
    note_font: pg.font.Font
    name_font: pg.font.Font
    hp_font: pg.font.Font
    
    def __init__(self):
        super().__init__()
        self.background = BackgroundSprite("backgrounds/background3.png")

        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT * 3 // 4
        self.back_button = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            px, py, 100, 100, #####
            lambda: scene_manager.change_scene("menu")
        )
        self.mute_button = Button(
            ("UI/raw/UI_Flat_BarFill01c.png" if GameSettings.MUTE == "OFF" else "UI/raw/UI_Flat_BarFill01a.png"), ("UI/raw/UI_Flat_BarFill01d.png" if GameSettings.MUTE == "OFF" else "UI/raw/UI_Flat_BarFill01b.png"),
            GameSettings.SCREEN_WIDTH*2/7 +185, GameSettings.SCREEN_HEIGHT//5 +200, 30, 20,
            lambda: self.mute_button_onclick() # mute: ON->OFF / OFF->ON
        )
        
        ## fonts
        self.title_font = load_font("Minecraft.ttf", 32) #path, size
        self.content_font = load_font("Minecraft.ttf", 28)
        self.note_font = load_font("Minecraft.ttf", 16)
        self.name_font = load_font("Minecraft.ttf", 12)
        self.hp_font = load_font("Minecraft.ttf", 8)
        
        self.slider_dragging = False
        
    # mute button clicked
    def mute_button_onclick(self):
        if(GameSettings.MUTE == "ON"):
            GameSettings.MUTE = "OFF"
            sound_manager.set_volume(GameSettings.AUDIO_VOLUME)
        else:
            GameSettings.MUTE = "ON"
            sound_manager.set_volume(0)
        
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 102 Opening (Part 2).ogg")
        pass

    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
        if input_manager.key_pressed(pg.K_SPACE):
            scene_manager.change_scene("menu")
            return
        self.back_button.update(dt)
        self.mute_button.update(dt)
        
        #%%%add
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
        
        if input_manager.key_pressed(pg.K_ESCAPE):
            scene_manager.change_scene("menu")
            return

    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        self.back_button.draw(screen)
        
        overlay_x, overlay_y = GameSettings.SCREEN_WIDTH*2/7, GameSettings.SCREEN_HEIGHT//5
        # text
        title = self.title_font.render("SETTINGS", True, (0, 0, 0))
        screen.blit(title, (overlay_x+35, overlay_y+35))
        volume_text = self.content_font.render(f"Volume: {int(GameSettings.AUDIO_VOLUME*100)}%", True, (0, 0, 0))
        screen.blit(volume_text, (overlay_x+35, overlay_y+110))
        mute_text = self.content_font.render(f"Mute: {GameSettings.MUTE}", True, (0, 0, 0))
        screen.blit(mute_text, (overlay_x+35, overlay_y+200))
        esc_text = self.note_font.render(f"press ESC to quit", True, (0, 0, 0))
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
