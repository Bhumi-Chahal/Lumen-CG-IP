"""content/level3.py — Level 3: Path of Light (Four Reflection Chambers).

Level 3 Architecture:
Four grand chambers arranged sequentially in an ancient sacred temple:
- Chamber 1: Entrance Gallery (Golden Entrance Door).
- Chamber 2: First Reflection Chamber (1 socket, 1 light-source crystal, door to Ch3).
- Chamber 3: Second Reflection Chamber (2 sockets, 1 light-source crystal, door to Ch4).
- Chamber 4: Final Reflection Chamber (3 sockets, 1 light-source crystal, exit door).

Unified visual language:
- Ancient ashlar flagstone floor, concentric carved stone discs, worn seams, celestial carvings.
- Golden entrance door with subtle firefly/sparkle particles.
- Consistent ancient brown/stone/wood styling on all internal doors.
- No RGB chamber color-coding.
- 3 player mirrors sourced directly from inventory.mirrors.
"""

import math
import random
import json
import os
from pathlib import Path
import pygame

from engine.collision import move_with_collision
from engine.reflection import trace_beam, BeamSegment
from entities.mirror import Mirror
from entities.puzzle_crystal import PuzzleCrystal
from engine.battery import BatterySystem, LanternMeter
from engine.lighting import LightingSystem, build_level3_darkness_mask
from systems.audio import audio
from content.level3_helpers import trace_source, mirror_face
from content.level3_helpers import Mural


# Key Integration Constants (Progression Inventory)
DEFAULT_DOOR_KEYS: dict[str, str | None] = {
    "entrance_door": None,
    "door_ch2_to_ch3": None,
    "door_ch3_to_ch4": None,
    "exit_door": None,
}

KEY_NAMES: dict[str, str] = {
    "key_bronze": "Bronze Key",
    "key_silver": "Silver Key",
    "key_gold": "Gold Key",
}


def is_light_active(lantern, color: str) -> bool:
    """True when lantern is possessed, active, and color matches."""
    if lantern is None:
        return False
    return bool(getattr(lantern, "active", False) and getattr(lantern, "color", "") == color)


def is_blue_light_active(lantern) -> bool:
    """True when lantern is possessed, active, and color is blue."""
    return is_light_active(lantern, "blue")


def is_red_light_active(lantern) -> bool:
    """True when lantern is possessed, active, and color is red."""
    return is_light_active(lantern, "red")


def is_green_light_active(lantern) -> bool:
    """True when lantern is possessed, active, and color is green."""
    return is_light_active(lantern, "green")


class Headstone:
    """Ancient weathered stone headstone with arched molding, climbing ivy, and delicate pink roses in Chamber 1."""

    def __init__(self, x: float = 740.0, y: float = 1190.0):
        self.x = float(x)
        self.y = float(y)
        self.width = 46
        self.height = 56
        self.rect = pygame.Rect(int(x - 23), int(y - 46), 46, 56)

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0)):
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])

        # 1. Base stone steps / pedestal (stepped chiseled plinth)
        base_w = 48
        # Lower foundation step
        pygame.draw.rect(surface, (54, 50, 60), (sx - 24, sy + 6, base_w, 8), border_radius=2)
        pygame.draw.rect(surface, (88, 84, 96), (sx - 24, sy + 6, base_w, 2))
        # Upper plinth block
        pygame.draw.rect(surface, (72, 68, 80), (sx - 21, sy + 1, 42, 6), border_radius=2)
        pygame.draw.rect(surface, (108, 104, 118), (sx - 21, sy + 1, 42, 2))

        # 2. Main carved stone tablet (weathered granite)
        body_r = pygame.Rect(sx - 18, sy - 36, 36, 38)
        pygame.draw.rect(surface, (126, 124, 134), body_r)
        # Rounded arch crest
        pygame.draw.circle(surface, (126, 124, 134), (sx, sy - 36), 18)

        # 3. Inner carved recessed arch border molding
        inner_r = pygame.Rect(sx - 14, sy - 34, 28, 34)
        pygame.draw.rect(surface, (98, 96, 106), inner_r)
        pygame.draw.circle(surface, (98, 96, 106), (sx, sy - 34), 14)

        # Inner tablet face (weathered grey stone)
        face_r = pygame.Rect(sx - 12, sy - 32, 24, 32)
        pygame.draw.rect(surface, (112, 110, 120), face_r)
        pygame.draw.circle(surface, (112, 110, 120), (sx, sy - 32), 12)

        # 4. Stone highlight and shadow beveling
        pygame.draw.line(surface, (168, 165, 178), (sx + 17, sy - 34), (sx + 17, sy + 1), 2)
        pygame.draw.line(surface, (60, 58, 68), (sx - 18, sy - 34), (sx - 18, sy + 1), 2)

        # 5. Weathered masonry cracks / organic fissures
        cracks = [
            ((sx - 6, sy - 28), (sx - 2, sy - 22)),
            ((sx - 2, sy - 22), (sx - 5, sy - 14)),
            ((sx + 4, sy - 12), (sx + 7, sy - 4)),
            ((sx + 1, sy - 20), (sx + 5, sy - 16)),
        ]
        for p1, p2 in cracks:
            pygame.draw.line(surface, (48, 46, 54), p1, p2, 1)

        # 6. Climbing Ivy Vines cascading over the arch crown and flanks
        # Deep vine runners
        pygame.draw.circle(surface, (32, 60, 28), (sx - 16, sy - 22), 8)
        pygame.draw.circle(surface, (32, 60, 28), (sx - 14, sy - 34), 9)
        pygame.draw.circle(surface, (32, 60, 28), (sx - 7, sy - 44), 9)
        pygame.draw.circle(surface, (32, 60, 28), (sx + 3, sy - 45), 9)
        pygame.draw.circle(surface, (32, 60, 28), (sx + 12, sy - 38), 8)
        pygame.draw.circle(surface, (32, 60, 28), (sx + 15, sy - 20), 7)
        pygame.draw.circle(surface, (32, 60, 28), (sx + 13, sy - 8), 7)

        # Rich foliage mid-tones
        pygame.draw.circle(surface, (55, 115, 45), (sx - 16, sy - 21), 6)
        pygame.draw.circle(surface, (55, 115, 45), (sx - 13, sy - 33), 7)
        pygame.draw.circle(surface, (55, 115, 45), (sx - 6, sy - 43), 7)
        pygame.draw.circle(surface, (55, 115, 45), (sx + 2, sy - 44), 7)
        pygame.draw.circle(surface, (55, 115, 45), (sx + 11, sy - 37), 6)
        pygame.draw.circle(surface, (55, 115, 45), (sx + 14, sy - 19), 6)
        pygame.draw.circle(surface, (55, 115, 45), (sx + 12, sy - 7), 6)

        # Bright leaf highlights
        pygame.draw.circle(surface, (95, 165, 55), (sx - 14, sy - 23), 4)
        pygame.draw.circle(surface, (95, 165, 55), (sx - 5, sy - 45), 5)
        pygame.draw.circle(surface, (95, 165, 55), (sx + 1, sy - 46), 4)
        pygame.draw.circle(surface, (95, 165, 55), (sx + 10, sy - 39), 4)
        pygame.draw.circle(surface, (135, 195, 65), (sx - 4, sy - 46), 2)
        pygame.draw.circle(surface, (135, 195, 65), (sx + 9, sy - 40), 2)

        # 7. Delicate Pink / Rose Blossoms draping across vines & plinth (Reference Image 4)
        rose_clusters = [
            # Top arch crown
            (sx - 8, sy - 44, 4), (sx + 4, sy - 45, 3), (sx - 2, sy - 47, 3),
            # Left flank climbing cascade
            (sx - 15, sy - 38, 4), (sx - 13, sy - 30, 4), (sx - 17, sy - 24, 3),
            (sx - 14, sy - 16, 4), (sx - 11, sy - 10, 3),
            # Right flank & face tendrils
            (sx + 12, sy - 35, 3), (sx + 15, sy - 22, 4), (sx + 14, sy - 12, 3),
            (sx + 8, sy - 6, 3), (sx + 14, sy - 4, 4),
            # Plinth base clusters
            (sx - 18, sy + 2, 4), (sx - 12, sy + 3, 3), (sx + 6, sy + 2, 3), (sx + 16, sy + 3, 4),
        ]
        for rx, ry, r_sz in rose_clusters:
            # Deep rose shadow
            pygame.draw.circle(surface, (180, 65, 100), (rx, ry + 1), r_sz)
            # Soft wild-rose pink petal body
            pygame.draw.circle(surface, (240, 135, 165), (rx, ry), max(1, r_sz - 1))
            # Pale blush highlight core
            if r_sz >= 3:
                pygame.draw.circle(surface, (255, 215, 230), (rx, ry), 1)

        # 8. Lush moss carpet & fern fronds across stone base
        pygame.draw.rect(surface, (45, 95, 35), (sx - 23, sy + 4, 46, 8), border_radius=2)
        pygame.draw.rect(surface, (95, 160, 48), (sx - 21, sy + 3, 42, 4), border_radius=2)
        pygame.draw.rect(surface, (145, 205, 60), (sx - 17, sy + 2, 34, 2))
        for fx in range(sx - 22, sx + 22, 5):
            pygame.draw.line(surface, (135, 195, 55), (fx, sy + 5), (fx + 2, sy), 1)


class SourceCrystal:
    """Ancient magical light-emitting crystal in Level 3 puzzle chambers."""

    def __init__(self, crystal_id: str, x: float, y: float, beam_dir: tuple[float, float] = (1.0, 0.0), name: str = "Source Crystal", color: str = "blue"):
        self.id = crystal_id
        self.x = float(x)
        self.y = float(y)
        self.beam_dir = beam_dir
        self.name = name
        self.color = color
        self.radius = 32.0
        self.active = False
        self.charged = False
        self.collected = False
        self.rect = pygame.Rect(int(x - 24), int(y - 24), 48, 48)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: tuple[int, int] = (0, 0),
        is_revealed: bool = True,
        flicker_phase: float = 0.0,
    ):
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])

        # Revealed state: radiant magical ancient light emitter
        pulse = 0.5 + 0.5 * math.sin(flicker_phase * 3.0)
        aura_rad = int(38 + 8 * pulse)
        aura_surf = pygame.Surface((aura_rad * 2, aura_rad * 2), pygame.SRCALPHA)
        alpha = int(45 + 20 * pulse)

        if not is_revealed:
            # Keep the faceted crystal visible without revealing its light color.
            aura_c1 = (105, 105, 105, 12)
            aura_c2 = (140, 140, 140, 18)
            c_dark = (78, 78, 78)
            c_mid = (120, 120, 120)
            c_light = (165, 165, 165)
            c_flare = (185, 185, 185)
        elif self.color == "red":
            aura_c1 = (255, 60, 80, alpha)
            aura_c2 = (255, 120, 140, alpha + 35)
            c_dark = (190, 35, 55)
            c_mid = (240, 65, 95)
            c_light = (255, 125, 150)
            c_flare = (255, 160, 180)
        elif self.color == "green":
            aura_c1 = (50, 220, 100, alpha)
            aura_c2 = (110, 245, 150, alpha + 35)
            c_dark = (30, 160, 70)
            c_mid = (55, 215, 105)
            c_light = (115, 250, 155)
            c_flare = (150, 255, 180)
        else:
            aura_c1 = (60, 160, 255, alpha)
            aura_c2 = (130, 215, 255, alpha + 35)
            c_dark = (35, 95, 190)
            c_mid = (65, 155, 240)
            c_light = (125, 210, 255)
            c_flare = (160, 230, 255)

        pygame.draw.circle(aura_surf, aura_c1, (aura_rad, aura_rad), aura_rad)
        pygame.draw.circle(aura_surf, aura_c2, (aura_rad, aura_rad), int(aura_rad * 0.65))
        surface.blit(aura_surf, (sx - aura_rad, sy - aura_rad))

        # Carved stone mounting base with bronze trim
        base_r = pygame.Rect(sx - 18, sy + 14, 36, 12)
        pygame.draw.rect(surface, (45, 38, 52), base_r, border_radius=3)
        pygame.draw.rect(surface, (150, 120, 60), base_r, width=1, border_radius=3)

        # Floating diamond spire with gentle levitation bob
        float_y = sy + int(3 * math.sin(flicker_phase * 2.2))
        pts_outer = [
            (sx, float_y - 26),
            (sx + 15, float_y - 2),
            (sx, float_y + 16),
            (sx - 15, float_y - 2),
        ]
        pygame.draw.polygon(surface, c_dark, pts_outer)
        pts_left = [(sx, float_y - 26), (sx - 15, float_y - 2), (sx, float_y + 16)]
        pts_right = [(sx, float_y - 26), (sx + 15, float_y - 2), (sx, float_y + 16)]
        pygame.draw.polygon(surface, c_mid, pts_left)
        pygame.draw.polygon(surface, c_light, pts_right)

        # Inner radiant crystal core
        pts_core = [
            (sx, float_y - 13),
            (sx + 7, float_y - 2),
            (sx, float_y + 8),
            (sx - 7, float_y - 2),
        ]
        pygame.draw.polygon(surface, (235, 250, 255) if is_revealed else (195, 195, 195), pts_core)
        pygame.draw.circle(surface, (255, 255, 255), (sx, float_y - 2), 4)
        pygame.draw.polygon(surface, (215, 175, 55) if is_revealed else (175, 175, 175), pts_outer, width=1)

        # Emitter lens flare in direction of beam
        ex = sx + int(self.beam_dir[0] * 16)
        ey = float_y + int(self.beam_dir[1] * 16)
        pygame.draw.circle(surface, c_flare, (ex, ey), 4)
        pygame.draw.circle(surface, (255, 255, 255), (ex, ey), 2)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

L3_SCREEN_WIDTH = 800
L3_SCREEN_HEIGHT = 600
L3_WORLD_WIDTH = 2600
L3_WORLD_HEIGHT = 2200
L3_BATTERY_DRAIN_RATE = 0.0  # This chamber supplies stable light; Level 2 is unchanged.

# Player spawns in Chamber 1 (Entrance Chamber)
L3_SPAWN_X = 650
L3_SPAWN_Y = 1850

# Visual Palette — Ancient Sacred Sun-Temple
_FLOOR_BASE = (10, 8, 16)
_FLOOR_TILE_A = (15, 12, 22)
_FLOOR_TILE_B = (12, 10, 18)
_WALL_COLOR = (24, 20, 32)
_WALL_STONE = (38, 32, 48)
_WALL_HIGHLIGHT = (56, 48, 70)
_POOL_WATER = (18, 30, 48)
_POOL_RIM = (35, 45, 65)

# Reclaimed Vegetation & Natural Ruins Palette (Reference Images 1-4)
_DECOR_MOSS_DEEP = (22, 42, 18)
_DECOR_MOSS_DARK = (32, 62, 26)
_DECOR_MOSS_MID = (52, 96, 38)
_DECOR_MOSS_LIGHT = (84, 146, 52)
_DECOR_MOSS_BRIGHT = (124, 186, 68)

_DECOR_STONE_SHADOW = (42, 38, 48)
_DECOR_STONE_DARK = (68, 64, 76)
_DECOR_STONE_MID = (112, 106, 120)
_DECOR_STONE_LIGHT = (162, 156, 170)
_DECOR_STONE_SPECULAR = (205, 200, 212)

_DECOR_GRASS_SHADOW = (26, 56, 20)
_DECOR_GRASS_DARK = (45, 95, 30)
_DECOR_GRASS_MID = (72, 142, 46)
_DECOR_GRASS_LIME = (114, 184, 58)
_DECOR_GRASS_TIP = (175, 225, 78)

_DECOR_MUSH_STALK_SHADOW = (158, 150, 138)
_DECOR_MUSH_STALK = (220, 214, 202)
_DECOR_MUSH_STALK_HIGH = (248, 245, 240)
_DECOR_MUSH_CAP_SHADOW = (120, 18, 24)
_DECOR_MUSH_CAP = (205, 34, 38)
_DECOR_MUSH_CAP_HIGH = (244, 76, 70)
_DECOR_MUSH_SPOTS = (252, 250, 244)

_DECOR_BARK_SHADOW = (42, 28, 18)
_DECOR_BARK_DARK = (68, 44, 28)
_DECOR_BARK_MID = (98, 66, 42)
_DECOR_BARK_LIGHT = (142, 102, 68)
_DECOR_BARK_HIGH = (175, 130, 90)

_DECOR_DEADWOOD_SHADOW = (48, 38, 30)
_DECOR_DEADWOOD_MID = (86, 68, 54)
_DECOR_DEADWOOD_LIGHT = (128, 104, 84)
_DECOR_DEADWOOD_HIGH = (165, 140, 118)
_DECOR_LICHEN = (118, 152, 126)
_DECOR_LICHEN_LIGHT = (156, 188, 162)

_DECOR_LEAF_SHADOW = (18, 38, 22)
_DECOR_LEAF_DARK = (28, 62, 32)
_DECOR_LEAF_MID = (48, 108, 48)
_DECOR_LEAF_EMERALD = (78, 156, 58)
_DECOR_LEAF_LIME = (128, 196, 70)
_DECOR_LEAF_SUN = (176, 228, 92)


def _draw_rock_grass_cluster(surface: pygame.Surface, cx: int, cy: int, scale: float = 1.0):
    """Draws layered weathered stones wrapped in stepped moss mounds and lush curved grass blades (Ref 1)."""
    s = scale
    # 1. Stepped Moss Base
    pygame.draw.ellipse(surface, _DECOR_MOSS_DEEP, (int(cx - 36 * s), int(cy - 12 * s), int(72 * s), int(26 * s)))
    pygame.draw.ellipse(surface, _DECOR_MOSS_DARK, (int(cx - 32 * s), int(cy - 9 * s), int(64 * s), int(20 * s)))
    pygame.draw.ellipse(surface, _DECOR_MOSS_MID, (int(cx - 24 * s), int(cy - 6 * s), int(48 * s), int(14 * s)))

    # Back grass blades
    back_blades = [
        (-24, -2, -6, 22, 3),
        (-14, -5, -4, 26, 3),
        (-2, -6, 2, 28, 3),
        (12, -4, 5, 24, 3),
        (22, -2, 7, 20, 3),
    ]
    for rx_rel, ry_rel, bend_x, tip_h, b_w in back_blades:
        bx0 = cx + int(rx_rel * s)
        by0 = cy + int(ry_rel * s)
        tx = bx0 + int(bend_x * s)
        ty = by0 - int(tip_h * s)
        mx = (bx0 + tx) // 2 + int(bend_x * 0.4 * s)
        my = (by0 + ty) // 2
        pygame.draw.polygon(surface, _DECOR_GRASS_SHADOW, [
            (bx0 - int(b_w * s), by0), (bx0 + int(b_w * s), by0), (mx + int(b_w * 0.5 * s), my), (tx, ty), (mx - int(b_w * 0.5 * s), my)
        ])
        pygame.draw.polygon(surface, _DECOR_GRASS_MID, [
            (bx0 - int((b_w - 1) * s), by0), (bx0 + int((b_w - 1) * s), by0), (mx + int(b_w * 0.3 * s), my), (tx, ty), (mx - int(b_w * 0.3 * s), my)
        ])
        pygame.draw.line(surface, _DECOR_GRASS_LIME, (mx, my), (tx, ty), max(1, int(1.5 * s)))
        pygame.draw.circle(surface, _DECOR_GRASS_TIP, (tx, ty), max(1, int(1.2 * s)))

    # 2. Weathered Granite Boulders
    bx = cx - int(6 * s)
    by = cy - int(2 * s)
    bw, bh = int(30 * s), int(22 * s)
    pygame.draw.ellipse(surface, _DECOR_STONE_SHADOW, (bx - bw // 2 - 1, by - bh // 2, bw + 2, bh + 3))
    pygame.draw.ellipse(surface, _DECOR_STONE_DARK, (bx - bw // 2, by - bh // 2, bw, bh))
    pygame.draw.ellipse(surface, _DECOR_STONE_MID, (bx - bw // 2 + 3, by - bh // 2 + 2, bw - 6, bh - 4))
    pygame.draw.ellipse(surface, _DECOR_STONE_LIGHT, (bx - bw // 2 + 5, by - bh // 2 + 3, int(bw * 0.55), int(bh * 0.52)))
    pygame.draw.ellipse(surface, _DECOR_STONE_SPECULAR, (bx - bw // 2 + 8, by - bh // 2 + 4, int(bw * 0.3), int(bh * 0.28)))

    rx = cx + int(16 * s)
    ry = cy + int(1 * s)
    rw, rh = int(20 * s), int(16 * s)
    pygame.draw.ellipse(surface, _DECOR_STONE_SHADOW, (rx - rw // 2 - 1, ry - rh // 2, rw + 2, rh + 2))
    pygame.draw.ellipse(surface, _DECOR_STONE_DARK, (rx - rw // 2, ry - rh // 2, rw, rh))
    pygame.draw.ellipse(surface, _DECOR_STONE_MID, (rx - rw // 2 + 2, ry - rh // 2 + 2, rw - 4, rh - 3))
    pygame.draw.ellipse(surface, _DECOR_STONE_LIGHT, (rx - rw // 2 + 4, ry - rh // 2 + 3, int(rw * 0.5), int(rh * 0.45)))

    fx = cx - int(18 * s)
    fy = cy + int(6 * s)
    fw, fh = int(14 * s), int(10 * s)
    pygame.draw.ellipse(surface, _DECOR_STONE_SHADOW, (fx - fw // 2, fy - fh // 2, fw + 1, fh + 1))
    pygame.draw.ellipse(surface, _DECOR_STONE_DARK, (fx - fw // 2, fy - fh // 2, fw, fh))
    pygame.draw.ellipse(surface, _DECOR_STONE_MID, (fx - fw // 2 + 2, fy - fh // 2 + 1, fw - 4, fh - 2))
    pygame.draw.ellipse(surface, _DECOR_STONE_LIGHT, (fx - fw // 2 + 3, fy - fh // 2 + 2, int(fw * 0.45), int(fh * 0.4)))

    # Moss creep onto boulders
    pygame.draw.ellipse(surface, _DECOR_MOSS_MID, (bx - int(6 * s), by - int(bh * 0.45), int(14 * s), int(7 * s)))
    pygame.draw.ellipse(surface, _DECOR_MOSS_LIGHT, (bx - int(4 * s), by - int(bh * 0.45) + 1, int(9 * s), int(4 * s)))
    pygame.draw.ellipse(surface, _DECOR_MOSS_BRIGHT, (bx - int(2 * s), by - int(bh * 0.45) + 2, int(4 * s), int(2 * s)))

    # 3. Foreground Grass Blades
    fore_blades = [
        (-28, 4, -9, 16, 2),
        (-20, 7, -6, 20, 3),
        (-10, 8, -3, 23, 3),
        (-1, 9, 3, 24, 3),
        (8, 8, 5, 21, 3),
        (18, 7, 8, 18, 2),
        (26, 4, 9, 14, 2),
    ]
    for rx_rel, ry_rel, bend_x, tip_h, b_w in fore_blades:
        bx0 = cx + int(rx_rel * s)
        by0 = cy + int(ry_rel * s)
        tx = bx0 + int(bend_x * s)
        ty = by0 - int(tip_h * s)
        mx = (bx0 + tx) // 2 + int(bend_x * 0.35 * s)
        my = (by0 + ty) // 2
        pygame.draw.polygon(surface, _DECOR_GRASS_DARK, [
            (bx0 - int(b_w * s), by0), (bx0 + int(b_w * s), by0), (mx + int(b_w * 0.5 * s), my), (tx, ty), (mx - int(b_w * 0.5 * s), my)
        ])
        pygame.draw.polygon(surface, _DECOR_GRASS_MID, [
            (bx0 - int((b_w - 1) * s), by0), (bx0 + int((b_w - 1) * s), by0), (mx + int(b_w * 0.3 * s), my), (tx, ty), (mx - int(b_w * 0.3 * s), my)
        ])
        pygame.draw.line(surface, _DECOR_GRASS_LIME, (mx, my), (tx, ty), max(1, int(1.5 * s)))
        pygame.draw.circle(surface, _DECOR_GRASS_TIP, (tx, ty), max(1, int(1.3 * s)))


def _draw_mushrooms(surface: pygame.Surface, cx: int, cy: int, scale: float = 1.0, count: int = 3):
    """Draws pixel-art fly agaric mushrooms with crimson caps, cream warts, and veil rings (Ref 2)."""
    s = scale
    mw, mh = int(32 * s), int(14 * s)
    pygame.draw.ellipse(surface, _DECOR_MOSS_DEEP, (cx - mw // 2, cy - mh // 2, mw, mh))
    pygame.draw.ellipse(surface, _DECOR_MOSS_DARK, (cx - mw // 2 + 2, cy - mh // 2 + 1, mw - 4, mh - 2))
    pygame.draw.ellipse(surface, _DECOR_MOSS_MID, (cx - mw // 2 + 5, cy - mh // 2 + 2, mw - 10, mh - 5))

    mush_list = [
        (0, 3, 20, 18, 12, 0),       # Central prime
        (-10, 4, 14, 13, 9, -2),     # Left companion
        (10, 2, 16, 15, 10, 2),      # Right companion
        (4, 6, 9, 10, 7, 1),         # Front button
    ]
    actual_count = min(count, len(mush_list))

    for i in range(actual_count):
        mx_rel, my_rel, st_h, cp_w, cp_h, tilt = mush_list[i]
        mx = cx + int(mx_rel * s)
        base_y = cy + int(my_rel * s)
        stem_len = int(st_h * s)
        cap_w = int(cp_w * s)
        cap_h = int(cp_h * s)
        top_x = mx + int(tilt * s)
        top_y = base_y - stem_len

        st_w = max(2, int(4 * s))
        pygame.draw.circle(surface, _DECOR_MUSH_STALK_SHADOW, (mx, base_y), max(2, int(st_w * 0.95)))
        pygame.draw.circle(surface, _DECOR_MUSH_STALK, (mx, base_y), max(1, int(st_w * 0.75)))
        pygame.draw.line(surface, _DECOR_MUSH_STALK_SHADOW, (mx, base_y), (top_x, top_y), st_w + 1)
        pygame.draw.line(surface, _DECOR_MUSH_STALK, (mx, base_y), (top_x, top_y), st_w)
        pygame.draw.line(surface, _DECOR_MUSH_STALK_HIGH, (mx + 1, base_y - 1), (top_x + 1, top_y + 1), max(1, st_w - 2))

        veil_y = base_y - int(stem_len * 0.42)
        veil_x = mx + int(tilt * 0.42 * s)
        pygame.draw.ellipse(surface, _DECOR_MUSH_STALK_SHADOW, (veil_x - int(3.5 * s), veil_y - 1, int(7 * s), int(4 * s)))
        pygame.draw.ellipse(surface, _DECOR_MUSH_STALK_HIGH, (veil_x - int(3 * s), veil_y - 1, int(6 * s), int(2.5 * s)))

        pygame.draw.arc(surface, _DECOR_MUSH_CAP_SHADOW, (top_x - cap_w // 2, top_y - int(2 * s), cap_w, int(5 * s)), 0, math.pi, 2)
        pygame.draw.ellipse(surface, _DECOR_MUSH_CAP_SHADOW, (top_x - cap_w // 2 - 1, top_y - cap_h - 1, cap_w + 2, cap_h + 2))
        pygame.draw.ellipse(surface, _DECOR_MUSH_CAP, (top_x - cap_w // 2, top_y - cap_h, cap_w, cap_h))
        pygame.draw.ellipse(surface, _DECOR_MUSH_CAP_HIGH, (top_x - int(cap_w * 0.36), top_y - cap_h + 1, int(cap_w * 0.72), int(cap_h * 0.58)))

        spots = [
            (0, -int(cap_h * 0.72)),
            (-int(cap_w * 0.24), -int(cap_h * 0.52)),
            (int(cap_w * 0.24), -int(cap_h * 0.54)),
            (-int(cap_w * 0.35), -int(cap_h * 0.26)),
            (int(cap_w * 0.34), -int(cap_h * 0.25)),
            (0, -int(cap_h * 0.35)),
            (-int(cap_w * 0.12), -int(cap_h * 0.18)),
            (int(cap_w * 0.14), -int(cap_h * 0.18)),
        ]
        for sp_x, sp_y in spots:
            dot_x = top_x + int(sp_x * (s if s > 0 else 1))
            dot_y = top_y + int(sp_y * (s if s > 0 else 1))
            pygame.draw.circle(surface, _DECOR_MUSH_SPOTS, (dot_x, dot_y), max(1, int(1.3 * s)))


def _draw_ancient_tree(surface: pygame.Surface, cx: int, cy: int, scale: float = 1.0):
    """Draws an ancient twisted temple tree with flared roots, gnarled bark, cloud canopy, and vines (Ref 3)."""
    s = scale

    # 1. Broad buttress roots
    root_curves = [
        (-22, 10, -48, 20, 9),
        (-14, 14, -28, 28, 10),
        (0, 16, 2, 32, 11),
        (16, 14, 32, 26, 9),
        (24, 10, 52, 18, 8),
    ]
    for c_x, c_y, e_x, e_y, rw in root_curves:
        p0 = (cx, cy + int(4 * s))
        p1 = (cx + int(c_x * s), cy + int(c_y * s))
        p2 = (cx + int(e_x * s), cy + int(e_y * s))
        pygame.draw.line(surface, _DECOR_BARK_SHADOW, p0, p1, int(rw * s) + 2)
        pygame.draw.line(surface, _DECOR_BARK_SHADOW, p1, p2, int(rw * s) + 1)
        pygame.draw.line(surface, _DECOR_BARK_DARK, p0, p1, int(rw * s))
        pygame.draw.line(surface, _DECOR_BARK_DARK, p1, p2, int((rw - 1) * s))
        pygame.draw.line(surface, _DECOR_BARK_MID, (p0[0] + 1, p0[1] - 1), (p1[0] + 1, p1[1] - 1), max(1, int((rw - 3) * s)))
        pygame.draw.line(surface, _DECOR_BARK_MID, (p1[0] + 1, p1[1] - 1), (p2[0] + 1, p2[1] - 1), max(1, int((rw - 4) * s)))
        pygame.draw.circle(surface, _DECOR_MOSS_DARK, p2, max(2, int(5 * s)))
        pygame.draw.circle(surface, _DECOR_MOSS_MID, p2, max(1, int(3.5 * s)))
        pygame.draw.circle(surface, _DECOR_MOSS_LIGHT, (p2[0], p2[1] - 1), max(1, int(2 * s)))

    # 2. Muscular spiraled gnarled trunk
    trunk_pts_left = [
        (cx - int(24 * s), cy + int(14 * s)),
        (cx - int(18 * s), cy - int(10 * s)),
        (cx - int(26 * s), cy - int(42 * s)),
        (cx - int(22 * s), cy - int(72 * s)),
    ]
    trunk_pts_right = [
        (cx + int(24 * s), cy + int(14 * s)),
        (cx + int(18 * s), cy - int(10 * s)),
        (cx + int(26 * s), cy - int(40 * s)),
        (cx + int(22 * s), cy - int(72 * s)),
    ]
    pygame.draw.polygon(surface, _DECOR_BARK_SHADOW, trunk_pts_left + list(reversed(trunk_pts_right)))
    pygame.draw.polygon(surface, _DECOR_BARK_DARK, [
        (cx - int(20 * s), cy + int(14 * s)),
        (cx - int(14 * s), cy - int(10 * s)),
        (cx - int(21 * s), cy - int(42 * s)),
        (cx - int(18 * s), cy - int(72 * s)),
        (cx + int(18 * s), cy - int(72 * s)),
        (cx + int(21 * s), cy - int(40 * s)),
        (cx + int(14 * s), cy - int(10 * s)),
        (cx + int(20 * s), cy + int(14 * s)),
    ])
    pygame.draw.polygon(surface, _DECOR_BARK_MID, [
        (cx - int(14 * s), cy + int(14 * s)),
        (cx - int(8 * s), cy - int(10 * s)),
        (cx - int(15 * s), cy - int(42 * s)),
        (cx - int(12 * s), cy - int(72 * s)),
        (cx + int(12 * s), cy - int(72 * s)),
        (cx + int(15 * s), cy - int(40 * s)),
        (cx + int(8 * s), cy - int(10 * s)),
        (cx + int(14 * s), cy + int(14 * s)),
    ])

    pygame.draw.line(surface, _DECOR_BARK_HIGH, (cx - int(10 * s), cy + int(10 * s)), (cx + int(6 * s), cy - int(16 * s)), max(1, int(3 * s)))
    pygame.draw.line(surface, _DECOR_BARK_HIGH, (cx + int(6 * s), cy - int(16 * s)), (cx - int(8 * s), cy - int(48 * s)), max(1, int(3 * s)))
    pygame.draw.line(surface, _DECOR_BARK_LIGHT, (cx + int(2 * s), cy + int(10 * s)), (cx + int(14 * s), cy - int(12 * s)), max(1, int(2 * s)))
    pygame.draw.line(surface, _DECOR_BARK_SHADOW, (cx - int(4 * s), cy + int(10 * s)), (cx + int(10 * s), cy - int(18 * s)), max(1, int(2 * s)))

    # Main massive boughs
    pygame.draw.line(surface, _DECOR_BARK_DARK, (cx - int(16 * s), cy - int(66 * s)), (cx - int(64 * s), cy - int(96 * s)), int(11 * s))
    pygame.draw.line(surface, _DECOR_BARK_MID, (cx - int(16 * s), cy - int(68 * s)), (cx - int(64 * s), cy - int(98 * s)), int(7 * s))
    pygame.draw.line(surface, _DECOR_BARK_LIGHT, (cx - int(16 * s), cy - int(70 * s)), (cx - int(64 * s), cy - int(100 * s)), max(1, int(3 * s)))

    pygame.draw.line(surface, _DECOR_BARK_DARK, (cx + int(16 * s), cy - int(66 * s)), (cx + int(64 * s), cy - int(94 * s)), int(11 * s))
    pygame.draw.line(surface, _DECOR_BARK_MID, (cx + int(16 * s), cy - int(68 * s)), (cx + int(64 * s), cy - int(96 * s)), int(7 * s))
    pygame.draw.line(surface, _DECOR_BARK_LIGHT, (cx + int(16 * s), cy - int(70 * s)), (cx + int(64 * s), cy - int(98 * s)), max(1, int(3 * s)))

    pygame.draw.line(surface, _DECOR_BARK_DARK, (cx, cy - int(68 * s)), (cx + int(6 * s), cy - int(112 * s)), int(12 * s))
    pygame.draw.line(surface, _DECOR_BARK_MID, (cx, cy - int(70 * s)), (cx + int(6 * s), cy - int(114 * s)), int(8 * s))

    # 3. Organic Tiered Cloud Canopy
    canopy_lobes = [
        (-64, -98, 44, 32),
        (64, -96, 44, 32),
        (-32, -122, 52, 36),
        (32, -120, 52, 36),
        (0, -108, 56, 38),
        (-76, -118, 38, 28),
        (76, -116, 38, 28),
        (0, -148, 60, 42),
        (-36, -156, 46, 32),
        (36, -154, 46, 32),
        (0, -172, 48, 34),
    ]
    for lx_rel, ly_rel, rw, rh in canopy_lobes:
        lx = cx + int(lx_rel * s)
        ly = cy + int(ly_rel * s)
        pygame.draw.ellipse(surface, _DECOR_LEAF_SHADOW, (lx - int(rw * s), ly - int(rh * s) + int(5 * s), int(rw * 2 * s), int(rh * 2 * s)))

    for lx_rel, ly_rel, rw, rh in canopy_lobes:
        lx = cx + int(lx_rel * s)
        ly = cy + int(ly_rel * s)
        pygame.draw.ellipse(surface, _DECOR_LEAF_DARK, (lx - int(rw * s), ly - int(rh * s), int(rw * 2 * s), int(rh * 2 * s)))
        pygame.draw.ellipse(surface, _DECOR_LEAF_MID, (lx - int((rw - 3) * s), ly - int((rh - 2) * s), int((rw - 3) * 2 * s), int((rh - 2) * 2 * s)))

    for lx_rel, ly_rel, rw, rh in canopy_lobes:
        lx = cx + int(lx_rel * s)
        ly = cy + int(ly_rel * s)
        pygame.draw.ellipse(surface, _DECOR_LEAF_EMERALD, (lx - int(rw * 0.75 * s), ly - int(rh * 0.88 * s), int(rw * 1.5 * s), int(rh * 1.4 * s)))
        pygame.draw.ellipse(surface, _DECOR_LEAF_LIME, (lx - int(rw * 0.5 * s), ly - int(rh * 0.88 * s), int(rw * 1.0 * s), int(rh * 0.8 * s)))
        pygame.draw.ellipse(surface, _DECOR_LEAF_SUN, (lx - int(rw * 0.25 * s), ly - int(rh * 0.88 * s) + 1, int(rw * 0.5 * s), int(rh * 0.45 * s)))

    # 4. Sinuous hanging vines & moss tendrils
    vines = [
        (-62, -78, 28),
        (-44, -72, 38),
        (-22, -78, 46),
        (0, -74, 52),
        (22, -76, 44),
        (46, -72, 36),
        (64, -76, 26),
    ]
    for vx_rel, vy_rel, v_len in vines:
        vx = cx + int(vx_rel * s)
        vy0 = cy + int(vy_rel * s)
        v_l = int(v_len * s)
        pts = [
            (vx, vy0),
            (vx + int(4 * s), vy0 + v_l // 3),
            (vx - int(3 * s), vy0 + 2 * v_l // 3),
            (vx + int(2 * s), vy0 + v_l),
        ]
        pygame.draw.lines(surface, _DECOR_MOSS_DARK, False, pts, max(1, int(2.5 * s)))
        pygame.draw.lines(surface, _DECOR_MOSS_LIGHT, False, pts, max(1, int(1.4 * s)))
        pygame.draw.circle(surface, _DECOR_LEAF_LIME, pts[-1], max(1, int(2.0 * s)))
        pygame.draw.circle(surface, _DECOR_LEAF_SUN, (pts[-1][0], pts[-1][1] - 1), max(1, int(1.2 * s)))


def _draw_broken_trunk(surface: pygame.Surface, cx: int, cy: int, scale: float = 1.0):
    """Draws a hollowed, splintered deadwood ancient tree trunk with bare limbs and lichen (Ref 4)."""
    s = scale

    # 1. Flared root base
    roots = [
        (-38, 14, 8),
        (-20, 22, 9),
        (0, 25, 10),
        (22, 21, 9),
        (40, 13, 7),
    ]
    for rx_end, ry_end, rw in roots:
        ex = cx + int(rx_end * s)
        ey = cy + int(ry_end * s)
        pygame.draw.line(surface, _DECOR_DEADWOOD_SHADOW, (cx, cy + int(4 * s)), (ex, ey), int(rw * s) + 2)
        pygame.draw.line(surface, _DECOR_DEADWOOD_MID, (cx, cy + int(4 * s)), (ex, ey), int(rw * s))
        pygame.draw.line(surface, _DECOR_DEADWOOD_LIGHT, (cx + 1, cy + int(3 * s)), (ex + 1, ey - 1), max(1, int((rw - 3) * s)))
        pygame.draw.circle(surface, _DECOR_MOSS_MID, (ex, ey), max(2, int(4 * s)))

    # 2. Hollow trunk body with splintered rim
    tw = int(28 * s)
    th = int(62 * s)
    trunk_poly_main = [
        (cx - tw, cy + int(12 * s)),
        (cx - int(tw * 0.9), cy - int(th * 0.5)),
        (cx - tw, cy - th + int(12 * s)),
        (cx + tw, cy - th + int(12 * s)),
        (cx + int(tw * 0.9), cy - int(th * 0.5)),
        (cx + tw, cy + int(12 * s)),
    ]
    pygame.draw.polygon(surface, _DECOR_DEADWOOD_SHADOW, trunk_poly_main)
    pygame.draw.polygon(surface, _DECOR_DEADWOOD_MID, [
        (cx - int(tw * 0.85), cy + int(12 * s)),
        (cx - int(tw * 0.75), cy - int(th * 0.5)),
        (cx - int(tw * 0.85), cy - th + int(12 * s)),
        (cx + int(tw * 0.85), cy - th + int(12 * s)),
        (cx + int(tw * 0.75), cy - int(th * 0.5)),
        (cx + int(tw * 0.85), cy + int(12 * s)),
    ])

    splinters = [
        (-tw, 0),
        (-int(tw * 0.75), -int(18 * s)),
        (-int(tw * 0.45), -int(6 * s)),
        (-int(tw * 0.15), -int(14 * s)),
        (int(tw * 0.15), -int(4 * s)),
        (int(tw * 0.5), -int(20 * s)),
        (int(tw * 0.8), -int(8 * s)),
        (tw, 0),
    ]
    rim_poly = [(cx + px, cy - th + int(12 * s) + py) for px, py in splinters]
    pygame.draw.polygon(surface, _DECOR_DEADWOOD_MID, rim_poly)
    pygame.draw.polygon(surface, _DECOR_DEADWOOD_LIGHT, rim_poly, 1)

    # Dark hollow void
    hollow_w = int(18 * s)
    hollow_h = int(32 * s)
    pygame.draw.ellipse(surface, (14, 10, 8), (cx - hollow_w // 2, cy - int(44 * s), hollow_w, hollow_h))
    pygame.draw.ellipse(surface, (28, 20, 16), (cx - hollow_w // 2 + 1, cy - int(42 * s), hollow_w - 2, hollow_h - 4))
    pygame.draw.ellipse(surface, (44, 32, 26), (cx - hollow_w // 2 + 3, cy - int(40 * s), hollow_w - 6, hollow_h - 8))

    # Dead bare limbs
    bx0, by0 = cx + int(20 * s), cy - int(34 * s)
    bx1, by1 = cx + int(52 * s), cy - int(56 * s)
    bx2, by2 = cx + int(68 * s), cy - int(48 * s)
    pygame.draw.lines(surface, _DECOR_DEADWOOD_SHADOW, False, [(bx0, by0), (bx1, by1), (bx2, by2)], int(6 * s))
    pygame.draw.lines(surface, _DECOR_DEADWOOD_MID, False, [(bx0, by0), (bx1, by1), (bx2, by2)], max(1, int(4 * s)))
    pygame.draw.lines(surface, _DECOR_DEADWOOD_LIGHT, False, [(bx0, by0 - 1), (bx1, by1 - 1), (bx2, by2 - 1)], max(1, int(2 * s)))

    lx0, ly0 = cx - int(20 * s), cy - int(28 * s)
    lx1, ly1 = cx - int(42 * s), cy - int(44 * s)
    pygame.draw.lines(surface, _DECOR_DEADWOOD_SHADOW, False, [(lx0, ly0), (lx1, ly1)], int(5 * s))
    pygame.draw.lines(surface, _DECOR_DEADWOOD_MID, False, [(lx0, ly0), (lx1, ly1)], max(1, int(3 * s)))

    # Spanish moss / lichen strands
    drapes = [
        (cx + int(42 * s), cy - int(48 * s), int(20 * s)),
        (cx + int(56 * s), cy - int(50 * s), int(26 * s)),
        (cx + int(66 * s), cy - int(44 * s), int(16 * s)),
        (cx - int(34 * s), cy - int(38 * s), int(18 * s)),
    ]
    for dx, dy, d_len in drapes:
        pts = [(dx, dy), (dx - 2, dy + d_len // 3), (dx + 2, dy + 2 * d_len // 3), (dx, dy + d_len)]
        pygame.draw.lines(surface, _DECOR_LICHEN, False, pts, max(1, int(2.5 * s)))
        pygame.draw.lines(surface, _DECOR_LICHEN_LIGHT, False, pts, max(1, int(1.2 * s)))

    pygame.draw.ellipse(surface, _DECOR_LICHEN, (cx - int(20 * s), cy - int(26 * s), int(12 * s), int(16 * s)))
    pygame.draw.ellipse(surface, _DECOR_LICHEN_LIGHT, (cx - int(18 * s), cy - int(24 * s), int(8 * s), int(11 * s)))

    pygame.draw.ellipse(surface, (175, 110, 50), (cx + int(16 * s), cy - int(20 * s), int(12 * s), int(6 * s)))
    pygame.draw.ellipse(surface, (235, 200, 135), (cx + int(16 * s), cy - int(21 * s), int(12 * s), int(2.5 * s)))


def _draw_fallen_log(surface: pygame.Surface, cx: int, cy: int, length: int = 48, angle_deg: float = 0):
    """Draws a mossy weathered fallen timber log with hollow end and bracket mushrooms."""
    rad = math.radians(angle_deg)
    dx = math.cos(rad)
    dy = math.sin(rad)
    perp_x = -dy
    perp_y = dx

    half_l = length // 2
    x0 = cx - int(dx * half_l)
    y0 = cy - int(dy * half_l)
    x1 = cx + int(dx * half_l)
    y1 = cy + int(dy * half_l)

    lw = 12
    poly = [
        (x0 + perp_x * lw // 2, y0 + perp_y * lw // 2),
        (x1 + perp_x * lw // 2, y1 + perp_y * lw // 2),
        (x1 - perp_x * lw // 2, y1 - perp_y * lw // 2),
        (x0 - perp_x * lw // 2, y0 - perp_y * lw // 2),
    ]
    pygame.draw.polygon(surface, _DECOR_BARK_SHADOW, poly)
    pygame.draw.polygon(surface, _DECOR_BARK_MID, [
        (x0 + perp_x * (lw // 2 - 2), y0 + perp_y * (lw // 2 - 2)),
        (x1 + perp_x * (lw // 2 - 2), y1 + perp_y * (lw // 2 - 2)),
        (x1 - perp_x * (lw // 2 - 2), y1 - perp_y * (lw // 2 - 2)),
        (x0 - perp_x * (lw // 2 - 2), y0 - perp_y * (lw // 2 - 2)),
    ])
    pygame.draw.line(surface, _DECOR_MOSS_LIGHT,
                     (x0 + perp_x * (lw // 2 - 1), y0 + perp_y * (lw // 2 - 1)),
                     (x1 + perp_x * (lw // 2 - 1), y1 + perp_y * (lw // 2 - 1)), 3)

    pygame.draw.circle(surface, _DECOR_BARK_SHADOW, (int(x0), int(y0)), lw // 2 + 1)
    pygame.draw.circle(surface, (135, 95, 65), (int(x0), int(y0)), lw // 2 - 1)
    pygame.draw.circle(surface, (45, 28, 18), (int(x0), int(y0)), lw // 2 - 3)

    fx = cx + int(perp_x * lw // 2)
    fy = cy + int(perp_y * lw // 2)
    pygame.draw.ellipse(surface, (185, 120, 55), (fx - 4, fy - 3, 9, 5))
    pygame.draw.ellipse(surface, (235, 205, 140), (fx - 4, fy - 4, 9, 2))


def _draw_ancient_stone_debris(surface: pygame.Surface, cx: int, cy: int):
    """Draws cracked carved masonry paver fragments and pebble drift."""
    pygame.draw.polygon(surface, (42, 38, 50), [
        (cx - 14, cy - 8), (cx + 12, cy - 10), (cx + 16, cy + 6), (cx - 10, cy + 8)
    ])
    pygame.draw.polygon(surface, (78, 72, 86), [
        (cx - 13, cy - 7), (cx + 10, cy - 9), (cx + 14, cy + 4), (cx - 9, cy + 6)
    ])
    pygame.draw.line(surface, (32, 28, 38), (cx - 12, cy - 1), (cx + 11, cy - 3), 2)
    pygame.draw.line(surface, (25, 20, 30), (cx - 2, cy - 7), (cx + 4, cy + 5), 1)
    pygame.draw.circle(surface, _DECOR_MOSS_LIGHT, (cx + 1, cy - 1), 2)
    pygame.draw.circle(surface, (120, 114, 126), (cx - 18, cy + 4), 3)
    pygame.draw.circle(surface, (150, 144, 156), (cx - 19, cy + 3), 1)
    pygame.draw.circle(surface, (98, 92, 104), (cx + 18, cy - 4), 2)


class Level3Room:
    """Orchestration layer for Level 3: Path of Light."""

    def __init__(self, inventory=None, door_keys: dict[str, str | None] | None = None):
        self.inventory = inventory
        self.door_keys_config = dict(DEFAULT_DOOR_KEYS)
        if door_keys:
            self.door_keys_config.update(door_keys)

        # Key warning cooldowns (prevents toast spam when light hits door without key)
        self._ch2_key_warn_cooldown = 0.0
        self._ch3_key_warn_cooldown = 0.0
        self._exit_key_warn_cooldown = 0.0

        # Battery & lighting systems (battery drains slowly, no shadow death)
        self.battery = BatterySystem(drain_rate=L3_BATTERY_DRAIN_RATE)
        self.lantern_meter = LanternMeter()
        self.lighting = LightingSystem(L3_WORLD_WIDTH, L3_WORLD_HEIGHT)
        self.current_chamber = None

        # Construction of level geometry
        self.walls = self._build_walls()
        self.pillars = self._build_pillars()
        self.reflective_pools = self._build_reflective_pools()
        self.doors = self._build_doors()
        self.exit_door = self.doors["exit_door"]

        # Combined obstacles: walls, pillars, closed doors, and Chamber 1 headstone
        self.headstone = Headstone(x=740.0, y=1190.0)
        self.all_obstacles = list(self.walls + self.pillars) + [self.headstone.rect]
        for door in self.doors.values():
            if not door.get("open", False):
                self.all_obstacles.append(door["rect"])

        # Sockets & Entities across the 4 chambers
        self.sockets = self._build_sockets()
        self.player_mirrors = self._build_player_mirrors()
        self.player_crystals = self._build_player_crystals()
        self.light_crystals = self.player_crystals

        # Beams and particles
        self.beam_segments = []
        self.placement_particles = []
        self.golden_door_particles = []
        self._init_golden_door_particles()

        # Legacy / compatibility attributes
        self.temp_mirrors = []
        self.active_clue = None
        self.clue_objects = []
        self.sun_core_center = (650.0, 550.0)
        self.sun_core_keepout_radius = 0.0

        # State flags
        self.flicker_phase = 0.0
        self.toast_msg = ""
        self.toast_timer = 0.0
        self.trigger_level4_transition = False
        self.exit_door_warning_active = False
        self.focused_socket = None
        self.paused = False
        self.help_open = False
        self.debug_optics = False
        self.reduced_motion = False
        self.mural = None
        self.restoration_time = 0.0
        self.puzzles = [
            dict(source="crystal_ch2", color="blue", receiver=(930,550), reward=(955,650),
                 reward_id="crystal_2", door="door_ch2_to_ch3", count=1, solved=False, hold=0.0),
            dict(source="crystal_ch3", color="red", receiver=(1680,470), reward=(1680,555),
                 reward_id="crystal_1", door="door_ch3_to_ch4", count=2, solved=False, hold=0.0),
            dict(source="crystal_ch4", color="green", receiver=(1860,1700), reward=(1800,1780),
                 reward_id="crystal_3", door="exit_door", count=3, solved=False, hold=0.0),
        ]
        self.checkpoint_path = Path(os.environ.get("LUMEN_LEVEL3_SAVE", str(Path(__file__).resolve().parents[1]/"saves/level3.json")))

        # Build environmental ancient trees (Reference Images 3 & 4)
        self.ancient_trees = self._build_ancient_trees()

        # Pre-render static ancient flagstone floor (includes ground flora)
        self.floor_surf = self._render_static_floor()

    def cleanup(self):
        """Cleanup any active resources or particles."""
        self.placement_particles.clear()
        self.golden_door_particles.clear()
        self.focused_socket = None

    def handle_keydown(self, key, player, lantern):
        if self.active_clue:
            if self.active_clue.get("kind") == "mural":
                if key == pygame.K_F3: self.debug_optics = not self.debug_optics
                elif key in (pygame.K_e, pygame.K_RIGHT, pygame.K_LEFT):
                    self.mural.clarity = max(0, min(3, self.mural.clarity + (-1 if key == pygame.K_LEFT else 1)))
                    if self.mural.clarity == 3 and self.inventory:
                        self.inventory.add_clue("l3_mural", "The Temple Remembered",
                            "Light once guided our people. Turn the mirrors. Wake the receiver. Every frame reflects alike; the source keeps its color.")
                        self.save_checkpoint(player, lantern)
                elif key in (pygame.K_ESCAPE, pygame.K_SPACE): self.active_clue = None
            elif key in (pygame.K_e, pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN): self.active_clue = None
            return
        if self.help_open:
            if key in (pygame.K_h, pygame.K_c, pygame.K_ESCAPE, pygame.K_e): self.help_open = False
            return
        if self.paused:
            if key in (pygame.K_ESCAPE, pygame.K_SPACE): self.paused = False
            elif key == pygame.K_m: return "menu"
            elif key == pygame.K_F6: self.reduced_motion = not self.reduced_motion
            return
        if self.focused_socket:
            if key in (pygame.K_e, pygame.K_ESCAPE):
                self.focused_socket = None
                self.save_checkpoint(player, lantern)
            elif key in (pygame.K_a, pygame.K_LEFT): self.handle_rotate_mirror(player, -1)
            elif key in (pygame.K_d, pygame.K_RIGHT): self.handle_rotate_mirror(player, 1)
            elif key == pygame.K_x:
                self.handle_retrieve_mirror(player)
                self.save_checkpoint(player, lantern)
            elif key == pygame.K_i: return "inventory"
            elif key == pygame.K_F3: self.debug_optics = not self.debug_optics
            elif key == pygame.K_r:
                lantern.set_color("red")
                lantern.active = True
            return
        colors = {pygame.K_1:"white", pygame.K_r:"red", pygame.K_g:"green", pygame.K_b:"blue",
                  pygame.K_2:"blue", pygame.K_3:"red", pygame.K_4:"green"}
        if key in colors:
            lantern.set_color(colors[key])
            lantern.active = True
        elif key == pygame.K_e: self.handle_interact(player, lantern)
        elif key == pygame.K_x:
            if self.handle_retrieve_mirror(player): self.save_checkpoint(player, lantern)
        elif key == pygame.K_ESCAPE: self.paused = True
        elif key == pygame.K_i: return "inventory"
        elif key in (pygame.K_h, pygame.K_c): self.help_open = True
        elif key == pygame.K_l: lantern.toggle()
        elif key == pygame.K_F3: self.debug_optics = not self.debug_optics
        elif key == pygame.K_F5: self.save_checkpoint(player, lantern)
        elif key == pygame.K_F9: self.load_checkpoint(player, lantern)
        elif key == pygame.K_SPACE and self.restoration_time > 0: self.restoration_time = 4.0

    def camera_target(self, player):
        if self.focused_socket:
            chamber = int(self.focused_socket.split("_")[1][-1])
            return {2:(780,490), 3:(1810,600), 4:(1950,1650)}[chamber]
        return player.center

    def save_checkpoint(self, player, lantern):
        if self.inventory is None: return False
        data = {"version":1, "keys":sorted(self.inventory.keys), "mirrors":sorted(self.inventory.mirrors),
                "position":[player.x, player.y], "color":lantern.color, "lit":lantern.active,
                "entrance":self.doors["entrance_door"]["open"],
                "solved":[p["solved"] for p in self.puzzles],
                "sources":[c.active for c in self.player_crystals],
                "rewards":[p["reward_id"] for p in self.puzzles if self.inventory.has_crystal(p["reward_id"])],
                "mural":self.inventory.has_clue("l3_mural"),
                "sockets":[[s["mirror"].id, s["mirror"].orientation] if s["mirror"] else None for s in self.sockets]}
        try:
            self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.checkpoint_path.with_suffix(".tmp")
            with temporary.open("w", encoding="utf-8") as file:
                json.dump(data, file)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temporary, self.checkpoint_path)
            return True
        except OSError:
            self._toast("Checkpoint could not be saved. You can keep playing.")
            return False

    def load_checkpoint(self, player, lantern):
        try:
            data = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            if data["version"] != 1 or data["keys"] != sorted(self.inventory.keys) or data["mirrors"] != sorted(self.inventory.mirrors):
                raise ValueError("Different incoming inventory")
            if any(not isinstance(data[k], list) or len(data[k]) != 3 or not all(type(v) is bool for v in data[k]) for k in ("solved", "sources")):
                raise ValueError("Invalid progress")
            if type(data["entrance"]) is not bool or type(data["mural"]) is not bool or type(data["lit"]) is not bool: raise ValueError()
            if len(data["sockets"]) != len(self.sockets) or data["color"] not in ("white", "blue", "red", "green"): raise ValueError()
            used = set()
            for entry in data["sockets"]:
                if entry is not None:
                    if not isinstance(entry, list) or len(entry) != 2: raise ValueError()
                    mid, angle = entry
                    if mid not in self.inventory.mirrors or mid in used or type(angle) is not int or angle not in range(4): raise ValueError()
                    used.add(mid)
            if not isinstance(data["rewards"], list) or any(r not in ("crystal_1", "crystal_2", "crystal_3") for r in data["rewards"]): raise ValueError()
            if len(set(data["rewards"])) != len(data["rewards"]): raise ValueError()
            for index, puzzle in enumerate(self.puzzles):
                if puzzle["reward_id"] in data["rewards"] and not data["solved"][index]: raise ValueError()
                if data["solved"][index] and not (data["entrance"] if index == 0 else data["solved"][index-1]): raise ValueError()
            x, y = data["position"]
            if not (40 <= x <= L3_WORLD_WIDTH-70 and 40 <= y <= L3_WORLD_HEIGHT-70): raise ValueError()
            blockers = self.walls + self.pillars + [self.headstone.rect]
            opened = [data["entrance"]] + data["solved"]
            blockers += [door["rect"] for door, is_open in zip(self.doors.values(), opened) if not is_open]
            if pygame.Rect(x,y,player.width,player.height).collidelist(blockers) != -1: raise ValueError()
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            self._toast("No compatible Level 3 checkpoint. Current progress is unchanged.")
            return False
        for socket in self.sockets: self.uninstall_mirror(socket["id"])
        for socket, entry in zip(self.sockets, data["sockets"]):
            if entry:
                self.install_mirror(entry[0], socket["id"])
                socket["mirror"].orientation = entry[1]
        for door, is_open in zip(self.doors.values(), opened):
            door["open"] = door["unlocked"] = is_open
        self.all_obstacles = blockers
        for puzzle, crystal, solved, active in zip(self.puzzles, self.player_crystals, data["solved"], data["sources"]):
            puzzle["solved"] = crystal.charged = solved
            puzzle["hold"] = 0.0
            crystal.active = active
        self.inventory.crystals = [c for c in self.inventory.crystals if c not in ("crystal_1","crystal_2","crystal_3")] + data["rewards"]
        if data["mural"]:
            self.inventory.add_clue("l3_mural", "The Temple Remembered", "Light once guided our people. Turn the mirrors. Wake the receiver. Every mirror reflects alike.")
        player.x, player.y = x, y
        lantern.set_color(data["color"])
        lantern.active = data["lit"]
        self.focused_socket = None
        self.restoration_time = 4.0 if all(data["solved"]) else 0.0
        self.trigger_level4_transition = False
        self._toast("Level 3 checkpoint restored.")
        return True

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def mirrors(self) -> list[Mirror]:
        """Returns installed player mirrors."""
        return [sock["mirror"] for sock in self.sockets if sock.get("mirror") is not None]

    @property
    def all_mirrors(self) -> list[Mirror]:
        """Returns all mirrors currently placed in sockets."""
        return [m for m in self.player_mirrors if getattr(m, "placed", False)]

    @property
    def crystals(self) -> list[PuzzleCrystal]:
        """Returns the light-source crystals."""
        return self.player_crystals

    @property
    def crystals_resonating(self) -> int:
        """Returns number of resonating / charged crystals."""
        return sum(p["solved"] for p in self.puzzles)

    def align_temp_mirrors_to_solution(self):
        """Legacy test helper, not bound to any gameplay input."""
        for puzzle, crystal in zip(self.puzzles, self.player_crystals):
            puzzle["solved"] = crystal.charged = crystal.active = True
            self.unlock_door(puzzle["door"])
            self.open_door(puzzle["door"])
        self.restoration_time = 4.0

    def heartbeat_value(self) -> float:
        return 0.5 + 0.5 * math.sin(self.flicker_phase * 1.5)

    def heartbeat_intensity(self) -> float:
        return 0.25

    def heartbeat_effective(self) -> float:
        return self.heartbeat_value() * self.heartbeat_intensity()

    # ------------------------------------------------------------------
    # Geometry & Structural Construction
    # ------------------------------------------------------------------

    def _build_walls(self) -> list[pygame.Rect]:
        """Creates perimeter boundaries and solid dividing walls between the 4 chambers."""
        W, H = L3_WORLD_WIDTH, L3_WORLD_HEIGHT
        return [
            # Outer perimeter boundaries (40px thick)
            pygame.Rect(0, 0, W, 40),          # North outer
            pygame.Rect(0, H - 40, W, 40),      # South outer
            pygame.Rect(0, 0, 40, H),          # West outer
            pygame.Rect(W - 40, 0, 40, H),      # East outer

            # Horizontal dividing wall (y: 1060..1140, 80px thick)
            # Left side (divides Chamber 1 & 2): x in [40..610] and [690..1260], gap at x=610..690 for Golden Door
            pygame.Rect(40, 1060, 570, 80),
            pygame.Rect(690, 1060, 570, 80),

            # Right side (divides Chamber 3 & 4): x in [1340..1910] and [1990..2560], gap at x=1910..1990 for Door 3
            pygame.Rect(1340, 1060, 570, 80),
            pygame.Rect(1990, 1060, 570, 80),

            # Vertical dividing wall (x: 1260..1340, 80px thick)
            # Top side (divides Chamber 2 & 3): y in [40..510] and [590..1060], gap at y=510..590 for Door 2
            pygame.Rect(1260, 40, 80, 470),
            pygame.Rect(1260, 590, 80, 470),

            # Central intersection block (y: 1060..1140, x: 1260..1340)
            pygame.Rect(1260, 1060, 80, 80),

            # Bottom side (completely solid divider between Chamber 1 & 4): y in [1140..2160]
            pygame.Rect(1260, 1140, 80, 1020),
        ]

    def _build_pillars(self) -> list[pygame.Rect]:
        """Decorative carved pillars supporting the high chamber ceilings."""
        pillar_positions = [
            # Chamber 1 (Entrance)
            (200, 1300), (1100, 1300), (200, 2000), (1100, 2000),
            # Chamber 2 (First Reflection)
            (200, 200), (1100, 200), (200, 900), (1100, 900),
            # Chamber 3 (Second Reflection)
            (1500, 200), (2400, 200), (1500, 900), (2400, 900),
            # Chamber 4 (Final Reflection)
            (1500, 1300), (2400, 1300), (1500, 2000), (2400, 2000),
        ]
        return [pygame.Rect(px - 24, py - 24, 48, 48) for px, py in pillar_positions]

    def _build_reflective_pools(self) -> list[pygame.Rect]:
        """Decorative dark polished reflective water pools in each chamber."""
        return [
            # Chamber 1
            pygame.Rect(450, 1500, 400, 90),
            # Chamber 2
            pygame.Rect(450, 750, 400, 80),
            # Chamber 3
            pygame.Rect(2120, 780, 260, 80),
            # Chamber 4
            pygame.Rect(2070, 1960, 260, 80),
        ]

    def _build_doors(self) -> dict[str, dict]:
        """Constructs the four doors governing chamber transitions."""
        return {
            "entrance_door": {
                "id": "entrance_door",
                "chamber": 1,
                "name": "Golden Entrance Door",
                "rect": pygame.Rect(610, 1060, 80, 80),
                "unlocked": False,
                "open": False,
                "style": "golden",
                "required_key": self.door_keys_config.get("entrance_door"),
                "key_turned": False,
            },
            "door_ch2_to_ch3": {
                "id": "door_ch2_to_ch3",
                "chamber": 2,
                "name": "First Reflection Chamber Door",
                "rect": pygame.Rect(1260, 510, 80, 80),
                "unlocked": False,
                "open": False,
                "style": "ancient_brown",
                "required_key": self.door_keys_config.get("door_ch2_to_ch3"),
                "key_turned": False,
            },
            "door_ch3_to_ch4": {
                "id": "door_ch3_to_ch4",
                "chamber": 3,
                "name": "Second Reflection Chamber Door",
                "rect": pygame.Rect(1910, 1060, 80, 80),
                "unlocked": False,
                "open": False,
                "style": "ancient_brown",
                "required_key": self.door_keys_config.get("door_ch3_to_ch4"),
                "key_turned": False,
            },
            "exit_door": {
                "id": "exit_door",
                "chamber": 4,
                "name": "Sanctum Exit Portal",
                "rect": pygame.Rect(1910, 2120, 80, 40),
                "unlocked": False,
                "open": False,
                "showing": False,
                "style": "ancient_brown",
                "required_key": self.door_keys_config.get("exit_door", None),
                "key_turned": False,
            },
        }

    def set_door_key(self, door_id: str, key_id: str | None):
        """Configures the key required for a specific door without changing door visuals."""
        self.door_keys_config[door_id] = key_id
        if door_id in self.doors:
            self.doors[door_id]["required_key"] = key_id

    def _build_sockets(self) -> list[dict]:
        """One, two, then three finite-face reflections; any carried frame fits."""
        return [
            # Chamber 2: 1 mirror placement position (Crystal South -> Mirror 1 East -> Door 2)
            {
                "id": "socket_ch2_1",
                "pos": (650.0, 550.0),
                "name": "Chamber 2 Socket",
                "dir": (1.0, 0.0),
                "required_mirror_id": None,
                "mirror": None,
                "placement_timer": 0.0,
                "placement_mirror_id": None,
            },
            # Chamber 3: 2 mirror placement positions spaced across the chamber circle circumference (R=240)
            {
                "id": "socket_ch3_1",
                "pos": (1940.0, 730.0),
                "name": "Chamber 3 West Socket",
                "dir": (2.0, 1.0),
                "required_mirror_id": None,
                "mirror": None,
                "placement_timer": 0.0,
                "placement_mirror_id": None,
            },
            {
                "id": "socket_ch3_2",
                "pos": (1940.0, 470.0),
                "name": "Chamber 3 East Socket",
                "dir": (1.0, 2.0),
                "required_mirror_id": None,
                "mirror": None,
                "placement_timer": 0.0,
                "placement_mirror_id": None,
            },
            # Chamber 4: 3 mirror placement positions forming an equilateral triangle along the R=240 floor circle
            {
                "id": "socket_ch4_1",
                "pos": (2180.0, 1820.0),
                "name": "Chamber 4 South-East Socket",
                "dir": (-1.0, -2.0),
                "required_mirror_id": None,
                "mirror": None,
                "placement_timer": 0.0,
                "placement_mirror_id": None,
            },
            {
                "id": "socket_ch4_2",
                "pos": (2180.0, 1480.0),
                "name": "Chamber 4 North Apex Socket",
                "dir": (2.0, 1.0),
                "required_mirror_id": None,
                "mirror": None,
                "placement_timer": 0.0,
                "placement_mirror_id": None,
            },
            {
                "id": "socket_ch4_3",
                "pos": (1860.0, 1480.0),
                "name": "Chamber 4 South-West Socket",
                "dir": (1.0, 2.0),
                "required_mirror_id": None,
                "mirror": None,
                "placement_timer": 0.0,
                "placement_mirror_id": None,
            },
        ]

    def _build_player_mirrors(self) -> list[Mirror]:
        """Binds directly to the player's refractor mirrors carried from existing inventory."""
        mirror_names = {
            "mirror_red": "Crimson Refractor Mirror",
            "mirror_blue": "Azure Refractor Mirror",
            "mirror_green": "Verdant Refractor Mirror",
        }
        if self.inventory is not None:
            source_ids = list(self.inventory.mirrors)
        else:
            source_ids = []

        mirrors = []
        for mid in source_ids:
            name = mirror_names.get(mid, f"Refractor Mirror ({mid})")
            m = Mirror(
                mirror_id=mid,
                socket_id="",
                x=0.0,
                y=0.0,
                orientation=0,
                name=name,
                is_trial=False,
            )
            m.placed = False
            m.NUM_ORIENTATIONS = 4
            mirrors.append(m)
        return mirrors

    def is_blue_active(self, lantern) -> bool:
        """Returns True if the Blue Light reveal mode is currently active."""
        return is_blue_light_active(lantern)

    def is_red_active(self, lantern) -> bool:
        """Returns True if the Red Light mode is currently active."""
        return is_red_light_active(lantern)

    def is_green_active(self, lantern) -> bool:
        """Returns True if the Green Light mode is currently active."""
        return is_green_light_active(lantern)

    def toggle_blue_light(self, lantern):
        """Toggles Blue Light reveal mode on the player's lantern."""
        if lantern is None:
            return
        if is_blue_light_active(lantern):
            lantern.set_color("white")
            self._toast("Blue Light deactivated.", 2.0)
        else:
            if self.battery.is_depleted:
                self._toast("Lantern battery depleted! Step into a chamber to reset.", 2.5)
                return
            lantern.active = True
            lantern.set_color("blue")
            self._toast("Blue Light active — Chamber 2 resonance awakened.", 2.5)

    def toggle_red_light(self, lantern):
        """Toggles Red Light mode on the player's lantern."""
        if lantern is None:
            return
        if is_red_light_active(lantern):
            lantern.set_color("white")
            self._toast("Red Light deactivated.", 2.0)
        else:
            if self.battery.is_depleted:
                self._toast("Lantern battery depleted! Step into a chamber to reset.", 2.5)
                return
            lantern.active = True
            lantern.set_color("red")
            self._toast("Red Light active — Chamber 3 resonance awakened.", 2.5)

    def toggle_green_light(self, lantern):
        """Toggles Green Light mode on the player's lantern."""
        if lantern is None:
            return
        if is_green_light_active(lantern):
            lantern.set_color("white")
            self._toast("Green Light deactivated.", 2.0)
        else:
            if self.battery.is_depleted:
                self._toast("Lantern battery depleted! Step into a chamber to reset.", 2.5)
                return
            lantern.active = True
            lantern.set_color("green")
            self._toast("Green Light active — Chamber 4 resonance awakened.", 2.5)

    def _build_player_crystals(self) -> list[SourceCrystal]:
        """Creates the 3 light-source crystals (Ch2 Blue, Ch3 Red, Ch4 Green)."""
        return [
            SourceCrystal("crystal_ch2", x=650.0, y=320.0, beam_dir=(0.0, 1.0), name="First Reflection Crystal", color="blue"),
            SourceCrystal("crystal_ch3", x=1690.0, y=730.0, beam_dir=(1.0, 0.0), name="Second Reflection Crystal", color="red"),
            SourceCrystal("crystal_ch4", x=1720.0, y=1820.0, beam_dir=(1.0, 0.0), name="Final Reflection Crystal", color="green"),
        ]

    def _init_golden_door_particles(self):
        """Initialises gentle floating firefly/sparkle particles for the Golden Entrance Door."""
        self.golden_door_particles = []
        dr = self.doors["entrance_door"]["rect"]
        for _ in range(18):
            bx = random.uniform(dr.x - 8, dr.right + 8)
            by = random.uniform(dr.y - 8, dr.bottom + 8)
            self.golden_door_particles.append({
                "x": bx,
                "y": by,
                "base_x": bx,
                "base_y": by,
                "phase": random.uniform(0, math.pi * 2),
                "speed": random.uniform(1.0, 2.0),
                "size": random.choice([2, 3]),
                "color": random.choice([(255, 220, 110), (255, 240, 160), (220, 180, 70), (255, 195, 75)]),
            })

    # ------------------------------------------------------------------
    # Door State Management
    # ------------------------------------------------------------------

    def unlock_door(self, door_id: str) -> bool:
        """Unlocks the specified door."""
        door = self.doors.get(door_id)
        if door:
            door["unlocked"] = True
            return True
        return False

    def open_door(self, door_id: str) -> bool:
        """Opens the door and removes its collision rectangle from all_obstacles."""
        door = self.doors.get(door_id)
        if door:
            door["open"] = True
            if door["rect"] in self.all_obstacles:
                self.all_obstacles.remove(door["rect"])
            return True
        return False

    def close_door(self, door_id: str) -> bool:
        """Closes the door and re-adds its collision rectangle to all_obstacles."""
        door = self.doors.get(door_id)
        if door:
            door["open"] = False
            if door["rect"] not in self.all_obstacles:
                self.all_obstacles.append(door["rect"])
            return True
        return False

    def is_door_open(self, door_id: str) -> bool:
        """Returns whether the specified door is open."""
        door = self.doors.get(door_id)
        return door.get("open", False) if door else False

    # ------------------------------------------------------------------
    # Floor Rendering (Grand Ancient Temple Aesthetics)
    # ------------------------------------------------------------------

    def _render_static_floor(self) -> pygame.Surface:
        """Pre-renders ancient worn temple flagstone floors with grand carved discs in each chamber."""
        W, H = L3_WORLD_WIDTH, L3_WORLD_HEIGHT
        surf = pygame.Surface((W, H))
        surf.fill(_FLOOR_BASE)

        tile_w = 48
        tile_h = 36

        # 1. Ashlar flagstone grid with offset rows across the whole temple
        for y in range(0, H, tile_h):
            row = y // tile_h
            offset = (tile_w // 2) if (row % 2 == 1) else 0
            for x in range(-tile_w + offset, W, tile_w):
                shade = ((x // tile_w) * 7 + row * 13) % 4
                if shade == 0:
                    c = (16, 13, 22)
                elif shade == 1:
                    c = (20, 16, 28)
                elif shade == 2:
                    c = (14, 11, 20)
                else:
                    c = (24, 19, 32)

                tr = pygame.Rect(x + 1, y + 1, tile_w - 2, tile_h - 2)
                pygame.draw.rect(surf, c, tr)
                pygame.draw.rect(surf, (8, 6, 12), tr, width=1)
                # Baked bevels and chips add stone detail without changing collision.
                pygame.draw.line(surf, tuple(v + 7 for v in c),
                                 (tr.left + 2, tr.top + 2), (tr.right - 3, tr.top + 2))
                if (row * 7 + x // tile_w) % 9 == 0:
                    pygame.draw.lines(surf, (10, 8, 15), False,
                                      [(tr.x + 12, tr.y + 2), (tr.x + 17, tr.y + 11),
                                       (tr.x + 14, tr.y + 18)], 1)

        # Galleries share the original stonework; only the finale has a circular dais.
        for rect in (pygame.Rect(440,1230,420,750), pygame.Rect(510,270,510,430),
                     pygame.Rect(1600,370,460,470)):
            pygame.draw.rect(surf, (31,27,37), rect)
            for inset in (0,8,22):
                pygame.draw.rect(surf, (87,72,48), rect.inflate(-inset*2,-inset*2), 1)
            for y in range(rect.top+45,rect.bottom-20,52):
                pygame.draw.line(surf,(45,38,48),(rect.left+24,y),(rect.right-24,y),2)
            for x,y in (rect.topleft,rect.topright,rect.bottomleft,rect.bottomright):
                pygame.draw.polygon(surf,(136,110,62),[(x,y-8),(x+8,y),(x,y+8),(x-8,y)],1)
        # Worn directional inlays lead the entrance gallery toward the mural.
        for y in range(1310,1940,115):
            pygame.draw.lines(surf,(121,102,64),False,[(632,y+8),(650,y-8),(668,y+8)],2)
            pygame.draw.line(surf,(76,64,47),(650,y-8),(650,y+31),1)
        chamber_centers = [(1950,1650)]

        c_rad = 360
        rings = [
            (355, (18, 15, 25)),
            (305, (24, 20, 32)),
            (255, (20, 17, 28)),
            (195, (26, 22, 36)),
            (135, (22, 18, 30)),
            (80,  (28, 23, 38)),
        ]

        for cx, cy in chamber_centers:
            # Outer carved granite rim
            pygame.draw.circle(surf, (32, 26, 40), (cx, cy), c_rad + 6, width=6)
            pygame.draw.circle(surf, (60, 48, 72), (cx, cy), c_rad + 2, width=2)
            pygame.draw.circle(surf, (140, 110, 50), (cx, cy), c_rad, width=1)
            for i in range(32):
                angle = math.tau * i / 32
                a = (cx + int(358 * math.cos(angle)), cy + int(358 * math.sin(angle)))
                b = (cx + int(367 * math.cos(angle)), cy + int(367 * math.sin(angle)))
                pygame.draw.line(surf, (17, 14, 23), a, b, 2)

            for r_val, r_col in rings:
                pygame.draw.circle(surf, r_col, (cx, cy), r_val)
                pygame.draw.circle(surf, (12, 10, 16), (cx, cy), r_val, width=1)
                pygame.draw.circle(surf, (48, 38, 60), (cx, cy), r_val - 2, width=1)

            # Radial astrological alignment seams
            for i in range(16):
                ang = (2.0 * math.pi * i) / 16.0
                x1 = cx + int(60 * math.cos(ang))
                y1 = cy + int(60 * math.sin(ang))
                x2 = cx + int(350 * math.cos(ang))
                y2 = cy + int(350 * math.sin(ang))
                pygame.draw.line(surf, (14, 11, 20), (x1, y1), (x2, y2), 1)

            # 8 primary sacred rays with subtle inlaid bronze/gold trim
            for i in range(8):
                ang = (2.0 * math.pi * i) / 8.0
                x1 = cx + int(60 * math.cos(ang))
                y1 = cy + int(60 * math.sin(ang))
                x2 = cx + int(350 * math.cos(ang))
                y2 = cy + int(350 * math.sin(ang))
                pygame.draw.line(surf, (62, 50, 75), (x1, y1), (x2, y2), 2)
                pygame.draw.line(surf, (115, 90, 45), (x1, y1), (x2, y2), 1)

            # Celestial sigils carved at r=240
            for i in range(8):
                ang = (2.0 * math.pi * i) / 8.0 + (math.pi / 8.0)
                gx = cx + int(240 * math.cos(ang))
                gy = cy + int(240 * math.sin(ang))
                pygame.draw.circle(surf, (55, 45, 68), (gx, gy), 8, width=1)
                pygame.draw.circle(surf, (85, 70, 40), (gx, gy), 3, width=1)

        # 3. Architectural Socket Mountings in Floor Stone
        for sock in self.sockets:
            sx, sy = int(sock["pos"][0]), int(sock["pos"][1])
            pygame.draw.circle(surf, (36, 30, 45), (sx, sy), 38)
            pygame.draw.circle(surf, (80, 68, 95), (sx, sy), 38, width=2)
            pygame.draw.circle(surf, (150, 120, 60), (sx, sy), 34, width=1)
            pygame.draw.circle(surf, (22, 18, 28), (sx, sy), 26)

        # 4. Reclaimed Ancient Temple Ground Flora (Static Pass)
        self._render_static_ground_flora(surf)

        return surf

    def _build_ancient_trees(self) -> list[dict]:
        """Returns elevated tree data for all chambers with generous wall and puzzle clearance."""
        return [
            # Chamber 1: Entrance Forecourt
            {"type": "lush", "x": 250, "y": 1460, "scale": 1.25},
            {"type": "broken", "x": 340, "y": 1940, "scale": 1.15},
            # Chamber 2: First Reflection Chamber
            {"type": "lush", "x": 260, "y": 320, "scale": 1.15},
            {"type": "broken", "x": 1080, "y": 840, "scale": 1.1},
            # Chamber 3: Second Reflection Chamber
            {"type": "broken", "x": 2360, "y": 280, "scale": 1.25},
            {"type": "lush", "x": 1520, "y": 360, "scale": 1.15},
            # Chamber 4: Final Sanctum
            {"type": "lush", "x": 2380, "y": 1460, "scale": 1.35},
            {"type": "broken", "x": 1520, "y": 1540, "scale": 1.2},
        ]

    def _render_static_ground_flora(self, surf: pygame.Surface):
        """Pre-renders static ground flora (rocks, grass clusters, mushrooms, fallen logs, stone debris) across all 4 chambers."""
        # --------------------------------------------------------------
        # Chamber 1: Reclaimed Forecourt & Sanctuary Pool
        # --------------------------------------------------------------
        _draw_rock_grass_cluster(surf, 210, 1490, scale=1.3)
        _draw_mushrooms(surf, 280, 1490, scale=1.2, count=3)
        _draw_rock_grass_cluster(surf, 320, 1960, scale=1.2)
        _draw_mushrooms(surf, 380, 1940, scale=1.1, count=4)
        _draw_fallen_log(surf, 360, 1980, length=54, angle_deg=-20)
        _draw_rock_grass_cluster(surf, 180, 1260, scale=1.1)
        _draw_mushrooms(surf, 220, 1240, scale=1.0, count=2)
        _draw_ancient_stone_debris(surf, 240, 1280)
        # Pool Banks (around (650, 1650))
        _draw_rock_grass_cluster(surf, 430, 1480, scale=1.1)
        _draw_mushrooms(surf, 430, 1510, scale=1.0, count=2)
        _draw_rock_grass_cluster(surf, 870, 1480, scale=1.1)
        _draw_mushrooms(surf, 870, 1510, scale=1.0, count=2)
        # Headstone Environs (around (740, 1190))
        _draw_rock_grass_cluster(surf, 800, 1210, scale=1.1)
        _draw_mushrooms(surf, 825, 1205, scale=1.0, count=3)
        _draw_ancient_stone_debris(surf, 680, 1215)

        # --------------------------------------------------------------
        # Chamber 2: First Reflection Chamber (Perimeter Overgrowth)
        # --------------------------------------------------------------
        _draw_rock_grass_cluster(surf, 220, 350, scale=1.2)
        _draw_mushrooms(surf, 290, 350, scale=1.1, count=3)
        _draw_fallen_log(surf, 220, 800, length=56, angle_deg=25)
        _draw_rock_grass_cluster(surf, 190, 810, scale=1.2)
        _draw_mushrooms(surf, 250, 785, scale=1.0, count=3)
        _draw_ancient_stone_debris(surf, 280, 820)
        _draw_rock_grass_cluster(surf, 1060, 860, scale=1.2)
        _draw_mushrooms(surf, 1110, 840, scale=1.1, count=3)
        _draw_rock_grass_cluster(surf, 1080, 260, scale=1.1)
        _draw_ancient_stone_debris(surf, 1050, 290)

        # --------------------------------------------------------------
        # Chamber 3: Second Reflection Chamber (Ruins & Deadwood)
        # --------------------------------------------------------------
        _draw_rock_grass_cluster(surf, 2330, 310, scale=1.3)
        _draw_mushrooms(surf, 2400, 290, scale=1.2, count=4)
        _draw_rock_grass_cluster(surf, 1480, 390, scale=1.2)
        _draw_mushrooms(surf, 1550, 380, scale=1.1, count=3)
        _draw_fallen_log(surf, 2350, 820, length=60, angle_deg=-30)
        _draw_rock_grass_cluster(surf, 2380, 830, scale=1.2)
        _draw_mushrooms(surf, 2310, 810, scale=1.0, count=3)
        _draw_ancient_stone_debris(surf, 2340, 850)
        _draw_rock_grass_cluster(surf, 1950, 200, scale=1.1)
        _draw_ancient_stone_debris(surf, 1910, 220)

        # --------------------------------------------------------------
        # Chamber 4: Final Sanctum & Exit Portal
        # --------------------------------------------------------------
        _draw_rock_grass_cluster(surf, 2340, 1500, scale=1.4)
        _draw_mushrooms(surf, 2420, 1480, scale=1.3, count=4)
        _draw_ancient_stone_debris(surf, 2320, 1450)
        _draw_rock_grass_cluster(surf, 1480, 1570, scale=1.2)
        _draw_mushrooms(surf, 1550, 1550, scale=1.1, count=3)
        _draw_fallen_log(surf, 1520, 1600, length=50, angle_deg=35)
        _draw_rock_grass_cluster(surf, 1500, 1260, scale=1.2)
        _draw_mushrooms(surf, 1540, 1240, scale=1.0, count=2)
        _draw_fallen_log(surf, 2380, 1260, length=56, angle_deg=-15)
        _draw_rock_grass_cluster(surf, 2410, 1280, scale=1.1)
        _draw_mushrooms(surf, 2350, 1250, scale=1.0, count=3)
        # Flanking Exit Portal at South (x=1950, y=2160)
        _draw_rock_grass_cluster(surf, 1780, 2110, scale=1.1)
        _draw_mushrooms(surf, 1750, 2110, scale=0.9, count=2)
        _draw_rock_grass_cluster(surf, 2120, 2110, scale=1.1)
        _draw_mushrooms(surf, 2150, 2110, scale=0.9, count=2)

    def _draw_trees_and_canopies(self, surface: pygame.Surface, camera_offset: tuple[int, int], vp: pygame.Rect):
        """Renders elevated ancient temple trees and billowing canopies with viewport culling."""
        cam_x, cam_y = camera_offset
        for tree in self.ancient_trees:
            tx = tree["x"]
            ty = tree["y"]
            scale = tree["scale"]
            ttype = tree["type"]
            tree_bounds = pygame.Rect(tx - int(120 * scale), ty - int(200 * scale), int(240 * scale), int(240 * scale))
            if not vp.colliderect(tree_bounds):
                continue
            sx = int(tx - cam_x)
            sy = int(ty - cam_y)
            if ttype == "lush":
                _draw_ancient_tree(surface, sx, sy, scale=scale)
            else:
                _draw_broken_trunk(surface, sx, sy, scale=scale)

    # ------------------------------------------------------------------
    # Chamber Progression & Energy Tracking
    # ------------------------------------------------------------------

    def _detect_chamber(self, px: float, py: float) -> int:
        """Determines chamber ID (1-4) based on coordinates in Level 3."""
        if px < 1300:
            return 1 if py >= 1100 else 2
        else:
            return 3 if py < 1100 else 4

    def _update_chamber(self, player, lantern):
        detected = self._detect_chamber(*player.center)
        if detected != self.current_chamber:
            self.current_chamber = detected
            names = {1: "Entrance Gallery", 2: "The Guiding Ray", 3: "The Returning Light", 4: "Chamber of Convergence"}
            self._toast(names[detected] + " — stable light", 2.5)

    # ------------------------------------------------------------------
    # Update Loop
    # ------------------------------------------------------------------

    def update(self, player, lantern, dt: float):
        if self.paused or self.help_open or self.active_clue:
            return
        self.flicker_phase += 0 if self.reduced_motion else dt
        self._update_chamber(player, lantern)
        self.toast_timer = max(0, self.toast_timer - dt)
        if self.toast_timer == 0: self.toast_msg = ""
        dx, dy = (0, 0) if self.focused_socket else player.get_input_vector()
        move_with_collision(player, dx, dy, self.all_obstacles, dt)
        player.update_animation(bool(dx or dy), dt)
        for p in self.golden_door_particles:
            if not self.reduced_motion: p["phase"] += dt * p["speed"]
            p["x"] = p["base_x"] + math.sin(p["phase"] * 1.5) * 8
            p["y"] = p["base_y"] + math.cos(p["phase"] * 1.1) * 6
        for p in self.placement_particles:
            p["life"] -= dt
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
        self.placement_particles = [p for p in self.placement_particles if p["life"] > 0][:48]
        self.beam_segments = []
        for index, puzzle in enumerate(self.puzzles):
            crystal = self.player_crystals[index]
            if not crystal.active: continue
            chain = trace_source((crystal.x, crystal.y), crystal.beam_dir, crystal.color,
                                 self.all_mirrors, self.all_obstacles, puzzle["receiver"])
            self.beam_segments.extend(chain)
            previous = "entrance_door" if index == 0 else self.puzzles[index - 1]["door"]
            mirrors_hit = {seg.hit_object.id for seg in chain if seg.termination_type == "mirror"}
            hit = bool(chain and chain[-1].termination_type == "receiver" and
                       len(mirrors_hit) == puzzle["count"] and self.doors[previous]["open"])
            if not puzzle["solved"]:
                puzzle["hold"] = min(1.25, puzzle["hold"] + dt) if hit else 0.0
                if puzzle["hold"] >= 1.25:
                    puzzle["solved"] = crystal.charged = True
                    self.unlock_door(puzzle["door"])
                    self.open_door(puzzle["door"])
                    audio.play("door_open")
                    self._toast("The receiver wakes. Collect its crystal, then retrieve your mirrors with X.", 4.0)
                    self.save_checkpoint(player, lantern)
        if all(p["solved"] for p in self.puzzles):
            self.restoration_time = 4.0 if self.reduced_motion else min(4.0, self.restoration_time + dt)

    def handle_rotate_mirror(self, player, direction: int) -> bool:
        sock = next((s for s in self.sockets if s["id"] == self.focused_socket), None)
        if not sock or sock["mirror"] is None: return False
        sock["mirror"].rotate(direction)
        self._toast("A/D turn the face · E finish · X retrieve", 2.0)
        return True

    def _toast(self, text: str, duration: float = 3.0):
        self.toast_msg = text
        self.toast_timer = duration

    # ------------------------------------------------------------------
    # Interaction Handling
    # ------------------------------------------------------------------

    def handle_interact(self, player, lantern, inventory=None) -> bool:
        inv = self.inventory if inventory is None else inventory
        if self.focused_socket:
            self.focused_socket = None
            self.save_checkpoint(player, lantern)
            return True
        for puzzle in self.puzzles:
            if puzzle["solved"] and math.dist(player.center, puzzle["reward"]) < 66:
                if inv and inv.add_crystal(puzzle["reward_id"]):
                    audio.play("pickup")
                    self._toast(puzzle["color"].title() + " resonance crystal collected.")
                    self.save_checkpoint(player, lantern)
                else: self._toast("This crystal is already in your inventory.")
                return True
        if player.rect.colliderect(self.headstone.rect.inflate(44, 44)):
            if self.mural is None: self.mural = Mural()
            self.active_clue = {"kind": "mural", "title": "The Faded Mural", "text": "Light once guided our people."}
            return True
        entrance = self.doors["entrance_door"]
        if player.rect.colliderect(entrance["rect"].inflate(44, 44)):
            required = entrance.get("required_key")
            if required and not (inv and inv.has_key(required)):
                self._toast("This configured threshold needs " + KEY_NAMES.get(required, required))
                return True
            entrance["key_turned"] = True
            self.unlock_door("entrance_door")
            self.open_door("entrance_door")
            self._toast("The gallery opens. Match blue light [B], then E at the source.", 4)
            self.save_checkpoint(player, lantern)
            return True
        if player.rect.colliderect(self.exit_door["rect"].inflate(44, 44)):
            if all(p["solved"] and inv and inv.has_crystal(p["reward_id"]) for p in self.puzzles):
                if self.restoration_time >= 4:
                    self.trigger_level4_transition = True
                    self.save_checkpoint(player, lantern)
                else: self._toast("The rings are turning. Space skips the restoration.")
            else: self._toast("Restore three receivers and collect all three crystals before leaving.")
            return True
        nearby = [s for s in self.sockets if math.dist(player.center, s["pos"]) < 68]
        if nearby:
            sock = min(nearby, key=lambda s: math.dist(player.center, s["pos"]))
            if sock["mirror"] is None:
                available = [m for m in self.player_mirrors if not m.placed and (inv is None or inv.has_mirror(m.id))]
                selected = getattr(inv, "selected_mirror_id", None)
                mirror = next((m for m in available if m.id == selected), available[0] if available else None)
                if mirror is None:
                    self._toast("Retrieve a placed mirror with X. Solved receivers stay awake.")
                    return True
                self.install_mirror(mirror.id, sock["id"])
                if inv: inv.clear_selected_mirror()
                audio.play("pickup")
            self.focused_socket = sock["id"]
            self._toast("A/D rotate · X retrieve · E/Esc leave focus. Every mirror works alike.", 4)
            return True
        for crystal in self.player_crystals:
            if math.dist(player.center, (crystal.x, crystal.y)) < 82:
                if not is_light_active(lantern, crystal.color):
                    self._toast("Select " + crystal.color.upper() + " [" + crystal.color[0].upper() + "] and press E to wake this source.")
                else:
                    crystal.active = True
                    self._toast("Guide this beam to the diamond receiver. Frame color does not change light.", 4)
                    self.save_checkpoint(player, lantern)
                return True
        self._toast("E at a source, mirror stand, mural, crystal cradle or doorway.")
        return False

    def handle_retrieve_mirror(self, player) -> bool:
        for sock in self.sockets:
            if sock["mirror"] and (sock["id"] == self.focused_socket or math.dist(player.center, sock["pos"]) < 68):
                self.uninstall_mirror(sock["id"])
                self.focused_socket = None
                self._toast("Mirror returned to your inventory. The solved receiver stays awake.")
                return True
        return False

    def _resolve_socket_id(self, socket_id: str) -> str:
        aliases = {
            "socket_1": "socket_ch2_1",
            "socket_2": "socket_ch3_1",
            "socket_3": "socket_ch3_2",
        }
        return aliases.get(socket_id, socket_id)

    def install_mirror(self, mirror_id: str, socket_id: str) -> bool:
        """Installs a player mirror into the specified socket."""
        target_id = self._resolve_socket_id(socket_id)
        sock = next((s for s in self.sockets if s["id"] == target_id), None)
        mirror = next((m for m in self.player_mirrors if m.id == mirror_id), None)
        if not sock or not mirror:
            return False
        if sock["mirror"] is not None and sock["mirror"] is not mirror:
            sock["mirror"].placed = False
            sock["mirror"].socket_id = ""
        for s in self.sockets:
            if s["mirror"] is mirror and s is not sock:
                s["mirror"] = None
                s["placement_timer"] = 0.0
                s["placement_mirror_id"] = None
        mirror.placed = True
        mirror.socket_id = target_id
        mirror.x, mirror.y = sock["pos"]
        sock["mirror"] = mirror
        sock["placement_timer"] = 0.0
        sock["placement_mirror_id"] = None
        return True

    def uninstall_mirror(self, socket_id: str) -> bool:
        """Uninstalls any mirror currently inside the specified socket."""
        target_id = self._resolve_socket_id(socket_id)
        sock = next((s for s in self.sockets if s["id"] == target_id), None)
        if not sock or sock["mirror"] is None:
            return False
        m = sock["mirror"]
        m.placed = False
        m.socket_id = ""
        sock["mirror"] = None
        sock["placement_timer"] = 0.0
        sock["placement_mirror_id"] = None
        return True

    def dismiss_exit_door_modal(self):
        self.exit_door["showing"] = False

    def dismiss_clue_modal(self):
        self.active_clue = None

    # ------------------------------------------------------------------
    # Drawing Pipeline
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: pygame.Surface,
        player,
        lantern,
        camera_offset: tuple[int, int] = (0, 0),
        debug_overlay: bool = False,
    ):
        sw, sh = L3_SCREEN_WIDTH, L3_SCREEN_HEIGHT
        vp = pygame.Rect(camera_offset[0], camera_offset[1], sw, sh)

        # 1. Flagstone Floor
        surface.blit(self.floor_surf, (-camera_offset[0], -camera_offset[1]))

        # 2. Reflective Pools
        self._draw_reflective_pools(surface, camera_offset, vp)

        # 2.5 Ancient Temple Trees & Billowing Foliage Canopies
        self._draw_trees_and_canopies(surface, camera_offset, vp)

        # Code-drawn lantern posts retain the warm temple palette.
        for wx in (425,875):
            for wy in (1330,1600,1870):
                x,y=wx-camera_offset[0],wy-camera_offset[1]
                if -50<x<850 and -70<y<670:
                    glow=pygame.Surface((100,100),pygame.SRCALPHA)
                    for radius,alpha in ((45,9),(30,15),(18,24)):
                        pygame.draw.circle(glow,(250,180,64,alpha),(50,50),radius)
                    surface.blit(glow,(x-50,y-74))
                    pygame.draw.ellipse(surface,(65,52,43),(x-15,y+12,30,10))
                    pygame.draw.line(surface,(137,106,59),(x,y+15),(x,y-20),4)
                    pygame.draw.polygon(surface,(89,65,39),[(x-13,y-22),(x-10,y-48),(x,y-59),(x+10,y-48),(x+13,y-22)])
                    pygame.draw.polygon(surface,(241,190,85),[(x-7,y-25),(x-7,y-44),(x+7,y-44),(x+7,y-25)])
                    pygame.draw.line(surface,(126,88,36),(x,y-47),(x,y-22),2)

        # 3. Obstacles (Dividing Walls, Pillars, and Chamber 1 Mossy Headstone)
        self._draw_obstacles(surface, camera_offset, vp)
        self.headstone.draw(surface, camera_offset)
        if player.rect.colliderect(self.headstone.rect.inflate(90,90)):
            label=pygame.font.SysFont("consolas",13).render("E examine the faded mural",True,(235,211,159))
            surface.blit(label,(self.headstone.rect.centerx-camera_offset[0]-label.get_width()//2,self.headstone.rect.bottom-camera_offset[1]+12))

        # 4. Doors (Golden Entrance Door and Ancient Brown Internal Doors)
        self._draw_doors(surface, player, camera_offset, vp)

        is_blue = self.is_blue_active(lantern)

        # 5. Sockets & Placed Mirrors
        self._draw_sockets_and_mirrors(surface, player, camera_offset, vp, is_blue=is_blue)

        # 6. Light-Source Crystals
        self._draw_crystals(surface, player, camera_offset, vp, is_blue=is_blue, lantern=lantern)

        # 7. Light Beams
        self._draw_beams(surface, camera_offset, vp)

        self._draw_receivers(surface, camera_offset)

        # 8. Player
        player.draw(surface, camera_offset=camera_offset, is_lantern_lit=False)

        # 9. Chamber Ambient Lighting Mask
        cam_x, cam_y = camera_offset
        l_color = getattr(lantern, "color", "white") if (lantern and getattr(lantern, "active", False)) else "dormant"

        beam_screen_segs = [
            ((seg.start[0] - cam_x, seg.start[1] - cam_y),
             (seg.end[0] - cam_x, seg.end[1] - cam_y),
             "blue" if getattr(seg, "color", "cyan") == "cyan" else getattr(seg, "color", "blue"))
            for seg in self.beam_segments
        ]

        ch2_col = "blue" if l_color == "blue" else "white"
        ch3_col = "red" if l_color == "red" else "white"
        ch4_col = "green" if l_color == "green" else "white"

        ch2_rad = 560 if l_color == "blue" else 280
        ch3_rad = 560 if l_color == "red" else 280
        ch4_rad = 560 if l_color == "green" else 280

        chamber_lights = [
            (int(650 - cam_x), int(1650 - cam_y), 520, "white"),   # Chamber 1
            (int(650 - cam_x), int(550 - cam_y), ch2_rad, ch2_col), # Chamber 2
            (int(1950 - cam_x), int(550 - cam_y), ch3_rad, ch3_col),# Chamber 3
            (int(1950 - cam_x), int(1650 - cam_y), ch4_rad, ch4_col),# Chamber 4
        ]
        d_alpha = int(135 - 65 * self.restoration_time / 4)

        p_screen = (int(player.rect.centerx - cam_x), int(player.rect.centery - cam_y))
        darkness_mask = build_level3_darkness_mask(
            size=(sw, sh),
            player_screen_pos=p_screen,
            lantern_radius=120.0,
            sun_core_screen_pos=(int(650 - cam_x), int(550 - cam_y)),
            sun_core_radius=0.0,
            beam_screen_segments=beam_screen_segs,
            darkness_alpha=d_alpha,
            flicker_offset=math.sin(self.flicker_phase * 2.5) * 6.0,
            chamber_lights=chamber_lights,
        )
        surface.blit(darkness_mask, (0, 0))

        # 10. Placement particles
        for p in self.placement_particles:
            px = int(p["x"] - camera_offset[0])
            py = int(p["y"] - camera_offset[1])
            if 0 <= px <= sw and 0 <= py <= sh:
                pygame.draw.circle(surface, p["color"], (px, py), 2)

        # 11. Exit Modal
        if self.exit_door.get("showing", False):
            self._draw_exit_modal(surface)

        # 12. Clue Modal (Headstone / ancient inscriptions)
        if self.active_clue:
            self._draw_clue_modal(surface)

    def _draw_reflective_pools(self, surface, camera_offset, vp):
        for pool in self.reflective_pools:
            if not vp.colliderect(pool.inflate(20, 20)):
                continue
            pr = pool.move(-camera_offset[0], -camera_offset[1])
            pygame.draw.rect(surface, _POOL_RIM, pr.inflate(8, 8), border_radius=4)
            pygame.draw.rect(surface, _POOL_WATER, pr, border_radius=3)
            sheen_y = pr.y + int(pr.height * 0.45 + math.sin(self.flicker_phase * 1.5) * 4)
            pygame.draw.line(surface, (45, 65, 95), (pr.x + 8, sheen_y), (pr.right - 8, sheen_y), 1)
            pygame.draw.rect(surface, (58, 57, 70), pr.inflate(8, 8), 1, border_radius=4)
            for i in range(3):
                ry = pr.y + 8 + i * max(5, (pr.height - 16) // 3)
                rx = pr.x + 12 + int(math.sin(self.flicker_phase + i * 1.7) * 3)
                pygame.draw.line(surface, (35, 48, 72), (rx, ry),
                                 (min(pr.right - 6, rx + max(5, pr.width // 3)), ry), 1)

    def _draw_obstacles(self, surface, camera_offset, vp):
        """Draws ancient carved stone dividing walls and pillars."""
        for wall in self.walls:
            if not vp.colliderect(wall.inflate(10, 10)):
                continue
            wr = wall.move(-camera_offset[0], -camera_offset[1])
            pygame.draw.rect(surface, _WALL_COLOR, wr)
            pygame.draw.rect(surface, _WALL_STONE, wr.inflate(-2, -2))
            pygame.draw.rect(surface, _WALL_HIGHLIGHT, wr, width=1)
            # Mortar follows the existing wall footprint; no new obstacles.
            for wy in range(wall.top + 20, wall.bottom, 20):
                sy = wy - camera_offset[1]
                if 0 <= sy < surface.get_height():
                    pygame.draw.line(surface, (22, 18, 30), (wr.left + 2, sy), (wr.right - 3, sy))
                    for wx in range(wall.left + (20 if wy // 20 % 2 else 40), wall.right, 40):
                        sx = wx - camera_offset[0]
                        if 0 <= sx < surface.get_width():
                            pygame.draw.line(surface, (22, 18, 30), (sx, sy - 17), (sx, sy - 1))

        for pillar in self.pillars:
            if not vp.colliderect(pillar.inflate(10, 10)):
                continue
            pr = pillar.move(-camera_offset[0], -camera_offset[1])
            pygame.draw.rect(surface, (28, 22, 36), pr.inflate(4, 4), border_radius=4)
            pygame.draw.rect(surface, (48, 40, 60), pr, border_radius=3)
            pygame.draw.rect(surface, (70, 58, 85), pr, width=2, border_radius=3)
            pygame.draw.circle(surface, (90, 75, 105), pr.center, 6, width=1)
            for px in (pr.left + 6, pr.right - 7):
                pygame.draw.line(surface, (62, 51, 73), (px, pr.top + 5), (px, pr.bottom - 6))
            pygame.draw.line(surface, (90, 75, 105),
                             (pr.left + 3, pr.top + 3), (pr.right - 4, pr.top + 3))

    def _draw_doors(self, surface, player, camera_offset, vp):
        """Renders the distinct Golden Entrance Door and the ancient brown internal doors."""
        if not pygame.font.get_init():
            pygame.font.init()
        font_prompt = pygame.font.SysFont("consolas", 11, bold=True)
        inv = getattr(self, "inventory", None)

        for door_id, door in self.doors.items():
            dr = door["rect"]
            if not vp.colliderect(dr.inflate(40, 40)):
                continue
            mr = dr.move(-camera_offset[0], -camera_offset[1])

            if door.get("style") == "golden":
                # === GOLDEN ENTRANCE DOOR ===
                # Heavy ancient gold architrave
                pygame.draw.rect(surface, (140, 110, 45), mr.inflate(12, 12), border_radius=6)
                pygame.draw.rect(surface, (215, 175, 55), mr.inflate(6, 6), width=3, border_radius=5)
                pygame.draw.rect(surface, (255, 225, 110), mr, width=2, border_radius=4)

                if not door["open"]:
                    # Sealed golden door leaves
                    pygame.draw.rect(surface, (95, 75, 30), mr, border_radius=3)
                    # Astrological celestial runes & central seal
                    pygame.draw.circle(surface, (235, 195, 70), mr.center, 16, width=2)
                    pygame.draw.polygon(surface, (255, 220, 100), [
                        (mr.centerx, mr.centery - 12),
                        (mr.centerx + 12, mr.centery),
                        (mr.centerx, mr.centery + 12),
                        (mr.centerx - 12, mr.centery),
                    ], width=1)
                    # Radiant golden ambient pulse
                    glow_surf = pygame.Surface((mr.width + 28, mr.height + 28), pygame.SRCALPHA)
                    alpha_glow = int(35 + 15 * math.sin(self.flicker_phase * 2.0))
                    pygame.draw.rect(glow_surf, (255, 215, 80, alpha_glow), (0, 0, mr.width + 28, mr.height + 28), border_radius=8)
                    surface.blit(glow_surf, (mr.x - 14, mr.y - 14))
                else:
                    # Open threshold with golden runic floor trim
                    pygame.draw.rect(surface, (22, 18, 28), mr)
                    pygame.draw.line(surface, (215, 175, 55), (mr.x + 4, mr.bottom - 4), (mr.right - 4, mr.bottom - 4), 2)

                # Floating golden sparkles / fireflies
                for p in self.golden_door_particles:
                    spx = int(p["x"] - camera_offset[0])
                    spy = int(p["y"] - camera_offset[1])
                    if 0 <= spx <= L3_SCREEN_WIDTH and 0 <= spy <= L3_SCREEN_HEIGHT:
                        sparkle_alpha = int(140 + 100 * math.sin(p["phase"]))
                        spark_surf = pygame.Surface((p["size"] * 2, p["size"] * 2), pygame.SRCALPHA)
                        pygame.draw.circle(spark_surf, (*p["color"], sparkle_alpha), (p["size"], p["size"]), p["size"])
                        surface.blit(spark_surf, (spx - p["size"], spy - p["size"]))

                # Subtle prompt near golden door
                if player.rect.colliderect(dr.inflate(40, 40)):
                    if not door["unlocked"]:
                        if door.get("key_turned", False):
                            txt = "Golden Threshold (Unsealed)"
                            col = (255, 245, 180)
                        else:
                            txt = "E open the gallery" if not door.get("required_key") else "E inspect lock"
                            col = (255, 235, 140)
                    else:
                        txt = "Golden Threshold (Open)"
                        col = (255, 245, 180)

                    pt = font_prompt.render(txt, True, col)
                    px = mr.centerx - pt.get_width() // 2
                    py = mr.top - 28 + int(2 * math.sin(self.flicker_phase * 2.0))
                    bg = pygame.Surface((pt.get_width() + 10, pt.get_height() + 4), pygame.SRCALPHA)
                    bg.fill((14, 12, 22, 220))
                    surface.blit(bg, (px - 5, py - 2))
                    surface.blit(pt, (px, py))

            else:
                # === ANCIENT BROWN / STONE / WOOD INTERNAL DOORS ===
                pygame.draw.rect(surface, (45, 38, 52), mr.inflate(10, 10), border_radius=4)
                pygame.draw.rect(surface, (28, 24, 34), mr.inflate(4, 4), width=2)

                if not door["open"]:
                    # Weathered timber planks
                    pygame.draw.rect(surface, (68, 50, 36), mr, border_radius=2)
                    for px in range(mr.x + 14, mr.right, 16):
                        pygame.draw.line(surface, (42, 30, 22), (px, mr.y + 2), (px, mr.bottom - 2), 1)
                    # Iron reinforcement straps & rivets
                    pygame.draw.line(surface, (48, 44, 52), (mr.x + 2, mr.y + 14), (mr.right - 2, mr.y + 14), 3)
                    pygame.draw.line(surface, (48, 44, 52), (mr.x + 2, mr.bottom - 14), (mr.right - 2, mr.bottom - 14), 3)
                    pygame.draw.circle(surface, (36, 32, 40), (mr.centerx, mr.centery), 6, width=2)
                else:
                    # Open stone archway
                    pygame.draw.rect(surface, (18, 14, 24), mr)

                # Subtle prompt near internal door
                if player.rect.colliderect(dr.inflate(40, 40)):
                    if door["open"]:
                        txt = "E leave with all three crystals" if door["id"] == "exit_door" else "Receiver awakened — passage open"
                        col = (210, 210, 220)
                    else:
                        if door.get("key_turned", False) or not door.get("required_key"):
                            txt = f"{door['name']} (Awaiting Sacred Light)"
                            col = (200, 195, 185)
                        else:
                            txt = "E open the gallery" if not door.get("required_key") else "E inspect lock"
                            col = (220, 210, 190)

                    pt = font_prompt.render(txt, True, col)
                    px = mr.centerx - pt.get_width() // 2
                    py = mr.top - 26
                    bg = pygame.Surface((pt.get_width() + 8, pt.get_height() + 4), pygame.SRCALPHA)
                    bg.fill((14, 12, 22, 220))
                    surface.blit(bg, (px - 4, py - 2))
                    surface.blit(pt, (px, py))

        # Prompt near Chamber 1 Mossy Headstone
        if hasattr(self, "headstone") and player.rect.colliderect(self.headstone.rect.inflate(44, 44)):
            pt = font_prompt.render("[E] Inspect Mossy Headstone", True, (180, 240, 160))
            hx = int(self.headstone.x - camera_offset[0]) - pt.get_width() // 2
            hy = int(self.headstone.y - 48 - camera_offset[1]) + int(2 * math.sin(self.flicker_phase * 2.0))
            bg = pygame.Surface((pt.get_width() + 8, pt.get_height() + 4), pygame.SRCALPHA)
            bg.fill((14, 12, 22, 220))
            surface.blit(bg, (hx - 4, hy - 2))
            surface.blit(pt, (hx, hy))

    def _draw_sockets_and_mirrors(self, surface, player, camera_offset, vp, is_blue: bool = False):
        """Renders mirror mounting pedestals, installed mirrors, and interaction prompts."""
        if not pygame.font.get_init():
            pygame.font.init()
        font_small = pygame.font.SysFont("consolas", 11, bold=True)
        inv = getattr(self, "inventory", None)

        for sock in self.sockets:
            sx, sy = int(sock["pos"][0]), int(sock["pos"][1])
            if not vp.colliderect(pygame.Rect(sx - 50, sy - 50, 100, 100)):
                continue
            screen_x = sx - camera_offset[0]
            screen_y = sy - camera_offset[1]

            # Carved stone mounting pedestal
            pygame.draw.circle(surface, (55, 45, 68), (screen_x, screen_y), 32)
            pygame.draw.circle(surface, (80, 68, 95), (screen_x, screen_y), 32, width=2)
            pygame.draw.circle(surface, (150, 120, 60), (screen_x, screen_y), 28, width=1)
            pygame.draw.circle(surface, (28, 22, 36), (screen_x, screen_y), 20)

            # When Blue Light is active, mirror surfaces and pedestals become readable with an azure sheen
            if is_blue:
                pygame.draw.circle(surface, (70, 160, 245), (screen_x, screen_y), 34, width=1)
                pygame.draw.circle(surface, (120, 210, 255), (screen_x, screen_y), 22, width=1)

            # Placed mirror rendering
            installed = sock["mirror"]
            if installed is not None:
                installed.draw(surface, camera_offset)
                if self.focused_socket == sock["id"]:
                    pygame.draw.circle(surface,(250,223,145),(screen_x,screen_y),40,2)
                if self.debug_optics:
                    nx,ny=installed.normal
                    pygame.draw.line(surface,(255,170,100),(screen_x,screen_y),(screen_x+nx*45,screen_y+ny*45),2)

            # Interactive prompts
            sock_rect = pygame.Rect(sx - 36, sy - 36, 72, 72)
            if player.rect.colliderect(sock_rect):
                if installed is None:
                    txt = "E place mirror | I choose frame"
                    col = (255, 235, 140)
                else:
                    deg = installed.orientation * 45
                    txt = f"A/D turn ({deg}°) | E finish | X retrieve" if self.focused_socket == sock["id"] else "E focus mirror | X retrieve"
                    col = (245, 245, 255)

                pt = font_small.render(txt, True, col)
                px = screen_x - pt.get_width() // 2
                py = screen_y - 48
                bg = pygame.Surface((pt.get_width() + 8, pt.get_height() + 4), pygame.SRCALPHA)
                bg.fill((14, 12, 22, 220))
                surface.blit(bg, (px - 4, py - 2))
                surface.blit(pt, (px, py))

    def _draw_crystals(self, surface, player, camera_offset, vp, is_blue: bool = False, lantern=None):
        font = pygame.font.SysFont("consolas", 12, bold=True)
        for crystal in self.player_crystals:
            if not vp.colliderect(crystal.rect.inflate(100, 100)): continue
            revealed = is_light_active(lantern, crystal.color)
            crystal.draw(surface, camera_offset, is_revealed=revealed, flicker_phase=self.flicker_phase)
            label = font.render((crystal.color.upper() + " " if revealed else "") + "SOURCE · E", True, (205, 195, 170))
            surface.blit(label, (int(crystal.x-camera_offset[0]-label.get_width()/2), int(crystal.y-camera_offset[1]+43)))

    def _draw_beams(self, surface, camera_offset, vp):
        """Draws radiant deterministic light beams emitted by active source crystals with realistic scattering particles and specular reflection flares."""
        if not self.beam_segments:
            return

        cam_x, cam_y = camera_offset
        f_phase = getattr(self, "flicker_phase", 0.0)

        for seg in self.beam_segments:
            sx1, sy1 = int(seg.start[0] - cam_x), int(seg.start[1] - cam_y)
            sx2, sy2 = int(seg.end[0] - cam_x), int(seg.end[1] - cam_y)

            # Viewport culling: segment bounding box
            min_x = min(seg.start[0], seg.end[0]) - 30
            max_x = max(seg.start[0], seg.end[0]) + 30
            min_y = min(seg.start[1], seg.end[1]) - 30
            max_y = max(seg.start[1], seg.end[1]) + 30
            if not vp.colliderect(pygame.Rect(min_x, min_y, max_x - min_x, max_y - min_y)):
                continue

            b_col = getattr(seg, "color", "cyan")
            if b_col == "red":
                bloom_c = (140, 15, 35)
                halo_c = (210, 30, 65)
                core_c = (255, 75, 115)
                center_c = (255, 235, 245)
                flare_c = (255, 120, 160)
                spark_c = (255, 180, 210)
            elif b_col == "green":
                bloom_c = (15, 100, 30)
                halo_c = (30, 180, 65)
                core_c = (75, 245, 120)
                center_c = (235, 255, 240)
                flare_c = (120, 255, 165)
                spark_c = (190, 255, 215)
            else:
                bloom_c = (15, 60, 140)
                halo_c = (35, 125, 225)
                core_c = (90, 205, 255)
                center_c = (235, 250, 255)
                flare_c = (120, 220, 255)
                spark_c = (185, 235, 255)

            # Multi-layer Laser Beam (Laser Ray reference: Image 5)
            # Layer 1: Wide atmospheric diffuse bloom
            pygame.draw.line(surface, bloom_c, (sx1, sy1), (sx2, sy2), 12)
            # Layer 2: Saturated beam corona
            pygame.draw.line(surface, halo_c, (sx1, sy1), (sx2, sy2), 6)
            # Layer 3: Vibrant high-energy laser core
            pygame.draw.line(surface, core_c, (sx1, sy1), (sx2, sy2), 3)
            # Layer 4: Brilliant white-hot diamond center filament
            pygame.draw.line(surface, center_c, (sx1, sy1), (sx2, sy2), 1)

            # 5. Surrounding Scattering Particles / Illuminated Photon Motes along ray (Tyndall Effect)
            dx = sx2 - sx1
            dy = sy2 - sy1
            seg_len = math.hypot(dx, dy)
            if seg_len > 12:
                nx = -dy / seg_len
                ny = dx / seg_len
                step = 20.0
                num_motes = int(seg_len // step)
                for i in range(1, num_motes):
                    t = (i * step) / seg_len
                    # Deterministic sine jitter based on mote index and flicker phase
                    jitter = math.sin(i * 12.7 + f_phase * 4.0) * (3.0 + 3.5 * math.sin(i * 3.1))
                    mx = int(sx1 + t * dx + nx * jitter)
                    my = int(sy1 + t * dy + ny * jitter)
                    mote_pulse = 0.5 + 0.5 * math.sin(i * 7.3 + f_phase * 5.0)
                    if mote_pulse > 0.35:
                        pygame.draw.circle(surface, halo_c, (mx, my), 2)
                        pygame.draw.circle(surface, spark_c, (mx, my), 1)

            # 6. Specular Mirror Reflection Hotspot (Reference Image 5)
            term_type = getattr(seg, "termination_type", "wall")
            if term_type == "mirror":
                # Intense specular diamond starburst at the reflection point on the mirror
                glint_len = int(9 + 3 * math.sin(f_phase * 6.0))
                # Starburst cross-flares
                pygame.draw.line(surface, flare_c, (sx2 - glint_len, sy2), (sx2 + glint_len, sy2), 2)
                pygame.draw.line(surface, flare_c, (sx2, sy2 - glint_len), (sx2, sy2 + glint_len), 2)
                pygame.draw.line(surface, (255, 255, 255), (sx2 - glint_len // 2, sy2), (sx2 + glint_len // 2, sy2), 1)
                pygame.draw.line(surface, (255, 255, 255), (sx2, sy2 - glint_len // 2), (sx2, sy2 + glint_len // 2), 1)

                # Specular reflection aura
                pygame.draw.circle(surface, flare_c, (sx2, sy2), 7, width=1)
                pygame.draw.circle(surface, (255, 255, 255), (sx2, sy2), 3)

                # Micro-sparks scattering off the mirror face
                for sp_i in range(4):
                    sp_ang = sp_i * (math.pi / 2.0) + (math.pi / 4.0) + math.sin(f_phase * 2.0 + sp_i) * 0.4
                    sp_d = 8 + int(3 * math.sin(f_phase * 4.0 + sp_i))
                    sp_x = sx2 + int(math.cos(sp_ang) * sp_d)
                    sp_y = sy2 + int(math.sin(sp_ang) * sp_d)
                    pygame.draw.circle(surface, spark_c, (sp_x, sp_y), 1)
            else:
                # Barrier / Door impact flare
                pygame.draw.circle(surface, flare_c, (sx2, sy2), 7, width=1)
                pygame.draw.circle(surface, (255, 255, 255), (sx2, sy2), 3)

    def _draw_exit_modal(self, surface):
        """Renders exit modal if activated."""
        pass

    def _draw_clue_modal(self, surface: pygame.Surface):
        """Renders ancient modal for headstone / environmental clues."""
        if not self.active_clue:
            return
        if self.active_clue.get("kind") == "mural":
            self.mural.draw(surface, self.debug_optics)
            return
        sw, sh = L3_SCREEN_WIDTH, L3_SCREEN_HEIGHT
        box_w, box_h = 560, 240
        bx = (sw - box_w) // 2
        by = (sh - box_h) // 2

        # Dim overlay background
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        # Modal box with gold/stone border
        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((16, 14, 24, 245))
        pygame.draw.rect(box, (150, 120, 60), (0, 0, box_w, box_h), width=2, border_radius=6)
        pygame.draw.rect(box, (70, 58, 40), (4, 4, box_w - 8, box_h - 8), width=1, border_radius=4)
        surface.blit(box, (bx, by))

        f_title = pygame.font.SysFont("georgia", 16, bold=True)
        f_body = pygame.font.SysFont("consolas", 12)
        f_prompt = pygame.font.SysFont("consolas", 11, bold=True)

        # Title
        title_text = self.active_clue.get("title", "Ancient Inscription")
        t_surf = f_title.render(title_text, True, (245, 220, 140))
        surface.blit(t_surf, (bx + (box_w - t_surf.get_width()) // 2, by + 16))

        pygame.draw.line(surface, (140, 110, 50), (bx + 30, by + 44), (bx + box_w - 30, by + 44), 1)

        # Body lines
        body_text = self.active_clue.get("text", "")
        lines = body_text.split("\n")
        curr_y = by + 56
        for line in lines:
            line = line.strip()
            if not line:
                curr_y += 8
                continue
            b_surf = f_body.render(line, True, (225, 220, 210))
            surface.blit(b_surf, (bx + (box_w - b_surf.get_width()) // 2, curr_y))
            curr_y += 18

        # Footer prompt
        prompt_text = self.active_clue.get("prompt", "Press [SPACE] or [E] to return")
        p_surf = f_prompt.render(prompt_text, True, (215, 185, 110))
        surface.blit(p_surf, (bx + (box_w - p_surf.get_width()) // 2, by + box_h - 26))

    def _draw_receivers(self, surface, camera_offset):
        font=pygame.font.SysFont("consolas",12,bold=True)
        palette={"blue":(100,200,255),"red":(255,120,105),"green":(130,245,175)}
        for p in self.puzzles:
            x,y=(int(p["receiver"][i]-camera_offset[i]) for i in range(2))
            color=palette[p["color"]] if p["solved"] or p["hold"] else (135,126,106)
            pygame.draw.circle(surface,(39,33,43),(x,y),27)
            pygame.draw.circle(surface,color,(x,y),24,2)
            pygame.draw.polygon(surface,color,[(x,y-18),(x+18,y),(x,y+18),(x-18,y)],2)
            if p["hold"]:
                pygame.draw.arc(surface,color,(x-30,y-30,60,60),-math.pi/2,-math.pi/2+math.tau*p["hold"]/1.25,3)
            label=font.render("RECEIVER",True,color)
            surface.blit(label,(x-label.get_width()//2,y+34))
            x,y=(int(p["reward"][i]-camera_offset[i]) for i in range(2))
            pygame.draw.ellipse(surface,(82,69,58),(x-25,y+10,50,18))
            pygame.draw.ellipse(surface,(160,132,75),(x-25,y+8,50,18),2)
            collected=self.inventory and self.inventory.has_crystal(p["reward_id"])
            if p["solved"] and not collected:
                bob=0 if self.reduced_motion else int(math.sin(self.flicker_phase*2)*3)
                y+=bob
                c=palette[p["color"]]
                pygame.draw.polygon(surface,c,[(x,y-25),(x+12,y-5),(x,y+13),(x-12,y-5)])
                pygame.draw.lines(surface,(240,240,220),False,[(x,y-25),(x-4,y-5),(x,y+13)],2)
            label=font.render("COLLECTED" if collected else ("E COLLECT" if p["solved"] else "CRYSTAL CRADLE"),True,(205,186,142))
            surface.blit(label,(x-label.get_width()//2,y+32))
        if self.restoration_time:
            cx,cy=1950-camera_offset[0],1650-camera_offset[1]
            for radius in (95,155,225,310):
                pygame.draw.circle(surface,(153,133,81),(cx,cy),radius,1)
                for i in range(8):
                    a=i*math.tau/8+self.restoration_time*(.15 if radius%2 else -.15)
                    x,y=int(cx+radius*math.cos(a)),int(cy+radius*math.sin(a))
                    pygame.draw.polygon(surface,(247,220,150),[(x,y-6),(x+4,y),(x,y+6),(x-4,y)])

    def draw_hud(self, surface, font_small, lantern=None, inventory=None):
        font=pygame.font.SysFont("consolas",14)
        title=pygame.font.SysFont("georgia",20,bold=True)
        names={1:"Entrance Gallery",2:"The Guiding Ray",3:"Returning Light",4:"Convergence"}
        panel=pygame.Surface((800,67),pygame.SRCALPHA); panel.fill((15,13,22,235)); surface.blit(panel,(0,0))
        surface.blit(title.render(names.get(self.current_chamber,"Path of Light"),True,(231,211,161)),(18,9))
        color=getattr(lantern,"color","white").upper() if getattr(lantern,"active",False) else "OFF"
        count=sum(bool(self.inventory and self.inventory.has_crystal(p["reward_id"])) for p in self.puzzles)
        surface.blit(font.render(f"Stable light: {color}   |   Crystals {count}/3   |   H help",True,(196,204,200)),(18,40))
        if not self.active_clue:
            text="E interact / focus   X retrieve   R G B light   I inventory   Esc pause"
            surface.blit(font.render(text,True,(215,204,178)),(16,577))
            if self.current_chamber==1 and self.toast_timer<=0:
                surface.blit(font.render("Follow the inlays north to the mural and golden door.",True,(218,194,145)),(18,548))
            if self.toast_timer>0:
                import textwrap
                words=textwrap.wrap(self.toast_msg,85)
                box=pygame.Surface((776,24+20*len(words)),pygame.SRCALPHA); box.fill((14,12,22,240))
                surface.blit(box,(12,550-box.get_height()))
                for i,line in enumerate(words): surface.blit(font.render(line,True,(251,224,166)),(24,562-box.get_height()+i*20))
        if self.paused or self.help_open:
            pygame.draw.rect(surface,(20,18,28),(85,125,630,345),border_radius=8)
            pygame.draw.rect(surface,(159,133,77),(85,125,630,345),2,border_radius=8)
            rows=(["PAUSED", "Esc / Space: resume   M: main menu", "F6: reduced motion " + ("ON" if self.reduced_motion else "OFF")]
                  if self.paused else ["PATH OF LIGHT", "Match R / G / B light, then E at a source.", "E at a stand places a carried mirror and focuses it.", "A/D or arrows turn the face. E/Esc releases focus.", "X retrieves the nearby mirror. Any frame fits any stand.", "Hold the beam on a receiver, then E at its cradle.", "Solved rooms stay lit: carry your mirrors onward.", "F5 saves here. F9 restores this Level 3 checkpoint.", "F3 shows normals / mural stages. H/Esc closes help."])
            for i,line in enumerate(rows): surface.blit((title if i==0 else font).render(line,True,(227,211,174)),(110,148+i*31))
