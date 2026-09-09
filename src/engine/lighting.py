"""Dynamic lighting and visibility masking for Lumen (FR-003, FR-004, FR-005).

Very deep darkness with warm golden lantern glow. Darker than default -
darkness is near-opaque pitch black. The lantern carves out a warm circle.
Includes atmospheric floating dust/ember particles.
"""

import math
import random
import pygame


class LightingSystem:
    """Handles dynamic darkness masking, warm lantern falloff, and atmospheric dust."""

    def __init__(self, room_width: int, room_height: int, num_particles: int = 55):
        self.particles: list[dict] = []
        for _ in range(num_particles):
            self.particles.append({
                "x": random.uniform(30, room_width - 30),
                "y": random.uniform(30, room_height - 30),
                "vx": random.uniform(-8, 8),
                "vy": random.uniform(-12, -2),
                "size": random.uniform(1.0, 2.8),
                "alpha": random.uniform(50, 180),
                "seed": random.uniform(0, 100),
                "is_ember": random.random() < 0.25,  # Some are warm embers
            })
        self.flicker_phase = 0.0

    def update(self, dt: float, room_width: int, room_height: int):
        """Updates ambient floating dust motes and light flicker."""
        self.flicker_phase += dt * 5.0
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            # Wrap around room boundaries
            if p["y"] < 30:
                p["y"] = room_height - 40
                p["x"] = random.uniform(30, room_width - 30)
            if p["x"] < 25:
                p["x"] = room_width - 30
            elif p["x"] > room_width - 25:
                p["x"] = 30

    def draw_particles(self, surface: pygame.Surface, light_center: tuple[float, float],
                       light_radius: float, camera_offset: tuple[int, int] = (0, 0)):
        """Draws floating temple dust motes and embers illuminated by the lantern."""
        lx, ly = light_center
        rad_sq = light_radius * light_radius

        for p in self.particles:
            dx = p["x"] - lx
            dy = p["y"] - ly
            dist_sq = dx * dx + dy * dy
            if dist_sq <= rad_sq:
                factor = 1.0 - (dist_sq / rad_sq)
                alpha = int(p["alpha"] * factor)
                if alpha > 10:
                    px = int(p["x"] - camera_offset[0])
                    py = int(p["y"] - camera_offset[1])
                    dust_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
                    if p["is_ember"]:
                        # Warm orange ember particle
                        color = (255, 180, 60, min(255, alpha + 30))
                    else:
                        # Pale dust mote
                        color = (240, 230, 200, alpha)
                    pygame.draw.circle(dust_surf, color, (3, 3), max(1, int(p["size"])))
                    surface.blit(dust_surf, (px - 3, py - 3))


def build_darkness_mask(size: tuple[int, int], light_center: tuple[int, int],
                        radius: int, darkness_alpha: int = 252,
                        flicker_offset: float = 0.0,
                        extra_lights: list[tuple[int, int, int]] | None = None) -> pygame.Surface:
    """Builds a very dark alpha mask, carving out a warm lit circle around the lantern.

    Darkness is near-opaque (alpha 252) for a very dark feel matching the reference.
    Supports extra light sources (e.g. wall torches) via `extra_lights`.
    """
    effective_radius = max(30, int(radius + flicker_offset))
    mask = pygame.Surface(size, pygame.SRCALPHA)
    # Pitch dark temple ambient — very dark as user requested
    mask.fill((2, 2, 6, darkness_alpha))

    # Multi-pass smooth gradient edge (more rings = smoother)
    num_rings = 18
    for i in range(num_rings, 0, -1):
        ratio = i / float(num_rings)
        r = int(effective_radius * ratio)
        # Smooth cubic falloff curve
        attenuation = ratio * ratio * (3.0 - 2.0 * ratio)
        ring_alpha = int(darkness_alpha * attenuation)
        pygame.draw.circle(mask, (2, 2, 6, ring_alpha), light_center, r)

    # Core visibility hole
    core_radius = int(effective_radius * 0.32)
    pygame.draw.circle(mask, (0, 0, 0, 0), light_center, core_radius)

    # Warm golden lantern glow layer
    glow = pygame.Surface(size, pygame.SRCALPHA)
    # Outer warm amber haze
    pygame.draw.circle(glow, (255, 195, 90, 28), light_center, int(effective_radius * 0.9))
    # Mid warm golden glow
    pygame.draw.circle(glow, (255, 220, 130, 42), light_center, int(effective_radius * 0.55))
    # Inner bright lantern core
    pygame.draw.circle(glow, (255, 245, 180, 50), light_center, int(effective_radius * 0.25))

    # Extra light sources (e.g. glowing wall torches)
    if extra_lights:
        for ex, ey, er in extra_lights:
            # Carve smooth visibility hole
            num_t_rings = 10
            for ti in range(num_t_rings, 0, -1):
                tratio = ti / float(num_t_rings)
                tr_cur = int(er * tratio)
                tattenuation = tratio * tratio
                tring_alpha = int(darkness_alpha * tattenuation)
                pygame.draw.circle(mask, (2, 2, 6, tring_alpha), (ex, ey), tr_cur)
            pygame.draw.circle(mask, (0, 0, 0, 0), (ex, ey), int(er * 0.35))

            # Warm amber glow around torch
            pygame.draw.circle(glow, (255, 160, 45, 32), (ex, ey), int(er * 0.85))
            pygame.draw.circle(glow, (255, 205, 80, 48), (ex, ey), int(er * 0.45))

    mask.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)

    return mask


def is_point_lit(point: tuple[float, float], light_center: tuple[float, float],
                 radius: float) -> bool:
    """Returns True if `point` is within the lit radius of `light_center` (FR-005)."""
    dx = point[0] - light_center[0]
    dy = point[1] - light_center[1]
    return (dx * dx + dy * dy) <= (radius * radius)


def build_level3_darkness_mask(
    size: tuple[int, int],
    player_screen_pos: tuple[int, int],
    lantern_radius: float,
    sun_core_screen_pos: tuple[int, int],
    sun_core_radius: float = 720.0,
    beam_screen_segments: list[tuple[tuple[float, float], tuple[float, float], str]] | None = None,
    darkness_alpha: int = 175,
    flicker_offset: float = 0.0,
    chamber_lights: list[tuple[int, int, int, str]] | None = None,
) -> pygame.Surface:
    """Builds Level 3 darkness mask featuring:
    - Mysterious yet readable dark temple atmosphere (alpha ~175, benchmarked against Level 2).
    - Large radiant solar illumination around the central Sun Core (radius ~720px).
    - Side chambers brighten dynamically when an active reflected beam enters them.
    - Local illumination along active light beam segment corridors.
    """
    mask = pygame.Surface(size, pygame.SRCALPHA)
    mask.fill((4, 3, 8, darkness_alpha))

    glow = pygame.Surface(size, pygame.SRCALPHA)

    # 1. Permanent Sun Core Light Hole & Solar Glow (if sun_core_radius > 0)
    if sun_core_radius > 0:
        sc_x, sc_y = sun_core_screen_pos
        sc_r = max(60, int(sun_core_radius))
        num_sc_rings = 18
        for i in range(num_sc_rings, 0, -1):
            ratio = i / float(num_sc_rings)
            r = int(sc_r * ratio)
            attenuation = ratio * ratio * (3.0 - 2.0 * ratio)
            ring_alpha = int(darkness_alpha * attenuation)
            pygame.draw.circle(mask, (4, 3, 8, ring_alpha), (sc_x, sc_y), r)
        pygame.draw.circle(mask, (0, 0, 0, 0), (sc_x, sc_y), int(sc_r * 0.45))

        # Solar glow around Sun Core
        pygame.draw.circle(glow, (255, 185, 60, 42), (sc_x, sc_y), int(sc_r * 0.88))
        pygame.draw.circle(glow, (255, 220, 110, 58), (sc_x, sc_y), int(sc_r * 0.50))
        pygame.draw.circle(glow, (255, 245, 180, 75), (sc_x, sc_y), int(sc_r * 0.25))

    # 2. Dynamic Chamber Illumination (reveals side chamber when light enters)
    if chamber_lights:
        col_map = {
            "white": ((255, 240, 200, 38), (255, 250, 225, 55)),
            "red":   ((255, 110, 130, 42), (255, 160, 180, 60)),
            "blue":  ((100, 180, 255, 42), (160, 220, 255, 60)),
            "green": ((100, 255, 150, 42), (160, 255, 190, 60)),
        }
        for (cx, cy, cr, col_key) in chamber_lights:
            num_c_rings = 12
            for ci in range(num_c_rings, 0, -1):
                c_ratio = ci / float(num_c_rings)
                cur_r = int(cr * c_ratio)
                c_atten = c_ratio * c_ratio
                c_alpha = int(darkness_alpha * c_atten)
                pygame.draw.circle(mask, (4, 3, 8, c_alpha), (cx, cy), cur_r)
            pygame.draw.circle(mask, (0, 0, 0, 0), (cx, cy), int(cr * 0.50))

            g_outer, g_inner = col_map.get(col_key, col_map["white"])
            pygame.draw.circle(glow, g_outer, (cx, cy), int(cr * 0.85))
            pygame.draw.circle(glow, g_inner, (cx, cy), int(cr * 0.45))

    # 3. Player Lantern Light Hole & Amber Glow
    if lantern_radius > 0:
        eff_radius = max(140, int(lantern_radius + flicker_offset))
        px, py = player_screen_pos
        num_p_rings = 12
        for i in range(num_p_rings, 0, -1):
            ratio = i / float(num_p_rings)
            r = int(eff_radius * ratio)
            attenuation = ratio * ratio * (3.0 - 2.0 * ratio)
            ring_alpha = int(darkness_alpha * attenuation)
            pygame.draw.circle(mask, (4, 3, 8, ring_alpha), (px, py), r)
        pygame.draw.circle(mask, (0, 0, 0, 0), (px, py), int(eff_radius * 0.35))

        # Warm amber lantern glow
        pygame.draw.circle(glow, (255, 195, 90, 25), (px, py), int(eff_radius * 0.85))
        pygame.draw.circle(glow, (255, 220, 130, 40), (px, py), int(eff_radius * 0.50))

    # 4. Beam Segment Local Illumination Corridors
    if beam_screen_segments:
        color_glow_map = {
            "white": (255, 240, 190, 50),
            "red":   (255, 100, 120, 55),
            "green": (100, 255, 140, 55),
            "blue":  (100, 180, 255, 55),
        }
        for (start_pt, end_pt, b_col) in beam_screen_segments:
            p_start = (int(start_pt[0]), int(start_pt[1]))
            p_end = (int(end_pt[0]), int(end_pt[1]))

            # Carve smooth visibility corridor into darkness mask
            pygame.draw.line(mask, (4, 3, 8, 80), p_start, p_end, 85)
            pygame.draw.line(mask, (4, 3, 8, 25), p_start, p_end, 50)
            pygame.draw.line(mask, (0, 0, 0, 0), p_start, p_end, 24)

            # Colored light glow along beam path
            g_col = color_glow_map.get(b_col, color_glow_map["white"])
            pygame.draw.line(glow, g_col, p_start, p_end, 34)
            pygame.draw.line(glow, (255, 255, 255, 70), p_start, p_end, 10)

    mask.blit(glow, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
    return mask
