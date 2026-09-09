"""entities/mirror.py — Ancient Refractor Mirror entity for Lumen Level 3.

Each mirror is seated in a fixed socket pedestal. The player can interact with
the mirror to rotate it through exactly 8 discrete orientations (45° increments).
"""

import math
import pygame
from engine.reflection import get_orientation_normal, calculate_reflection


class Mirror:
    """Fixed-socket refractor mirror with 8 discrete orientation states."""

    NUM_ORIENTATIONS = 8

    def __init__(
        self,
        mirror_id: str,
        socket_id: str,
        x: float,
        y: float,
        orientation: int = 0,
        name: str = "Refractor Mirror",
        is_trial: bool = False,
    ):
        self.id = mirror_id
        self.socket_id = socket_id
        self.x = float(x)
        self.y = float(y)
        self.orientation = int(orientation) % self.NUM_ORIENTATIONS
        self.name = name
        self.radius = 24.0
        self.is_trial = bool(is_trial)
        self.placed = False

        # Refractor color styling
        if self.is_trial:
            self.gem_color = (200, 170, 120)
            self.aura_color = (210, 190, 150)
        elif "red" in mirror_id:
            self.gem_color = (230, 50, 65)
            self.aura_color = (255, 90, 110)
        elif "blue" in mirror_id:
            self.gem_color = (50, 140, 255)
            self.aura_color = (90, 160, 255)
        elif "green" in mirror_id:
            self.gem_color = (50, 220, 100)
            self.aura_color = (90, 245, 140)
        else:
            self.gem_color = (220, 200, 140)
            self.aura_color = (240, 230, 190)

    @property
    def refractor_color(self) -> str | None:
        """Returns the refractor color associated with this mirror ('red', 'blue', 'green', or None for trial)."""
        if self.is_trial:
            return None
        if "red" in self.id:
            return "red"
        elif "blue" in self.id:
            return "blue"
        elif "green" in self.id:
            return "green"
        return None

    @property
    def is_trial_mirror(self) -> bool:
        """Indicates if this mirror is an environmental trial mirror or a player mirror."""
        return self.is_trial

    @property
    def is_collectible(self) -> bool:
        """Level 3 mirrors are permanently socketed and cannot be collected into inventory."""
        return False

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            int(self.radius * 2),
            int(self.radius * 2)
        )

    @property
    def normal(self) -> tuple[float, float]:
        """Returns the normal unit vector for the mirror's current orientation."""
        return get_orientation_normal(self.orientation)

    def rotate(self, step: int = 1):
        """Rotates the mirror by a discrete number of steps (default 1 = 45°)."""
        self.orientation = (self.orientation + step) % self.NUM_ORIENTATIONS

    def reflect_beam(self, incoming_dir: tuple[float, float]) -> tuple[float, float]:
        """Calculates reflected direction using the mirror's current normal."""
        return calculate_reflection(incoming_dir, self.normal)

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: tuple[int, int] = (0, 0),
        player_near: bool = False,
        flicker_phase: float = 0.0
    ):
        """Renders the socket pedestal, ornate rotating mirror face, and interaction prompt."""
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])

        # 1. Socket Stone Pedestal
        pedestal_r = int(self.radius)
        pygame.draw.circle(surface, (28, 24, 35), (sx, sy), pedestal_r)
        pygame.draw.circle(surface, (60, 50, 42), (sx, sy), pedestal_r, width=2)
        pygame.draw.circle(surface, (85, 75, 58), (sx, sy), pedestal_r - 5, width=1)

        # 2. Reflective Aura
        aura_surf = pygame.Surface((pedestal_r * 2 + 16, pedestal_r * 2 + 16), pygame.SRCALPHA)
        pulse = int(30 + 12 * math.sin(flicker_phase * 2.0))
        pygame.draw.circle(aura_surf, (*self.aura_color, pulse), (pedestal_r + 8, pedestal_r + 8), pedestal_r + 4)
        surface.blit(aura_surf, (sx - pedestal_r - 8, sy - pedestal_r - 8))

        # 3. Rotating Mirror Plane (perpendicular to mirror normal)
        # Normal is (nx, ny). Surface vector along the mirror face is (-ny, nx).
        nx, ny = self.normal
        tx, ty = -ny, nx
        mirror_half_len = 16.0

        p1 = (int(sx - tx * mirror_half_len), int(sy - ty * mirror_half_len))
        p2 = (int(sx + tx * mirror_half_len), int(sy + ty * mirror_half_len))

        # Ornate Brass backing bar
        pygame.draw.line(surface, (140, 115, 60), p1, p2, 6)
        pygame.draw.line(surface, (80, 65, 30), p1, p2, 8)

        # Reverse-side Filigree Backing Crest (Image 4 antique metalwork)
        crest_x = int(sx - nx * 7)
        crest_y = int(sy - ny * 7)
        pygame.draw.circle(surface, (95, 75, 35), (crest_x, crest_y), 4)
        pygame.draw.circle(surface, (215, 175, 75), (crest_x, crest_y), 2)

        # Polished Reflective Glass Face
        pygame.draw.line(surface, (235, 245, 255), p1, p2, 3)

        # Ornate Filigree End Lugs / Scroll Caps (Image 4 decorative curls)
        pygame.draw.circle(surface, (165, 130, 65), p1, 4)
        pygame.draw.circle(surface, (80, 60, 30), p1, 4, width=1)
        pygame.draw.circle(surface, (225, 190, 95), p1, 1)

        pygame.draw.circle(surface, (165, 130, 65), p2, 4)
        pygame.draw.circle(surface, (80, 60, 30), p2, 4, width=1)
        pygame.draw.circle(surface, (225, 190, 95), p2, 1)

        # Center Pivot Gem
        pygame.draw.circle(surface, (50, 40, 30), (sx, sy), 6)
        pygame.draw.circle(surface, self.gem_color, (sx, sy), 4)
        pygame.draw.circle(surface, (255, 255, 255), (sx - 1, sy - 1), 1)

        # Facing normal pointer notch
        notch_len = 8.0
        n_pt = (int(sx + nx * notch_len), int(sy + ny * notch_len))
        pygame.draw.line(surface, (250, 230, 180), (sx, sy), n_pt, 2)

        # 4. Interaction Prompt
        if player_near:
            font_small = pygame.font.SysFont("consolas", 11, bold=True)
            deg = self.orientation * 45
            pt = font_small.render(f"[E] Rotate ({deg}°)", True, (245, 235, 210))
            px = sx - pt.get_width() // 2
            py = sy - 34 + int(2 * math.sin(flicker_phase))
            bg = pygame.Surface((pt.get_width() + 8, pt.get_height() + 4), pygame.SRCALPHA)
            bg.fill((12, 10, 18, 225))
            surface.blit(bg, (px - 4, py - 2))
            surface.blit(pt, (px, py))
