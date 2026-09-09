"""Lumen — Level 1: Light Reveals Reality.

FULLSCREEN 2D top-down puzzle adventure.
Bootstraps Pygame, manages centralized game state transitions (MENU -> PLAYING -> LEVEL1_COMPLETE),
and wires the player, lantern, inventory, camera, and UI into the ancient temple chamber.

Controls:
    WASD / Arrow keys  — Move explorer
    E                  — Inspect clues / Attempt exit
    1 / 2 / 3          — Try collected keys at the exit
    L                  — Toggle lantern on/off
    C / H              — Toggle controls guide
    F11                — Toggle fullscreen / windowed
    Esc                — Pause / Menu / Quit
"""

import sys
import math
import time
import pygame

from engine.player import Player
from engine.lantern import Lantern
from engine.inventory import Inventory
from engine.camera import Camera
from systems.ui import ClueModal, HUD, StoryModal, DoorModal
from systems.inventory_ui import InventoryModal
from systems.audio import audio
from content.level1 import Level1Room, SCREEN_WIDTH, SCREEN_HEIGHT, ROOM_WIDTH, ROOM_HEIGHT

FPS = 60

# Game States as specified in architecture.md section 5
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_LEVEL1_COMPLETE = "level1_complete"


class GameManager:
    """Central game loop, state controller, and presentation renderer."""

    def __init__(self):
        pygame.init()

        # Get native display resolution for fullscreen
        display_info = pygame.display.Info()
        self.native_w = display_info.current_w
        self.native_h = display_info.current_h

        # Internal render resolution (game world)
        self.render_w = SCREEN_WIDTH
        self.render_h = SCREEN_HEIGHT

        # Start in fullscreen
        self.is_fullscreen = True
        self._set_display_mode()
        pygame.display.set_caption("Lumen: Light Reveals Reality — Level 1")
        self.clock = pygame.time.Clock()

        # Internal render surface (always at game resolution)
        self.game_surface = pygame.Surface((self.render_w, self.render_h))

        # Fonts
        self.font_title = pygame.font.SysFont("georgia", 34, bold=True)
        self.font_subtitle = pygame.font.SysFont("consolas", 15)
        self.font_modal_title = pygame.font.SysFont("georgia", 20, bold=True)
        self.font_body = pygame.font.SysFont("consolas", 15)
        self.font_small = pygame.font.SysFont("consolas", 13, bold=True)

        self.state = STATE_MENU
        self.show_controls = False
        self.menu_pulse = 0.0

        # UI & Camera systems
        self.camera = Camera(self.render_w, self.render_h, ROOM_WIDTH, ROOM_HEIGHT)
        self.clue_modal = ClueModal(self.render_w, self.render_h)
        self.story_modal = StoryModal(self.render_w, self.render_h)
        self.door_modal = DoorModal(self.render_w, self.render_h)
        self.inventory_modal = InventoryModal(self.render_w, self.render_h)
        self.inventory_btn_rect = pygame.Rect(self.render_w - 138, 76, 124, 28)
        self.hud = HUD(self.render_w, self.render_h)

        # Game session state
        self.player: Player = Player(x=780, y=1100)
        self.lantern: Lantern = Lantern(radius=130)
        self.inventory: Inventory = Inventory()
        self.room: Level1Room = Level1Room()

        self.start_time = 0.0
        self.elapsed_time = 0.0

    def _set_display_mode(self):
        """Set the display mode based on current fullscreen state."""
        if self.is_fullscreen:
            self.screen = pygame.display.set_mode(
                (self.native_w, self.native_h), pygame.FULLSCREEN
            )
        else:
            self.screen = pygame.display.set_mode(
                (self.render_w, self.render_h)
            )

    def _toggle_fullscreen(self):
        """Toggle between fullscreen and windowed mode."""
        self.is_fullscreen = not self.is_fullscreen
        self._set_display_mode()

    def _scale_and_blit(self):
        """Scale the internal render surface to fill the display."""
        if self.is_fullscreen:
            # Calculate scaling to fill screen while maintaining aspect ratio
            scale_x = self.native_w / self.render_w
            scale_y = self.native_h / self.render_h
            scale = min(scale_x, scale_y)

            scaled_w = int(self.render_w * scale)
            scaled_h = int(self.render_h * scale)

            # Center on screen
            offset_x = (self.native_w - scaled_w) // 2
            offset_y = (self.native_h - scaled_h) // 2

            # Fill letterbox areas with black
            self.screen.fill((0, 0, 0))

            scaled = pygame.transform.smoothscale(self.game_surface, (scaled_w, scaled_h))
            self.screen.blit(scaled, (offset_x, offset_y))
        else:
            self.screen.blit(self.game_surface, (0, 0))

    def _screen_to_game_coords(self, pos: tuple[int, int]) -> tuple[int, int]:
        """Translates screen pixel coordinates to internal game surface coordinates."""
        sx, sy = pos
        if self.is_fullscreen:
            scale_x = self.native_w / self.render_w
            scale_y = self.native_h / self.render_h
            scale = min(scale_x, scale_y)
            scaled_w = int(self.render_w * scale)
            scaled_h = int(self.render_h * scale)
            offset_x = (self.native_w - scaled_w) // 2
            offset_y = (self.native_h - scaled_h) // 2
            if scale > 0:
                gx = int((sx - offset_x) / scale)
                gy = int((sy - offset_y) / scale)
                return (gx, gy)
        return (sx, sy)

    def reset_level1(self):
        """Initializes or resets a fresh Level 1 session."""
        self.player = Player(x=780, y=1100)
        self.lantern = Lantern(radius=130)
        self.inventory.clear()
        self.room = Level1Room()
        self.clue_modal.close()
        self.story_modal.close()
        self.door_modal.close()
        self.door_modal.reset_chances()
        self.door_auto_opened = False
        self.camera = Camera(self.render_w, self.render_h, ROOM_WIDTH, ROOM_HEIGHT)
        self.start_time = time.time()
        self.elapsed_time = 0.0

        # Story beat: Awakening in Pitch Darkness
        self.story_modal.open(
            "Awakening in the Dark",
            "You awaken trapped in an ancient subterranean temple shrouded in darkness.\n\nNearby, a faint light flickers. Move carefully through the shadows, find the lantern, and pick it up to reveal your path.",
            modal_id="intro",
            footer_prompt="Press [SPACE] or [ESC] to begin"
        )




    def run(self, max_frames=None):
        frames=0
        while True:
            dt=min(self.clock.tick(FPS)/1000.0,.05)
            for event in pygame.event.get():
                if event.type==pygame.QUIT:
                    pygame.quit()
                    return
                if event.type==pygame.KEYDOWN and event.key==pygame.K_F11:
                    self._toggle_fullscreen()
                    continue
                if self.inventory_modal.is_open:
                    pos=self._screen_to_game_coords(event.pos) if event.type==pygame.MOUSEBUTTONDOWN else None
                    self.inventory_modal.handle_input(event,game_pos=pos,inventory=self.inventory)
                    continue
                if event.type==pygame.MOUSEBUTTONDOWN and event.button==1 and self.state==STATE_PLAYING:
                    if not (self.story_modal.is_open or self.clue_modal.is_open or self.door_modal.is_open) and self.inventory_btn_rect.collidepoint(self._screen_to_game_coords(event.pos)):
                        self.inventory_modal.toggle()
                        continue
                if event.type==pygame.KEYDOWN:self._handle_keydown(event.key)
            self._update(dt)
            self._draw()
            self._scale_and_blit()
            pygame.display.flip()
            frames+=1
            if max_frames is not None and frames>=max_frames:
                pygame.quit()
                return

    def _handle_keydown(self, key: int):
        # Global Story Modal priority across all states
        if self.story_modal.is_open:
            if key in (pygame.K_SPACE, pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_e):
                self.story_modal.close()
            return

        if self.state == STATE_MENU:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.reset_level1()
                self.state = STATE_PLAYING
            elif key in (pygame.K_c, pygame.K_h):
                self.show_controls = not self.show_controls
            elif key == pygame.K_ESCAPE:
                if self.show_controls:
                    self.show_controls = False
                else:
                    pygame.quit()
                    sys.exit()

        elif self.state == STATE_PLAYING:
            # 1. Story Modal priority (Awakening intro, All keys gathered, Clue follow-up)
            if self.story_modal.is_open:
                if key in (pygame.K_SPACE, pygame.K_e, pygame.K_ESCAPE, pygame.K_RETURN):
                    self.story_modal.close()
                return

            # 2. Door Keyhole Selection Modal priority (Image 4 - 2 Chances Trial)
            if self.door_modal.is_open:
                if self.door_modal.failed or self.door_modal.unlocked:
                    return
                if key in (pygame.K_ESCAPE, pygame.K_e):
                    self.door_modal.close()
                    return
                elif key in (pygame.K_1, pygame.K_2, pygame.K_3):
                    num = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3}[key]
                    key_id_map = {1: "key_bronze", 2: "key_silver", 3: "key_gold"}
                    kid = key_id_map[num]
                    if not self.inventory.has_key(kid):
                        self.door_modal.feedback_msg = f"You have not discovered Key #{num} yet."
                        self.door_modal.feedback_color = (235, 160, 140)
                        audio.play("door_locked")
                    elif kid in self.door_modal.tried_keys:
                        self.door_modal.feedback_msg = f"You already tried this key! Choose another."
                        self.door_modal.feedback_color = (235, 160, 140)
                    elif kid == "key_gold":
                        self.door_modal.unlocked = True
                        self.door_modal.feedback_msg = "The Gold Key turns! The ancient threshold unseals!"
                        self.door_modal.feedback_color = (255, 235, 120)
                        self.room.is_complete = True
                        audio.play("door_open")
                        self.camera.trigger_shake(intensity=5.0, duration=0.8)
                    else:
                        label = "Bronze Key" if kid == "key_bronze" else "Silver Key"
                        self.door_modal.tried_keys.add(kid)
                        self.door_modal.chances_left -= 1
                        audio.play("door_locked")
                        if self.door_modal.chances_left == 1:
                            self.camera.trigger_shake(intensity=4.0, duration=0.35)
                            self.door_modal.feedback_msg = f"Wrong key! The {label} jams in the lock! (1 CHANCE LEFT!)"
                            self.door_modal.feedback_color = (255, 130, 80)
                        else:
                            self.door_modal.failed = True
                            self.door_modal.failed_timer = 2.0
                            self.camera.trigger_shake(intensity=7.0, duration=0.8)
                            self.door_modal.feedback_msg = "Both chances failed! The sanctum seals shut! Returning to menu..."
                            self.door_modal.feedback_color = (255, 60, 60)
                return

            # 3. Clue Modal priority
            if self.clue_modal.is_open:
                if key in (pygame.K_e, pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN):
                    self.clue_modal.close()
                    # If this was the first object inspected, show the follow-up guidance popup!
                    if getattr(self.room, "first_inspect_followup_pending", False):
                        self.room.first_inspect_followup_pending = False
                        self.story_modal.open(
                            "Searching the Sanctum",
                            "You can inspect objects throughout the temple by pressing [E]. Some relics hold vital clues, while others are mere ruins. Keep looking out for objects as you explore.",
                            modal_id="inspect_followup",
                            footer_prompt="Press [SPACE] or [E] to continue"
                        )
                return

            # Normal Gameplay inputs
            if key == pygame.K_ESCAPE:
                self.state = STATE_MENU
            elif key == pygame.K_i:
                self.inventory_modal.toggle()
            elif key == pygame.K_SPACE:
                self.player.jump()
            elif key == pygame.K_e:
                self.room.handle_interact(
                    self.player, self.inventory, self.clue_modal,
                    lantern=self.lantern, door_modal=self.door_modal
                )
            elif key == pygame.K_l:
                if self.lantern.possessed:
                    self.lantern.toggle()
            elif key in (pygame.K_1, pygame.K_2, pygame.K_3):
                num = {pygame.K_1: 1, pygame.K_2: 2, pygame.K_3: 3}[key]
                door_trigger = self.room.exit_rect.inflate(36, 36)
                if self.player.rect.colliderect(door_trigger):
                    self.room.select_and_try_key(self.inventory, num, self.camera)
                else:
                    self.room._show_message("You must reach the Sanctum Threshold to insert a key.", 2.5)
                    audio.play("door_locked")
            elif key in (pygame.K_c, pygame.K_h):
                self.show_controls = not self.show_controls

        elif self.state == STATE_LEVEL1_COMPLETE:
            if key == pygame.K_SPACE:
                self.reset_level1()
                self.state = STATE_PLAYING
            elif key in (pygame.K_m, pygame.K_RETURN):
                self.state = STATE_MENU
            elif key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()

    def _update(self, dt: float):
        self.menu_pulse = (self.menu_pulse + dt * 2.5) % (2 * math.pi)

        if self.inventory_modal.is_open:
            self.inventory_modal.update(dt)
            return

        if self.state == STATE_PLAYING:
            if self.story_modal.is_open:
                self.story_modal.update(dt)
            elif self.door_modal.is_open:
                self.door_modal.update(dt)
                if self.door_modal.failed:
                    self.door_modal.failed_timer -= dt
                    if self.door_modal.failed_timer <= 0:
                        self.door_modal.close()
                        self.reset_level1()
                        self.state = STATE_MENU
                elif self.door_modal.unlocked:
                    self.room.update(self.player, self.inventory, self.lantern, dt, self.camera)
                    if self.room.door_open_progress >= 1.0:
                        self.door_modal.close()
                        self.state = STATE_LEVEL1_COMPLETE
            elif self.clue_modal.is_open:
                self.clue_modal.update(dt)
            else:
                self.elapsed_time = time.time() - self.start_time

                self.room.update(self.player, self.inventory, self.lantern, dt, self.camera)
                self.camera.update(self.player.center, dt)
                self.hud.update(dt)

                # Landing on final door automatically triggers the keyhole selection modal
                door_trigger = self.room.exit_rect.inflate(36, 36)
                if self.player.rect.colliderect(door_trigger):
                    if not self.door_modal.is_open and not self.room.is_complete and not self.door_modal.failed:
                        if not getattr(self, "door_auto_opened", False):
                            self.door_auto_opened = True
                            self.door_modal.open(self.inventory)
                            audio.play("clue")
                else:
                    self.door_auto_opened = False

                # Check if a story modal was queued (e.g. all 3 keys collected)
                if self.room.pending_story_modal:
                    title, text, mid = self.room.pending_story_modal
                    self.room.pending_story_modal = None
                    self.story_modal.open(title, text, modal_id=mid)

                # Check level completion transition
                if self.room.is_complete and self.room.door_open_progress >= 1.0:
                    self.state = STATE_LEVEL1_COMPLETE

    def _draw(self):
        if self.state == STATE_MENU:self._draw_menu()
        elif self.state == STATE_PLAYING:self._draw_playing()
        elif self.state == STATE_LEVEL1_COMPLETE:self._draw_complete()
        if self.state == STATE_PLAYING:self._draw_side_inventory_button()
        if self.story_modal.is_open:self.story_modal.draw(self.game_surface,self.font_modal_title,self.font_body)
        if self.inventory_modal.is_open:self.inventory_modal.draw(self.game_surface,self.inventory)
        if self.show_controls:self._draw_controls_overlay()

    def _draw_side_inventory_button(self):
        """Draws a refined antique temple satchel / inventory access button on the side screen."""
        mx, my = self._screen_to_game_coords(pygame.mouse.get_pos())
        hovered = self.inventory_btn_rect.collidepoint(mx, my)

        btn_surf = pygame.Surface((self.inventory_btn_rect.width, self.inventory_btn_rect.height), pygame.SRCALPHA)
        bg_col = (30, 24, 40, 235) if hovered else (18, 14, 24, 210)
        border_col = (255, 220, 120) if hovered else (160, 130, 65)

        pygame.draw.rect(btn_surf, bg_col, (0, 0, self.inventory_btn_rect.width, self.inventory_btn_rect.height), border_radius=6)
        pygame.draw.rect(btn_surf, border_col, (0, 0, self.inventory_btn_rect.width, self.inventory_btn_rect.height), width=1, border_radius=6)

        # Subtle gold corner rivets
        rivet_col = (235, 195, 90) if hovered else (120, 95, 45)
        pygame.draw.circle(btn_surf, rivet_col, (4, 4), 1)
        pygame.draw.circle(btn_surf, rivet_col, (self.inventory_btn_rect.width - 5, 4), 1)
        pygame.draw.circle(btn_surf, rivet_col, (4, self.inventory_btn_rect.height - 5), 1)
        pygame.draw.circle(btn_surf, rivet_col, (self.inventory_btn_rect.width - 5, self.inventory_btn_rect.height - 5), 1)

        text_col = (255, 235, 175) if hovered else (210, 195, 160)
        lbl = self.font_small.render("[I] INVENTORY", True, text_col)
        btn_surf.blit(lbl, ((self.inventory_btn_rect.width - lbl.get_width()) // 2, (self.inventory_btn_rect.height - lbl.get_height()) // 2))

        self.game_surface.blit(btn_surf, (self.inventory_btn_rect.x, self.inventory_btn_rect.y))

    # --- Menu Drawing --------------------------------------------------------

    def _draw_menu(self):
        self.game_surface.fill((8, 6, 14))

        # Atmospheric background stone pattern
        for y in range(0, self.render_h, 40):
            for x in range(0, self.render_w, 40):
                if (x + y) % 80 == 0:
                    pygame.draw.rect(self.game_surface, (12, 10, 20), (x, y, 38, 38))

        # Title ambient lantern glow
        glow_pulse = int(140 + 35 * math.sin(self.menu_pulse))
        glow_surf = pygame.Surface((320, 320), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 210, 110, glow_pulse // 5), (160, 160), 150)
        pygame.draw.circle(glow_surf, (255, 235, 170, glow_pulse // 3), (160, 160), 80)
        self.game_surface.blit(glow_surf, (self.render_w // 2 - 160, 100))

        # Title text
        title_text = self.font_title.render("L U M E N", True, (255, 225, 130))
        sub_text = self.font_subtitle.render("LIGHT REVEALS REALITY", True, (210, 185, 120))
        level_tag = self.font_subtitle.render("LEVEL 1: THE AWAKENING", True, (160, 155, 175))

        self.game_surface.blit(title_text, (self.render_w // 2 - title_text.get_width() // 2, 180))
        self.game_surface.blit(sub_text, (self.render_w // 2 - sub_text.get_width() // 2, 230))
        self.game_surface.blit(level_tag, (self.render_w // 2 - level_tag.get_width() // 2, 270))

        # Golden divider
        pygame.draw.line(self.game_surface, (190, 155, 75),
                         (self.render_w // 2 - 140, 256), (self.render_w // 2 + 140, 256), 2)
        pygame.draw.circle(self.game_surface, (240, 205, 90), (self.render_w // 2, 256), 4)

        # Menu options
        btn_y = 350
        enter_color = (255, 240, 190) if int(self.menu_pulse * 2) % 2 == 0 else (210, 195, 150)
        btn1 = self.font_body.render("Press [ENTER] or [SPACE] to Begin", True, enter_color)
        btn2 = self.font_body.render("Press [C] for Controls & Guide", True, (175, 170, 190))
        btn3 = self.font_body.render("[F11] Toggle Fullscreen   |   [ESC] Exit", True, (135, 130, 145))

        self.game_surface.blit(btn1, (self.render_w // 2 - btn1.get_width() // 2, btn_y))
        self.game_surface.blit(btn2, (self.render_w // 2 - btn2.get_width() // 2, btn_y + 36))
        self.game_surface.blit(btn3, (self.render_w // 2 - btn3.get_width() // 2, btn_y + 72))

        # Footer
        footer = self.font_small.render("CG & IP Project — 2D Top-Down Puzzle Adventure", True, (100, 95, 115))
        self.game_surface.blit(footer, (self.render_w // 2 - footer.get_width() // 2, self.render_h - 30))

    # --- Gameplay Drawing ----------------------------------------------------

    def _draw_playing(self):
        # 1. Render Level 1 Chamber
        self.room.draw(self.game_surface, self.player, self.lantern, camera_offset=self.camera.offset)

        # 2. Render HUD (Objective, Energy Bar, Lantern Status, Keys Collected, Toasts)
        obj_hint = self.room.get_objective_hint(self.inventory, lantern=self.lantern)
        self.hud.draw(self.game_surface, self.font_body, self.font_small, self.inventory,

                      self.lantern, obj_hint, self.room.message)

        # 3. Render Clue Modal (if open)
        if self.clue_modal.is_open:
            self.clue_modal.draw(self.game_surface, self.font_modal_title, self.font_body)

        # 4. Render Door Keyhole Modal (if open)
        if self.door_modal.is_open:
            self.door_modal.draw(self.game_surface, self.font_modal_title, self.font_body,
                                 self.font_small, self.inventory)

    # --- Level Complete Drawing ----------------------------------------------

    def _draw_complete(self):
        # Dim existing game scene
        overlay = pygame.Surface((self.render_w, self.render_h), pygame.SRCALPHA)
        overlay.fill((8, 6, 14, 215))
        self.game_surface.blit(overlay, (0, 0))

        card_w = 640
        card_h = 440
        cx = (self.render_w - card_w) // 2
        cy = (self.render_h - card_h) // 2

        # Ornate victory tablet
        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_surf.fill((22, 19, 28, 245))
        pygame.draw.rect(card_surf, (220, 185, 80), (0, 0, card_w, card_h), width=3, border_radius=10)
        pygame.draw.rect(card_surf, (75, 65, 45), (6, 6, card_w - 12, card_h - 12), width=1, border_radius=6)
        self.game_surface.blit(card_surf, (cx, cy))

        # Title
        t_surf = self.font_title.render("LEVEL 1 COMPLETE", True, (255, 225, 120))
        self.game_surface.blit(t_surf, (self.render_w // 2 - t_surf.get_width() // 2, cy + 30))

        sub_surf = self.font_subtitle.render("The Ancient Sanctum Threshold Has Opened", True, (215, 195, 150))
        self.game_surface.blit(sub_surf, (self.render_w // 2 - sub_surf.get_width() // 2, cy + 80))

        pygame.draw.line(self.game_surface, (190, 155, 75), (cx + 50, cy + 110), (cx + card_w - 50, cy + 110), 2)

        # Statistics
        clues_found = sum(1 for c in self.room.clue_objects if c.triggered)
        mins = int(self.elapsed_time // 60)
        secs = int(self.elapsed_time % 60)

        stats = [
            f"Keys Collected: {self.inventory.key_count} / 3",
            f"Clues Uncovered: {clues_found} / 3",
            f"Chamber Solved In: {mins:02d}:{secs:02d}",
        ]


        for i, s in enumerate(stats):
            st_surf = self.font_body.render(s, True, (240, 235, 220))
            self.game_surface.blit(st_surf, (cx + 80, cy + 135 + i * 28))

        # Level 1 closing text
        lore_lines = [
            "With the Gold Key, the heavy stone portals slide apart.",
            "Ahead, cold subterranean drafts murmur through forgotten corridors.",
            "Your lantern's flame trembles...",
            "You have escaped the ancient sanctum.",
        ]
        for i, l in enumerate(lore_lines):
            l_surf = self.font_subtitle.render(l, True, (180, 175, 195))
            self.game_surface.blit(l_surf, (self.render_w // 2 - l_surf.get_width() // 2, cy + 248 + i * 22))

        # Options
        opt1 = self.font_body.render("Press [SPACE] to Replay Level 1", True, (255, 240, 180))
        opt2 = self.font_body.render("Press [M] for Main Menu   |   [ESC] Exit", True, (160, 150, 135))
        self.game_surface.blit(opt1, (self.render_w // 2 - opt1.get_width() // 2, cy + card_h - 68))
        self.game_surface.blit(opt2, (self.render_w // 2 - opt2.get_width() // 2, cy + card_h - 38))





    # --- Controls Overlay ----------------------------------------------------

    def _draw_controls_overlay(self):
        items_l1 = [
            ("WASD / Arrow Keys", "Move explorer through the chamber"),
            ("[SPACE] Key", "Hop across decorative terrain gaps"),
            ("[I] Key", "Open / Close Inventory & Journal"),
            ("[L] Key", "Toggle the lantern on / off"),
            ("[E] Key", "Inspect clues / Open door lock"),
            ("[1], [2], [3] Keys", "Select & insert key at door"),
            ("[C] / [H] Keys", "Toggle this guide overlay"),
            ("[F11] Key", "Toggle fullscreen / windowed mode"),
            ("[ESC] Key", "Return to Main Menu / Close modal"),
        ]
        items = items_l1

        modal_w = 520
        modal_h = 440
        x = (self.render_w - modal_w) // 2
        y = (self.render_h - modal_h) // 2

        surf = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
        surf.fill((16, 14, 22, 245))
        pygame.draw.rect(surf, (190, 160, 80), (0, 0, modal_w, modal_h), width=2, border_radius=8)
        self.game_surface.blit(surf, (x, y))

        title = "EXPLORER CONTROLS & GUIDE"
        t = self.font_modal_title.render(title, True, (250, 225, 140))
        self.game_surface.blit(t, (x + (modal_w - t.get_width()) // 2, y + 16))
        pygame.draw.line(self.game_surface, (150, 120, 60), (x + 30, y + 44), (x + modal_w - 30, y + 44), 1)

        row_h = 32
        for i, (k, desc) in enumerate(items):
            k_surf = self.font_small.render(k, True, (245, 215, 110))
            d_surf = self.font_small.render(desc, True, (220, 215, 225))
            self.game_surface.blit(k_surf, (x + 30, y + 54 + i * row_h))
            self.game_surface.blit(d_surf, (x + 220, y + 54 + i * row_h))

        close_t = self.font_small.render("Press [C] or [ESC] to close", True, (150, 140, 130))
        self.game_surface.blit(close_t, (x + (modal_w - close_t.get_width()) // 2, y + modal_h - 24))


def main(max_frames=None):
    game = GameManager()
    game.run(max_frames=max_frames)


if __name__ == "__main__":
    main()
