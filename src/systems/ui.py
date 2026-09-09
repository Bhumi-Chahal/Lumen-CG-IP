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
