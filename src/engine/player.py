"""Player entity: position, movement, animation, and lantern state for Lumen.

Implements FR-001 (four-directional movement with WASD / Arrow keys),
collision box tracking, walking animations, directional facing, and
rendering with a wise pixel-art wizard sprite matching the reference art:
- Conical indigo wizard hat with curved tip and gold band
- Flowing white beard and mustache
- Indigo wizard robe with golden embroidery and trim
- Ornate brass lantern that reacts dynamically to lit / unlit state
"""

import math
import pygame
from systems.audio import audio


class Player:
    """Represents the player-controlled wizard-explorer inside the temple.

    Attributes:
        x, y: World-space position (top-left of collision bounding box).
        width, height: Size of the player's collision box.
        speed: Movement speed in pixels per second.
        facing: Current facing direction ('down', 'up', 'left', 'right').
        is_moving: Whether the player is actively walking this frame.
        lantern_color: Currently active lantern color mode (FR-003).
    """

    WIDTH = 26
    HEIGHT = 30
    SPEED = 180.0  # pixels per second

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.width = Player.WIDTH
        self.height = Player.HEIGHT
        self.speed = Player.SPEED
        self.lantern_color = "white"

        self.facing = "down"
        self.is_moving = False
        self.anim_timer = 0.0
        self.walk_frame = 0
        self.step_timer = 0.0
        self.glow_phase = 0.0

        # 2D jump state / timer (short duration, pure 2D)
        self.jump_duration = 0.30
        self.jump_timer = 0.0

    @property
    def is_jumping(self) -> bool:
        return self.jump_timer > 0.0

    def jump(self) -> bool:
        """Triggers a short 2D jump state if not already jumping."""
        if self.is_jumping:
            return False
        self.jump_timer = self.jump_duration
        return True

    def update(self, dt: float):
        """Updates the 2D jump timer."""
        if self.jump_timer > 0.0:
            self.jump_timer = max(0.0, self.jump_timer - dt)

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    @property
    def center(self) -> tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    def get_input_vector(self) -> tuple[float, float]:
        """Reads keyboard state and returns a normalized (dx, dy) vector."""
        keys = pygame.key.get_pressed()
        dx = 0.0
        dy = 0.0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1.0
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1.0
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1.0

        # Update primary facing direction
        if abs(dy) >= abs(dx) and dy != 0:
            self.facing = "down" if dy > 0 else "up"
        elif dx != 0:
            self.facing = "right" if dx > 0 else "left"

        if dx != 0 and dy != 0:
            length = (dx * dx + dy * dy) ** 0.5
            dx /= length
            dy /= length

        return dx, dy

    def update_animation(self, is_moving: bool, dt: float):
        """Updates walk cycle animation frames and triggers step audio."""
        if self.jump_timer > 0.0:
            self.jump_timer = max(0.0, self.jump_timer - dt)

        self.is_moving = is_moving
        self.glow_phase = (self.glow_phase + dt * 3.5) % (2 * math.pi)
        if is_moving:
            self.anim_timer += dt * 9.0
            self.walk_frame = int(self.anim_timer) % 4
            self.step_timer += dt
            if self.step_timer >= 0.30:
                self.step_timer = 0.0
                audio.play("footstep")
        else:
            self.anim_timer = 0.0
            self.walk_frame = 0
            self.step_timer = 0.22

    def draw(self, surface: pygame.Surface, camera_offset: tuple[int, int] = (0, 0),
             is_lantern_lit: bool = True):
        """Renders the wizard explorer matching reference art with reactive lantern."""
        sx = int(self.x - camera_offset[0])
        sy = int(self.y - camera_offset[1])

        # Walk bob & 2D hop visual offset
        bob = 0
        leg_offset = 0
        if self.is_jumping:
            # 2D visual hop offset for sprite rendering while shadow stays on floor
            progress = self.jump_timer / self.jump_duration
            hop = int(8 * 4 * progress * (1.0 - progress))
            bob -= hop
        elif self.is_moving:
            bob = -2 if self.walk_frame in (1, 3) else 0
            leg_offset = 3 if self.walk_frame == 1 else (-3 if self.walk_frame == 3 else 0)

        cx = sx + self.width // 2
        by = sy + self.height + bob

        # --- 1. Floor Shadow ---
        shd = pygame.Surface((28, 10), pygame.SRCALPHA)
        pygame.draw.ellipse(shd, (0, 0, 0, 80), (0, 0, 28, 10))
        surface.blit(shd, (cx - 14, sy + self.height - 3))

        # --- 2. Boots (Brown Leather) ---
        boot_color = (48, 34, 22)
        if self.facing in ("down", "up"):
            lly = by - 5 + (leg_offset if leg_offset > 0 else 0)
            rly = by - 5 + (-leg_offset if leg_offset < 0 else 0)
            pygame.draw.rect(surface, boot_color, (cx - 8, lly, 6, 6), border_radius=2)
            pygame.draw.rect(surface, boot_color, (cx + 2, rly, 6, 6), border_radius=2)
        else:
            pygame.draw.rect(surface, boot_color, (cx - 5 + leg_offset, by - 5, 10, 6), border_radius=2)

        # --- 3. Indigo Wizard Robe (matching reference art) ---
        robe_dark = (26, 36, 85)
        robe_color = (38, 52, 125)
        robe_light = (52, 72, 168)
        gold_trim = (215, 175, 60)

        # Main robe skirt / body
        robe_rect = pygame.Rect(cx - 10, sy + 8 + bob, 20, 17)
        pygame.draw.rect(surface, robe_color, robe_rect, border_radius=4)
        # Robe shadow folds
        pygame.draw.rect(surface, robe_dark, (cx - 10, sy + 14 + bob, 4, 11), border_radius=2)
        pygame.draw.rect(surface, robe_dark, (cx + 6, sy + 14 + bob, 4, 11), border_radius=2)
        # Center tunic panel
        pygame.draw.rect(surface, robe_light, (cx - 5, sy + 9 + bob, 10, 14), border_radius=2)

        # Golden Hem / Trim along bottom edge of robe
        pygame.draw.rect(surface, gold_trim, (cx - 10, sy + 23 + bob, 20, 2))

        # Gold Belt / Sash with buckle
        pygame.draw.rect(surface, gold_trim, (cx - 10, sy + 17 + bob, 20, 3))
        pygame.draw.circle(surface, (250, 220, 100), (cx, sy + 18 + bob), 2)

        # Robe Sleeves
        pygame.draw.rect(surface, robe_color, (cx - 13, sy + 8 + bob, 5, 8), border_radius=2)
        pygame.draw.rect(surface, gold_trim, (cx - 13, sy + 14 + bob, 5, 2))
        pygame.draw.rect(surface, robe_color, (cx + 8, sy + 8 + bob, 5, 8), border_radius=2)
        pygame.draw.rect(surface, gold_trim, (cx + 8, sy + 14 + bob, 5, 2))

        # --- 4. Wizard Head: Face, Beard, Mustache, and Pointed Hat ---
        skin_color = (220, 185, 150)
        beard_white = (248, 248, 252)
        beard_shadow = (200, 205, 218)

        if self.facing == "down":
            # Face base
            pygame.draw.rect(surface, skin_color, (cx - 6, sy + 2 + bob, 12, 7), border_radius=2)
            # Eyes
            pygame.draw.rect(surface, (25, 25, 35), (cx - 4, sy + 4 + bob, 2, 2))
            pygame.draw.rect(surface, (25, 25, 35), (cx + 2, sy + 4 + bob, 2, 2))

            # Flowing White Mustache
            pygame.draw.rect(surface, beard_white, (cx - 6, sy + 7 + bob, 12, 3), border_radius=1)

            # Long Fluffy White Beard (matching reference wizard!)
            pygame.draw.polygon(surface, beard_shadow, [
                (cx - 7, sy + 8 + bob), (cx + 7, sy + 8 + bob),
                (cx + 4, sy + 19 + bob), (cx, sy + 21 + bob), (cx - 4, sy + 19 + bob)
            ])
            pygame.draw.polygon(surface, beard_white, [
                (cx - 6, sy + 8 + bob), (cx + 6, sy + 8 + bob),
                (cx + 3, sy + 18 + bob), (cx, sy + 20 + bob), (cx - 3, sy + 18 + bob)
            ])

        elif self.facing == "left":
            pygame.draw.rect(surface, skin_color, (cx - 7, sy + 2 + bob, 10, 7), border_radius=2)
            pygame.draw.rect(surface, (25, 25, 35), (cx - 5, sy + 4 + bob, 2, 2))
            # White beard side profile
            pygame.draw.polygon(surface, beard_white, [
                (cx - 7, sy + 7 + bob), (cx, sy + 7 + bob),
                (cx - 2, sy + 18 + bob), (cx - 6, sy + 16 + bob)
            ])

        elif self.facing == "right":
            pygame.draw.rect(surface, skin_color, (cx - 3, sy + 2 + bob, 10, 7), border_radius=2)
            pygame.draw.rect(surface, (25, 25, 35), (cx + 3, sy + 4 + bob, 2, 2))
            # White beard side profile
            pygame.draw.polygon(surface, beard_white, [
                (cx, sy + 7 + bob), (cx + 7, sy + 7 + bob),
                (cx + 6, sy + 16 + bob), (cx + 2, sy + 18 + bob)
            ])

        elif self.facing == "up":
            # Back of hood / neck
            pygame.draw.rect(surface, robe_dark, (cx - 6, sy + 2 + bob, 12, 8), border_radius=3)

        # --- Conical Pointed Wizard Hat (matching reference art!) ---
        hat_color = (32, 44, 105)
        hat_light = (48, 65, 150)
        hat_trim = (220, 180, 60)

        # Hat Brim (wide oval brim)
        pygame.draw.ellipse(surface, hat_color, (cx - 13, sy - 1 + bob, 26, 6))
        pygame.draw.line(surface, hat_light, (cx - 11, sy + bob), (cx + 11, sy + bob), 1)

        # Hat Gold Band
        pygame.draw.rect(surface, hat_trim, (cx - 8, sy - 3 + bob, 16, 3), border_radius=1)

        # Hat Cone (pointed triangle folding slightly back)
        hat_top = (cx + 2, sy - 14 + bob)
        pygame.draw.polygon(surface, hat_color, [
            (cx - 8, sy - 2 + bob), (cx + 8, sy - 2 + bob), hat_top
        ])
        pygame.draw.polygon(surface, hat_light, [
            (cx - 2, sy - 2 + bob), (cx + 7, sy - 2 + bob), hat_top
        ])
        # Crooked tip of hat
        pygame.draw.polygon(surface, hat_color, [
            hat_top, (hat_top[0] - 4, hat_top[1] + 3), (hat_top[0] + 4, hat_top[1] - 2)
        ])

        # --- 5. Ornate Lantern (Fully reactive to is_lantern_lit) ---
        lantern_side = 1 if self.facing in ("right", "down") else -1
        lx = cx + lantern_side * 14
        ly = sy + 9 + bob

        if is_lantern_lit:
            # 1. Radiant warm amber aura (drawn ONLY when lit!)
            glow_alpha = int(45 + 15 * math.sin(self.glow_phase))
            glow_surf = pygame.Surface((36, 36), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 200, 70, glow_alpha), (18, 18), 16)
            pygame.draw.circle(glow_surf, (255, 235, 120, glow_alpha + 15), (18, 18), 8)
            surface.blit(glow_surf, (lx - 18, ly - 14))

            # Brass frame colors
            brass_body = (145, 110, 40)
            brass_highlight = (195, 160, 65)
            # Glowing inner flame
            inner_glow = int(230 + 25 * math.sin(self.glow_phase * 1.5))
            glass_color = (inner_glow, int(inner_glow * 0.78), 45)
        else:
            # UNLIT STATE: Cold, dark, smoky glass with dark brass frame
            brass_body = (75, 60, 35)
            brass_highlight = (95, 80, 45)
            glass_color = (25, 22, 20)  # Dark extinguished glass

        # Top crescent hook
        pygame.draw.arc(surface, brass_highlight, (lx - 3, ly - 16, 7, 6), 0.2, 3.0, 2)
        pygame.draw.circle(surface, brass_highlight, (lx, ly - 13), 2)
        pygame.draw.line(surface, brass_body, (lx, ly - 11), (lx, ly - 6), 2)

        # Lantern Pagoda Cap
        pygame.draw.polygon(surface, brass_body, [
            (lx - 7, ly - 4), (lx + 7, ly - 4),
            (lx + 5, ly - 7), (lx - 5, ly - 7)
        ])
        pygame.draw.line(surface, brass_highlight, (lx - 7, ly - 4), (lx + 7, ly - 4), 1)

        # Lantern Glass Body
        body_rect = pygame.Rect(lx - 6, ly - 4, 12, 13)
        pygame.draw.rect(surface, brass_body, body_rect, border_radius=2)
        # Glass panel
        pygame.draw.rect(surface, glass_color, (lx - 4, ly - 2, 8, 9), border_radius=1)

        if is_lantern_lit:
            # Flickering wick flame dot
            pygame.draw.circle(surface, (255, 250, 200), (lx, ly + 2), 2)

        # Brass frame ribs
        pygame.draw.line(surface, brass_highlight, (lx - 6, ly + 2), (lx + 6, ly + 2), 1)
        pygame.draw.line(surface, brass_highlight, (lx, ly - 4), (lx, ly + 9), 1)

        # Bottom finial point
        pygame.draw.polygon(surface, brass_body, [
            (lx - 3, ly + 9), (lx + 3, ly + 9), (lx, ly + 14)
        ])
