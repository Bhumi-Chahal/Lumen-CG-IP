"""entities/crystal.py — Energy Crystal Recharge Station (Level 2+).

Per architecture.md §3, rules.md §1.4, and design.md §6:
-----------------------------------------------------------------------------
DESIGN SPECIFICATION FOR LEVEL 2:
- Energy Crystal stations are introduced in Level 2 as the primary method
  for restoring lantern energy / battery.
- There is no passive recharge in Lumen (rules.md §1.4).
- The player must locate and interact with (or step onto) an Energy Crystal
  station to restore lantern energy.
- Energy Crystal stations emit their own radiant cyan light so players can
  locate them even when lantern energy is depleted.
-----------------------------------------------------------------------------
"""

import math
import random
import pygame


class EnergyCrystalStation:
    """Sacred luminous crystal station that recharges the lantern.

    Features an arched stone alcove inscribed with glowing ancient cyan runes,
    a carved stone pedestal, tall radiant crystalline spires, floating sparkle motes,
    and a soft cyan ambient light aura that shines through darkness.
    """

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.radius = 28
        self.pulse = 0.0
        self.recharge_fx_timer = 0.0
        self.sparkles: list[dict] = [
            {
                "x": random.uniform(-14, 14),
                "y": random.uniform(-18, 6),
                "vy": random.uniform(-14, -6),
                "life": random.uniform(0.2, 1.0),
                "size": random.uniform(1.2, 2.5)
            }
            for _ in range(12)
        ]

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def update(self, dt: float):
        self.pulse = (self.pulse + dt * 3.5) % (2 * math.pi)
        if self.recharge_fx_timer > 0:
            self.recharge_fx_timer = max(0.0, self.recharge_fx_timer - dt)

        for s in self.sparkles:
            s["y"] += s["vy"] * dt
            s["life"] -= dt * 0.8
            if s["life"] <= 0:
                s["x"] = random.uniform(-14, 14)
                s["y"] = random.uniform(0, 10)
                s["vy"] = random.uniform(-16, -6)
                s["life"] = random.uniform(0.6, 1.2)
                s["size"] = random.uniform(1.2, 2.5)

    def trigger_recharge_effect(self):
        self.recharge_fx_timer = 0.8
        for s in self.sparkles:
            s["vy"] = random.uniform(-35, -15)
            s["life"] = 1.0

    def draw_glow(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)):
        """Draws radiant cyan light that cuts through pitch darkness."""
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])

        pulse = math.sin(self.pulse)
        base_r = int(48 + 8 * pulse)
        if self.recharge_fx_timer > 0:
            base_r += int(35 * (self.recharge_fx_timer / 0.8))

        glow_surf = pygame.Surface((base_r * 2, base_r * 2), pygame.SRCALPHA)
        # Soft outer cyan aura
        pygame.draw.circle(glow_surf, (20, 140, 240, 35), (base_r, base_r), base_r)
        # Mid electric cyan
        pygame.draw.circle(glow_surf, (60, 200, 255, 60), (base_r, base_r), int(base_r * 0.6))
        # Bright core
        pygame.draw.circle(glow_surf, (180, 240, 255, 110), (base_r, base_r), int(base_r * 0.28))
        surface.blit(glow_surf, (sx - base_r, sy - base_r))

    def draw(self, surface: pygame.Surface, player_near: bool = False,
             camera_offset: tuple[int, int] = (0, 0)):
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])

        # 1. Stone Archway Alcove
        arch_w = 46
        arch_h = 56
        arch_rect = pygame.Rect(sx - arch_w // 2, sy - arch_h // 2 - 4, arch_w, arch_h)
        pygame.draw.rect(surface, (10, 14, 25), arch_rect, border_radius=12)
        pygame.draw.rect(surface, (45, 42, 58), arch_rect, width=3, border_radius=12)
        pygame.draw.rect(surface, (25, 22, 35), arch_rect.inflate(4, 4), width=1, border_radius=14)

        # 2. Glowing Ancient Cyan Runes on the Arch
        rune_glow = int(180 + 60 * math.sin(self.pulse))
        rune_color = (60, min(255, rune_glow + 30), 255)
        runes = [
            (sx - 16, sy - 24), (sx - 10, sy - 29), (sx, sy - 31),
            (sx + 10, sy - 29), (sx + 16, sy - 24),
            (sx - 18, sy - 12), (sx + 18, sy - 12),
            (sx - 18, sy + 2),  (sx + 18, sy + 2)
        ]
        for rx, ry in runes:
            pygame.draw.line(surface, rune_color, (rx - 2, ry - 2), (rx + 2, ry + 2), 1)
            pygame.draw.line(surface, rune_color, (rx, ry - 3), (rx, ry + 3), 1)

        # 3. Pedestal / Altar base
        base_rect = pygame.Rect(sx - 16, sy + 10, 32, 10)
        pygame.draw.rect(surface, (40, 38, 52), base_rect, border_radius=2)
        pygame.draw.rect(surface, (70, 65, 85), base_rect, width=1, border_radius=2)

        # 4. Radiant Crystalline Cluster (tall multifaceted shards)
        c1_top = (sx, sy - 20)
        pygame.draw.polygon(surface, (30, 90, 190), [c1_top, (sx - 6, sy + 10), (sx, sy + 10)])
        pygame.draw.polygon(surface, (70, 205, 255), [c1_top, (sx, sy + 10), (sx + 6, sy + 10)])
        pygame.draw.line(surface, (230, 250, 255), c1_top, (sx, sy + 10), 1)

        c2_top = (sx - 9, sy - 13)
        pygame.draw.polygon(surface, (20, 75, 165), [c2_top, (sx - 14, sy + 10), (sx - 7, sy + 10)])
        pygame.draw.polygon(surface, (55, 185, 245), [c2_top, (sx - 7, sy + 10), (sx - 2, sy + 10)])
        pygame.draw.line(surface, (200, 240, 255), c2_top, (sx - 7, sy + 10), 1)

        c3_top = (sx + 8, sy - 15)
        pygame.draw.polygon(surface, (35, 100, 205), [c3_top, (sx + 2, sy + 10), (sx + 7, sy + 10)])
        pygame.draw.polygon(surface, (90, 225, 255), [c3_top, (sx + 7, sy + 10), (sx + 13, sy + 10)])
        pygame.draw.line(surface, (240, 255, 255), c3_top, (sx + 7, sy + 10), 1)

        pygame.draw.polygon(surface, (110, 235, 255), [(sx - 3, sy), (sx - 7, sy + 10), (sx + 1, sy + 10)])
        pygame.draw.polygon(surface, (140, 245, 255), [(sx + 4, sy - 3), (sx, sy + 10), (sx + 8, sy + 10)])

        # 5. Floating Sparkle Particles
        for s in self.sparkles:
            spx = int(sx + s["x"])
            spy = int(sy + s["y"])
            alpha = max(10, min(255, int(255 * min(1.0, max(0.0, s["life"])))))
            sp_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            pygame.draw.circle(sp_surf, (150, 235, 255, alpha), (2, 2), max(1, int(s["size"])))
            surface.blit(sp_surf, (spx - 2, spy - 2))

        # 6. Interaction prompt
        if player_near:
            prompt_y = sy - arch_h // 2 - 20 + int(2 * math.sin(self.pulse))
            font = pygame.font.SysFont("consolas", 12, bold=True)
            prompt_txt = font.render("[E] Recharge Lantern", True, (160, 240, 255))
            box = pygame.Rect(sx - prompt_txt.get_width() // 2 - 5, prompt_y - 2,
                              prompt_txt.get_width() + 10, prompt_txt.get_height() + 4)
            box_surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
            box_surf.fill((10, 15, 30, 225))
            pygame.draw.rect(box_surf, (70, 200, 255), (0, 0, box.width, box.height), width=1, border_radius=3)
            surface.blit(box_surf, (box.x, box.y))
            surface.blit(prompt_txt, (box.x + 5, box.y + 2))
