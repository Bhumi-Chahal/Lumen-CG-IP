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
