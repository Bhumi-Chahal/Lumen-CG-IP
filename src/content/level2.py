"""content/level2.py — Level 2: The Deepening Dark.

Composition root for Level 2.  Follows the same pattern as content/level1.py:
the room owns its layout, entities, lighting, and draw/update loops.

Layout (3200×2400 world):
    Entry Hall (south)  →  South Corridor  →  Central Hub
    Hub branches to West Catacombs, North Passage, East Sanctum
    North Passage leads to North Gallery

Phase B scope:
    ✓ World geometry, walls, pillars, floor, architecture
    ✓ Camera integration (reuses engine/camera.py unchanged)
    ✓ 4 Energy Crystal stations with battery recharge
    ✓ RGB lantern switching (R/G/B keys, colored glow)
    ✓ Shadow creature placement and update/draw
    ✓ Battery drain / death / restart
    ✓ HUD (LanternMeter + color indicator)
    ✓ Hidden red doors (Phase C) — implemented, see `get_red_door_visual_state()`
    ✓ Invisible blue bridge (Phase C) — implemented, dynamic chasm collision swap via `bridge_discovered`
    ✓ Green AncientWriting (Phase C) — implemented, 3 lore fragments, green-light-gated
"""

import math
import random
import pygame

from engine.collision import move_with_collision
from engine.lighting import LightingSystem, is_point_lit
from engine.battery import BatterySystem, LanternMeter
from entities.shadow import ShadowCreature, level2_death_triggered
from entities.crystal import EnergyCrystalStation
from systems.audio import audio

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

L2_SCREEN_WIDTH = 800
L2_SCREEN_HEIGHT = 600
L2_WORLD_WIDTH = 3200
L2_WORLD_HEIGHT = 2400

CRYSTAL_RECHARGE_AMOUNT = 50.0   # Configurable — preserves battery pressure

L2_SPAWN_X = 1600
L2_SPAWN_Y = 2150

L2_SHADOW_SPAWN_X = 1900
L2_SHADOW_SPAWN_Y = 200

# Visual palette (deeper than Level 1 — "descending into the temple")
_FLOOR_BASE = (12, 10, 18)
_FLOOR_TILE_A = (16, 14, 24)
_FLOOR_TILE_B = (10, 8, 16)
_FLOOR_GROUT = (7, 5, 12)
_WALL_COLOR = (28, 24, 38)
_WALL_STONE = (38, 33, 48)
_WALL_HIGHLIGHT = (50, 44, 60)
_WALL_DARK = (14, 12, 22)

# Lantern colour → glow tint tuples (outer, mid, inner RGBA)
_COLOR_GLOW = {
    "white": ((255, 195, 90, 28), (255, 220, 130, 42), (255, 245, 180, 50)),
    "red":   ((255, 80, 60, 32), (255, 120, 90, 48), (255, 170, 140, 58)),
    "green": ((80, 255, 100, 28), (130, 255, 150, 42), (190, 255, 210, 50)),
    "blue":  ((60, 120, 255, 32), (110, 170, 255, 45), (170, 215, 255, 55)),
}

# ---------------------------------------------------------------------------
# Phase-C foundation helpers (no gameplay yet — just the query interface)
# ---------------------------------------------------------------------------


def is_color_active(lantern, target_color: str) -> bool:
    """True when the lantern is ON *and* set to *target_color*.

    Phase C reveal systems (doors/bridge/writings) will call this to decide
    whether they should respond.  Lantern OFF → always False, preventing
    the player from exploiting darkness to bypass puzzles.
    """
    return lantern.active and lantern.color == target_color


def has_line_of_sight(pos1: tuple[float, float], pos2: tuple[float, float], walls: list[pygame.Rect]) -> bool:
    """Returns True if the direct line between pos1 and pos2 is not occluded by any wall."""
    p1 = (int(pos1[0]), int(pos1[1]))
    p2 = (int(pos2[0]), int(pos2[1]))
    for wall in walls:
        if wall.clipline(p1, p2):
            return False
    return True


# ---------------------------------------------------------------------------
# Coloured darkness mask (Level 2-specific; does NOT modify engine/lighting.py)
# ---------------------------------------------------------------------------


def build_colored_darkness_mask(
    size, light_center, radius,
    lantern_color="white",
    darkness_alpha=252,
    flicker_offset=0.0,
    crystal_lights=None,
    battery_ratio=1.0,
):
    """Produces a darkness overlay with a coloured lantern glow.

    Mirrors the structure of ``engine.lighting.build_darkness_mask`` but
    tints the glow circle by the active lantern colour.  Crystal stations
    provide independent cyan light holes regardless of lantern colour.

    Light intensity scales dynamically with ``battery_ratio``.
    """
    eff_r = max(30, int(radius + flicker_offset))
    b = max(0.0, min(1.0, battery_ratio))

    mask = pygame.Surface(size, pygame.SRCALPHA)
    mask.fill((2, 2, 6, darkness_alpha))

    # Center alpha scales continuously from 0 (at 100% battery) to ~210 (at 0% battery)
    core_alpha = int(210.0 * (1.0 - b))
    core_alpha = max(0, min(darkness_alpha, core_alpha))

    # Gradient rings: smooth interpolation from core_alpha at center to darkness_alpha at edge
    for i in range(18, 0, -1):
        ratio = i / 18.0
        r = int(eff_r * ratio)
        att = ratio * ratio * (3.0 - 2.0 * ratio)
        ring_a = int(core_alpha + (darkness_alpha - core_alpha) * att)
        pygame.draw.circle(mask, (2, 2, 6, ring_a), light_center, r)

    # Core visibility hole
    hole_radius = int(eff_r * (0.20 + 0.12 * b))
    pygame.draw.circle(mask, (2, 2, 6, core_alpha), light_center, hole_radius)

    # Coloured glow overlay — scaled by battery_ratio
    glow = pygame.Surface(size, pygame.SRCALPHA)
    tint = _COLOR_GLOW.get(lantern_color, _COLOR_GLOW["white"])
    g0 = (tint[0][0], tint[0][1], tint[0][2], int(tint[0][3] * b))
    g1 = (tint[1][0], tint[1][1], tint[1][2], int(tint[1][3] * b))
    g2 = (tint[2][0], tint[2][1], tint[2][2], int(tint[2][3] * b))

    pygame.draw.circle(glow, g0, light_center, int(eff_r * 0.9))
    pygame.draw.circle(glow, g1, light_center, int(eff_r * 0.55))
    pygame.draw.circle(glow, g2, light_center, int(eff_r * 0.25))

    # Crystal station light holes (always cyan — independent of lantern colour)
    if crystal_lights:
        for cx, cy, cr in crystal_lights:
            for ti in range(10, 0, -1):
                tr = ti / 10.0
                pygame.draw.circle(
                    mask, (2, 2, 6, int(darkness_alpha * tr * tr)),
                    (cx, cy), int(cr * tr),
                )
            pygame.draw.circle(mask, (0, 0, 0, 0), (cx, cy), int(cr * 0.35))
            pygame.draw.circle(glow, (40, 180, 255, 35),
                               (cx, cy), int(cr * 0.85))
            pygame.draw.circle(glow, (120, 220, 255, 50),
                               (cx, cy), int(cr * 0.45))

    mask.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
    return mask


# ===================================================================
# Level2Room
# ===================================================================


class Level2Room:
    """Level 2: The Deepening Dark — vast ancient temple depths.

    Seven interconnected zones:
        Entry Hall  →  South Corridor  →  Central Hub
        Hub  →  West Catacombs  |  North Passage  |  East Sanctum
        North Passage  →  North Gallery

    Contains 4 Energy Crystal stations, a Shadow creature, and supports
    RGB lantern switching.
    """

    def __init__(self, inventory=None):
        self.inventory = inventory
        self.trigger_level3_transition = False
        self.door_locked = True
        self.door_rect = pygame.Rect(1840, 1580, 100, 100)
        self.door_wall_above = pygame.Rect(1840, 1450, 100, 130)
        self.door_wall_below = pygame.Rect(1840, 1680, 100, 120)
        self.door_wall_solid = pygame.Rect(1840, 1450, 100, 350)

        # Phase C2 Blue Bridge & Chasm
        self.bridge_discovered = False
        self.bridge_rect = pygame.Rect(910, 650, 80, 80)
        self.chasm_full_rect = pygame.Rect(750, 650, 400, 80)
        self.chasm_left_rect = pygame.Rect(750, 650, 160, 80)
        self.chasm_right_rect = pygame.Rect(990, 650, 160, 80)

        self.walls = self._build_walls()
        self.pillars = self._build_pillars()
        self.crystals = self._build_crystals()
        self.debris_positions = self._build_debris()

        self.all_obstacles = self.walls + self.pillars
        if self.door_locked:
            self.all_obstacles.append(self.door_rect)

        if self.bridge_discovered:
            self.all_obstacles.append(self.chasm_left_rect)
            self.all_obstacles.append(self.chasm_right_rect)
        else:
            self.all_obstacles.append(self.chasm_full_rect)

        # No jumpable gaps in Level 2 (blue bridge is Phase C — NOT a gap)
        self.jumpable_gaps = []
        self.jumpable_gap_rects = []

        # Phase A systems
        self.battery = BatterySystem()
        self.lantern_meter = LanternMeter()
        self.shadow = ShadowCreature(L2_SHADOW_SPAWN_X, L2_SHADOW_SPAWN_Y)

        # Lighting particles
        self.lighting = LightingSystem(L2_WORLD_WIDTH, L2_WORLD_HEIGHT,
                                       num_particles=90)

        # Runtime state
        self.is_dead = False
        self.death_timer = 0.0
        self.death_cause = ""
        self.message = ""
        self.message_timer = 0.0
        self.recharge_cooldown = 0.0

        self.pending_story_modal = None
        self.exit_door_warning_active = False

        # Ancient inscription — discovery hint for RGB lantern
        self.inscription = {
            "x": 1600, "y": 1800,
            "rect": pygame.Rect(1600 - 18, 1800 - 22, 36, 44),
            "title": "Ancient Inscription",
            "line1": "The flame is not what it seems.",
            "line2": "Three colors sleep within it.",
            "showing": False,
        }

        # Phase C3 Ancient Writings (Revealed ONLY under Green light)
        self.ancient_writings = [
            {
                "id": "writing_1",
                "rect": pygame.Rect(280, 580, 40, 40),
                "title": "Fragment of the First Record",
                "line1": "The flame does not create what is seen.",
                "line2": "It only remembers what the shadow sought to erase.",
                "showing": False,
            },
            {
                "id": "writing_2",
                "rect": pygame.Rect(1580, 160, 40, 40),
                "title": "Fragment of the Unbound Flame",
                "line1": "Three colors sleep within one light.",
                "line2": "Truth is not found by choosing the path that seems most bright.",
                "showing": False,
            },
            {
                "id": "writing_3",
                "rect": pygame.Rect(2850, 360, 40, 40),
                "title": "Fragment of the Final Threshold",
                "line1": "At the deep gate, reality divides threefold.",
                "line2": "Only the mind that weighed all three lights shall see past the illusion.",
                "showing": False,
            },
        ]

        # Phase C4 Collectible Ancient Mirrors — embedded in believable environmental objects
        self.mirrors_in_world = [
            {
                "id": "mirror_red",
                "name": "Crimson Refractor Mirror",
                "rect": pygame.Rect(2200 - 14, 1620 - 18, 28, 36),
                "collected": False,
                "container_type": "ruined_altar",
                "container_name": "Ruined Crimson Altar",
            },
            {
                "id": "mirror_blue",
                "name": "Azure Refractor Mirror",
                "rect": pygame.Rect(950 - 14, 540 - 18, 28, 36),
                "collected": False,
                "container_type": "petrified_roots",
                "container_name": "Petrified Root Formation",
            },
            {
                "id": "mirror_green",
                "name": "Verdant Refractor Mirror",
                "rect": pygame.Rect(2600 - 14, 750 - 18, 28, 36),
                "collected": False,
                "container_type": "collapsed_arch",
                "container_name": "Collapsed Archway Debris",
            },
        ]

        # Visually similar Dummy Environmental Discovery Objects (empty locations to investigate)
        self.dummy_objects = [
            {
                "id": "dummy_roots_south",
                "name": "Twisted Cave Roots",
                "type": "petrified_roots",
                "rect": pygame.Rect(1480 - 16, 1950 - 16, 32, 32),
                "inspect_text": "You examine the twisted roots curling through the stone floor... only dry dust and dead lichen cling to the wood.",
            },
            {
                "id": "dummy_altar_hub",
                "name": "Weathered Pedestal",
                "type": "ruined_altar",
                "rect": pygame.Rect(1720 - 18, 1250 - 18, 36, 36),
                "inspect_text": "An ancient broken altar pedestal. The reliquary recess is empty, carved with forgotten sun emblems.",
            },
            {
                "id": "dummy_arch_west",
                "name": "Shattered Masonry Pile",
                "type": "collapsed_arch",
                "rect": pygame.Rect(620 - 16, 480 - 16, 32, 32),
                "inspect_text": "You search through the cracked stone blocks and crumbled mortar... nothing but cold shale.",
            },
            {
                "id": "dummy_roots_north",
                "name": "Creeping Root Cluster",
                "type": "petrified_roots",
                "rect": pygame.Rect(2350 - 16, 850 - 16, 32, 32),
                "inspect_text": "Lichen and deep roots weave between the flags. Searching carefully yields no hidden relics.",
            },
            {
                "id": "dummy_altar_east",
                "name": "Cracked Offering Basin",
                "type": "ruined_altar",
                "rect": pygame.Rect(2450 - 18, 1700 - 18, 36, 36),
                "inspect_text": "A fractured stone basin hollowed into the rock. It holds only stagnant water and ancient sediment.",
            },
        ]

        # Phase C4 Level 2 -> Level 3 Exit Door
        self.exit_door = {
            "rect": pygame.Rect(1600 - 30, 22, 60, 42),
            "title": "Portal to the Chamber of Convergence",
            "line1": "The ancient stone portal hums with crystalline resonance.",
            "line2": "Step through into the Path of Light. Press [E] to proceed.",
            "showing": False,
        }

        # Pre-rendered floor (static — large but drawn once)
        self.floor_surf = self._render_static_floor()

    def get_red_door_visual_state(self, lantern) -> str:
        """Returns the Red Door visual rendering state:
        'hidden'   : Locked door under WHITE, GREEN, BLUE or OFF (normal wall visual, blocked).
        'revealed' : Locked door under active RED light (revealed frame + rune + prompt, blocked).
        'open'     : Unlocked door under active RED light (open portal visual, passable).
        'wall'     : Unlocked door under WHITE, GREEN, BLUE or OFF (restored wall visual, passable).
        """
        is_red = lantern.possessed and lantern.active and lantern.color == "red"
        if self.door_locked:
            return "revealed" if is_red else "hidden"
        else:
            return "open" if is_red else "wall"

    # ------------------------------------------------------------------
    # Layout construction
    # ------------------------------------------------------------------

    def _build_walls(self):
        """Defines every solid wall rectangle in the Level 2 world.

        Zone map (walkable interiors):
            Entry Hall:      x 1100-2100,  y 1880-2368
            South Corridor:  x 1360-1840,  y 1400-1880
            Central Hub:     x  200-3000,  y  900-1400
            West Catacombs:  x  100- 700,  y  300- 900
            North Passage:   x 1200-2000,  y  300- 900
            East Sanctum:    x 2500-3100,  y  300- 900
            North Gallery:   x  700-2500,  y   32- 300
        """
        W, H = L2_WORLD_WIDTH, L2_WORLD_HEIGHT
        return [
            # ── outer boundary (32 px) ──────────────────────────────
            pygame.Rect(0, 0, W, 32),
            pygame.Rect(0, H - 32, W, 32),
            pygame.Rect(0, 0, 32, H),
            pygame.Rect(W - 32, 0, 32, H),

            # ── Entry Hall  (x 1100-2100, y 1880-2368) ─────────────
            pygame.Rect(32, 1880, 1068, 488),        # SW fill
            pygame.Rect(2100, 1880, 1068, 488),      # SE fill

            # ── South Corridor  (x 1360-1840, y 1400-1880) ────────
            pygame.Rect(32, 1400, 1328, 480),        # left fill
            # Right fill broken up for Red Chamber (x 1940-2800, y 1450-1800)
            pygame.Rect(1840, 1400, 1328, 50),       # North of Red Chamber
            pygame.Rect(1840, 1800, 1328, 80),       # South of Red Chamber
            pygame.Rect(2800, 1450, 368, 350),       # East of Red Chamber
            pygame.Rect(1840, 1450, 100, 130),       # West block above door
            pygame.Rect(1840, 1680, 100, 120),       # West block below door

            # ── Central Hub  (x 200-3000, y 900-1400) ─────────────
            pygame.Rect(32, 900, 168, 500),           # left fill
            pygame.Rect(3000, 900, 168, 500),         # right fill
            # south wall of hub (gap at corridor entry x 1360-1840)
            pygame.Rect(200, 1370, 1160, 30),         # hub-south-left
            pygame.Rect(1840, 1370, 1160, 30),        # hub-south-right

            # ── North-area fills  (y 300-900) ─────────────────────
            # West Catacombs: x 100-700
            pygame.Rect(32, 300, 68, 600),             # far-west
            # ── Blue Chamber & Chasm Section  (x 700-1200, y 300-900) ──
            pygame.Rect(700, 300, 50, 600),            # Far-left bounding wall (x 700-750)
            pygame.Rect(1150, 300, 50, 600),           # Far-right bounding wall (x 1150-1200)
            pygame.Rect(750, 300, 400, 50),            # North wall of Blue Chamber (y 300-350)
            pygame.Rect(750, 850, 150, 50),            # South wall left of entry corridor
            pygame.Rect(1000, 850, 150, 50),           # South wall right of entry corridor
            # East Sanctum: x 2500-3100
            pygame.Rect(3100, 300, 68, 600),           # far-east
            # fill between north passage and sanctum
            pygame.Rect(2000, 300, 500, 600),          # divider

            # ── North Gallery  (x 700-2500, y 32-300) ─────────────
            pygame.Rect(32, 32, 668, 268),             # NW fill
            pygame.Rect(2500, 32, 668, 268),           # NE fill

            # ── Internal detail walls ──────────────────────────────
            # West Catacombs loop-divider
            pygame.Rect(380, 420, 28, 360),
            # East Sanctum loop-divider
            pygame.Rect(2790, 420, 28, 360),
            # Hub cross-barriers
            pygame.Rect(600, 1080, 100, 24),
            pygame.Rect(2500, 1080, 100, 24),
            # North passage narrowing walls
            pygame.Rect(1200, 500, 80, 24),
            pygame.Rect(1920, 500, 80, 24),
            # Level 3 Exit Door (solid physical boundary)
            pygame.Rect(1600 - 30, 22, 60, 42),
        ]

    def _build_pillars(self):
        """Pillars are collision obstacles rendered with carved-column art."""
        return [
            # Entry Hall
            pygame.Rect(1200, 2000, 36, 48),
            pygame.Rect(1964, 2000, 36, 48),
            # South Corridor
            pygame.Rect(1420, 1560, 36, 48),
            pygame.Rect(1744, 1560, 36, 48),
            pygame.Rect(1420, 1740, 36, 48),
            pygame.Rect(1744, 1740, 36, 48),
            # Central Hub – grand colonnade
            pygame.Rect(500, 980, 40, 52),
            pygame.Rect(900, 980, 40, 52),
            pygame.Rect(1300, 980, 40, 52),
            pygame.Rect(1860, 980, 40, 52),
            pygame.Rect(2260, 980, 40, 52),
            pygame.Rect(2660, 980, 40, 52),
            pygame.Rect(500, 1280, 40, 52),
            pygame.Rect(900, 1280, 40, 52),
            pygame.Rect(2260, 1280, 40, 52),
            pygame.Rect(2660, 1280, 40, 52),
            # West Catacombs
            pygame.Rect(200, 500, 32, 44),
            pygame.Rect(550, 700, 32, 44),
            # East Sanctum
            pygame.Rect(2620, 500, 32, 44),
            pygame.Rect(2960, 700, 32, 44),
            # Red Chamber
            pygame.Rect(2000, 1500, 36, 48),
            pygame.Rect(2000, 1700, 36, 48),
            pygame.Rect(2400, 1500, 36, 48),
            pygame.Rect(2400, 1700, 36, 48),
            # Blue Chamber
            pygame.Rect(830, 460, 36, 48),
            pygame.Rect(1070, 460, 36, 48),
            # North Passage
            pygame.Rect(1300, 550, 36, 48),
            pygame.Rect(1864, 550, 36, 48),
            pygame.Rect(1300, 750, 36, 48),
            pygame.Rect(1864, 750, 36, 48),
            # North Gallery – grand row
            pygame.Rect(900, 100, 40, 52),
            pygame.Rect(1200, 100, 40, 52),
            pygame.Rect(1560, 100, 40, 52),
            pygame.Rect(1960, 100, 40, 52),
            pygame.Rect(2260, 100, 40, 52),
            pygame.Rect(900, 210, 40, 52),
            pygame.Rect(2260, 210, 40, 52),
        ]

    def _build_crystals(self):
        """Energy Crystal stations — strategic placement for battery management."""
        return [
            EnergyCrystalStation(1950, 2100),   # Entry Hall, east corner
            EnergyCrystalStation(220, 620),      # West Catacombs, left passage
            EnergyCrystalStation(2950, 620),     # East Sanctum Green Chamber, right passage
            EnergyCrystalStation(1600, 200),     # North Gallery, centre
            EnergyCrystalStation(2700, 1625),    # Red Chamber, deep inside
            EnergyCrystalStation(950, 450),      # Blue Chamber, north of bridge
            EnergyCrystalStation(2980, 500),     # Green Chamber, right side shrine alcove
        ]

    @staticmethod
    def _build_debris():
        """Decorative rubble/stone positions for atmosphere."""
        return [
            (1200, 2200, "rubble"), (1900, 2250, "rubble"),
            (1500, 1600, "stones"), (1700, 1750, "stones"),
            (400, 1150, "rubble"),  (800, 1300, "stones"),
            (2400, 1200, "rubble"), (2800, 1350, "stones"),
            (1500, 1100, "rubble"), (1700, 1300, "stones"),
            (150, 450, "rubble"),   (500, 800, "stones"),
            (300, 700, "rubble"),
            (2600, 450, "rubble"),  (2850, 800, "stones"),
            (2700, 700, "rubble"),
            (1400, 650, "stones"),  (1800, 830, "rubble"),
            (800, 220, "rubble"),   (1400, 250, "stones"),
            (2000, 180, "rubble"),  (2300, 250, "stones"),
            (2100, 1550, "rubble"), (2200, 1600, "stones"),
            (2600, 1700, "rubble"), (2700, 1500, "stones"),
            (800, 400, "rubble"),   (1100, 400, "stones"),
            (950, 380, "rubble"),
        ]

    # ------------------------------------------------------------------
    # Pre-rendered static floor
    # ------------------------------------------------------------------

    def _render_static_floor(self):
        surf = pygame.Surface((L2_WORLD_WIDTH, L2_WORLD_HEIGHT))
        surf.fill(_FLOOR_BASE)

        tile = 36
        for y in range(0, L2_WORLD_HEIGHT, tile):
            for x in range(0, L2_WORLD_WIDTH, tile):
                shade = (x * 7 + y * 13) % 5
                if shade < 2:
                    c = list(_FLOOR_TILE_A)
                elif shade < 4:
                    c = list(_FLOOR_TILE_B)
                else:
                    c = [14, 12, 22]

                # Area-specific tints
                if 750 <= x <= 1150 and 640 <= y <= 730:
                    c = [4, 2, 8]                     # Blue Chasm abyss
                elif 750 <= x <= 1150 and 350 <= y <= 640:
                    c[0] -= 4; c[1] += 1; c[2] += 8   # Blue Chamber — sapphire tint
                elif 700 <= x <= 2500 and 32 <= y <= 300:
                    c[0] += 3; c[1] += 2; c[2] += 1   # Gallery — warmer
                elif 100 <= x <= 700 and 300 <= y <= 900:
                    c[0] -= 2; c[1] -= 1; c[2] += 3   # Catacombs — colder
                elif 2500 <= x <= 3100 and 300 <= y <= 900:
                    c[0] += 2; c[1] -= 1; c[2] += 4   # Sanctum — purple

                c = [max(0, min(255, v)) for v in c]
                tr = pygame.Rect(x, y, tile - 2, tile - 2)
                pygame.draw.rect(surf, tuple(c), tr)
                pygame.draw.rect(surf, _FLOOR_GROUT, tr, width=1)

        # Scattered floor cracks
        cracks = [
            ((200, 1000), (220, 1020), (250, 1012)),
            ((600, 1200), (620, 1220), (648, 1210)),
            ((1500, 2000), (1520, 2020), (1545, 2012)),
            ((2000, 1100), (2025, 1125), (2050, 1115)),
            ((2800, 600), (2825, 625), (2850, 615)),
            ((400, 500), (425, 525), (450, 518)),
            ((1600, 500), (1625, 525), (1650, 518)),
            ((1300, 1700), (1325, 1725), (1350, 1718)),
            ((800, 200), (825, 224), (855, 216)),
            ((2200, 200), (2225, 225), (2255, 218)),
        ]
        for pts in cracks:
            pygame.draw.lines(surf, (6, 4, 10), False, pts, 1)

        # Central Hub rune circle (visual landmark)
        hcx, hcy = 1600, 1150
        for r in (80, 60, 40, 20):
            pygame.draw.circle(surf, (20, 16, 30), (hcx, hcy), r, width=1)
        for i in range(8):
            a = i * math.pi / 4
            pygame.draw.line(
                surf, (25, 20, 35),
                (hcx + int(50 * math.cos(a)), hcy + int(50 * math.sin(a))),
                (hcx + int(70 * math.cos(a)), hcy + int(70 * math.sin(a))),
                1,
            )

        # Gallery floor grid inlay
        for gx in range(800, 2400, 200):
            pygame.draw.line(surf, (18, 15, 26), (gx, 60), (gx, 280), 1)
        for gy in range(80, 280, 50):
            pygame.draw.line(surf, (18, 15, 26), (800, gy), (2400, gy), 1)

        return surf

    # ------------------------------------------------------------------
    # Runtime — update
    # ------------------------------------------------------------------

    def update(self, player, lantern, dt):
        """Main Level 2 per-frame update."""
        if self.is_dead:
            self.death_timer -= dt
            return

        # Lighting particles
        self.lighting.update(dt, L2_WORLD_WIDTH, L2_WORLD_HEIGHT)

        # Player movement
        dx, dy = player.get_input_vector()
        move_with_collision(player, dx, dy, self.all_obstacles, dt,
                            jumpable_gaps=self.jumpable_gap_rects)
        player.update_animation(dx != 0.0 or dy != 0.0, dt)

        # Dynamic Blue Light bridge activity
        is_blue_active = is_color_active(lantern, "blue")
        p_dx = player.center[0] - 950
        p_dy = player.center[1] - 690
        dist_to_bridge = math.hypot(p_dx, p_dy)
        is_player_on_bridge = player.rect.colliderect(self.bridge_rect)

        # Player standing on bridge safety check
        if is_player_on_bridge and lantern.color != "blue":
            lantern.set_color("blue")
            self._toast("Blue light is required to sustain the bridge...", 2.0)
            is_blue_active = is_color_active(lantern, "blue")

        should_bridge_be_active = is_blue_active and (dist_to_bridge < 320.0 or is_player_on_bridge)

        if should_bridge_be_active and not self.bridge_discovered:
            self.bridge_discovered = True
            if self.chasm_full_rect in self.all_obstacles:
                self.all_obstacles.remove(self.chasm_full_rect)
            if self.chasm_left_rect not in self.all_obstacles:
                self.all_obstacles.append(self.chasm_left_rect)
            if self.chasm_right_rect not in self.all_obstacles:
                self.all_obstacles.append(self.chasm_right_rect)
            audio.play("clue")
            self._toast("An ancient invisible bridge materializes...", 2.5)
        elif not should_bridge_be_active and self.bridge_discovered:
            self.bridge_discovered = False
            if self.chasm_left_rect in self.all_obstacles:
                self.all_obstacles.remove(self.chasm_left_rect)
            if self.chasm_right_rect in self.all_obstacles:
                self.all_obstacles.remove(self.chasm_right_rect)
            if self.chasm_full_rect not in self.all_obstacles:
                self.all_obstacles.append(self.chasm_full_rect)

        # Auto-close writing modal overlays if lantern color is not GREEN
        if not is_color_active(lantern, "green"):
            for w in self.ancient_writings:
                w["showing"] = False

        # Battery drain (only while lantern is ON)
        self.battery.update(dt, lantern.active)
        self.lantern_meter.update(dt, self.battery.ratio)

        # Shadow
        self.shadow.update(dt, player.center, self.battery.ratio)

        # Crystals
        for crystal in self.crystals:
            crystal.update(dt)

        # Recharge cooldown
        if self.recharge_cooldown > 0:
            self.recharge_cooldown -= dt

        # Death check (Phase A locked logic)
        if level2_death_triggered(self.battery, self.shadow, player.center):
            self.is_dead = True
            self.death_timer = 2.5
            if self.battery.is_depleted:
                self.death_cause = "YOUR LIGHT DIED IN THE DEEP\nLantern battery depleted. Recharge at glowing Energy Crystals."
            else:
                self.death_cause = "THE SHADOW OVERWHELMED YOU\nThe creature caught you in the dark. Keep your distance and maintain light."

        # Automatic exit portal transition when all 3 mirrors are collected
        door_trigger = self.exit_door["rect"].inflate(40, 40)
        if player.rect.colliderect(door_trigger):
            required_mirrors = ["mirror_red", "mirror_blue", "mirror_green"]
            collected_count = 0
            if self.inventory:
                collected_count = sum(1 for m in required_mirrors if self.inventory.has_mirror(m))
            else:
                collected_count = sum(1 for m in self.mirrors_in_world if m["collected"])
            if collected_count == 3:
                self.trigger_level3_transition = True
            elif not self.exit_door_warning_active:
                self.exit_door_warning_active = True
                self.exit_door["showing"] = True
                self.exit_door["title"] = "THE PORTAL REMAINS SILENT"
                self.exit_door["line1"] = "You need all three mirrors to enter the Chamber of Convergence."
                self.exit_door["line2"] = f"Mirrors Collected: {collected_count}/3. Return to the temple and find the remaining mirror(s)."
                self.pending_story_modal = (
                    "MISSING MIRRORS",
                    f"Three refractor mirrors are required to unseal the Path of Light.\n\nYou need all three mirrors to enter the Chamber of Convergence.\n\nMirrors Collected: {collected_count}/3\n\nReturn to the temple depths and retrieve the remaining mirror(s).",
                    "l2_exit_missing"
                )
                audio.play("clue")
        elif not player.rect.colliderect(self.exit_door["rect"].inflate(70, 70)):
            self.exit_door_warning_active = False

        # Toast timer
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""

    # ------------------------------------------------------------------
    # Interaction
    # ------------------------------------------------------------------

    def handle_interact(self, player, lantern, inventory=None) -> bool:
        """E-key interaction: crystal recharge and hidden door."""
        if self.is_dead or self.recharge_cooldown > 0:
            return False

        # Hidden Door
        if self.door_locked and is_color_active(lantern, "red"):
            if player.rect.colliderect(self.door_rect.inflate(40, 40)):
                if inventory and inventory.has_key("key_gold"):
                    self.door_locked = False
                    if self.door_rect in self.all_obstacles:
                        self.all_obstacles.remove(self.door_rect)
                    audio.play("door_open")
                    self._toast("The ancient seal breaks...", 3.0)
                else:
                    audio.play("door_locked")
                    self._toast("It is sealed. A gold key is required.", 3.0)
                return True

        for crystal in self.crystals:
            if player.rect.colliderect(crystal.rect.inflate(30, 30)):
                if not has_line_of_sight(player.rect.center, crystal.rect.center, self.walls):
                    continue
                if self.battery.energy >= BatterySystem.MAX_ENERGY:
                    self._toast("Lantern is already fully charged.", 2.0)
                    return True
                self.battery.recharge(CRYSTAL_RECHARGE_AMOUNT)
                crystal.trigger_recharge_effect()
                audio.play("recharge")
                self.recharge_cooldown = 0.5
                pct = int(self.battery.ratio * 100)
                self._toast(f"Lantern recharged! ({pct}%)", 2.5)
                return True

        # Exit Door Inspection
        if player.rect.colliderect(self.exit_door["rect"].inflate(40, 40)):
            inv = inventory if inventory is not None else self.inventory
            required_mirrors = ["mirror_red", "mirror_blue", "mirror_green"]
            count = 0
            if inv:
                count = sum(1 for m in required_mirrors if inv.has_mirror(m))
            else:
                count = sum(1 for m in self.mirrors_in_world if m["collected"])

            if count == 3:
                self.trigger_level3_transition = True
                return True
            else:
                self.exit_door["showing"] = True
                self.exit_door["title"] = "THE PORTAL REMAINS SILENT"
                self.exit_door["line1"] = "You need all three mirrors to enter the Chamber of Convergence."
                self.exit_door["line2"] = f"Mirrors Collected: {count}/3. Return to the temple and find the remaining mirror(s)."
                self.pending_story_modal = (
                    "MISSING MIRRORS",
                    f"Three refractor mirrors are required to unseal the Path of Light.\n\nYou need all three mirrors to enter the Chamber of Convergence.\n\nMirrors Collected: {count}/3\n\nReturn to the temple depths and retrieve the remaining mirror(s).",
                    "l2_exit_missing"
                )
                audio.play("clue")
                return True

        # Collectible Mirrors interaction
        for m in self.mirrors_in_world:
            if m["collected"]:
                continue
            mirror_color = m["id"].replace("mirror_", "")
            if not is_color_active(lantern, mirror_color):
                continue
            if player.rect.colliderect(m["rect"].inflate(30, 30)):
                if not has_line_of_sight(player.rect.center, m["rect"].center, self.walls):
                    continue
                m["collected"] = True
                if inventory:
                    inventory.add_mirror(m["id"])
                    count = inventory.mirror_count
                else:
                    count = 1
                audio.play("clue")
                self._toast(f"Retrieved {m['name']} from the {m.get('container_name', 'ruins')}! ({count}/3 Mirrors)", 3.0)
                return True

        # Dummy Environmental Discovery Objects interaction (investigate empty ruins)
        for dummy in self.dummy_objects:
            if player.rect.colliderect(dummy["rect"].inflate(30, 30)):
                if not has_line_of_sight(player.rect.center, dummy["rect"].center, self.walls):
                    continue
                audio.play("clue")
                self._toast(dummy["inspect_text"], 3.5)
                return True

        # Ancient inscription
        ins = self.inscription
        if player.rect.colliderect(ins["rect"].inflate(30, 30)):
            ins["showing"] = True
            if inventory:
                inventory.add_clue("inscription_l2", ins["title"], ins["line1"] + " " + ins["line2"], "plaque")
            return True

        # Dismiss any open writing modal
        for w in self.ancient_writings:
            if w["showing"]:
                w["showing"] = False
                return True

        # Check Green Light Ancient Writings interaction
        if is_color_active(lantern, "green"):
            for w in self.ancient_writings:
                if player.rect.colliderect(w["rect"].inflate(40, 40)):
                    if not has_line_of_sight(player.rect.center, w["rect"].center, self.walls):
                        continue
                    w["showing"] = True
                    if inventory:
                        inventory.add_clue(w["id"], w["title"], w["line1"] + " " + w["line2"], "sigil")
                    audio.play("clue")
                    return True

        return False

    # ------------------------------------------------------------------
    # Reset (Level 2 only — Level 1 inventory is preserved)
    # ------------------------------------------------------------------

    def reset(self, player):
        """Resets Level 2 state on death.  Does NOT clear Level 1 inventory."""
        self.battery.reset()
        self.shadow.reset()
        player.x = L2_SPAWN_X
        player.y = L2_SPAWN_Y
        self.is_dead = False
        self.death_timer = 0.0
        self.death_cause = ""
        self.recharge_cooldown = 0.0
        
        self.door_locked = True
        if self.door_rect not in self.all_obstacles:
            self.all_obstacles.append(self.door_rect)

        self.bridge_discovered = False
        if self.chasm_left_rect in self.all_obstacles:
            self.all_obstacles.remove(self.chasm_left_rect)
        if self.chasm_right_rect in self.all_obstacles:
            self.all_obstacles.remove(self.chasm_right_rect)
        if self.chasm_full_rect not in self.all_obstacles:
            self.all_obstacles.append(self.chasm_full_rect)

        for crystal in self.crystals:
            crystal.recharge_fx_timer = 0.0
        self._toast("", 0.0)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, surface, player, lantern, camera_offset=(0, 0)):
        """Full Level 2 render pass."""
        is_lit = lantern.possessed and lantern.active
        light_center = player.center
        eff_radius = lantern.radius if is_lit else 0.0
        if is_lit:
            eff_radius = 1200.0

        is_red = is_color_active(lantern, "red")

        vp = pygame.Rect(
            camera_offset[0] - 60, camera_offset[1] - 60,
            L2_SCREEN_WIDTH + 120, L2_SCREEN_HEIGHT + 120,
        )

        # 1  Floor
        surface.blit(self.floor_surf,
                      (-camera_offset[0], -camera_offset[1]))

        # 2  Crystal ground glow (visible through darkness)
        for cr in self.crystals:
            if vp.colliderect(cr.rect.inflate(120, 120)):
                cr.draw_glow(surface, camera_offset)

        # 3  Walls
        self._draw_walls(surface, camera_offset, vp, lantern)

        # 3.5 Red Door Visual Rendering
        dr = self.door_rect.move(-camera_offset[0], -camera_offset[1])
        vstate = self.get_red_door_visual_state(lantern)

        if vstate == "revealed":
            if vp.colliderect(self.door_rect):
                pygame.draw.rect(surface, (35, 20, 25), dr)
                pygame.draw.rect(surface, (80, 30, 35), dr, width=2)
                pygame.draw.rect(surface, (120, 40, 45), dr.inflate(-16, -16), width=1)
                pygame.draw.circle(surface, (200, 60, 60), dr.center, 8, width=2)
                
                near = player.rect.colliderect(self.door_rect.inflate(40, 40))
                if near:
                    font = pygame.font.SysFont("consolas", 11, bold=True)
                    pt = font.render("[E] Open", True, (255, 150, 150))
                    px = dr.centerx - pt.get_width() // 2
                    py = dr.centery - 30 + int(2 * math.sin(self.lighting.flicker_phase))
                    bg = pygame.Surface((pt.get_width() + 8, pt.get_height() + 4), pygame.SRCALPHA)
                    bg.fill((10, 0, 0, 210))
                    surface.blit(bg, (px - 4, py - 2))
                    surface.blit(pt, (px, py))
        elif vstate == "open":
            if vp.colliderect(self.door_rect):
                # Open stone portal archway under active RED light
                pygame.draw.rect(surface, (14, 10, 20), dr)
                pygame.draw.rect(surface, (45, 38, 55), dr, width=2)
                pygame.draw.rect(surface, (70, 60, 35), (dr.x, dr.y, dr.width, 10))
        # For "hidden" and "wall", _draw_walls rendered the unbroken ancient wall visual; Section 3.5 draws nothing extra!

        # 3.6 Blue Chasm Void
        chasm_world = pygame.Rect(750, 640, 400, 90)
        if vp.colliderect(chasm_world):
            cr = chasm_world.move(-camera_offset[0], -camera_offset[1])
            pygame.draw.rect(surface, (3, 2, 6), cr)
            pygame.draw.line(surface, (12, 10, 20), (cr.x, cr.y), (cr.right, cr.y), 2)
            pygame.draw.line(surface, (12, 10, 20), (cr.x, cr.bottom), (cr.right, cr.bottom), 2)
            pygame.draw.lines(surface, (8, 6, 14), False,
                               [(cr.x, cr.y + 3), (cr.x + 100, cr.y + 9), (cr.x + 220, cr.y + 5), (cr.right, cr.y + 11)], 2)
            pygame.draw.lines(surface, (8, 6, 14), False,
                               [(cr.x, cr.bottom - 3), (cr.x + 120, cr.bottom - 9), (cr.x + 280, cr.bottom - 5), (cr.right, cr.bottom - 11)], 2)

        # 3.7 Ancient Blue Bridge (Visible & Traversable ONLY when bridge_discovered is True)
        if self.bridge_discovered and vp.colliderect(self.bridge_rect):
            br = self.bridge_rect.move(-camera_offset[0], -camera_offset[1])

            # End supports / stone abutments
            n_supp = pygame.Rect(br.x - 4, br.y - 10, br.width + 8, 12)
            s_supp = pygame.Rect(br.x - 4, br.bottom - 2, br.width + 8, 12)
            pygame.draw.rect(surface, (35, 42, 58), n_supp, border_radius=2)
            pygame.draw.rect(surface, (18, 22, 32), n_supp, width=1, border_radius=2)
            pygame.draw.rect(surface, (35, 42, 58), s_supp, border_radius=2)
            pygame.draw.rect(surface, (18, 22, 32), s_supp, width=1, border_radius=2)

            # Aged stone masonry body
            pygame.draw.rect(surface, (38, 46, 62), br)
            
            # 4 distinct stone slabs with color variation and seams
            slabs = [
                (pygame.Rect(br.x, br.y, br.width, 20), (44, 52, 70)),
                (pygame.Rect(br.x, br.y + 20, br.width, 20), (36, 44, 60)),
                (pygame.Rect(br.x, br.y + 40, br.width, 20), (46, 54, 72)),
                (pygame.Rect(br.x, br.y + 60, br.width, 20), (38, 46, 62)),
            ]
            for s_rect, s_col in slabs:
                pygame.draw.rect(surface, s_col, s_rect)
            
            for seam_y in (br.y + 20, br.y + 40, br.y + 60):
                pygame.draw.line(surface, (18, 22, 32), (br.x, seam_y), (br.right, seam_y), 2)
            
            # Worn side curbs & outer border
            pygame.draw.rect(surface, (55, 68, 90), (br.x, br.y, 6, br.height))
            pygame.draw.rect(surface, (55, 68, 90), (br.right - 6, br.y, 6, br.height))
            pygame.draw.rect(surface, (20, 25, 36), br, width=2)

            # Central ancient carved ritual rune
            pygame.draw.circle(surface, (60, 140, 240), br.center, 14, width=1)
            pygame.draw.circle(surface, (100, 180, 255), br.center, 8, width=1)
            pygame.draw.circle(surface, (160, 215, 255), br.center, 3)

            # Restrained mystic blue aura & sparks
            aura = pygame.Surface((br.width + 24, br.height + 24), pygame.SRCALPHA)
            pygame.draw.rect(aura, (30, 100, 240, 25), (0, 0, br.width + 24, br.height + 24), border_radius=6)
            spark_pulse = int(35 + 15 * math.sin(self.lighting.flicker_phase * 2))
            pygame.draw.circle(aura, (80, 170, 255, spark_pulse), (br.width // 2 + 12, br.height // 2 + 12), 20)
            surface.blit(aura, (br.x - 12, br.y - 12))

        # 3.7 Level 3 Exit Door (sealed stone doorway)
        self._draw_exit_door(surface, player, camera_offset, vp)

        # 4  Pillars
        self._draw_pillars(surface, camera_offset, vp)

        # 5  Debris
        self._draw_debris(surface, camera_offset, vp,
                          is_lit, light_center, eff_radius)

        # 6a  Inscription
        self._draw_inscription(surface, player, camera_offset, vp,
                               is_lit, light_center, eff_radius)

        # 6b  Green light ancient writings (revealed ONLY when GREEN light is active)
        self._draw_green_writings(surface, player, camera_offset, vp,
                                  is_color_active(lantern, "green"))

        # 6c  Crystals
        for cr in self.crystals:
            if vp.colliderect(cr.rect.inflate(60, 60)):
                near = player.rect.colliderect(cr.rect.inflate(30, 30))
                cr.draw(surface, player_near=near,
                        camera_offset=camera_offset)

        # 6d  Collectible Mirrors
        self._draw_mirrors(surface, player, camera_offset, vp, lantern)

        # 6e  Dummy Environmental Discovery Objects
        self._draw_dummy_objects(surface, player, camera_offset, vp, lantern)

        # 7  Shadow
        self.shadow.draw(surface, player.center,
                         camera_offset=camera_offset)

        # 8  Player
        player.draw(surface, camera_offset=camera_offset,
                     is_lantern_lit=is_lit)

        # 9  Particles
        if is_lit:
            self.lighting.draw_particles(surface, light_center,
                                         eff_radius, camera_offset)

        # 10  Darkness mask
        self._draw_darkness(surface, lantern, light_center, eff_radius,
                            camera_offset)

        # 11  Death fade
        if self.is_dead:
            alpha = min(220, int(220 * (1.0 - self.death_timer / 2.5)))
            ov = pygame.Surface((L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT),
                                pygame.SRCALPHA)
            ov.fill((5, 0, 10, alpha))
            surface.blit(ov, (0, 0))

        # 12a  Inscription modal overlay (drawn last — above darkness)
        if self.inscription["showing"]:
            self._draw_inscription_modal(surface)

        # 12b  Ancient writing modal overlays (drawn last — above darkness)
        for w in self.ancient_writings:
            if w["showing"]:
                self._draw_writing_modal(surface, w)

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def draw_hud(self, surface, font_small, lantern, inventory=None):
        """Battery meter, lantern ON/OFF, colour mode indicator, and mirror counter."""
        # Battery meter (top-left)
        self.lantern_meter.draw(surface, 12, 12, self.battery.ratio,
                                font_small)

        # Lantern status (top-right)
        status = "ON" if lantern.active else "OFF"
        sc = (255, 230, 120) if lantern.active else (100, 100, 100)
        lbl = font_small.render(f"Lantern: {status}", True, sc)
        surface.blit(lbl, (L2_SCREEN_WIDTH - lbl.get_width() - 20, 14))

        # Colour mode dot + label
        cmap = {
            "white": (255, 245, 220), "red": (255, 100, 80),
            "green": (100, 255, 120), "blue": (100, 150, 255),
        }
        dot = cmap.get(lantern.color, (200, 200, 200)) \
            if lantern.active else (80, 80, 80)
        clbl = lantern.color.upper() if lantern.active else "---"
        ml = font_small.render(f"Light: {clbl}", True, dot)
        surface.blit(ml, (L2_SCREEN_WIDTH - ml.get_width() - 20, 32))
        pygame.draw.circle(surface, dot,
                           (L2_SCREEN_WIDTH - ml.get_width() - 30, 39), 4)

        # Mirror Collection Badge (top-right, below color indicator)
        if inventory:
            m_count = inventory.mirror_count
            m_col = (245, 215, 140) if m_count > 0 else (130, 120, 110)
            m_txt = font_small.render(f"Mirrors: {m_count}/3", True, m_col)
            surface.blit(m_txt, (L2_SCREEN_WIDTH - m_txt.get_width() - 20, 52))

        # Death overlay notification box
        if self.is_dead and self.death_cause:
            lines = [ln.strip() for ln in self.death_cause.split("\n") if ln.strip()]
            rendered = []
            for i, ln in enumerate(lines):
                col = (255, 95, 95) if i == 0 else (230, 210, 180)
                rendered.append(font_small.render(ln, True, col))
            max_w = max(r.get_width() for r in rendered) if rendered else 100
            total_h = sum(r.get_height() + 6 for r in rendered)
            bx = (L2_SCREEN_WIDTH - max_w) // 2 - 20
            by = L2_SCREEN_HEIGHT // 2 - total_h // 2 - 10
            box = pygame.Surface((max_w + 40, total_h + 20), pygame.SRCALPHA)
            box.fill((14, 10, 18, 235))
            pygame.draw.rect(box, (200, 60, 60), (0, 0, max_w + 40, total_h + 20), width=2, border_radius=6)
            surface.blit(box, (bx, by))
            cy = by + 10
            for r in rendered:
                surface.blit(r, ((L2_SCREEN_WIDTH - r.get_width()) // 2, cy))
                cy += r.get_height() + 6

        # Toast
        if self.message:
            ms = font_small.render(self.message, True, (200, 240, 255))
            mx = (L2_SCREEN_WIDTH - ms.get_width()) // 2
            my = L2_SCREEN_HEIGHT - 60
            box = pygame.Surface((ms.get_width() + 20,
                                  ms.get_height() + 8), pygame.SRCALPHA)
            box.fill((10, 12, 24, 220))
            pygame.draw.rect(box, (70, 180, 255),
                             (0, 0, box.get_width(), box.get_height()),
                             width=1, border_radius=4)
            surface.blit(box, (mx - 10, my - 4))
            surface.blit(ms, (mx, my))

    # ------------------------------------------------------------------
    # Private drawing helpers
    # ------------------------------------------------------------------

    def _draw_darkness(self, surface, lantern, light_center, eff_radius,
                       camera_offset):
        """Applies the darkness mask — coloured glow when lit."""
        is_lit = lantern.possessed and lantern.active
        scr_w, scr_h = L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT

        # Collect crystal screen-space positions for mask
        crystal_lights = []
        for cr in self.crystals:
            cx = int(cr.x - camera_offset[0])
            cy = int(cr.y - camera_offset[1])
            if -80 <= cx <= scr_w + 80 and -80 <= cy <= scr_h + 80:
                pr = int(48 + 8 * math.sin(cr.pulse))
                crystal_lights.append((cx, cy, pr))

        if is_lit:
            flicker = 3.0 * math.sin(self.lighting.flicker_phase)
            sc = (int(light_center[0] - camera_offset[0]),
                  int(light_center[1] - camera_offset[1]))
            mask = build_colored_darkness_mask(
                (scr_w, scr_h), sc, eff_radius,
                lantern_color=lantern.color,
                darkness_alpha=252,
                flicker_offset=flicker,
                crystal_lights=crystal_lights,
                battery_ratio=self.battery.ratio,
            )
        else:
            # Lantern OFF — near-total darkness; crystals still glow
            mask = pygame.Surface((scr_w, scr_h), pygame.SRCALPHA)
            mask.fill((2, 2, 5, 253))
            for cx, cy, pr in crystal_lights:
                for ti in range(10, 0, -1):
                    tr = ti / 10.0
                    pygame.draw.circle(
                        mask, (2, 2, 5, int(253 * tr * tr)),
                        (cx, cy), int(pr * tr),
                    )
                pygame.draw.circle(mask, (0, 0, 0, 0),
                                   (cx, cy), int(pr * 0.35))

        surface.blit(mask, (0, 0))

    def _draw_walls(self, surface, camera_offset, vp, lantern):
        brick_h, brick_w = 12, 26
        
        walls_to_draw = []
        for wall in self.walls:
            if wall in (self.door_wall_above, self.door_wall_below):
                continue
            walls_to_draw.append(wall)

        vstate = self.get_red_door_visual_state(lantern)
        if vstate in ("hidden", "revealed", "wall"):
            walls_to_draw.append(self.door_wall_solid)
        else:
            walls_to_draw.append(self.door_wall_above)
            walls_to_draw.append(self.door_wall_below)

        for wall in walls_to_draw:
            if not vp.colliderect(wall):
                continue
            wr = wall.move(-camera_offset[0], -camera_offset[1])

            pygame.draw.rect(surface, _WALL_COLOR, wr)

            # Viewport-clipped brick loop
            vis_t = max(wr.top, -brick_h)
            vis_b = min(wr.bottom, L2_SCREEN_HEIGHT + brick_h)
            vis_l = max(wr.left, -brick_w)
            vis_r = min(wr.right, L2_SCREEN_WIDTH + brick_w)

            row0 = ((vis_t - wr.y) // brick_h) * brick_h + wr.y
            for by in range(row0, vis_b, brick_h):
                off = brick_w // 2 if ((by - wr.y) // brick_h) % 2 else 0
                col0_raw = vis_l - wr.x - off
                col0 = (col0_raw // brick_w) * brick_w + wr.x + off
                for bx in range(col0, vis_r, brick_w):
                    bw = min(brick_w - 1, wr.right - bx)
                    bh = min(brick_h - 1, wr.bottom - by)
                    if bw > 0 and bh > 0:
                        br = pygame.Rect(bx, by, bw, bh)
                        pygame.draw.rect(surface, _WALL_STONE, br)
                        pygame.draw.rect(surface, _WALL_DARK, br, width=1)

            pygame.draw.rect(surface, _WALL_DARK, wr, width=2)

    def _draw_pillars(self, surface, camera_offset, vp):
        for p in self.pillars:
            if not vp.colliderect(p):
                continue
            pr = p.move(-camera_offset[0], -camera_offset[1])

            # Shadow
            pygame.draw.rect(surface, (5, 3, 8),
                             (pr.x - 4, pr.bottom - 3, pr.width + 8, 7))
            # Base
            base = pygame.Rect(pr.x - 3, pr.bottom - 7, pr.width + 6, 7)
            pygame.draw.rect(surface, (50, 44, 58), base, border_radius=2)
            pygame.draw.rect(surface, _WALL_DARK, base, width=1,
                             border_radius=2)
            # Body
            pygame.draw.rect(surface, (42, 37, 52), pr, border_radius=3)
            pygame.draw.rect(surface, (56, 50, 65),
                             (pr.x + 3, pr.y + 6, pr.width - 6,
                              pr.height - 12), border_radius=2)
            # Carved bands
            pygame.draw.rect(surface, (120, 90, 45),
                             (pr.x + 2, pr.y + 8, pr.width - 4, 3))
            pygame.draw.rect(surface, (120, 90, 45),
                             (pr.x + 2, pr.bottom - 12, pr.width - 4, 3))
            # Capital
            cap = pygame.Rect(pr.x - 3, pr.y - 3, pr.width + 6, 8)
            pygame.draw.rect(surface, (50, 44, 58), cap, border_radius=2)
            pygame.draw.rect(surface, _WALL_DARK, cap, width=1,
                             border_radius=2)
            # Rune mark
            pygame.draw.circle(surface, (90, 70, 40),
                               (pr.centerx, pr.centery), 3, width=1)
            # Outline
            pygame.draw.rect(surface, _WALL_DARK, pr, width=2,
                             border_radius=3)

    def _draw_debris(self, surface, camera_offset, vp, is_lit,
                     light_center, eff_radius):
        for dx, dy, dtype in self.debris_positions:
            drect = pygame.Rect(int(dx) - 12, int(dy) - 12, 24, 24)
            if not vp.colliderect(drect):
                continue
            sx = int(dx - camera_offset[0])
            sy = int(dy - camera_offset[1])
            lit = is_lit and is_point_lit((dx, dy), light_center, eff_radius)
            if not lit:
                pygame.draw.circle(surface, (10, 8, 16), (sx, sy), 6,
                                   width=1)
                continue
            if dtype == "rubble":
                for rx, ry, rw, rh in [(sx-5, sy-2, 7, 5),
                                       (sx+2, sy-3, 6, 6),
                                       (sx-2, sy+2, 8, 4)]:
                    pygame.draw.rect(surface, (48, 42, 56),
                                     (rx, ry, rw, rh), border_radius=1)
                    pygame.draw.rect(surface, (32, 28, 38),
                                     (rx, ry, rw, rh), width=1,
                                     border_radius=1)
            else:
                for i, (ox, oy) in enumerate([(-4, -3), (3, -1),
                                              (0, 4), (-6, 2)]):
                    c = (52, 46, 60) if i % 2 == 0 else (40, 35, 48)
                    pygame.draw.circle(surface, c, (sx + ox, sy + oy), 3)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _toast(self, text, duration):
        self.message = text
        self.message_timer = duration

    # ------------------------------------------------------------------
    # Inscription — ancient carved tablet (Phase B.1 discovery hint)
    # ------------------------------------------------------------------

    def _draw_inscription(self, surface, player, camera_offset, vp,
                          is_lit, light_center, eff_radius):
        """Renders the ancient inscription tablet in world space."""
        ins = self.inscription
        ir = ins["rect"]
        if not vp.colliderect(ir):
            return

        sx = int(ins["x"] - camera_offset[0])
        sy = int(ins["y"] - camera_offset[1])

        # Carved stone slab
        slab = pygame.Rect(sx - 18, sy - 22, 36, 44)
        pygame.draw.rect(surface, (22, 18, 30), slab, border_radius=3)
        pygame.draw.rect(surface, (40, 35, 50), slab, width=2,
                         border_radius=3)
        # Worn carved lines (decorative — suggest ancient text)
        for i in range(4):
            ly = sy - 14 + i * 8
            lx1 = sx - 12 + (i % 2) * 4
            lx2 = sx + 12 - ((i + 1) % 2) * 4
            pygame.draw.line(surface, (55, 48, 65), (lx1, ly), (lx2, ly), 1)
        # Small rune mark at bottom
        pygame.draw.circle(surface, (80, 65, 45), (sx, sy + 14), 3, width=1)

        # "[E] Inspect" prompt when player is near
        near = player.rect.colliderect(ir.inflate(30, 30))
        if near:
            font = pygame.font.SysFont("consolas", 11, bold=True)
            pt = font.render("[E] Inspect", True, (180, 170, 155))
            px = sx - pt.get_width() // 2
            py = sy - 32 + int(2 * math.sin(self.lighting.flicker_phase))
            bg = pygame.Surface((pt.get_width() + 8, pt.get_height() + 4),
                                pygame.SRCALPHA)
            bg.fill((10, 8, 16, 210))
            surface.blit(bg, (px - 4, py - 2))
            surface.blit(pt, (px, py))

    def _draw_inscription_modal(self, surface):
        """Draws the inscription reading overlay — small, atmospheric."""
        sw, sh = L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT
        modal_w, modal_h = 380, 160
        mx = (sw - modal_w) // 2
        my = (sh - modal_h) // 2

        # Dark stone panel
        panel = pygame.Surface((modal_w, modal_h), pygame.SRCALPHA)
        panel.fill((14, 12, 22, 240))
        pygame.draw.rect(panel, (80, 65, 45),
                         (0, 0, modal_w, modal_h), width=2, border_radius=6)
        pygame.draw.rect(panel, (45, 38, 28),
                         (4, 4, modal_w - 8, modal_h - 8),
                         width=1, border_radius=4)
        surface.blit(panel, (mx, my))

        # Title
        ft = pygame.font.SysFont("georgia", 14, bold=True)
        fb = pygame.font.SysFont("consolas", 13)
        fs = pygame.font.SysFont("consolas", 11)

        ins = self.inscription
        title = ft.render(ins["title"], True, (190, 165, 110))
        surface.blit(title, (mx + (modal_w - title.get_width()) // 2,
                             my + 16))

        # Divider
        pygame.draw.line(surface, (80, 65, 45),
                         (mx + 30, my + 40), (mx + modal_w - 30, my + 40), 1)

        # Body lines — the two cryptic hints
        l1 = fb.render(ins["line1"], True, (210, 200, 185))
        l2 = fb.render(ins["line2"], True, (210, 200, 185))
        surface.blit(l1, (mx + (modal_w - l1.get_width()) // 2, my + 56))
        surface.blit(l2, (mx + (modal_w - l2.get_width()) // 2, my + 82))

        # Close prompt
        cl = fs.render("Press [E] or [SPACE] to close", True,
                        (120, 115, 105))
        surface.blit(cl, (mx + (modal_w - cl.get_width()) // 2,
                          my + modal_h - 26))

    def dismiss_inscription(self):
        """Closes any active modal overlays (called from main.py on E/SPACE/ESC)."""
        self.inscription["showing"] = False
        self.exit_door["showing"] = False
        for w in self.ancient_writings:
            w["showing"] = False

    # ------------------------------------------------------------------
    # Phase C3 Ancient Writings (Green Light Reveal)
    # ------------------------------------------------------------------

    def _draw_green_writings(self, surface, player, camera_offset, vp, is_green_active):
        if not is_green_active:
            return

        font_small = pygame.font.SysFont("consolas", 11, bold=True)
        for w in self.ancient_writings:
            if vp.colliderect(w["rect"].inflate(80, 80)):
                wr = w["rect"].move(-camera_offset[0], -camera_offset[1])
                
                # Render emerald ancient carved glyph on the stone
                pygame.draw.rect(surface, (18, 48, 28), wr, border_radius=3)
                pygame.draw.rect(surface, (50, 180, 90), wr, width=1, border_radius=3)
                
                # Engraved rune symbols
                pygame.draw.line(surface, (80, 240, 140), (wr.x + 8, wr.y + 10), (wr.right - 8, wr.y + 10), 2)
                pygame.draw.line(surface, (60, 200, 110), (wr.x + 12, wr.y + 20), (wr.right - 12, wr.y + 20), 1)
                pygame.draw.circle(surface, (100, 255, 160), wr.center, 4, width=1)

                # Soft glowing emerald aura
                aura = pygame.Surface((wr.width + 20, wr.height + 20), pygame.SRCALPHA)
                pulse = int(30 + 15 * math.sin(self.lighting.flicker_phase * 2))
                pygame.draw.rect(aura, (40, 200, 100, pulse), (0, 0, wr.width + 20, wr.height + 20), border_radius=6)
                surface.blit(aura, (wr.x - 10, wr.y - 10))

                # Interaction prompt when near
                near = player.rect.colliderect(w["rect"].inflate(40, 40))
                if near and not w["showing"]:
                    pt = font_small.render("[E] Inspect Ancient Writing", True, (160, 255, 190))
                    px = wr.centerx - pt.get_width() // 2
                    py = wr.centery - 32 + int(2 * math.sin(self.lighting.flicker_phase))
                    bg = pygame.Surface((pt.get_width() + 8, pt.get_height() + 4), pygame.SRCALPHA)
                    bg.fill((6, 20, 12, 220))
                    surface.blit(bg, (px - 4, py - 2))
                    surface.blit(pt, (px, py))

    def _draw_writing_modal(self, surface, writing):
        sw, sh = L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT
        box_w, box_h = 540, 140
        bx = (sw - box_w) // 2
        by = (sh - box_h) // 2

        # Dim overlay background
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        # Modal box
        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((10, 20, 14, 235))
        pygame.draw.rect(box, (60, 220, 120), (0, 0, box_w, box_h), width=2, border_radius=6)
        pygame.draw.rect(box, (30, 100, 50), (4, 4, box_w - 8, box_h - 8), width=1, border_radius=4)
        surface.blit(box, (bx, by))

        # Text rendering
        f_title = pygame.font.SysFont("consolas", 13, bold=True)
        f_body = pygame.font.SysFont("consolas", 11)
        f_prompt = pygame.font.SysFont("consolas", 11, bold=True)

        t_surf = f_title.render(writing["title"], True, (140, 255, 180))
        surface.blit(t_surf, (bx + 20, by + 16))

        pygame.draw.line(surface, (40, 120, 70), (bx + 20, by + 38), (bx + box_w - 20, by + 38), 1)

        b1 = f_body.render(writing["line1"], True, (220, 245, 230))
        b2 = f_body.render(writing["line2"], True, (200, 235, 215))
        surface.blit(b1, (bx + 20, by + 48))
        surface.blit(b2, (bx + 20, by + 72))

        p_surf = f_prompt.render("Press [E] or [SPACE] to close", True, (120, 180, 140))
        surface.blit(p_surf, (bx + box_w - p_surf.get_width() - 20, by + box_h - 26))

    # ------------------------------------------------------------------
    # Phase C4 Collectible Mirrors & Level 3 Exit Door
    # ------------------------------------------------------------------

    def _draw_mirrors(self, surface, player, camera_offset, vp, lantern):
        if not pygame.font.get_init():
            pygame.font.init()
        font_small = pygame.font.SysFont("consolas", 11, bold=True)
        color_styles = {
            "mirror_red": {
                "glass": (225, 175, 185), "sheen": (255, 220, 230),
                "rim": (140, 65, 75), "aura": (255, 95, 115), "gem": (220, 50, 65),
            },
            "mirror_blue": {
                "glass": (175, 215, 240), "sheen": (225, 245, 255),
                "rim": (65, 95, 145), "aura": (90, 165, 255), "gem": (50, 135, 245),
            },
            "mirror_green": {
                "glass": (175, 235, 195), "sheen": (225, 255, 235),
                "rim": (65, 135, 85), "aura": (90, 245, 145), "gem": (50, 215, 105),
            },
        }

        for m in self.mirrors_in_world:
            if m["collected"]:
                continue
            mirror_color = m["id"].replace("mirror_", "")
            if not is_color_active(lantern, mirror_color):
                continue
            if not vp.colliderect(m["rect"].inflate(60, 60)):
                continue
            mr = m["rect"].move(-camera_offset[0], -camera_offset[1])
            m_style = color_styles.get(m["id"], {
                "glass": (180, 210, 220), "sheen": (240, 250, 255),
                "rim": (100, 130, 140), "aura": (200, 230, 255), "gem": (180, 200, 220),
            })

            # Environmental Container Rendering (believable ancient ruin embedding)
            container_type = m.get("container_type", "ruined_altar")
            if container_type == "ruined_altar":
                # Ancient weathered stone altar pedestal
                altar_rect = pygame.Rect(mr.x - 8, mr.y - 4, mr.width + 16, mr.height + 10)
                step_rect = pygame.Rect(altar_rect.x - 4, altar_rect.bottom - 6, altar_rect.width + 8, 8)
                pygame.draw.rect(surface, (20, 17, 26), step_rect, border_radius=2)
                pygame.draw.rect(surface, (38, 33, 44), altar_rect, border_radius=4)
                pygame.draw.rect(surface, (22, 19, 28), altar_rect, width=1, border_radius=4)
                pygame.draw.line(surface, (16, 14, 20), (altar_rect.x + 6, altar_rect.y + 4), (altar_rect.centerx - 2, altar_rect.centery), 2)
                pygame.draw.line(surface, (16, 14, 20), (altar_rect.centerx - 2, altar_rect.centery), (altar_rect.centerx + 4, altar_rect.bottom - 4), 1)
                # Crevice cavity
                cleft = pygame.Rect(mr.x + 2, mr.y + 4, mr.width - 4, mr.height - 4)
                pygame.draw.rect(surface, (14, 11, 18), cleft, border_radius=3)
                # Embedded Crimson Refractor Mirror: exposed bronze frame edge and crimson glass sliver
                glass = pygame.Rect(cleft.x + 3, cleft.y + 3, cleft.width - 6, cleft.height - 6)
                pygame.draw.rect(surface, (135, 75, 45), glass.inflate(2, 2), border_radius=4)
                pygame.draw.rect(surface, m_style["glass"], glass, border_radius=3)
                pygame.draw.line(surface, m_style["sheen"], (glass.x + 2, glass.bottom - 3), (glass.right - 2, glass.y + 3), 1)
                pygame.draw.circle(surface, m_style["gem"], (glass.centerx, glass.y + 2), 2)
            elif container_type == "petrified_roots":
                # Ancient twisted root knot
                root_rect = pygame.Rect(mr.x - 8, mr.y - 4, mr.width + 16, mr.height + 10)
                pygame.draw.ellipse(surface, (36, 28, 22), (root_rect.x - 4, root_rect.y + 8, root_rect.width + 8, 14))
                pygame.draw.ellipse(surface, (45, 36, 30), root_rect)
                pygame.draw.line(surface, (55, 68, 48), (root_rect.x + 4, root_rect.y + 6), (root_rect.x + 12, root_rect.y + 10), 2)
                pygame.draw.line(surface, (48, 60, 42), (root_rect.right - 12, root_rect.y + 14), (root_rect.right - 4, root_rect.y + 18), 2)
                cleft = pygame.Rect(mr.x + 2, mr.y + 4, mr.width - 4, mr.height - 4)
                pygame.draw.rect(surface, (18, 14, 12), cleft, border_radius=3)
                # Embedded Azure Refractor Mirror: silver rim and azure glass facet
                glass = pygame.Rect(cleft.x + 3, cleft.y + 3, cleft.width - 6, cleft.height - 6)
                pygame.draw.rect(surface, (120, 150, 175), glass.inflate(2, 2), border_radius=4)
                pygame.draw.rect(surface, m_style["glass"], glass, border_radius=3)
                pygame.draw.line(surface, m_style["sheen"], (glass.x + 2, glass.bottom - 3), (glass.right - 2, glass.y + 3), 1)
                pygame.draw.circle(surface, m_style["gem"], (glass.centerx, glass.y + 2), 2)
            elif container_type == "collapsed_arch":
                # Fallen carved keystone & fractured masonry
                arch_rect = pygame.Rect(mr.x - 8, mr.y - 4, mr.width + 16, mr.height + 10)
                pygame.draw.rect(surface, (28, 25, 34), (arch_rect.x - 5, arch_rect.bottom - 6, 8, 6), border_radius=1)
                pygame.draw.rect(surface, (30, 27, 36), (arch_rect.right - 3, arch_rect.y + 2, 7, 7), border_radius=1)
                pygame.draw.rect(surface, (44, 40, 52), arch_rect, border_radius=3)
                pygame.draw.rect(surface, (26, 23, 32), arch_rect, width=1, border_radius=3)
                pygame.draw.line(surface, (60, 55, 70), (arch_rect.x + 4, arch_rect.y + 6), (arch_rect.right - 4, arch_rect.y + 6), 1)
                cleft = pygame.Rect(mr.x + 2, mr.y + 4, mr.width - 4, mr.height - 4)
                pygame.draw.rect(surface, (14, 12, 18), cleft, border_radius=3)
                # Embedded Verdant Refractor Mirror: bronze frame edge and emerald refractor face
                glass = pygame.Rect(cleft.x + 3, cleft.y + 3, cleft.width - 6, cleft.height - 6)
                pygame.draw.rect(surface, (90, 115, 75), glass.inflate(2, 2), border_radius=4)
                pygame.draw.rect(surface, m_style["glass"], glass, border_radius=3)
                pygame.draw.line(surface, m_style["sheen"], (glass.x + 2, glass.bottom - 3), (glass.right - 2, glass.y + 3), 1)
                pygame.draw.circle(surface, m_style["gem"], (glass.centerx, glass.y + 2), 2)
            else:
                # Fallback clean frame
                pygame.draw.rect(surface, (55, 48, 40), mr, border_radius=10)
                pygame.draw.rect(surface, (130, 115, 85), mr, width=2, border_radius=10)
                glass = pygame.Rect(mr.x + 4, mr.y + 4, mr.width - 8, mr.height - 8)
                pygame.draw.rect(surface, m_style["glass"], glass, border_radius=6)
                pygame.draw.line(surface, m_style["sheen"], (glass.x + 3, glass.bottom - 4), (glass.right - 3, glass.y + 4), 2)
                pygame.draw.rect(surface, m_style["rim"], glass, width=1, border_radius=6)
                pygame.draw.circle(surface, m_style["gem"], (mr.centerx, mr.y + 3), 2)

            # Subtle specular glint (1-2px) instead of giant pulsing aura
            glint_alpha = int(90 + 50 * math.sin(self.lighting.flicker_phase * 2.0))
            glint_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
            glint_surf.fill((*m_style["sheen"][:3], glint_alpha))
            surface.blit(glint_surf, (mr.centerx - 2, mr.centery - 2))

            # Prompt when player is near and has direct line of sight
            near = player.rect.colliderect(m["rect"].inflate(30, 30))
            if near and has_line_of_sight(player.rect.center, m["rect"].center, self.walls):
                pt = font_small.render(f"[E] Take {m['name']}", True, (245, 245, 255))
                px = mr.centerx - pt.get_width() // 2
                py = mr.centery - 30 + int(2 * math.sin(self.lighting.flicker_phase))
                bg = pygame.Surface((pt.get_width() + 8, pt.get_height() + 4), pygame.SRCALPHA)
                bg.fill((14, 12, 22, 220))
                surface.blit(bg, (px - 4, py - 2))
                surface.blit(pt, (px, py))

    def _draw_dummy_objects(self, surface, player, camera_offset, vp, lantern):
        """Draws visually similar dummy environmental objects (empty discovery locations)."""
        if not pygame.font.get_init():
            pygame.font.init()
        font_small = pygame.font.SysFont("consolas", 11, bold=True)

        for dummy in self.dummy_objects:
            if not vp.colliderect(dummy["rect"].inflate(60, 60)):
                continue
            dr = dummy["rect"].move(-camera_offset[0], -camera_offset[1])
            dtype = dummy.get("type", "ruined_altar")

            if dtype == "ruined_altar":
                altar_rect = pygame.Rect(dr.x - 8, dr.y - 4, dr.width + 16, dr.height + 10)
                step_rect = pygame.Rect(altar_rect.x - 4, altar_rect.bottom - 6, altar_rect.width + 8, 8)
                pygame.draw.rect(surface, (20, 17, 26), step_rect, border_radius=2)
                pygame.draw.rect(surface, (38, 33, 44), altar_rect, border_radius=4)
                pygame.draw.rect(surface, (22, 19, 28), altar_rect, width=1, border_radius=4)
                pygame.draw.line(surface, (16, 14, 20), (altar_rect.x + 6, altar_rect.y + 4), (altar_rect.centerx - 2, altar_rect.centery), 2)
                pygame.draw.line(surface, (16, 14, 20), (altar_rect.centerx - 2, altar_rect.centery), (altar_rect.centerx + 4, altar_rect.bottom - 4), 1)
                # Empty recessed cavity — weathered dark stone
                cleft = pygame.Rect(dr.x + 2, dr.y + 4, dr.width - 4, dr.height - 4)
                pygame.draw.rect(surface, (14, 11, 18), cleft, border_radius=3)
                pygame.draw.circle(surface, (24, 20, 30), (cleft.centerx, cleft.centery), 3)

            elif dtype == "petrified_roots":
                root_rect = pygame.Rect(dr.x - 8, dr.y - 4, dr.width + 16, dr.height + 10)
                pygame.draw.ellipse(surface, (36, 28, 22), (root_rect.x - 4, root_rect.y + 8, root_rect.width + 8, 14))
                pygame.draw.ellipse(surface, (45, 36, 30), root_rect)
                pygame.draw.line(surface, (55, 68, 48), (root_rect.x + 4, root_rect.y + 6), (root_rect.x + 12, root_rect.y + 10), 2)
                pygame.draw.line(surface, (48, 60, 42), (root_rect.right - 12, root_rect.y + 14), (root_rect.right - 4, root_rect.y + 18), 2)
                # Empty gap between root strands
                cleft = pygame.Rect(dr.x + 2, dr.y + 4, dr.width - 4, dr.height - 4)
                pygame.draw.rect(surface, (18, 14, 12), cleft, border_radius=3)

            elif dtype == "collapsed_arch":
                arch_rect = pygame.Rect(dr.x - 8, dr.y - 4, dr.width + 16, dr.height + 10)
                pygame.draw.rect(surface, (28, 25, 34), (arch_rect.x - 5, arch_rect.bottom - 6, 8, 6), border_radius=1)
                pygame.draw.rect(surface, (30, 27, 36), (arch_rect.right - 3, arch_rect.y + 2, 7, 7), border_radius=1)
                pygame.draw.rect(surface, (44, 40, 52), arch_rect, border_radius=3)
                pygame.draw.rect(surface, (26, 23, 32), arch_rect, width=1, border_radius=3)
                pygame.draw.line(surface, (60, 55, 70), (arch_rect.x + 4, arch_rect.y + 6), (arch_rect.right - 4, arch_rect.y + 6), 1)
                # Empty hollow under block
                cleft = pygame.Rect(dr.x + 2, dr.y + 4, dr.width - 4, dr.height - 4)
                pygame.draw.rect(surface, (14, 12, 18), cleft, border_radius=3)

            # Prompt when player is near and has LOS and lantern is active
            near = player.rect.colliderect(dummy["rect"].inflate(30, 30))
            if near and lantern.active and has_line_of_sight(player.rect.center, dummy["rect"].center, self.walls):
                pt = font_small.render(f"[E] Investigate {dummy['name']}", True, (210, 210, 225))
                px = dr.centerx - pt.get_width() // 2
                py = dr.centery - 28 + int(2 * math.sin(self.lighting.flicker_phase))
                bg = pygame.Surface((pt.get_width() + 8, pt.get_height() + 4), pygame.SRCALPHA)
                bg.fill((14, 12, 22, 220))
                surface.blit(bg, (px - 4, py - 2))
                surface.blit(pt, (px, py))

    def _draw_exit_door(self, surface, player, camera_offset, vp):
        dr_world = self.exit_door["rect"]
        if not vp.colliderect(dr_world.inflate(60, 60)):
            return
        dr = dr_world.move(-camera_offset[0], -camera_offset[1])

        # Large carved stone doorway archway
        arch = pygame.Rect(dr.x - 6, dr.y - 6, dr.width + 12, dr.height + 12)
        pygame.draw.rect(surface, (32, 28, 42), arch, border_radius=4)
        pygame.draw.rect(surface, (65, 55, 75), arch, width=2, border_radius=4)

        # Sealed double stone door body
        pygame.draw.rect(surface, (24, 20, 32), dr)
        pygame.draw.line(surface, (12, 10, 18), (dr.centerx, dr.y), (dr.centerx, dr.bottom), 2)
        pygame.draw.rect(surface, (50, 42, 60), dr, width=2)

        # Iron bands & ancient lock medallion
        pygame.draw.line(surface, (75, 65, 85), (dr.x + 4, dr.y + 12), (dr.right - 4, dr.y + 12), 2)
        pygame.draw.line(surface, (75, 65, 85), (dr.x + 4, dr.bottom - 12), (dr.right - 4, dr.bottom - 12), 2)
        pygame.draw.circle(surface, (110, 95, 60), dr.center, 6)
        pygame.draw.circle(surface, (160, 140, 90), dr.center, 3)

        # Interaction prompt when near
        near = player.rect.colliderect(dr_world.inflate(40, 40))
        if near and not self.exit_door["showing"]:
            font_small = pygame.font.SysFont("consolas", 11, bold=True)
            pt = font_small.render("Portal to Level 3", True, (210, 195, 140))
            px = dr.centerx - pt.get_width() // 2
            py = dr.centery + 26 + int(2 * math.sin(self.lighting.flicker_phase))
            bg = pygame.Surface((pt.get_width() + 8, pt.get_height() + 4), pygame.SRCALPHA)
            bg.fill((12, 10, 18, 220))
            surface.blit(bg, (px - 4, py - 2))
            surface.blit(pt, (px, py))

    def _draw_exit_door_modal(self, surface):
        sw, sh = L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT
        box_w, box_h = 480, 140
        bx = (sw - box_w) // 2
        by = (sh - box_h) // 2

        # Dim overlay background
        overlay = pygame.Surface((sw, sh), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        # Modal box
        box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        box.fill((14, 12, 22, 240))
        pygame.draw.rect(box, (80, 65, 45), (0, 0, box_w, box_h), width=2, border_radius=6)
        pygame.draw.rect(box, (45, 38, 28), (4, 4, box_w - 8, box_h - 8), width=1, border_radius=4)
        surface.blit(box, (bx, by))

        # Text rendering
        f_title = pygame.font.SysFont("georgia", 14, bold=True)
        f_body = pygame.font.SysFont("consolas", 12)
        f_prompt = pygame.font.SysFont("consolas", 11, bold=True)

        t_surf = f_title.render(self.exit_door["title"], True, (200, 180, 140))
        surface.blit(t_surf, (bx + (box_w - t_surf.get_width()) // 2, by + 16))

        pygame.draw.line(surface, (80, 65, 45), (bx + 30, by + 40), (bx + box_w - 30, by + 40), 1)

        b1 = f_body.render(self.exit_door["line1"], True, (220, 210, 195))
        b2 = f_body.render(self.exit_door["line2"], True, (180, 170, 155))
        surface.blit(b1, (bx + (box_w - b1.get_width()) // 2, by + 56))
        surface.blit(b2, (bx + (box_w - b2.get_width()) // 2, by + 82))

        p_surf = f_prompt.render("Press [SPACE] or [ESC] to return", True, (210, 195, 140))
        surface.blit(p_surf, (bx + (box_w - p_surf.get_width()) // 2, by + box_h - 26))
