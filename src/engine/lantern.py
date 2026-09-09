"""Lantern state: on/off toggle and active color mode (rules.md §1.2-1.3, design.md §5).

Level 1 baseline lantern:
- Simple on/off toggle via [L].
- Fixed visibility radius that illuminates the chamber.
- Color mode tracking ("white", "red", "blue", "green").
- No battery, drain or energy cost in this standalone level.
"""

from systems.audio import audio


class Lantern:
    VALID_COLORS = ("white", "red", "blue", "green")

    def __init__(self, radius: int = 130, possessed: bool = False):
        self.possessed = possessed
        self.active = True
        self.base_radius = radius
        self.radius = radius
        self.color = "white"

    def toggle(self):
        """Toggle lantern light on or off."""
        self.active = not self.active
        self.radius = self.base_radius if self.active else 0
        audio.play("lantern_toggle")

    def set_color(self, color: str):
        """Set active lantern color mode."""
        if color not in Lantern.VALID_COLORS:
            raise ValueError(f"Unknown lantern color: {color}")
        self.color = color
