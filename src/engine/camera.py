"""Camera system for Lumen (architecture.md).

Handles smooth camera following, viewport clamping to room bounds,
and screen shake effects during impacts or puzzle events.
"""

import random
import pygame


class Camera:
    """Tracks a target entity with smooth lerp movement and optional screen shake."""

    def __init__(self, viewport_width: int, viewport_height: int,
                 room_width: int, room_height: int):
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.room_width = room_width
        self.room_height = room_height

        self.x = 0.0
        self.y = 0.0
        self.target_x = 0.0
        self.target_y = 0.0

        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_offset_x = 0.0
        self.shake_offset_y = 0.0

    @property
    def offset(self) -> tuple[int, int]:
        """Returns the current camera offset including screen shake."""
        return (
            int(self.x + self.shake_offset_x),
            int(self.y + self.shake_offset_y)
        )

    def trigger_shake(self, intensity: float = 6.0, duration: float = 0.3):
        """Triggers a screen shake effect."""
        self.shake_intensity = intensity
        self.shake_duration = duration

    def update(self, target_center: tuple[float, float], dt: float):
        """Updates camera position smoothly toward the target center."""
        # Desired camera offset to center target in viewport
        desired_x = target_center[0] - self.viewport_width / 2
        desired_y = target_center[1] - self.viewport_height / 2

        # Clamp desired position to room boundaries
        max_x = max(0, self.room_width - self.viewport_width)
        max_y = max(0, self.room_height - self.viewport_height)
        desired_x = max(0.0, min(desired_x, float(max_x)))
        desired_y = max(0.0, min(desired_y, float(max_y)))

        # Smooth camera lerp (if room is larger than viewport)
        lerp_speed = 8.0
        self.x += (desired_x - self.x) * min(1.0, lerp_speed * dt)
        self.y += (desired_y - self.y) * min(1.0, lerp_speed * dt)

        # Handle screen shake
        if self.shake_duration > 0:
            self.shake_duration -= dt
            decay = max(0.0, self.shake_duration / 0.3)
            current_intensity = self.shake_intensity * decay
            self.shake_offset_x = (random.random() * 2 - 1) * current_intensity
            self.shake_offset_y = (random.random() * 2 - 1) * current_intensity
        else:
            self.shake_offset_x = 0.0
            self.shake_offset_y = 0.0

    def to_screen_rect(self, rect: pygame.Rect) -> pygame.Rect:
        """Converts a world-space rect to screen-space rect."""
        off_x, off_y = self.offset
        return rect.move(-off_x, -off_y)

    def to_screen_pos(self, pos: tuple[float, float]) -> tuple[int, int]:
        """Converts a world-space coordinate to screen-space coordinate."""
        off_x, off_y = self.offset
        return (int(pos[0] - off_x), int(pos[1] - off_y))
