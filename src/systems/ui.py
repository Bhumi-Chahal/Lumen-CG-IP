"""UI system for Lumen: HUD, Clue Modal, and Toast (Level 1 baseline).

Renders:
- Top Objective Banner (centered)
- Lantern Status indicator (top-right)
- Key collection badges (bottom center)
- Toast notifications
- Interactive ClueModal stone tablet
"""

import math
import pygame


def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Wraps text so no line exceeds max_width pixels, properly respecting newlines."""
    paragraphs = text.split("\n")
    lines: list[str] = []
    for para in paragraphs:
        clean_para = para.strip()
        if not clean_para:
            lines.append("")
            continue
        words = clean_para.split()
        current = ""
        for word in words:
            test = f"{current} {word}".strip()
            if font.size(test)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
    return lines


class ClueModal:
    """Carved stone tablet modal popup for displaying examined clues."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_open = False
        self.title = ""
        self.text = ""
        self.clue_type = ""
        self.anim_alpha = 0.0

    def open(self, title: str, text: str, clue_type: str = "statue"):
        self.is_open = True
        self.title = title
        self.text = text
        self.clue_type = clue_type
        self.anim_alpha = 0.0

    def close(self):
        self.is_open = False

    def update(self, dt: float):
        if self.is_open and self.anim_alpha < 1.0:
            self.anim_alpha = min(1.0, self.anim_alpha + dt * 5.0)

    def draw(self, surface: pygame.Surface, font_title: pygame.font.Font, font_body: pygame.font.Font):
        if not self.is_open:
            return

        # Dim backdrop
        dim_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim_alpha = int(170 * self.anim_alpha)
        dim_surf.fill((0, 0, 0, dim_alpha))
        surface.blit(dim_surf, (0, 0))

        # Modal dimensions
        modal_w = min(560, self.screen_width - 80)
        wrapped_lines = wrap_text(self.text, font_body, modal_w - 60)
        modal_h = 130 + len(wrapped_lines) * 24

        x = (self.screen_width - modal_w) // 2
        y = (self.screen_height - modal_h) // 2

        # Carved stone tablet background
        tablet = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
        tablet.fill((22, 20, 28, int(245 * self.anim_alpha)))

        # Ancient gold ornate border
        gold_color = (200, 165, 75, int(255 * self.anim_alpha))
        inner_color = (75, 65, 45, int(220 * self.anim_alpha))
        pygame.draw.rect(tablet, gold_color, (0, 0, modal_w, modal_h), width=3, border_radius=8)
        pygame.draw.rect(tablet, inner_color, (6, 6, modal_w - 12, modal_h - 12), width=1, border_radius=5)

        # Corner gold gems
        corners = [(6, 6), (modal_w - 10, 6), (6, modal_h - 10), (modal_w - 10, modal_h - 10)]
        for cx, cy in corners:
            pygame.draw.rect(tablet, (240, 200, 90), (cx, cy, 4, 4))

        surface.blit(tablet, (x, y))

        # Title
        title_surf = font_title.render(self.title, True, (245, 220, 140))
        surface.blit(title_surf, (x + (modal_w - title_surf.get_width()) // 2, y + 22))

        # Decorative Divider line
        div_y = y + 54
        pygame.draw.line(surface, (170, 135, 55), (x + 35, div_y), (x + modal_w - 35, div_y), 2)
        pygame.draw.circle(surface, (230, 190, 80), (x + modal_w // 2, div_y), 4)

        # Body Lore Text
        for i, line in enumerate(wrapped_lines):
            line_surf = font_body.render(line, True, (225, 220, 205))
            surface.blit(line_surf, (x + 30, y + 74 + i * 24))

        # Dismiss footer
        footer_font = pygame.font.SysFont("consolas", 13, bold=True)
        footer_surf = footer_font.render("Press [E] or [ESC] to return to the chamber", True, (160, 145, 120))
        surface.blit(footer_surf, (x + (modal_w - footer_surf.get_width()) // 2, y + modal_h - 28))


class StoryModal:
    """Carved stone narrative popup modal for tutorial and story milestones."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_open = False
        self.title = ""
        self.text = ""
        self.footer_prompt = "Press [SPACE] or [E] to continue"
        self.anim_alpha = 0.0
        self.modal_id = ""

    def open(self, title: str, text: str, modal_id: str = "", footer_prompt: str = "Press [SPACE] or [E] to continue"):
        self.is_open = True
        self.title = title
        self.text = text
        self.modal_id = modal_id
        self.footer_prompt = footer_prompt
        self.anim_alpha = 0.0

    def close(self):
        self.is_open = False

    def update(self, dt: float):
        if self.is_open and self.anim_alpha < 1.0:
            self.anim_alpha = min(1.0, self.anim_alpha + dt * 6.0)

    def draw(self, surface: pygame.Surface, font_title: pygame.font.Font, font_body: pygame.font.Font):
        if not self.is_open:
            return

        dim_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, int(185 * self.anim_alpha)))
        surface.blit(dim_surf, (0, 0))

        modal_w = min(560, self.screen_width - 80)
        wrapped_lines = wrap_text(self.text, font_body, modal_w - 60)
        modal_h = 135 + len(wrapped_lines) * 24

        x = (self.screen_width - modal_w) // 2
        y = (self.screen_height - modal_h) // 2

        tablet = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
        tablet.fill((20, 17, 26, int(248 * self.anim_alpha)))

        gold_color = (215, 180, 80, int(255 * self.anim_alpha))
        inner_color = (80, 68, 48, int(220 * self.anim_alpha))
        pygame.draw.rect(tablet, gold_color, (0, 0, modal_w, modal_h), width=3, border_radius=10)
        pygame.draw.rect(tablet, inner_color, (6, 6, modal_w - 12, modal_h - 12), width=1, border_radius=6)

        # Corner jewels
        for cx, cy in [(8, 8), (modal_w - 12, 8), (8, modal_h - 12), (modal_w - 12, modal_h - 12)]:
            pygame.draw.rect(tablet, (240, 200, 90), (cx, cy, 4, 4))

        surface.blit(tablet, (x, y))

        # Title
        t_surf = font_title.render(self.title, True, (250, 225, 140))
        surface.blit(t_surf, (x + (modal_w - t_surf.get_width()) // 2, y + 20))

        # Divider
        div_y = y + 54
        pygame.draw.line(surface, (170, 135, 55), (x + 35, div_y), (x + modal_w - 35, div_y), 2)
        pygame.draw.circle(surface, (230, 190, 80), (x + modal_w // 2, div_y), 4)

        # Body text
        for i, line in enumerate(wrapped_lines):
            line_surf = font_body.render(line, True, (230, 225, 215))
            surface.blit(line_surf, (x + 30, y + 72 + i * 24))

        # Footer
        foot_font = pygame.font.SysFont("consolas", 13, bold=True)
        foot_surf = foot_font.render(self.footer_prompt, True, (170, 150, 120))
        surface.blit(foot_surf, (x + (modal_w - foot_surf.get_width()) // 2, y + modal_h - 28))


class DoorModal:
    """Grand Sanctum Threshold modal with antique brass keyhole plate.

    Directly inspired by reference art: features an oval antique brass
    escutcheon plate with 4 spherical rivet studs, deep keyhole aperture,
    key selection tray, 2-chances trial system, and triumphant unsealing animation.
    """

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.is_open = False
        self.feedback_msg = "Select a key to insert into the ancient lock."
        self.feedback_color = (230, 215, 170)
        self.unlocked = False
        self.glow_phase = 0.0
        self.anim_alpha = 0.0
        self.chances_left = 2
        self.failed = False
        self.failed_timer = 0.0
        self.tried_keys: set[str] = set()

    def open(self, inventory):
        self.is_open = True
        self.anim_alpha = 0.0
        if self.failed:
            self.feedback_msg = "The door is sealed. Both attempts failed."
            self.feedback_color = (240, 70, 70)
            return
        if not inventory.keys:
            self.feedback_msg = "The door is sealed. You have no keys in your possession."
            self.feedback_color = (220, 160, 140)
        else:
            chance_word = "chance" if self.chances_left == 1 else "chances"
            self.feedback_msg = f"Choose wisely. You have {self.chances_left} {chance_word} to unseal the threshold."
            self.feedback_color = (230, 215, 170)

    def close(self):
        self.is_open = False

    def reset_chances(self):
        self.chances_left = 2
        self.failed = False
        self.failed_timer = 0.0
        self.unlocked = False
        self.tried_keys.clear()

    def update(self, dt: float):
        if self.is_open and self.anim_alpha < 1.0:
            self.anim_alpha = min(1.0, self.anim_alpha + dt * 6.0)
        self.glow_phase = (self.glow_phase + dt * 4.0) % (2 * math.pi)

    def draw(self, surface: pygame.Surface, font_title: pygame.font.Font,
             font_body: pygame.font.Font, font_small: pygame.font.Font, inventory):
        if not self.is_open:
            return

        # 1. Darkened backdrop
        dim_surf = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, int(205 * self.anim_alpha)))
        surface.blit(dim_surf, (0, 0))

        # 2. Main Modal Frame (scaled with smooth entry)
        modal_w = 640
        modal_h = 440
        x = (self.screen_width - modal_w) // 2
        y = (self.screen_height - modal_h) // 2

        frame_surf = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
        frame_surf.fill((22, 18, 28, int(250 * self.anim_alpha)))
        pygame.draw.rect(frame_surf, (200, 165, 75), (0, 0, modal_w, modal_h), width=3, border_radius=12)
        pygame.draw.rect(frame_surf, (75, 62, 45), (6, 6, modal_w - 12, modal_h - 12), width=1, border_radius=8)
        surface.blit(frame_surf, (x, y))

        # 3. Header
        t_surf = font_title.render("THE SANCTUM THRESHOLD", True, (255, 225, 130))
        surface.blit(t_surf, (x + (modal_w - t_surf.get_width()) // 2, y + 16))
        sub_font = pygame.font.SysFont("consolas", 13)
        sub_surf = sub_font.render("An ancient portal forged in the First Age. Trial of the Three Keys.", True, (195, 185, 165))
        surface.blit(sub_surf, (x + (modal_w - sub_surf.get_width()) // 2, y + 48))

        pygame.draw.line(surface, (160, 130, 60), (x + 40, y + 68), (x + modal_w - 40, y + 68), 1)

        # 4. Left Side: Antique Brass Keyhole Plate (Matching Reference Art)
        plate_cx = x + 145
        plate_cy = y + 240
        self._draw_brass_keyhole(surface, plate_cx, plate_cy)

        # 5. Right Side: Key Selection Tray with Chances Badge
        tray_x = x + 270
        tray_y = y + 112
        slot_w = 330

        # Chances Remaining Badge
        badge_w = 310
        badge_h = 24
        badge_x = tray_x + (slot_w - badge_w) // 2
        badge_y = y + 78
        badge_surf = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        if self.chances_left == 2:
            b_border = (200, 165, 75)
            b_bg = (30, 24, 18, 220)
            b_txt_col = (245, 220, 130)
            b_txt = "CHANCES REMAINING: 2 / 2"
        elif self.chances_left == 1:
            b_border = (235, 100, 60)
            b_bg = (42, 16, 16, 230)
            b_txt_col = (255, 140, 100)
            b_txt = "FINAL ATTEMPT: 1 / 2 REMAINING!"
        else:
            b_border = (220, 45, 45)
            b_bg = (48, 10, 10, 245)
            b_txt_col = (255, 75, 75)
            b_txt = "LOCKOUT: 0 / 2 CHANCES"
        pygame.draw.rect(badge_surf, b_bg, (0, 0, badge_w, badge_h), border_radius=4)
        pygame.draw.rect(badge_surf, b_border, (0, 0, badge_w, badge_h), width=1, border_radius=4)
        surface.blit(badge_surf, (badge_x, badge_y))
        ch_font = pygame.font.SysFont("consolas", 12, bold=True)
        ch_lbl = ch_font.render(b_txt, True, b_txt_col)
        surface.blit(ch_lbl, (badge_x + (badge_w - ch_lbl.get_width()) // 2, badge_y + 5))

        keys_info = [
            (1, "key_bronze", "1: Bronze Key", "Orb Hallmark", (180, 115, 60), (120, 75, 35)),
            (2, "key_silver", "2: Silver Key", "Spiral Hallmark", (195, 200, 210), (130, 135, 145)),
            (3, "key_gold",   "3: Gold Key",   "Sun Hallmark",    (245, 205, 60), (170, 135, 35)),
        ]

        for i, (num, k_id, label, hallmark, color, dark_color) in enumerate(keys_info):
            has = inventory.has_key(k_id)
            is_tried = k_id in self.tried_keys
            slot_y = tray_y + i * 66
            slot_h = 56

            slot_surf = pygame.Surface((slot_w, slot_h), pygame.SRCALPHA)
            if is_tried:
                bg = (38, 14, 18, 230)
                border = (200, 60, 60)
            elif has:
                bg = (32, 26, 42, 240)
                border = color
            else:
                bg = (18, 14, 22, 180)
                border = (60, 50, 65)

            slot_surf.fill(bg)
            pygame.draw.rect(slot_surf, border, (0, 0, slot_w, slot_h), width=2 if has else 1, border_radius=6)
            surface.blit(slot_surf, (tray_x, slot_y))

            # Metallic Key Icon
            ic_x = tray_x + 28
            ic_y = slot_y + slot_h // 2
            ic_color = (130, 50, 50) if is_tried else (color if has else (70, 65, 75))
            pygame.draw.circle(surface, ic_color, (ic_x, ic_y - 6), 9, width=2)
            pygame.draw.circle(surface, ic_color, (ic_x, ic_y - 6), 4)
            pygame.draw.rect(surface, ic_color, (ic_x - 2, ic_y + 3, 4, 14))
            pygame.draw.rect(surface, ic_color, (ic_x, ic_y + 11, 6, 3))

            # Key Text Labels
            lbl_color = (200, 120, 120) if is_tried else ((250, 240, 220) if has else (120, 110, 125))
            k_lbl = font_body.render(f"[{num}] {label}", True, lbl_color)
            surface.blit(k_lbl, (tray_x + 55, slot_y + 10))

            if is_tried:
                status_text = "REJECTED (TRIAL FAILED)"
                status_color = (240, 90, 90)
            elif has:
                status_text = hallmark
                status_color = (190, 175, 140)
            else:
                status_text = "Locked / Not Found"
                status_color = (110, 95, 105)

            s_lbl = font_small.render(status_text, True, status_color)
            surface.blit(s_lbl, (tray_x + 55, slot_y + 31))

            # Action button indicator
            if has and not self.failed and not self.unlocked:
                btn_font = pygame.font.SysFont("consolas", 11, bold=True)
                if is_tried:
                    btn_lbl = btn_font.render("[FAILED]", True, (240, 80, 80))
                else:
                    btn_lbl = btn_font.render(f"PRESS [{num}]", True, color)
                surface.blit(btn_lbl, (tray_x + slot_w - btn_lbl.get_width() - 14, slot_y + 20))

        # 6. Feedback & Prompt Bar (Bottom)
        fb_y = y + modal_h - 70
        fb_box = pygame.Surface((modal_w - 60, 32), pygame.SRCALPHA)
        fb_box.fill((14, 11, 20, 220))
        fb_border = (200, 50, 50) if self.failed else (140, 110, 55)
        pygame.draw.rect(fb_box, fb_border, (0, 0, modal_w - 60, 32), width=1, border_radius=4)
        surface.blit(fb_box, (x + 30, fb_y))

        fb_surf = font_small.render(self.feedback_msg, True, self.feedback_color)
        surface.blit(fb_surf, (x + (modal_w - fb_surf.get_width()) // 2, fb_y + 8))

        # Footer Step Back prompt
        close_font = pygame.font.SysFont("consolas", 12)
        close_txt = "Door is locking down..." if self.failed else "Press [ESC] to step away from the door"
        close_surf = close_font.render(close_txt, True, (150, 140, 130))
        surface.blit(close_surf, (x + (modal_w - close_surf.get_width()) // 2, y + modal_h - 26))

    def _draw_brass_keyhole(self, surface: pygame.Surface, cx: int, cy: int):
        """Renders the detailed antique brass oval keyhole plate matching the reference image."""
        rx, ry = 80, 110

        # Background drop shadow
        shd_surf = pygame.Surface((rx * 2 + 16, ry * 2 + 16), pygame.SRCALPHA)
        pygame.draw.ellipse(shd_surf, (0, 0, 0, 120), (0, 0, rx * 2 + 16, ry * 2 + 16))
        surface.blit(shd_surf, (cx - rx - 8, cy - ry - 4))

        # Outer antique dark brass bevel rim
        pygame.draw.ellipse(surface, (95, 65, 30), (cx - rx - 3, cy - ry - 3, (rx + 3) * 2, (ry + 3) * 2))

        # Main brushed brass escutcheon plate
        plate_rect = pygame.Rect(cx - rx, cy - ry, rx * 2, ry * 2)
        pygame.draw.ellipse(surface, (155, 110, 48), plate_rect)

        # Warm highlight brushed texture layers
        pygame.draw.ellipse(surface, (175, 128, 58), (cx - rx + 5, cy - ry + 5, (rx - 5) * 2, (ry - 5) * 2))
        pygame.draw.ellipse(surface, (195, 148, 70), (cx - rx + 14, cy - ry + 14, (rx - 14) * 2, (ry - 14) * 2))
        pygame.draw.ellipse(surface, (168, 122, 54), (cx - rx + 24, cy - ry + 24, (rx - 24) * 2, (ry - 24) * 2))

        # 4 Spherical Rivet Studs (Top, Bottom, Left, Right)
        rivets = [
            (cx, cy - ry + 16),      # Top (12 o'clock)
            (cx, cy + ry - 16),      # Bottom (6 o'clock)
            (cx - rx + 16, cy),      # Left (9 o'clock)
            (cx + rx - 16, cy),      # Right (3 o'clock)
        ]
        for rx_pos, ry_pos in rivets:
            # Rivet shadow
            pygame.draw.circle(surface, (55, 35, 15), (rx_pos + 1, ry_pos + 1), 6)
            # Rivet dome
            pygame.draw.circle(surface, (185, 135, 55), (rx_pos, ry_pos), 6)
            pygame.draw.circle(surface, (235, 195, 95), (rx_pos - 1, ry_pos - 1), 3)
            pygame.draw.circle(surface, (255, 240, 180), (rx_pos - 1, ry_pos - 2), 1)

        # --- KEYHOLE CUTOUT ---
        # Top circular aperture
        kc_y = cy - 20
        # Left golden thickness bevel (giving depth to the plate like reference art)
        pygame.draw.circle(surface, (235, 190, 65), (cx - 4, kc_y), 27)
        # Deep dark keyhole interior
        pygame.draw.circle(surface, (12, 10, 16), (cx, kc_y), 26)

        # Bottom keyhole slot (flared trapezoid)
        slot_top_w = 26
        slot_bot_w = 38
        slot_h = 58
        slot_top_y = cy - 6

        # Golden left inner bevel for slot
        bevel_pts = [
            (cx - slot_top_w // 2 - 5, slot_top_y),
            (cx - slot_bot_w // 2 - 5, slot_top_y + slot_h),
            (cx + slot_bot_w // 2, slot_top_y + slot_h),
            (cx + slot_top_w // 2, slot_top_y)
        ]
        pygame.draw.polygon(surface, (230, 185, 60), bevel_pts)

        # Deep black slot interior
        slot_pts = [
            (cx - slot_top_w // 2, slot_top_y),
            (cx - slot_bot_w // 2, slot_top_y + slot_h),
            (cx + slot_bot_w // 2 - 2, slot_top_y + slot_h),
            (cx + slot_top_w // 2 - 2, slot_top_y)
        ]
        pygame.draw.polygon(surface, (12, 10, 16), slot_pts)

        # Bottom ledge bevel (yellow golden highlight ledge from reference)
        pygame.draw.line(surface, (220, 175, 55),
                         (cx - slot_bot_w // 2 - 5, slot_top_y + slot_h),
                         (cx + slot_bot_w // 2, slot_top_y + slot_h), 2)

        # Triumphant radiant light burst through keyhole if unlocked
        if self.unlocked:
            glow_surf = pygame.Surface((rx * 2 + 40, ry * 2 + 40), pygame.SRCALPHA)
            pulse = math.sin(self.glow_phase)
            g_alpha = int(140 + 60 * pulse)
            pygame.draw.circle(glow_surf, (255, 230, 120, g_alpha), (rx + 20, ry + 20), 45)
            pygame.draw.circle(glow_surf, (255, 255, 220, min(255, g_alpha + 40)), (rx + 20, ry + 20), 20)
            surface.blit(glow_surf, (cx - rx - 20, cy - ry - 20))


class HUD:
    """Renders the HUD for Level 1: objective banner, lantern status, and key badges."""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

    def update(self, dt: float, lantern=None):
        """Animation update hook (no-op in Level 1)."""
        pass

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, font_small: pygame.font.Font,
             inventory, lantern, objective: str, toast_msg: str):
        # 1. Top Objective Banner (cleanly centered)
        banner_w = 440
        banner_h = 32
        banner_x = (self.screen_width - banner_w) // 2
        banner_y = 10

        banner_surf = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)
        banner_surf.fill((8, 6, 14, 210))
        pygame.draw.rect(banner_surf, (80, 65, 40), (0, 0, banner_w, banner_h), width=1, border_radius=4)
        surface.blit(banner_surf, (banner_x, banner_y))

        obj_str = f"Goal: {objective}"
        while font_small.size(obj_str)[0] > banner_w - 20 and len(obj_str) > 10:
            obj_str = obj_str[:-4] + "..."
        obj_text = font_small.render(obj_str, True, (240, 215, 140))
        surface.blit(obj_text, (banner_x + (banner_w - obj_text.get_width()) // 2, banner_y + 7))

        # 2. Lantern status (top-right)
        if not lantern.possessed:
            lantern_color = (130, 125, 135)
            status_txt = "NOT FOUND"
            status_label = font_small.render(f"Lantern: {status_txt}", True, lantern_color)
            surface.blit(status_label, (self.screen_width - status_label.get_width() - 20, 16))
            lx = self.screen_width - status_label.get_width() - 38
            pygame.draw.rect(surface, (75, 60, 35), (lx, 16, 8, 12), border_radius=2)
            pygame.draw.rect(surface, (40, 35, 30), (lx + 1, 19, 6, 6))
        else:
            lantern_color = (255, 230, 120) if lantern.active else (100, 100, 100)
            status_txt = "ON" if lantern.active else "OFF"
            status_label = font_small.render(f"Lantern [L]: {status_txt}", True, lantern_color)
            surface.blit(status_label, (self.screen_width - status_label.get_width() - 20, 16))
            lx = self.screen_width - status_label.get_width() - 38
            pygame.draw.rect(surface, (160, 120, 45), (lx, 16, 8, 12), border_radius=2)
            pygame.draw.rect(surface, lantern_color, (lx + 1, 19, 6, 6))

        # 3. Bottom HUD Bar (Keys Collected)
        bar_h = 44
        bar_y = self.screen_height - bar_h
        bar_surf = pygame.Surface((self.screen_width, bar_h), pygame.SRCALPHA)
        bar_surf.fill((6, 5, 12, 220))
        pygame.draw.line(bar_surf, (50, 42, 35), (0, 0), (self.screen_width, 0), 2)
        surface.blit(bar_surf, (0, bar_y))

        # Key Collection Badges (Center)
        keys_info = [
            ("key_bronze", "1: Bronze", (180, 110, 60)),
            ("key_silver", "2: Silver", (195, 200, 210)),
            ("key_gold", "3: Gold", (240, 195, 55)),
        ]

        total_key_w = 3 * 150 + 2 * 10
        keys_start_x = (self.screen_width - total_key_w) // 2

        for i, (k_id, label, color) in enumerate(keys_info):
            has = inventory.has_key(k_id)
            bx = keys_start_x + i * 160
            by = bar_y + 8
            badge_surf = pygame.Surface((145, 28), pygame.SRCALPHA)
            bg_color = (28, 22, 38, 230) if has else (15, 12, 20, 160)
            badge_surf.fill(bg_color)
            border_color = color if has else (50, 45, 60)
            pygame.draw.rect(badge_surf, border_color, (0, 0, 145, 28), width=1, border_radius=4)
            surface.blit(badge_surf, (bx, by))

            # Small key icon
            icon_color = color if has else (70, 65, 75)
            pygame.draw.circle(surface, icon_color, (bx + 16, by + 14), 5)
            pygame.draw.line(surface, icon_color, (bx + 16, by + 14), (bx + 26, by + 14), 2)
            pygame.draw.line(surface, icon_color, (bx + 23, by + 14), (bx + 23, by + 18), 2)

            text_color = (240, 235, 225) if has else (100, 95, 105)
            lbl = font_small.render(label, True, text_color)
            surface.blit(lbl, (bx + 34, by + 6))

        # 4. Toast Message Alert
        if toast_msg:
            wrapped = wrap_text(toast_msg, font, self.screen_width - 100)
            toast_h = 24 * len(wrapped) + 16
            toast_w = min(self.screen_width - 60, max(font.size(w)[0] for w in wrapped) + 40)
            tx = (self.screen_width - toast_w) // 2
            ty = bar_y - toast_h - 10

            box = pygame.Surface((toast_w, toast_h), pygame.SRCALPHA)
            box.fill((10, 8, 16, 235))
            pygame.draw.rect(box, (160, 130, 65), (0, 0, toast_w, toast_h), width=1, border_radius=6)
            surface.blit(box, (tx, ty))

            for i, line in enumerate(wrapped):
                rendered = font.render(line, True, (245, 235, 210))
                surface.blit(rendered, (tx + (toast_w - rendered.get_width()) // 2, ty + 8 + i * 24))
