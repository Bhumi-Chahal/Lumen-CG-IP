"""entities/puzzle_crystal.py — Level 3 Resonance / Puzzle Crystal.

Distinct from Level 2 Energy Crystal stations (which recharge the battery).
Puzzle crystals are resonance targets that activate when struck by a light beam
of matching required_color (or any color if required_color is None).
Features approximately 0.5 seconds of sustain grace to prevent visual flicker.
"""

import math
import pygame


class PuzzleCrystal:
    """Target crystal entity that activates when struck by a matching light beam."""

    SUSTAIN_GRACE = 0.5  # seconds

    def __init__(
        self,
        crystal_id: str,
        x: float,
        y: float,
        required_color: str | None = None,
        name: str = "Resonance Crystal",
        charge_duration: float = 0.0,
    ):
        self.id = crystal_id
        self.x = float(x)
        self.y = float(y)
        self.required_color = required_color  # None, "red", "blue", or "green"
        self.name = name
        self.radius = 36.0

        self.active = False
        self.charged = False
        self.collected = False
        self.charge_timer = 0.0
        self.charge_duration = float(charge_duration)
        self.charge_progress = 0.0

        self.grace_timer = 0.0
        self.was_active = False  # Used to detect rising edge for audio chime
        self.dim_pulse_timer = 0.0
        self.active_color: str | None = None

        # Visual color palette
        self.palette = self._get_palette()

    DORMANT_PALETTE = {
        "core": (255, 245, 220),
        "mid":  (210, 195, 140),
        "dark": (120, 105, 70),
        "aura": (230, 215, 160),
    }

    TARGET_PALETTES = {
        "red": {
            "core": (255, 135, 150),
            "mid":  (235, 50, 70),
            "dark": (145, 20, 35),
            "aura": (255, 65, 85),
        },
        "blue": {
            "core": (155, 215, 255),
            "mid":  (45, 140, 245),
            "dark": (20, 65, 155),
            "aura": (60, 150, 255),
        },
        "green": {
            "core": (160, 255, 190),
            "mid":  (40, 220, 100),
            "dark": (18, 125, 48),
            "aura": (50, 240, 115),
        },
        "neutral": {
            "core": (255, 245, 220),
            "mid":  (230, 205, 130),
            "dark": (130, 110, 60),
            "aura": (255, 225, 140),
        },
    }

    def _get_palette(self) -> dict:
        color_key = self.active_color if (self.active and self.active_color) else (self.required_color or "neutral")
        target = self.TARGET_PALETTES.get(color_key, self.TARGET_PALETTES["neutral"])

        if self.charged or self.active:
            return target

        if self.charge_progress > 0.0:
            # Smooth color emergence as charging progresses from dormant neutral to target color
            t = self.charge_progress
            def _lerp_c(c1, c2, ratio):
                return (
                    int(c1[0] + (c2[0] - c1[0]) * ratio),
                    int(c1[1] + (c2[1] - c1[1]) * ratio),
                    int(c1[2] + (c2[2] - c1[2]) * ratio),
                )
            return {
                "core": _lerp_c(self.DORMANT_PALETTE["core"], target["core"], t),
                "mid":  _lerp_c(self.DORMANT_PALETTE["mid"], target["mid"], t),
                "dark": _lerp_c(self.DORMANT_PALETTE["dark"], target["dark"], t),
                "aura": _lerp_c(self.DORMANT_PALETTE["aura"], target["aura"], t),
            }

        # Initial dormant state: neutral, pale, slightly magical, subdued
        return self.DORMANT_PALETTE

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(
            int(self.x - self.radius),
            int(self.y - self.radius),
            int(self.radius * 2),
            int(self.radius * 2)
        )

    def check_activation(self, hit_by_beam: bool, beam_color: str = "white") -> bool:
        """Determines if the crystal should be active given current beam intersection."""
        if not hit_by_beam:
            return False
        if self.required_color is None:
            return True
        return beam_color == self.required_color

    def collect(self) -> bool:
        """Collects the crystal once it has completed its resonance sequence."""
        if (self.charged or self.active) and not self.collected:
            self.collected = True
            return True
        return False

    def update(self, dt: float, is_hit: bool = False, hit_color: str = "white") -> bool:
        """Updates charging and activation state with sustain grace.

        Gradually charges for ~1.5s when hit by matching light.
        Transitions from dim to brighter resonance and adopts the light's color.
        Returns True when full resonance is achieved this frame.
        """
        just_activated = False
        color_matches = (self.required_color is None or hit_color == self.required_color)

        if is_hit:
            if color_matches:
                if not self.charged:
                    if self.charge_duration <= 0.0:
                        self.charge_timer = 0.0
                        self.charge_progress = 1.0
                        self.charged = True
                        self.active = True
                        self.active_color = hit_color
                        self.grace_timer = self.SUSTAIN_GRACE
                        just_activated = True
                    else:
                        self.charge_timer = min(self.charge_duration, self.charge_timer + dt)
                        self.charge_progress = self.charge_timer / self.charge_duration
                        if self.charge_timer >= self.charge_duration:
                            self.charged = True
                            self.active = True
                            self.active_color = hit_color
                            self.grace_timer = self.SUSTAIN_GRACE
                            just_activated = True
                else:
                    self.active = True
                    self.active_color = hit_color
                    self.grace_timer = self.SUSTAIN_GRACE
            else:
                # Wrong color: triggers dim pulse feedback without penalty
                self.dim_pulse_timer = 0.3

        if not is_hit or not color_matches:
            if not self.charged:
                if self.charge_duration > 0.0:
                    self.charge_timer = max(0.0, self.charge_timer - dt * 0.8)
                    self.charge_progress = self.charge_timer / self.charge_duration
                else:
                    self.charge_timer = 0.0
                    self.charge_progress = 0.0

            if self.grace_timer > 0:
                self.grace_timer -= dt
                if self.grace_timer <= 0:
                    self.active = False
                    self.charged = False
                    self.active_color = None
                    self.charge_timer = 0.0
                    self.charge_progress = 0.0
            else:
                self.active = False
                self.charged = False
                self.active_color = None
                self.charge_timer = 0.0
                self.charge_progress = 0.0

        if self.dim_pulse_timer > 0:
            self.dim_pulse_timer = max(0.0, self.dim_pulse_timer - dt)

        self.palette = self._get_palette()
        self.was_active = self.active
        return just_activated

    def draw(
        self,
        surface: pygame.Surface,
        camera_offset: tuple[int, int] = (0, 0),
        flicker_phase: float = 0.0
    ):
        """Renders the sacred pedestal, crystalline prism spires, and resonant glow."""
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])

        # 1. Carved Ancient Stone Pedestal
        pygame.draw.circle(surface, (24, 20, 32), (sx, sy + 6), int(self.radius))
        pygame.draw.circle(surface, (55, 48, 62), (sx, sy + 6), int(self.radius), width=2)
        pygame.draw.circle(surface, (80, 70, 90), (sx, sy + 6), int(self.radius) - 6, width=1)

        # 2. Resonant Glow Aura
        if self.active:
            aura_r = int(self.radius + 24)
        elif self.charge_progress > 0.0:
            aura_r = int(self.radius + 8 + 16 * self.charge_progress)
        else:
            aura_r = int(self.radius + 8)

        aura_surf = pygame.Surface((aura_r * 2, aura_r * 2), pygame.SRCALPHA)

        if self.active:
            pulse = int(55 + 22 * math.sin(flicker_phase * 4.0))
            pygame.draw.circle(aura_surf, (*self.palette["aura"], pulse), (aura_r, aura_r), aura_r)
            pygame.draw.circle(aura_surf, (*self.palette["core"], int(pulse * 0.85)), (aura_r, aura_r), int(aura_r * 0.55))
        elif self.charge_progress > 0.0:
            # Increasing glow during charging
            pulse = int((30 + 16 * math.sin(flicker_phase * 3.5)) * (0.35 + 0.65 * self.charge_progress))
            pygame.draw.circle(aura_surf, (*self.palette["aura"], pulse), (aura_r, aura_r), aura_r)
            pygame.draw.circle(aura_surf, (*self.palette["core"], int(pulse * 0.8)), (aura_r, aura_r), int(aura_r * 0.50))
        elif self.dim_pulse_timer > 0:
            # Dim pulse when hit with wrong color
            d_pulse = int(40 * (self.dim_pulse_timer / 0.3))
            pygame.draw.circle(aura_surf, (200, 180, 190, d_pulse), (aura_r, aura_r), aura_r)
        else:
            # Idle faint dormant shimmer
            idle_pulse = int(14 + 6 * math.sin(flicker_phase * 1.5))
            pygame.draw.circle(aura_surf, (*self.palette["aura"], idle_pulse), (aura_r, aura_r), aura_r - 4)

        surface.blit(aura_surf, (sx - aura_r, sy - aura_r))

        # Gathering energy particles during charging
        if 0.0 < self.charge_progress < 1.0:
            num_sparks = 5
            for p_i in range(num_sparks):
                p_t = (flicker_phase * 2.0 + p_i * (2.0 * math.pi / num_sparks)) % (2.0 * math.pi)
                spark_dist = (self.radius + 12.0) * (1.0 - (p_t / (2.0 * math.pi)))
                px = sx + int(spark_dist * math.cos(p_t))
                py = (sy - 4) + int(spark_dist * 0.65 * math.sin(p_t))
                p_alpha = min(255, int(180 * self.charge_progress * (p_t / (2.0 * math.pi))))
                p_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (*self.palette["core"], p_alpha), (2, 2), 1)
                surface.blit(p_surf, (px - 2, py - 2))

        # 3. Crystal Spire Prism (Diamond / Octahedral facets)
        tip_y = sy - 18
        base_y = sy + 6
        left_x = sx - 11
        right_x = sx + 11

        pts_main = [(sx, tip_y), (right_x, sy - 4), (sx, base_y), (left_x, sy - 4)]
        pts_left_facet = [(sx, tip_y), (left_x, sy - 4), (sx, base_y)]
        pts_right_facet = [(sx, tip_y), (right_x, sy - 4), (sx, base_y)]

        col_mid = self.palette["core"] if self.active else self.palette["mid"]
        col_dark = self.palette["mid"] if self.active else self.palette["dark"]

        pygame.draw.polygon(surface, col_dark, pts_left_facet)
        pygame.draw.polygon(surface, col_mid, pts_right_facet)
        pygame.draw.polygon(surface, (245, 240, 255) if self.active else (180, 170, 190), pts_main, width=1)

        # Core Gleam Sparkle
        if self.active or self.collected:
            pygame.draw.circle(surface, (255, 255, 255), (sx, sy - 4), 3)
            pygame.draw.line(surface, (255, 255, 255), (sx - 7, sy - 4), (sx + 7, sy - 4), 2)
            pygame.draw.line(surface, (255, 255, 255), (sx, sy - 11), (sx, sy + 3), 2)

            # Subtle floating sparkles drifting upward when resonant
            if self.active and not self.collected:
                for s_i in range(3):
                    st = (flicker_phase * 0.75 + s_i * 0.33) % 1.0
                    spark_y = (sy - 18) - int(st * 20.0)
                    spark_x = sx + int(3.5 * math.sin(flicker_phase * 2.2 + s_i * 2.0))
                    sp_alpha = min(255, int(200 * (1.0 - st)))
                    sp_surf = pygame.Surface((4, 4), pygame.SRCALPHA)
                    pygame.draw.circle(sp_surf, (255, 255, 255, sp_alpha), (2, 2), 1)
                    surface.blit(sp_surf, (spark_x - 2, spark_y - 2))
        else:
            pygame.draw.circle(surface, self.palette["core"], (sx, sy - 4), 2)

        # 4. Charging Arc Indicator (when receiving matching light before full resonance)
        if 0.0 < self.charge_progress < 1.0:
            arc_rect = pygame.Rect(sx - int(self.radius) - 4, sy - int(self.radius) + 2,
                                   int(self.radius * 2) + 8, int(self.radius * 2) + 8)
            end_ang = -math.pi / 2 + self.charge_progress * 2 * math.pi
            pygame.draw.arc(surface, self.palette["dark"], arc_rect, -math.pi / 2, end_ang, 3)
            pygame.draw.arc(surface, self.palette["core"], arc_rect, -math.pi / 2, end_ang, 2)
