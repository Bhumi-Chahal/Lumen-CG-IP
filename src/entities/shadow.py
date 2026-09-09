"""entities/shadow.py — Shadow Creature entity (Level 2+).

Per architecture.md §3, rules.md §1.5, design.md §6, and the locked Level 2
design decisions in docs/memory.md:
-----------------------------------------------------------------------------
DESIGN SPECIFICATION FOR LEVEL 2 (LOCKED — DO NOT BUILD INVERTED):
- In Level 1, the Shadow is completely inactive (design.md §5).
- In Level 2, the Shadow's distance from the player is driven CONTINUOUSLY
  by battery percentage (the single source of truth), not by a lantern
  on/off boolean:

      100% battery -> far away, low immediate threat
       75% battery -> noticeably closer
       50% battery -> dangerous
       25% battery -> very close / intense pressure
        0% battery -> critical / near-contact range

  Movement interpolates smoothly between these checkpoints — never
  teleports.
- There are TWO INDEPENDENT death conditions in Level 2:
      A. Battery reaches 0 (checked via BatterySystem.is_depleted)
      B. The Shadow physically touches the player (checked via
         ShadowCreature.is_touching_player)
  Battery hitting 0 is death on its own, even if the Shadow hasn't
  physically reached the player yet. Do not conflate the two.
- The Shadow must remain partially visible/trackable at all battery
  levels (never fully invisible, never a permanent unmissable presence)
  and should read as increasingly obvious/threatening as it closes in.
-----------------------------------------------------------------------------
"""

import math
import random
import pygame


def _lerp_breakpoints(x: float, points: list[tuple[float, float]]) -> float:
    """Piecewise-linear interpolation across breakpoints sorted descending by key.

    `points` must be sorted so points[0] has the largest key and points[-1]
    has the smallest. Used both for (battery ratio -> target distance) and
    (distance -> visibility alpha), since both relationships share this shape.
    """
    if x >= points[0][0]:
        return points[0][1]
    if x <= points[-1][0]:
        return points[-1][1]
    for i in range(len(points) - 1):
        k_hi, v_hi = points[i]
        k_lo, v_lo = points[i + 1]
        if k_lo <= x <= k_hi:
            if k_hi == k_lo:
                return v_hi
            t = (x - k_lo) / (k_hi - k_lo)
            return v_lo + (v_hi - v_lo) * t
    return points[-1][1]


class ShadowCreature:
    """Dark spectral lurker whose distance from the player is driven by
    battery percentage (rules.md §1.5, design.md §6, locked Level 2 spec).

    Matches reference art: hunched shadowy fiend with pointed ears/horns,
    spiky shadow silhouette, long clawed arms, and piercing glowing eyes.
    """

    DIST_FAR = 520.0
    DIST_CLOSE = 340.0
    DIST_DANGEROUS = 220.0
    DIST_VERY_CLOSE = 120.0
    DIST_CRITICAL = 60.0

    CONTACT_RADIUS = 30.0
    MAX_SPEED = 70.0

    _DISTANCE_BREAKPOINTS = [
        (1.00, DIST_FAR),
        (0.75, DIST_CLOSE),
        (0.50, DIST_DANGEROUS),
        (0.25, DIST_VERY_CLOSE),
        (0.00, DIST_CRITICAL),
    ]

    _VISIBILITY_BREAKPOINTS = [
        (DIST_FAR, 0.15),
        (DIST_CLOSE, 0.40),
        (DIST_DANGEROUS, 0.65),
        (DIST_VERY_CLOSE, 0.88),
        (DIST_CRITICAL, 1.0),
    ]

    def __init__(self, x: float, y: float):
        self.spawn_x = x
        self.spawn_y = y
        self.x = x
        self.y = y
        self.phase = random.uniform(0, 2 * math.pi)
        self.wisps = [
            {"x": random.uniform(-16, 16), "y": random.uniform(-20, 10),
             "vy": random.uniform(-14, -6), "life": random.uniform(0.3, 1.0)}
            for _ in range(8)
        ]
        self.soul_orbs = [
            {"t": random.uniform(0.0, 1.0), "speed": random.uniform(0.6, 1.2),
             "offset": random.uniform(-8, 8)}
            for _ in range(6)
        ]

    def reset(self):
        """Returns the Shadow to its spawn position — used on Level 2 death/restart."""
        self.x = self.spawn_x
        self.y = self.spawn_y

    @staticmethod
    def target_distance_for_battery(battery_ratio: float) -> float:
        """Battery ratio (0..1) -> desired distance from player (world pixels)."""
        ratio = max(0.0, min(1.0, battery_ratio))
        return _lerp_breakpoints(ratio, ShadowCreature._DISTANCE_BREAKPOINTS)

    @staticmethod
    def visibility_alpha_for_distance(distance: float) -> float:
        """Current distance to player -> visibility alpha (0..1)."""
        return _lerp_breakpoints(max(0.0, distance), ShadowCreature._VISIBILITY_BREAKPOINTS)

    def distance_to(self, player_pos: tuple[float, float]) -> float:
        return math.hypot(self.x - player_pos[0], self.y - player_pos[1])

    def is_touching_player(self, player_pos: tuple[float, float]) -> bool:
        """Death condition B — independent of battery level."""
        return self.distance_to(player_pos) <= ShadowCreature.CONTACT_RADIUS

    def update(self, dt: float, player_pos: tuple[float, float], battery_ratio: float):
        """Moves smoothly toward the distance implied by current battery ratio.

        Never teleports: each frame it steps at most MAX_SPEED * dt toward
        wherever it needs to be to match the target distance from the
        player, along the line between the Shadow and the player.
        """
        self.phase = (self.phase + dt * 3.0) % (2 * math.pi)

        for w in self.wisps:
            w["y"] += w["vy"] * dt
            w["life"] -= dt * 0.9
            if w["life"] <= 0:
                w["x"] = random.uniform(-14, 14)
                w["y"] = random.uniform(-4, 12)
                w["life"] = random.uniform(0.5, 1.0)

        for orb in self.soul_orbs:
            orb["t"] += orb["speed"] * dt
            if orb["t"] > 1.0:
                orb["t"] = 0.0
                orb["offset"] = random.uniform(-10, 10)

        desired_dist = self.target_distance_for_battery(battery_ratio)
        px, py = player_pos
        dx = self.x - px
        dy = self.y - py
        dist = math.hypot(dx, dy)

        if dist < 1e-4:
            dir_x, dir_y = 1.0, 0.0
        else:
            dir_x, dir_y = dx / dist, dy / dist

        desired_x = px + dir_x * desired_dist
        desired_y = py + dir_y * desired_dist

        to_x = desired_x - self.x
        to_y = desired_y - self.y
        move_dist = math.hypot(to_x, to_y)
        if move_dist > 1e-4:
            step = min(ShadowCreature.MAX_SPEED * dt, move_dist)
            self.x += (to_x / move_dist) * step
            self.y += (to_y / move_dist) * step

    def draw(self, surface: pygame.Surface, player_center: tuple[float, float],
             camera_offset: tuple[int, int] = (0, 0)):
        """Renders the Shadow with visibility scaled by current distance to player.

        Silhouette/aura/eyes are always drawn (at whatever alpha applies) so
        the Shadow is never a permanently invisible or permanently obvious
        presence. The intense siphon-beam/soul-orb effects only render at
        close range.
        """
        dist = self.distance_to(player_center)
        alpha = self.visibility_alpha_for_distance(dist)
        if alpha <= 0.03:
            return

        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])
        px = int(player_center[0] - camera_offset[0])
        py = int(player_center[1] - camera_offset[1])

        pulse = math.sin(self.phase)

        local_w, local_h = 100, 130
        local = pygame.Surface((local_w, local_h), pygame.SRCALPHA)
        lcx, lcy = local_w // 2, local_h - 30

        body_black = (8, 6, 15, 255)
        edge_violet = (70, 25, 110, 255)

        aura_r = int(40 + 8 * pulse)
        pygame.draw.circle(local, (100, 20, 170, 40), (lcx, lcy), aura_r)
        pygame.draw.circle(local, (150, 40, 220, 65), (lcx, lcy), int(aura_r * 0.65))
        pygame.draw.circle(local, (190, 70, 255, 90), (lcx, lcy), int(aura_r * 0.35))

        pygame.draw.polygon(local, body_black, [
            (lcx - 18, lcy - 8), (lcx - 26, lcy - 20), (lcx - 12, lcy - 14),
            (lcx, lcy - 22), (lcx + 12, lcy - 14), (lcx + 26, lcy - 20), (lcx + 18, lcy - 8)
        ])
        pygame.draw.lines(local, edge_violet, False, [
            (lcx - 26, lcy - 20), (lcx - 12, lcy - 14), (lcx, lcy - 22),
            (lcx + 12, lcy - 14), (lcx + 26, lcy - 20)
        ], 1)

        torso_rect = pygame.Rect(lcx - 14, lcy - 12, 28, 26)
        pygame.draw.ellipse(local, body_black, torso_rect)
        pygame.draw.ellipse(local, edge_violet, torso_rect, width=1)

        pygame.draw.circle(local, body_black, (lcx, lcy - 14), 10)
        pygame.draw.polygon(local, body_black, [(lcx - 8, lcy - 16), (lcx - 14, lcy - 28), (lcx - 3, lcy - 18)])
        pygame.draw.polygon(local, body_black, [(lcx + 8, lcy - 16), (lcx + 14, lcy - 28), (lcx + 3, lcy - 18)])
        pygame.draw.line(local, edge_violet, (lcx - 14, lcy - 28), (lcx - 5, lcy - 17), 1)
        pygame.draw.line(local, edge_violet, (lcx + 14, lcy - 28), (lcx + 5, lcy - 17), 1)

        eye_glow = int(220 + 35 * pulse)
        eye_color = (eye_glow, 60, min(255, eye_glow + 35), 255)
        pygame.draw.circle(local, eye_color, (lcx - 4, lcy - 14), 2)
        pygame.draw.circle(local, eye_color, (lcx + 4, lcy - 14), 2)
        pygame.draw.circle(local, (255, 255, 255, 255), (lcx - 4, lcy - 14), 1)
        pygame.draw.circle(local, (255, 255, 255, 255), (lcx + 4, lcy - 14), 1)

        facing = 1 if px >= sx else -1
        pygame.draw.line(local, body_black, (lcx - 10, lcy - 4), (lcx - 18 + facing * 8, lcy + 10), 3)
        pygame.draw.line(local, (180, 60, 240, 255), (lcx - 18 + facing * 8, lcy + 10),
                         (lcx - 22 + facing * 12, lcy + 14), 2)
        pygame.draw.line(local, body_black, (lcx + 10, lcy - 4), (lcx + 18 + facing * 8, lcy + 10), 3)
        pygame.draw.line(local, (180, 60, 240, 255), (lcx + 18 + facing * 8, lcy + 10),
                         (lcx + 22 + facing * 12, lcy + 14), 2)

        for w in self.wisps:
            wx = int(lcx + w["x"])
            wy = int(lcy + w["y"])
            w_alpha = max(10, min(140, int(140 * w["life"])))
            pygame.draw.circle(local, (80, 20, 130, w_alpha), (wx, wy), 2)

        mult = max(0, min(255, int(255 * alpha)))
        local.fill((255, 255, 255, mult), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(local, (sx - lcx, sy - lcy))

        if dist <= ShadowCreature.DIST_VERY_CLOSE:
            num_strands = 3
            for s_idx in range(num_strands):
                strand_phase = self.phase * 2.0 + s_idx * 2.09
                mid_offset_x = int(32 * math.sin(strand_phase))
                mid_offset_y = int(24 * math.cos(strand_phase * 0.8))
                mid_x = (px + sx) // 2 + mid_offset_x
                mid_y = (py + sy) // 2 + mid_offset_y

                steps = 14
                pts = []
                for step in range(steps + 1):
                    f = step / float(steps)
                    bx = (1 - f) ** 2 * px + 2 * (1 - f) * f * mid_x + f ** 2 * sx
                    by = (1 - f) ** 2 * (py - 6) + 2 * (1 - f) * f * mid_y + f ** 2 * sy
                    pts.append((int(bx), int(by)))
                for i in range(len(pts) - 1):
                    pygame.draw.line(surface, (130, 30, 200), pts[i], pts[i + 1], 3)
                    pygame.draw.line(surface, (210, 80, 255), pts[i], pts[i + 1], 1)

            for orb in self.soul_orbs:
                f = orb["t"]
                mid_x = (px + sx) // 2 + int(24 * math.sin(self.phase + f * 4))
                mid_y = (py + sy) // 2 + int(18 * math.cos(self.phase * 1.3))
                ox = int((1 - f) ** 2 * px + 2 * (1 - f) * f * mid_x + f ** 2 * sx)
                oy = int((1 - f) ** 2 * (py - 6) + 2 * (1 - f) * f * mid_y + f ** 2 * sy + orb["offset"])
                orb_r = max(2, int(4 * (1.0 - f * 0.5)))
                pygame.draw.circle(surface, (230, 110, 255), (ox, oy), orb_r)
                pygame.draw.circle(surface, (255, 230, 255), (ox, oy), max(1, orb_r - 1))


def level2_death_triggered(battery, shadow: "ShadowCreature", player_center: tuple[float, float]) -> bool:
    """Combines Level 2's two independent death conditions.

    A. battery.is_depleted
    B. shadow.is_touching_player(player_center)

    Either one is sufficient on its own.
    """
    return battery.is_depleted or shadow.is_touching_player(player_center)
