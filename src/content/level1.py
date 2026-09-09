"""Level 1 room: dark temple ruins with columns, arches,
ornate medieval keys, and atmospheric environmental obstacles.

Visual style: dark pixel-art dungeon ruins with cracked stone walls, pillars
with carved arches, rubble/skull obstacles, flickering torch sconces,
and ornate Bronze/Silver/Gold keys matching reference art.
"""

import math
import random
import pygame

from engine.collision import move_with_collision
from engine.lighting import build_darkness_mask, is_point_lit, LightingSystem
from systems.clues import get_level1_clues, ClueObject
from systems.audio import audio

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

ROOM_WIDTH = SCREEN_WIDTH * 2    # 1600
ROOM_HEIGHT = SCREEN_HEIGHT * 2  # 1200

# Deep dark dungeon palette matching reference art
WALL_COLOR = (32, 28, 42)
WALL_STONE = (45, 40, 55)
WALL_HIGHLIGHT = (58, 52, 68)
WALL_DARK = (18, 15, 25)
FLOOR_COLOR = (16, 14, 22)
FLOOR_TILE_A = (20, 18, 28)
FLOOR_TILE_B = (14, 12, 20)
FLOOR_GROUT = (10, 8, 15)




# ---------------------------------------------------------------------------
#  Torch Sconce (wall-mounted fire with radiant shine & warm ground-cast glow)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
#  Wall-Side Foliage & Overgrowth (leaves, moss, grass & crimson weeds)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
#  Line-of-Sight & Wall Occlusion Helper
# ---------------------------------------------------------------------------
def has_line_of_sight(pos1: tuple[float, float], pos2: tuple[float, float], walls: list[pygame.Rect]) -> bool:
    """Returns True if no solid wall obstructs the straight line between pos1 and pos2."""
    p1 = (int(pos1[0]), int(pos1[1]))
    p2 = (int(pos2[0]), int(pos2[1]))
    for wall in walls:
        if wall.clipline(p1, p2):
            return False
    return True


# ---------------------------------------------------------------------------
#  Environmental Obstacle (rubble, skulls, broken pottery, roots, boulders)
# ---------------------------------------------------------------------------
class Obstacle:
    """Environmental detail matching the dark ruins theme. All obstacles are inspectable with [E]."""

    def __init__(self, x: float, y: float, obs_type: str = "rubble", radius: int = 18):
        self.x = x
        self.y = y
        self.obs_type = obs_type
        self.radius = radius

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    @property
    def inspect_text(self) -> str:
        if self.obs_type == "rubble":
            return "Crumbled stone fragments. Loose rubble and masonry dust, but no hidden secrets."
        elif self.obs_type == "book":
            return "An ancient leatherbound grimoire. Its weathered pages have rotted away to ash."
        elif self.obs_type == "pottery":
            return "A cracked ceremonial urn from the First Age. Empty except for ancient silt."
        elif self.obs_type == "skull":
            return "The bleached skull of a fallen wanderer. Its hollow eye sockets hold no clues."
        elif self.obs_type == "chains":
            return "Heavy iron shackles suspended from the stone vault. Rusted solid over centuries."
        elif self.obs_type == "roots":
            return "You search the tangled roots and damp soil... only dried moss and decayed bark lie within."
        elif self.obs_type == "cracked_boulder":
            return "You inspect the cracked limestone boulder... weathered fissures, but nothing concealed inside."
        elif self.obs_type == "masonry_debris":
            return "You search the collapsed masonry rubble... loose stones and ancient mortar dust, but nothing concealed within."
        return "You inspect the ancient ruins... nothing of interest remains here."

    def draw(self, surface: pygame.Surface, is_lit: bool,
             camera_offset: tuple[int, int] = (0, 0)):
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])

        if not is_lit:
            # Barely visible dark silhouette
            pygame.draw.circle(surface, (12, 10, 18), (sx, sy), 8, width=1)
            return

        if self.obs_type == "rubble":
            # Broken stone rubble pile
            stones = [(sx - 6, sy - 2, 8, 6), (sx + 2, sy - 4, 7, 7),
                      (sx - 3, sy + 2, 10, 5), (sx + 4, sy + 1, 6, 5)]
            for rx, ry, rw, rh in stones:
                pygame.draw.rect(surface, (55, 48, 65), (rx, ry, rw, rh), border_radius=2)
                pygame.draw.rect(surface, (35, 30, 42), (rx, ry, rw, rh), width=1, border_radius=2)

        elif self.obs_type == "book":
            # Ancient leatherbound tome resting on the flagstones (matching reference art)
            pygame.draw.rect(surface, (110, 75, 45), (sx - 9, sy - 6, 18, 13), border_radius=2)
            pygame.draw.rect(surface, (145, 105, 65), (sx - 7, sy - 5, 14, 11))
            pygame.draw.line(surface, (215, 205, 185), (sx - 8, sy + 4), (sx + 7, sy + 4), 2)
            pygame.draw.line(surface, (60, 40, 25), (sx - 9, sy - 6), (sx - 9, sy + 6), 2)
            pygame.draw.circle(surface, (200, 165, 75), (sx, sy - 1), 2)

        elif self.obs_type == "skull":
            # Skull and crossbones
            pygame.draw.circle(surface, (185, 175, 160), (sx, sy - 3), 7)
            pygame.draw.circle(surface, (165, 155, 140), (sx, sy - 3), 7, width=1)
            pygame.draw.rect(surface, (175, 165, 150), (sx - 5, sy + 2, 10, 4), border_radius=1)
            pygame.draw.circle(surface, (25, 20, 30), (sx - 3, sy - 4), 2)
            pygame.draw.circle(surface, (25, 20, 30), (sx + 3, sy - 4), 2)
            pygame.draw.rect(surface, (25, 20, 30), (sx - 1, sy - 1, 2, 2))
            pygame.draw.line(surface, (170, 160, 145), (sx - 9, sy + 5), (sx + 9, sy + 11), 2)
            pygame.draw.line(surface, (170, 160, 145), (sx + 9, sy + 5), (sx - 9, sy + 11), 2)

        elif self.obs_type == "pottery":
            # Broken ancient vase/urn
            pygame.draw.polygon(surface, (120, 80, 50), [
                (sx - 5, sy - 8), (sx + 5, sy - 8),
                (sx + 7, sy + 4), (sx - 7, sy + 4)
            ])
            pygame.draw.polygon(surface, (100, 65, 40), [
                (sx - 5, sy - 8), (sx + 5, sy - 8),
                (sx + 7, sy + 4), (sx - 7, sy + 4)
            ], 1)
            pygame.draw.line(surface, (85, 55, 35), (sx - 4, sy - 8), (sx + 2, sy - 5), 2)
            pygame.draw.line(surface, (160, 120, 60), (sx - 6, sy - 2), (sx + 6, sy - 2), 1)

        elif self.obs_type == "chains":
            # Hanging chains from ceiling
            for offset in (-4, 4):
                for link in range(5):
                    ly = sy - 10 + link * 6
                    color = (90, 85, 75) if link % 2 == 0 else (75, 70, 60)
                    pygame.draw.rect(surface, color, (sx + offset - 1, ly, 3, 5), border_radius=1)

        elif self.obs_type == "roots":
            # Dummy hollow root cluster (looks visually similar to Bronze Key hiding spot)
            pygame.draw.ellipse(surface, (26, 22, 18), (sx - 15, sy - 5, 30, 16))
            pygame.draw.circle(surface, (32, 50, 30), (sx - 9, sy + 4), 5)
            pygame.draw.arc(surface, (58, 40, 26), (sx - 13, sy - 10, 26, 18), 0.2, 2.8, 4)
            pygame.draw.arc(surface, (42, 28, 18), (sx - 11, sy - 7, 22, 14), 0.5, 3.1, 3)
            pygame.draw.line(surface, (50, 35, 22), (sx - 11, sy + 3), (sx + 13, sy + 7), 3)
            # Empty hollow
            pygame.draw.ellipse(surface, (12, 10, 16), (sx - 4, sy - 3, 8, 7))

        elif self.obs_type == "cracked_boulder":
            # Dummy fractured limestone boulder (looks visually similar to Silver Key hiding spot)
            pts = [(sx - 14, sy + 9), (sx - 17, sy - 2), (sx - 7, sy - 13), (sx + 8, sy - 11), (sx + 15, sy - 2), (sx + 13, sy + 9)]
            pygame.draw.polygon(surface, (48, 42, 56), pts)
            pygame.draw.polygon(surface, (32, 28, 38), pts, 1)
            pygame.draw.lines(surface, (12, 10, 18), False, [(sx - 7, sy - 13), (sx - 2, sy - 3), (sx + 4, sy + 2), (sx + 2, sy + 9)], 3)

        elif self.obs_type == "masonry_debris":
            # Dummy collapsed lintel and wall masonry (looks visually similar to Gold Key hiding spot)
            pygame.draw.rect(surface, (54, 48, 62), (sx - 15, sy - 7, 30, 9), border_radius=2)
            pygame.draw.rect(surface, (38, 32, 45), (sx - 15, sy - 7, 30, 9), width=1, border_radius=2)
            pygame.draw.rect(surface, (44, 38, 52), (sx - 11, sy + 2, 20, 7), border_radius=1)
            pygame.draw.rect(surface, (28, 24, 35), (sx - 11, sy + 2, 20, 7), width=1, border_radius=1)


def draw_inspect_prompt(surface: pygame.Surface, pos: tuple[int, int], pulse: float = 0.0):
    """Draws the [E] Inspect floating prompt badge matching reference art."""
    prompt_y = pos[1] - 32 + int(2 * math.sin(pulse))
    font = pygame.font.SysFont("consolas", 12, bold=True)
    prompt_txt = font.render("[E] Inspect", True, (255, 235, 180))
    box = pygame.Rect(pos[0] - prompt_txt.get_width() // 2 - 5, prompt_y - 2,
                      prompt_txt.get_width() + 10, prompt_txt.get_height() + 4)
    box_surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
    box_surf.fill((15, 12, 25, 225))
    pygame.draw.rect(box_surf, (190, 160, 90), (0, 0, box.width, box.height), width=1, border_radius=4)
    surface.blit(box_surf, (box.x, box.y))
    surface.blit(prompt_txt, (box.x + 5, box.y + 2))


# ---------------------------------------------------------------------------
#  Jumpable Decorative Terrain Gap (crossable with short 2D jump [SPACE])
# ---------------------------------------------------------------------------
class JumpableGap:
    """A small decorative terrain gap / floor fissure in Level 1.

    Acts as a physical obstacle to normal walking, but can be crossed
    with a short 2D jump [SPACE]. Explicitly flagged as jumpable.
    """

    def __init__(self, x: float, y: float, width: float, height: float, label: str = "decorative_gap"):
        self.rect = pygame.Rect(int(x), int(y), int(width), int(height))
        self.label = label
        self.is_jumpable = True

    def draw(self, surface: pygame.Surface, is_lit: bool,
             camera_offset: tuple[int, int] = (0, 0)):
        r = self.rect.move(-camera_offset[0], -camera_offset[1])
        # Dark pit abyss
        pygame.draw.rect(surface, (6, 5, 10), r, border_radius=2)
        if is_lit:
            # Cracked stone edges
            pygame.draw.rect(surface, (55, 48, 65), r, width=2, border_radius=2)
            pygame.draw.line(surface, (20, 16, 26), (r.left + 2, r.top + 2), (r.right - 2, r.top + 2), 1)
        else:
            pygame.draw.rect(surface, (12, 10, 18), r, width=1, border_radius=2)




# ---------------------------------------------------------------------------
#  Ornate Key (matching reference: hexagonal head with spiral emblem, ornate shaft)
# ---------------------------------------------------------------------------
class Key:
    """Collectible ornate medieval key embedded within authentic environmental features.

    Features hexagonal head plate with spiral/sun emblem, decorative handle, and toothed shaft.
    Subtly concealed within rocks, roots, or masonry with only an exposed metallic edge visible.
    """

    def __init__(self, key_id: str, x: float, y: float, correct: bool,
                 label: str, color: tuple[int, int, int], emblem: str,
                 dark_color: tuple[int, int, int], highlight: tuple[int, int, int],
                 container_type: str = "roots", container_name: str = "Gnarled Roots"):
        self.id = key_id
        self.x = x
        self.y = y
        self.correct = correct
        self.label = label
        self.color = color
        self.dark_color = dark_color
        self.highlight = highlight
        self.emblem = emblem
        self.container_type = container_type
        self.container_name = container_name
        self.collected = False
        self.radius = 20
        self.bob_phase = random.uniform(0, 2 * math.pi)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def update(self, dt: float):
        self.bob_phase = (self.bob_phase + dt * 2.5) % (2 * math.pi)

    def draw(self, surface: pygame.Surface, is_lit: bool,
             camera_offset: tuple[int, int] = (0, 0)):
        px = int(self.x - camera_offset[0])
        py = int(self.y - camera_offset[1])

        if not is_lit:
            # Barely visible dark environmental silhouette in total darkness
            pygame.draw.circle(surface, (12, 10, 18), (px, py), 12, width=1)
            return

        glint_phase = 0.5 + 0.5 * math.sin(self.bob_phase * 2.0)

        # ── 1. RENDER ENVIRONMENTAL CONTAINER & EMBEDDED OBJECT ──
        if self.container_type == "roots":
            # Bronze Key: embedded in gnarled roots and broken flagstones
            pygame.draw.ellipse(surface, (26, 22, 18), (px - 16, py - 6, 32, 18))
            pygame.draw.circle(surface, (32, 50, 30), (px - 10, py + 4), 5)  # Moss patch
            # Twisted root cords
            pygame.draw.arc(surface, (58, 40, 26), (px - 14, py - 12, 28, 20), 0.2, 2.8, 4)
            pygame.draw.arc(surface, (42, 28, 18), (px - 12, py - 8, 24, 16), 0.5, 3.1, 3)
            pygame.draw.line(surface, (50, 35, 22), (px - 12, py + 2), (px + 14, py + 8), 3)

            if not self.collected:
                # Key is partially hidden in hollow: exposed bronze ring & tooth peek out
                hex_pts = [
                    (px - 1, py - 8), (px + 5, py - 8), (px + 8, py - 3),
                    (px + 5, py + 2), (px - 1, py + 2), (px - 4, py - 3)
                ]
                pygame.draw.polygon(surface, self.dark_color, hex_pts)
                pygame.draw.polygon(surface, self.color, hex_pts, width=1)
                pygame.draw.circle(surface, self.color, (px + 2, py - 3), 3)
                # Exposed partial shaft
                pygame.draw.line(surface, self.color, (px + 2, py + 1), (px + 2, py + 7), 2)
                pygame.draw.rect(surface, self.color, (px + 3, py + 4, 3, 2))  # small bit tooth
                # Subtle metallic glint on exposed rim
                if glint_phase > 0.85:
                    pygame.draw.circle(surface, (255, 230, 160), (px - 1, py - 7), 1)
            else:
                # Empty root hollow after collection
                pygame.draw.ellipse(surface, (14, 12, 18), (px - 4, py - 3, 8, 7))

        elif self.container_type == "cracked_boulder":
            # Silver Key: wedged in cracked limestone boulder fissure
            pts = [(px - 15, py + 10), (px - 18, py - 2), (px - 8, py - 14), (px + 8, py - 12), (px + 16, py - 2), (px + 14, py + 10)]
            pygame.draw.polygon(surface, (48, 42, 56), pts)
            pygame.draw.polygon(surface, (32, 28, 38), pts, 1)
            # Deep fracture fissure
            pygame.draw.lines(surface, (12, 10, 18), False, [(px - 8, py - 14), (px - 2, py - 4), (px + 4, py + 2), (px + 2, py + 10)], 3)

            if not self.collected:
                # Silver key nestled in crack: polished edge and spiral plate visible
                pygame.draw.circle(surface, self.dark_color, (px - 1, py - 3), 5)
                pygame.draw.circle(surface, self.color, (px - 1, py - 3), 5, width=1)
                pygame.draw.arc(surface, self.highlight, (px - 4, py - 6, 6, 6), 0, 4.0, 1)
                pygame.draw.line(surface, self.color, (px, py + 2), (px + 3, py + 9), 2)
                pygame.draw.rect(surface, self.color, (px + 3, py + 6, 3, 2))
                # Subtle silver specular glint
                if glint_phase > 0.85:
                    pygame.draw.circle(surface, (245, 250, 255), (px - 3, py - 5), 1)

        elif self.container_type == "masonry_debris":
            # Gold Key: tucked under fallen temple lintel and masonry rubble
            pygame.draw.rect(surface, (54, 48, 62), (px - 16, py - 8, 32, 10), border_radius=2)
            pygame.draw.rect(surface, (38, 32, 45), (px - 16, py - 8, 32, 10), width=1, border_radius=2)
            pygame.draw.rect(surface, (44, 38, 52), (px - 12, py + 2, 22, 8), border_radius=1)
            pygame.draw.rect(surface, (28, 24, 35), (px - 12, py + 2, 22, 8), width=1, border_radius=1)

            if not self.collected:
                # Gold sun plate corner exposed under lintel stone
                gold_corner = [(px - 2, py - 2), (px + 7, py - 6), (px + 10, py + 1), (px + 2, py + 3)]
                pygame.draw.polygon(surface, self.dark_color, gold_corner)
                pygame.draw.polygon(surface, self.color, gold_corner, width=1)
                pygame.draw.circle(surface, self.highlight, (px + 4, py - 1), 3)
                pygame.draw.circle(surface, self.dark_color, (px + 4, py - 1), 1)
                # Subtle gold glint tick
                if glint_phase > 0.85:
                    pygame.draw.circle(surface, (255, 240, 140), (px + 8, py - 5), 1)


# ---------------------------------------------------------------------------
#  Lantern Pickup (small distant light glowing in the darkness)
# ---------------------------------------------------------------------------
class LanternPickup:
    """The glowing lantern resting in the dark temple ruins at the start of Level 1."""

    def __init__(self, x: float = 280, y: float = 390):
        self.x = x
        self.y = y
        self.radius = 18
        self.bob_phase = 0.0
        self.collected = False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def update(self, dt: float):
        self.bob_phase = (self.bob_phase + dt * 4.0) % (2 * math.pi)

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0), player_near: bool = False):
        if self.collected:
            return

        px = int(self.x - camera_offset[0])
        py = int(self.y - camera_offset[1])
        flicker = math.sin(self.bob_phase)

        # Distant warm glowing halo visible piercing through the darkness
        halo_r = int(24 + 5 * flicker)
        glow_surf = pygame.Surface((halo_r * 2, halo_r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 175, 55, 45), (halo_r, halo_r), halo_r)
        pygame.draw.circle(glow_surf, (255, 215, 100, 85), (halo_r, halo_r), halo_r // 2)
        pygame.draw.circle(glow_surf, (255, 245, 180, 160), (halo_r, halo_r), max(2, halo_r // 4))
        surface.blit(glow_surf, (px - halo_r, py - halo_r))

        # Lantern frame, hood, and base
        pygame.draw.rect(surface, (50, 40, 28), (px - 5, py - 4, 10, 12), border_radius=2)
        pygame.draw.rect(surface, (160, 125, 60), (px - 5, py - 4, 10, 12), width=1, border_radius=2)
        # Glowing lantern glass
        pygame.draw.rect(surface, (255, 235, 150), (px - 3, py - 2, 6, 8))
        # Brilliant flame core
        pygame.draw.circle(surface, (255, 255, 230), (px, py + 2), 2)
        # Ring handle
        pygame.draw.circle(surface, (150, 120, 60), (px, py - 6), 3, width=1)

        # Interaction prompt if player is nearby
        if player_near:
            prompt_y = py - self.radius - 14 + int(2 * math.sin(self.bob_phase))
            font = pygame.font.SysFont("consolas", 12, bold=True)
            prompt_txt = font.render("[E] Pick Up Lantern", True, (255, 235, 180))
            box = pygame.Rect(px - prompt_txt.get_width() // 2 - 4, prompt_y - 2,
                              prompt_txt.get_width() + 8, prompt_txt.get_height() + 4)
            box_surf = pygame.Surface((box.width, box.height), pygame.SRCALPHA)
            box_surf.fill((15, 12, 25, 220))
            pygame.draw.rect(box_surf, (190, 160, 90), (0, 0, box.width, box.height), width=1, border_radius=3)
            surface.blit(box_surf, (box.x, box.y))
            surface.blit(prompt_txt, (box.x + 4, box.y + 2))





# ---------------------------------------------------------------------------
#  Level 1 Room
# ---------------------------------------------------------------------------
class Level1Room:
    """Ancient dark temple ruins — Level 1 chamber.

    Features: cracked stone walls with arched alcoves, thick pillars, torch
    sconces, rubble/skull obstacles, and ornate medieval keys.

    Maze layout (1600x1200, south→north):
    - Spawn chamber: bottom center, player wakes here in darkness
    - Main corridor: north from spawn to a three-way fork
    - West branch: leads to Bronze Key dead end (NW area) — forces backtracking
    - East branch: leads to Silver Key in a side chamber (NE area)
    - North passage: central path continuing to Gold Key alcove and exit
    - Gold Key alcove: western pocket requiring a detour from north passage
    - Exit chamber: top center, reached via north passage
    """

    def __init__(self):
        self.walls = self._build_walls()
        self.wall_rects = self.walls
        self.pillars = self._build_pillars()
        self.keys = self._build_keys()
        self.clue_objects: list[ClueObject] = get_level1_clues()

        # Add clue rects to obstacles so they block movement
        self.clue_rects = [c.rect for c in self.clue_objects]

        # Explicitly flagged jumpable decorative gaps (crossable with Spacebar jump)
        self.jumpable_gaps = self._build_jumpable_gaps()
        self.jumpable_gap_rects = [gap.rect for gap in self.jumpable_gaps]

        # All obstacles: walls, pillars, clues, and jumpable gaps (when not jumping)
        self.all_obstacles = self.walls + self.pillars + self.clue_rects + self.jumpable_gap_rects

        # Environmental features
        self.torches = self._build_torches()
        self.obstacles = self._build_obstacles()
        self.wall_foliage = self._build_wall_foliage()

        # Story & tutorial popup triggers
        self.pending_story_modal = None  # (title, text, modal_id)
        self.has_inspected_first_object = False
        self.first_inspect_followup_pending = False
        self.all_keys_popup_shown = False

        # Distant lantern pickup object (in spawn chamber)
        self.lantern_pickup = LanternPickup(680, 1090)

        # Exit door (top center of maze)
        self.exit_rect = pygame.Rect(ROOM_WIDTH // 2 - 38, 28, 76, 34)
        self.is_complete = False
        self.door_open_progress = 0.0

        # Lighting & particles
        self.lighting = LightingSystem(ROOM_WIDTH, ROOM_HEIGHT)

        # UI messaging - Start with narrative wake-up message
        self.message = "You've been trapped in this abandoned temple. Find a way out."
        self.message_timer = 6.0

        # Tutorial state
        self.tutorial_step = 0
        self.has_moved = False
        self.has_toggled_lantern = False
        self.has_opened_clue = False

        # Pre-rendered floor
        self.floor_surf = self._render_static_floor()

    @property
    def first_clue_inspected(self) -> bool:
        return self.has_inspected_first_object

    @first_clue_inspected.setter
    def first_clue_inspected(self, val: bool):
        self.has_inspected_first_object = val

    @property
    def clue_followup_pending(self) -> bool:
        return self.first_inspect_followup_pending

    @clue_followup_pending.setter
    def clue_followup_pending(self, val: bool):
        self.first_inspect_followup_pending = val

    # --- Static layout construction ------------------------------------------

    def _build_walls(self) -> list[pygame.Rect]:
        """Intentionally designed maze for the 1600x1200 temple.

        Layout (south to north):
        - Spawn chamber: bottom center (x:560-1040, y:1048-1168)
        - Main corridor south: x:588-1012, y:756-1048
        - Three-way fork at y≈660-756: open branches west, north, east
        - West branch with dead-end Bronze Key pocket (x:32-250, y:408-680)
        - East branch with dead-end Silver Key chamber (x:1350-1568, y:408-680)
        - North passage: x:536-1064, y:158-650
        - Gold Key alcove: x:32-508, y:158-380 (via gap in north passage left wall at y:280-380)
        - Exit approach: x:740-860, y:40-158
        """
        RW, RH = ROOM_WIDTH, ROOM_HEIGHT
        return [
            # ── OUTER BOUNDARY ──
            # North wall with gap for exit door (gap at x:740-860)
            pygame.Rect(0, 0, 740, 40),
            pygame.Rect(860, 0, RW - 860, 40),
            # South wall
            pygame.Rect(0, RH - 32, RW, 32),
            # West wall
            pygame.Rect(0, 0, 32, RH),
            # East wall
            pygame.Rect(RW - 32, 0, 32, RH),

            # ── SOUTH FILL (seals left/right of spawn & corridor below y=756) ──
            pygame.Rect(32, 756, 528, 412),           # SW fill: x:32-560, y:756-1168
            pygame.Rect(1040, 756, 528, 412),          # SE fill: x:1040-1568, y:756-1168

            # ── MAIN CORRIDOR WALLS (south section y:756-1048) ──
            pygame.Rect(560, 756, 28, 292),            # Left: x:560-588, y:756-1048
            pygame.Rect(1012, 756, 28, 292),           # Right: x:1012-1040, y:756-1048

            # ── WEST BRANCH ──
            pygame.Rect(32, 380, 476, 28),             # West branch top wall: x:32-508, y:380-408
            pygame.Rect(250, 480, 28, 200),            # West divider: x:250-278, y:480-680 (open at y:408-480 into Bronze room, open at y:680-756 into Stump hall)

            # ── EAST BRANCH ──
            pygame.Rect(1092, 380, 476, 28),           # East branch top wall: x:1092-1568, y:380-408
            pygame.Rect(1322, 480, 28, 200),           # East divider: x:1322-1350, y:480-680 (open at y:408-480 into Silver room, open at y:680-756 into Stone hall)

            # ── NORTH PASSAGE ──
            # Left wall with gap for Gold Key alcove entry (gap at y:280-380)
            pygame.Rect(508, 380, 28, 270),            # Left lower: x:508-536, y:380-650
            pygame.Rect(508, 158, 28, 122),            # Left upper: x:508-536, y:158-280
            # Right wall
            pygame.Rect(1064, 158, 28, 492),           # Right: x:1064-1092, y:158-650

            # ── NE FILL (blocks NE corner above east branch) ──
            pygame.Rect(1092, 40, 476, 340),           # x:1092-1568, y:40-380

            # ── NW FILL / GOLD KEY ALCOVE TOP ──
            pygame.Rect(32, 40, 476, 118),             # x:32-508, y:40-158
            # Alcove walkable: x:32-508, y:158-380

            # ── EXIT APPROACH (narrows toward exit door) ──
            pygame.Rect(536, 40, 204, 118),            # Left narrows: x:536-740, y:40-158
            pygame.Rect(860, 40, 204, 118),            # Right narrows: x:860-1064, y:40-158
        ]

    def _build_pillars(self) -> list[pygame.Rect]:
        return [
            # Main corridor south atmosphere
            pygame.Rect(640, 870, 40, 55),
            pygame.Rect(920, 870, 40, 55),
            # North passage columned hall
            pygame.Rect(600, 460, 40, 50),
            pygame.Rect(960, 460, 40, 50),
            pygame.Rect(600, 610, 40, 50),
            pygame.Rect(960, 610, 40, 50),
            # Gold key alcove landmark
            pygame.Rect(300, 240, 40, 50),
            # West branch
            pygame.Rect(100, 670, 35, 50),
            # East branch
            pygame.Rect(1450, 670, 35, 50),
        ]

    def _build_keys(self) -> list[Key]:
        """Keys embedded within authentic environmental features across distinct exploration branches."""
        return [
            Key("key_bronze", 140, 500, correct=False, label="Bronze Key",
                color=(165, 105, 55), emblem="orb",
                dark_color=(100, 60, 30), highlight=(220, 160, 80),
                container_type="roots", container_name="Gnarled Roots"),
            Key("key_silver", 1460, 500, correct=False, label="Silver Key",
                color=(185, 190, 200), emblem="spiral",
                dark_color=(120, 125, 135), highlight=(230, 235, 245),
                container_type="cracked_boulder", container_name="Cracked Pillar Base"),
            Key("key_gold", 270, 260, correct=True, label="Gold Key",
                color=(225, 185, 45), emblem="sun",
                dark_color=(160, 120, 25), highlight=(255, 235, 100),
                container_type="masonry_debris", container_name="Fallen Masonry"),
        ]

    def _build_torches(self):
        return []

    def _build_obstacles(self) -> list[Obstacle]:
        return [
            # Main corridor south (stones, book, skull, pottery)
            Obstacle(650, 800, "rubble"),
            Obstacle(730, 940, "book"),
            Obstacle(950, 810, "rubble"),
            Obstacle(700, 1000, "skull"),
            Obstacle(900, 990, "pottery"),
            # West branch (book, skull, chains)
            Obstacle(190, 620, "book"),
            Obstacle(200, 700, "skull"),
            Obstacle(80, 430, "chains"),
            # East branch (book, rubble, chains)
            Obstacle(1430, 520, "book"),
            Obstacle(1350, 650, "rubble"),
            Obstacle(1500, 430, "chains"),
            # North passage
            Obstacle(650, 400, "pottery"),
            Obstacle(900, 500, "rubble"),
            Obstacle(700, 650, "skull"),
            # Gold alcove
            Obstacle(150, 200, "chains"),
            Obstacle(400, 300, "rubble"),
            # Spawn area
            Obstacle(620, 1100, "pottery"),
            Obstacle(950, 1120, "rubble"),

            # ── DUMMY ENVIRONMENTAL OBJECTS (Visually similar to real key containers) ──
            # Dummy gnarled roots (looks similar to Bronze Key hiding spot, but empty)
            Obstacle(880, 720, "roots"),
            Obstacle(440, 540, "roots"),
            Obstacle(1200, 620, "roots"),

            # Dummy cracked boulders (looks similar to Silver Key hiding spot, but empty)
            Obstacle(680, 520, "cracked_boulder"),
            Obstacle(1380, 440, "cracked_boulder"),
            Obstacle(220, 620, "cracked_boulder"),

            # Dummy fallen masonry debris (looks similar to Gold Key hiding spot, but empty)
            Obstacle(180, 320, "masonry_debris"),
            Obstacle(820, 480, "masonry_debris"),
            Obstacle(1020, 320, "masonry_debris"),
        ]

    def _build_wall_foliage(self):
        return []



    def _build_jumpable_gaps(self) -> list[JumpableGap]:
        """Explicitly flagged decorative terrain gaps for Level 1 traversal.

        These are small, optional floor fissures that block normal walking
        but can be hopped across with [SPACE]. They do NOT block keys, clues,
        or the exit, nor do they bypass major maze exploration.
        """
        return [
            # Gap 1: Decorative floor fissure in south main corridor (between pillars)
            # Corridor is 424px wide; gap is 70px wide in the center, leaving >160px on either side.
            JumpableGap(760, 880, 70, 16, label="south_corridor_fissure"),
            # Gap 2: Decorative floor fissure in north passage
            # Passage is 528px wide; gap is 70px wide in the center, leaving >200px on either side.
            JumpableGap(765, 500, 70, 16, label="north_passage_fissure"),
        ]

    def _render_static_floor(self) -> pygame.Surface:
        """Dark stone flagstone floor with deep grout lines and cracks."""
        surf = pygame.Surface((ROOM_WIDTH, ROOM_HEIGHT))
        surf.fill(FLOOR_COLOR)

        tile_size = 38
        for y in range(0, ROOM_HEIGHT, tile_size):
            for x in range(0, ROOM_WIDTH, tile_size):
                tr = pygame.Rect(x, y, tile_size - 2, tile_size - 2)
                # Randomized stone shade
                shade = ((x * 7 + y * 13) % 5)
                if shade < 2:
                    c = FLOOR_TILE_A
                elif shade < 4:
                    c = FLOOR_TILE_B
                else:
                    c = (18, 16, 25)
                pygame.draw.rect(surf, c, tr)
                pygame.draw.rect(surf, FLOOR_GROUT, tr, width=1)

        # Deep ancient cracks (spread across expanded floor)
        cracks = [
            ((130, 170), (150, 185), (175, 180), (195, 200)),
            ((600, 280), (620, 300), (640, 295)),
            ((350, 480), (370, 495), (395, 490)),
            ((260, 155), (280, 175), (275, 195)),
            ((500, 450), (520, 465), (535, 462)),
            ((400, 150), (380, 165), (390, 180)),
            ((900, 500), (920, 520), (940, 515)),
            ((1200, 650), (1220, 670), (1240, 665)),
            ((800, 900), (820, 915), (845, 910)),
            ((1400, 450), (1420, 465), (1435, 462)),
            ((200, 800), (220, 815), (240, 810)),
            ((700, 1050), (720, 1065), (735, 1060)),
        ]
        for crack in cracks:
            pygame.draw.lines(surf, (8, 6, 12), False, crack, 1)

        # Blood/moss stains
        stains = [
            (200, 380), (550, 400), (380, 280), (150, 490),
            (900, 600), (1300, 500), (750, 850), (1100, 700),
            (300, 700), (600, 1050), (1400, 600),
        ]
        for stx, sty in stains:
            stain_surf = pygame.Surface((16, 12), pygame.SRCALPHA)
            pygame.draw.ellipse(stain_surf, (20, 35, 18, 40), (0, 0, 16, 12))
            surf.blit(stain_surf, (stx, sty))

        return surf

    # --- Runtime Updates -----------------------------------------------------

    def update(self, player, inventory, lantern, dt: float, camera=None):
        self.lighting.update(dt, ROOM_WIDTH, ROOM_HEIGHT)

        if self.lantern_pickup and not self.lantern_pickup.collected:
            self.lantern_pickup.update(dt)

        for key in self.keys:
            key.update(dt)
        for clue in self.clue_objects:
            clue.update(dt)
        for torch in self.torches:
            torch.update(dt)

        # Player movement & collision
        dx, dy = player.get_input_vector()
        is_moving = (dx != 0.0 or dy != 0.0)
        if is_moving and not self.has_moved:
            self.has_moved = True
            if self.tutorial_step == 0:
                self.tutorial_step = 1

        move_with_collision(player, dx, dy, self.all_obstacles, dt,
                            jumpable_gaps=self.jumpable_gap_rects)
        player.update_animation(is_moving, dt)

        # Key Auto-Pickup
        for key in self.keys:
            if not key.collected and player.rect.colliderect(key.rect):
                if has_line_of_sight(player.rect.center, key.rect.center, self.wall_rects):
                    key.collected = True
                    inventory.add_key(key.id)
                    audio.play("pickup")
                    self._show_message(f"Collected the {key.label}! ({inventory.key_count} of 3 keys)", 3.0)
                    if self.tutorial_step < 3:
                        self.tutorial_step = 3

                    # Milestone: All 3 keys collected triggers grand guidance popup
                    if inventory.key_count == 3 and not self.all_keys_popup_shown:
                        self.all_keys_popup_shown = True
                        self.pending_story_modal = (
                            "All Three Keys Acquired!",
                            "You have gathered all three ancient keys (Bronze, Silver, Gold)! The Sanctum Threshold awaits at the far north end of the chamber. Approach the door to make your choice.",
                            "all_keys"
                        )

        # Exit Door opening animation
        if self.is_complete and self.door_open_progress < 1.0:
            self.door_open_progress = min(1.0, self.door_open_progress + dt * 1.2)

        # Toast timer countdown
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message = ""

    # --- Player Interaction --------------------------------------------------

    def handle_interact(self, player, inventory, clue_modal=None, lantern=None, door_modal=None) -> bool:
        # 0. Check Lantern pickup proximity (if not yet possessed)
        if self.lantern_pickup and not self.lantern_pickup.collected:
            if player.rect.colliderect(self.lantern_pickup.rect.inflate(30, 30)):
                if has_line_of_sight(player.rect.center, self.lantern_pickup.rect.center, self.wall_rects):
                    self.lantern_pickup.collected = True
                    if lantern:
                        lantern.possessed = True
                        lantern.active = True
                        lantern.radius = lantern.base_radius
                    audio.play("pickup")
                    self._show_message("You'll need to collect keys to unlock the way forward.", 5.0)
                    return True

        # 1. Check Clue proximity (3 true clues)
        for clue in self.clue_objects:
            if clue.rect.colliderect(player.rect.inflate(28, 28)):
                if not has_line_of_sight(player.rect.center, clue.rect.center, self.wall_rects):
                    continue
                clue.triggered = True
                self.has_opened_clue = True
                if inventory:
                    inventory.add_clue(clue.id, clue.title, clue.prompt_text, clue.clue_type)
                audio.play("clue")
                if not self.has_inspected_first_object:
                    self.has_inspected_first_object = True
                    self.first_inspect_followup_pending = True
                if clue_modal:
                    clue_modal.open(clue.title, clue.prompt_text, clue.clue_type)
                else:
                    self._show_message(clue.prompt_text, 6.0)
                if self.tutorial_step < 2:
                    self.tutorial_step = 2
                return True

        # 1b. Check Key inspection / pickup via [E]
        for key in self.keys:
            if not key.collected and player.rect.colliderect(key.rect.inflate(32, 32)):
                if not has_line_of_sight(player.rect.center, key.rect.center, self.wall_rects):
                    continue
                key.collected = True
                inventory.add_key(key.id)
                audio.play("pickup")
                self._show_message(f"Investigated the {key.container_name}... Discovered and collected the {key.label}! ({inventory.key_count} of 3 keys)", 3.5)
                if not self.has_inspected_first_object:
                    self.has_inspected_first_object = True
                    self.pending_story_modal = (
                        "Searching the Sanctum",
                        "You can inspect objects throughout the temple by pressing [E]. Some relics hold vital clues, while others are mere ruins. Keep looking out for objects as you explore.",
                        "inspect_followup"
                    )
                if self.tutorial_step < 3:
                    self.tutorial_step = 3
                if inventory.key_count == 3 and not self.all_keys_popup_shown:
                    self.all_keys_popup_shown = True
                    self.pending_story_modal = (
                        "All Three Keys Acquired!",
                        "You have gathered all three ancient keys (Bronze, Silver, Gold)! The Sanctum Threshold awaits at the far north end of the chamber. Approach the door to make your choice.",
                        "all_keys"
                    )
                return True

        # 2. Check Obstacle proximity (all environmental objects in path are [E] inspectable!)
        for obs in self.obstacles:
            if player.rect.colliderect(obs.rect.inflate(28, 28)):
                if not has_line_of_sight(player.rect.center, obs.rect.center, self.wall_rects):
                    continue
                audio.play("clue")
                if not self.has_inspected_first_object:
                    self.has_inspected_first_object = True
                    self.pending_story_modal = (
                        "Searching the Sanctum",
                        "You can inspect objects throughout the temple by pressing [E]. Some relics hold vital clues, while others are mere ruins. Keep looking out for objects as you explore.",
                        "inspect_followup"
                    )
                self._show_message(obs.inspect_text, 3.5)
                return True

        # 3. Check Exit door proximity
        if player.rect.colliderect(self.exit_rect.inflate(36, 36)):
            if door_modal:
                door_modal.open(inventory)
                audio.play("clue")
                return True
            self._attempt_exit(inventory)
            return True

        return False

    def select_and_try_key(self, inventory, key_number: int, camera=None):
        key_id_map = {1: "key_bronze", 2: "key_silver", 3: "key_gold"}
        key_id = key_id_map.get(key_number)
        if not key_id:
            return
        if not inventory.has_key(key_id):
            self._show_message(f"You haven't found Key #{key_number} yet.", 2.5)
            audio.play("door_locked")
            return
        self._try_key(key_id, camera)

    def _attempt_exit(self, inventory):
        if not inventory.keys:
            self._show_message("The sanctum door is sealed shut. You need a key.", 3.0)
            audio.play("door_locked")
            return
        self._show_message("Press [1], [2], or [3] to select a key to insert.", 3.5)

    def _try_key(self, key_id: str, camera=None):
        key = next((k for k in self.keys if k.id == key_id), None)
        if not key:
            return
        if key.correct:
            self.is_complete = True
            audio.play("door_open")
            if camera:
                camera.trigger_shake(intensity=5.0, duration=0.6)
            self._show_message("The Gold Key turns! The ancient threshold opens.", 4.0)
        else:
            audio.play("door_locked")
            if camera:
                camera.trigger_shake(intensity=4.0, duration=0.25)
            self._show_message(f"The {key.label} rattles. Reconsider the temple clues.", 3.5)

    def _show_message(self, text: str, duration: float):
        self.message = text
        self.message_timer = duration

    def get_objective_hint(self, inventory, lantern=None) -> str:
        if lantern and not lantern.possessed:
            return "Find the source of light in the darkness."
        if self.is_complete:
            return "Sanctum unsealed! Proceed forward."
        if not inventory.keys:
            return "Explore the dark ruins. Find keys and read the clues."
        if len(inventory.keys) < 3:
            return f"Keys: {len(inventory.keys)}/3. Use clues to find the true key."
        return "All keys found! Choose the true key at the Exit Door."

    # --- Rendering -----------------------------------------------------------

    def draw(self, surface: pygame.Surface, player, lantern,
             camera_offset: tuple[int, int] = (0, 0)):
        is_lit_effective = lantern.possessed and lantern.active
        light_center = (player.center[0], player.center[1])
        eff_radius = lantern.radius if is_lit_effective else 0.0

        # 1. Floor
        surface.blit(self.floor_surf, (-camera_offset[0], -camera_offset[1]))

        # 1b. Torch Ground-Cast Glow Pools (warm light pools on stone pavers beneath sconces, Image 2)
        for torch in self.torches:
            lit = is_lit_effective and is_point_lit((torch.x, torch.y), light_center, eff_radius + 60)
            torch.draw_ground_glow(surface, lit, camera_offset)

        # 1c. Jumpable Decorative Terrain Gaps
        for gap in self.jumpable_gaps:
            lit = is_lit_effective and is_point_lit(gap.rect.center, light_center, eff_radius)
            gap.draw(surface, lit, camera_offset)

        # 1d. Wall-side Overgrowth, Leaves, Moss, and Crimson Weeds (along wall bases, Image 1)
        for fol in self.wall_foliage:
            lit = is_lit_effective and is_point_lit((fol.x, fol.y), light_center, eff_radius)
            fol.draw(surface, lit, camera_offset)

        # 2. Outer Walls with stone texture and arched alcoves
        self._draw_walls(surface, camera_offset)

        # 3. Pillars (thick stone columns with carved detail)
        self._draw_pillars(surface, camera_offset)

        # 4. Exit Door
        self._draw_exit_door(surface, camera_offset)

        # 5. Torch Sconces (iron brackets, multi-layer flame, rising embers, and radiant shine)
        for torch in self.torches:
            lit = is_lit_effective and is_point_lit((torch.x, torch.y), light_center, eff_radius + 60)
            torch.draw(surface, lit, camera_offset)

        # 6. Environmental Obstacles
        for obs in self.obstacles:
            lit = is_lit_effective and is_point_lit((obs.x, obs.y), light_center, eff_radius)
            obs.draw(surface, lit, camera_offset)

        # 7. Clues & Keys
        for clue in self.clue_objects:
            lit = is_lit_effective and is_point_lit((clue.x, clue.y), light_center, eff_radius)
            clue.draw(surface, lit, camera_offset=camera_offset)

        # 7b. Tutorial [E] Inspect label: shown ONLY for the first object the player ever approaches
        if not self.has_inspected_first_object and is_lit_effective:
            target_obj = None
            for clue in self.clue_objects:
                if player.rect.colliderect(clue.rect.inflate(28, 28)):
                    if has_line_of_sight(player.rect.center, clue.rect.center, self.wall_rects):
                        target_obj = clue
                        break
            if not target_obj:
                for obs in self.obstacles:
                    if player.rect.colliderect(obs.rect.inflate(28, 28)):
                        if has_line_of_sight(player.rect.center, obs.rect.center, self.wall_rects):
                            target_obj = obs
                            break
            if not target_obj:
                for key in self.keys:
                    if not key.collected and player.rect.colliderect(key.rect.inflate(28, 28)):
                        if has_line_of_sight(player.rect.center, key.rect.center, self.wall_rects):
                            target_obj = key
                            break
            if target_obj:
                draw_pos = (int(target_obj.x - camera_offset[0]), int(target_obj.y - camera_offset[1]))
                draw_inspect_prompt(surface, draw_pos, getattr(target_obj, "pulse", 0.0))

        for key in self.keys:
            lit = is_lit_effective and is_point_lit((key.x, key.y), light_center, eff_radius)
            key.draw(surface, lit, camera_offset=camera_offset)

        # 8. Player
        player.draw(surface, camera_offset=camera_offset, is_lantern_lit=is_lit_effective)

        # 9. Dust/ember particles
        if is_lit_effective:
            self.lighting.draw_particles(surface, light_center, eff_radius, camera_offset)

        # 10. Dynamic Darkness Mask
        if is_lit_effective:
            flicker = 3.0 * math.sin(self.lighting.flicker_phase)
            scr_center = (int(light_center[0] - camera_offset[0]),
                          int(light_center[1] - camera_offset[1]))

            # Gather active torches discovered in lantern range to illuminate darkness mask
            torch_lights = []
            for torch in self.torches:
                if is_point_lit((torch.x, torch.y), light_center, eff_radius + 60):
                    tx = int(torch.x - camera_offset[0])
                    ty = int(torch.y - camera_offset[1])
                    if -60 <= tx <= SCREEN_WIDTH + 60 and -60 <= ty <= SCREEN_HEIGHT + 60:
                        torch_lights.append((tx, ty, 68))

            mask = build_darkness_mask(
                (SCREEN_WIDTH, SCREEN_HEIGHT), scr_center,
                lantern.radius, darkness_alpha=252, flicker_offset=flicker,
                extra_lights=torch_lights
            )
            surface.blit(mask, (0, 0))
        else:
            # Near-total darkness when unpossessed or lantern is off
            black_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            black_mask.fill((2, 2, 5, 253))
            if not lantern.possessed:
                # Faint ambient presence around explorer so the player can discern their wizard silhouette in the dark
                pl_sx = int(light_center[0] - camera_offset[0])
                pl_sy = int(light_center[1] - camera_offset[1])
                for r_sub, a_sub in [(34, 242), (24, 222), (16, 195)]:
                    pygame.draw.circle(black_mask, (2, 2, 5, a_sub), (pl_sx, pl_sy), r_sub)
            surface.blit(black_mask, (0, 0))

        # 11. Distant Lantern Pickup (glowing in darkness until picked up)
        if not lantern.possessed and self.lantern_pickup and not self.lantern_pickup.collected:
            is_near = player.rect.colliderect(self.lantern_pickup.rect.inflate(30, 30))
            self.lantern_pickup.draw(surface, camera_offset=camera_offset, player_near=is_near)



    def _draw_walls(self,surface,camera_offset):
        for obstacle in self.walls:
            rect=obstacle.move(-camera_offset[0],-camera_offset[1])
            pygame.draw.rect(surface,WALL_STONE,rect)
            pygame.draw.rect(surface,WALL_HIGHLIGHT,rect,2)

    def _draw_pillars(self,surface,camera_offset):
        for obstacle in self.pillars:
            rect=obstacle.move(-camera_offset[0],-camera_offset[1])
            pygame.draw.rect(surface,WALL_STONE,rect)
            pygame.draw.rect(surface,WALL_HIGHLIGHT,rect,2)

    def _draw_exit_door(self, surface: pygame.Surface, camera_offset: tuple[int, int]):
        dr = self.exit_rect.move(-camera_offset[0], -camera_offset[1])

        # Grand stone archway frame
        arch_w = dr.width + 28
        arch_h = dr.height + 24
        arch_x = dr.centerx - arch_w // 2
        arch_y = dr.y - 16

        # Arch keystone blocks
        pygame.draw.rect(surface, (55, 48, 40), (arch_x, arch_y, arch_w, arch_h),
                         border_radius=8)
        pygame.draw.rect(surface, (80, 65, 45), (arch_x, arch_y, arch_w, 10),
                         border_radius=4)
        pygame.draw.rect(surface, (35, 28, 22), (arch_x, arch_y, arch_w, arch_h),
                         width=2, border_radius=8)

        # Ornate gold arch trim
        pygame.draw.rect(surface, (190, 155, 65),
                         (arch_x + 3, arch_y + 3, arch_w - 6, arch_h - 6),
                         width=1, border_radius=6)

        # Sun Sigil carved at the apex
        apex = (dr.centerx, arch_y + 8)
        pygame.draw.circle(surface, (220, 180, 60), apex, 6)
        for i in range(8):
            a = i * math.pi / 4
            rx = apex[0] + int(10 * math.cos(a))
            ry = apex[1] + int(10 * math.sin(a))
            pygame.draw.line(surface, (235, 200, 80), apex, (rx, ry), 1)

        # Door
        if not self.is_complete:
            # Closed heavy stone double doors
            pygame.draw.rect(surface, (30, 25, 20), dr)
            # Center seam
            pygame.draw.line(surface, (18, 14, 10),
                             (dr.centerx, dr.y), (dr.centerx, dr.bottom), 2)
            # Iron bands
            pygame.draw.line(surface, (65, 60, 50),
                             (dr.x + 4, dr.centery - 5), (dr.right - 4, dr.centery - 5), 2)
            pygame.draw.line(surface, (65, 60, 50),
                             (dr.x + 4, dr.centery + 5), (dr.right - 4, dr.centery + 5), 2)
            # Keyhole
            pygame.draw.circle(surface, (180, 150, 70), (dr.centerx, dr.centery), 4)
            pygame.draw.polygon(surface, (180, 150, 70), [
                (dr.centerx - 2, dr.centery + 2),
                (dr.centerx + 2, dr.centery + 2),
                (dr.centerx + 3, dr.centery + 8),
                (dr.centerx - 3, dr.centery + 8),
            ])
        else:
            # Door opened — golden light floods through
            open_w = int(dr.width * self.door_open_progress)
            glow_rect = pygame.Rect(dr.centerx - open_w // 2, dr.y,
                                    open_w, dr.height)
            pygame.draw.rect(surface, (255, 240, 190), glow_rect)
            # Light beams
            beam = pygame.Surface((dr.width + 100, 90), pygame.SRCALPHA)
            pygame.draw.polygon(beam, (255, 235, 160, 60), [
                (50, 0), (dr.width + 50, 0),
                (dr.width + 100, 90), (0, 90)
            ])
            surface.blit(beam, (dr.x - 50, dr.bottom))
