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





def has_line_of_sight(pos1: tuple[float, float], pos2: tuple[float, float], walls: list[pygame.Rect]) -> bool:
    """Returns True if no solid wall obstructs the straight line between pos1 and pos2."""
    p1 = (int(pos1[0]), int(pos1[1]))
    p2 = (int(pos2[0]), int(pos2[1]))
    for wall in walls:
        if wall.clipline(p1, p2):
            return False
    return True

class Level1Room:
    """Temple foundation assembled from the existing local Level 1 prototype."""

    def __init__(self):
        self.walls=self._build_walls()
        self.pillars=self._build_pillars()
        self.all_obstacles=self.walls+self.pillars
        self.floor_surf=self._render_static_floor()

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

    def update(self,player,dt,inventory=None):
        dx,dy=player.get_input_vector()
        move_with_collision(player,dx,dy,self.all_obstacles,dt)
        player.update_animation(bool(dx or dy),dt)

    def draw(self,surface,player,offset=(0,0),lantern=None):
        surface.blit(self.floor_surf,(-offset[0],-offset[1]))
        for wall in self.walls+self.pillars:
            rect=wall.move(-offset[0],-offset[1])
            pygame.draw.rect(surface,WALL_STONE,rect)
            pygame.draw.rect(surface,WALL_HIGHLIGHT,rect,2)
        player.draw(surface,camera_offset=offset)
