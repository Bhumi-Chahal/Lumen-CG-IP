"""Interactive environmental clue objects for Lumen (FR-007, FR-008, design.md).

Clues provide indirect lore and environmental guidance toward the true key
needed to unlock the Level 1 exit, without giving away the answer directly.
"""

import math
import pygame


class ClueObject:
    """Schema for an interactive environmental clue.

    Attributes:
        id: Unique identifier for the clue.
        title: Human-readable name shown in the clue inspection modal.
        x, y: Center coordinates of the object.
        target_key_id: The key this clue indirectly hints toward ('key_gold').
        prompt_text: The indirect narrative clue text.
        clue_type: Visual archetype ('statue', 'plaque', 'sigil').
    """

    def __init__(self, clue_id: str, title: str, x: float, y: float,
                 target_key_id: str, prompt_text: str, clue_type: str = "statue",
                 radius: int = 22):
        self.id = clue_id
        self.title = title
        self.x = x
        self.y = y
        self.radius = radius
        self.target_key_id = target_key_id
        self.prompt_text = prompt_text
        self.clue_type = clue_type
        self.triggered = False
        self.pulse = 0.0

    @property
    def rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x - self.radius), int(self.y - self.radius),
                           self.radius * 2, self.radius * 2)

    def update(self, dt: float):
        self.pulse = (self.pulse + dt * 3.0) % (2 * math.pi)

    def draw(self, surface: pygame.Surface, is_lit: bool, player_near: bool = False,
             camera_offset: tuple[int, int] = (0, 0)):
        pos = (int(self.x - camera_offset[0]), int(self.y - camera_offset[1]))

        if not is_lit:
            # Outside lantern light: faint stone silhouette
            pygame.draw.circle(surface, (20, 20, 26), pos, self.radius, width=1)
            return

        # Lit state rendering based on archetype
        glow_pulse = int(180 + 35 * math.sin(self.pulse))

        if self.clue_type == "statue":
            # Ancient humanoid stone statue on pedestal
            # Pedestal base
            pedestal = pygame.Rect(pos[0] - 14, pos[1] + 4, 28, 10)
            pygame.draw.rect(surface, (45, 42, 54), pedestal, border_radius=2)
            pygame.draw.rect(surface, (70, 66, 82), pedestal, width=2, border_radius=2)
            # Torso (trapezoid body)
            pygame.draw.polygon(surface, (85, 82, 100), [
                (pos[0] - 8, pos[1] + 4), (pos[0] + 8, pos[1] + 4),
                (pos[0] + 5, pos[1] - 8), (pos[0] - 5, pos[1] - 8),
            ])
            # Neck
            pygame.draw.rect(surface, (90, 86, 105), (pos[0] - 2, pos[1] - 10, 4, 3))
            # Head
            pygame.draw.circle(surface, (105, 100, 120), (pos[0], pos[1] - 14), 5)
            pygame.draw.circle(surface, (80, 76, 95), (pos[0], pos[1] - 14), 5, width=1)
            # Outstretched arm with bronze hand
            pygame.draw.line(surface, (80, 76, 95), (pos[0] + 5, pos[1] - 4), (pos[0] + 13, pos[1] - 2), 2)
            pygame.draw.circle(surface, (190, 150, 80), (pos[0] + 13, pos[1] - 2), 3)
            # Moss on base
            pygame.draw.rect(surface, (45, 95, 60), (pos[0] - 12, pos[1] + 10, 8, 3))

        elif self.clue_type == "plaque":
            # Engraved temple wall plaque
            plaque_rect = pygame.Rect(pos[0] - 18, pos[1] - 14, 36, 28)
            pygame.draw.rect(surface, (38, 36, 46), plaque_rect, border_radius=4)
            pygame.draw.rect(surface, (170, 140, 80), plaque_rect, width=2, border_radius=4)
            # Carved lines of ancient script
            for row in range(3):
                y_line = pos[1] - 6 + row * 6
                pygame.draw.line(surface, (140, 130, 110), (pos[0] - 12, y_line), (pos[0] + 12, y_line), 1)

        elif self.clue_type == "sigil":
            # Sun-shaped rune carving in the stone floor
            pygame.draw.circle(surface, (45, 38, 30), pos, self.radius)
            pygame.draw.circle(surface, (215, 175, 55), pos, 9)
            # Radiating sun rays
            for i in range(8):
                angle = i * (math.pi / 4)
                rx1 = pos[0] + int(11 * math.cos(angle))
                ry1 = pos[1] + int(11 * math.sin(angle))
                rx2 = pos[0] + int(17 * math.cos(angle))
                ry2 = pos[1] + int(17 * math.sin(angle))
                pygame.draw.line(surface, (230, 185, 65), (rx1, ry1), (rx2, ry2), 2)

        elif self.clue_type == "tree_stump":
            # Cut tree stump with bark and ring details
            # Bark exterior (irregular circle)
            pygame.draw.circle(surface, (65, 45, 30), pos, 14)
            pygame.draw.circle(surface, (50, 35, 22), pos, 14, width=2)
            # Cut top surface (lighter wood)
            pygame.draw.circle(surface, (90, 70, 45), pos, 11)
            # Tree rings (concentric)
            pygame.draw.circle(surface, (75, 58, 38), pos, 8, width=1)
            pygame.draw.circle(surface, (75, 58, 38), pos, 5, width=1)
            pygame.draw.circle(surface, (65, 50, 32), pos, 2)
            # Bark texture radiating lines
            for i in range(6):
                angle = i * math.pi / 3
                bx1 = pos[0] + int(11 * math.cos(angle))
                by1 = pos[1] + int(11 * math.sin(angle))
                bx2 = pos[0] + int(14 * math.cos(angle))
                by2 = pos[1] + int(14 * math.sin(angle))
                pygame.draw.line(surface, (40, 28, 18), (bx1, by1), (bx2, by2), 1)
            # Small moss patch
            pygame.draw.circle(surface, (40, 75, 35), (pos[0] - 8, pos[1] + 8), 4)

        elif self.clue_type == "standing_stone":
            # Ancient megalith / standing stone — rough, clearly distinct from pillars
            stone_pts = [
                (pos[0] - 8, pos[1] + 14), (pos[0] - 10, pos[1] - 4),
                (pos[0] - 7, pos[1] - 16), (pos[0] - 2, pos[1] - 20),
                (pos[0] + 3, pos[1] - 18), (pos[0] + 8, pos[1] - 12),
                (pos[0] + 10, pos[1] + 2), (pos[0] + 8, pos[1] + 14),
            ]
            pygame.draw.polygon(surface, (62, 58, 72), stone_pts)
            pygame.draw.polygon(surface, (42, 38, 50), stone_pts, 2)
            # Carved groove markings
            pygame.draw.line(surface, (48, 44, 56), (pos[0] - 5, pos[1] - 10), (pos[0] + 5, pos[1] - 8), 1)
            pygame.draw.line(surface, (48, 44, 56), (pos[0] - 4, pos[1] - 4), (pos[0] + 6, pos[1] - 2), 1)
            pygame.draw.line(surface, (48, 44, 56), (pos[0] - 3, pos[1] + 4), (pos[0] + 5, pos[1] + 6), 1)
            # Ancient rune symbol
            pygame.draw.circle(surface, (85, 75, 55), (pos[0], pos[1] - 6), 3, width=1)

        # Triggered checkmark / indicator
        if self.triggered:
            # Small green discovery jewel
            pygame.draw.circle(surface, (60, 210, 140), (pos[0] + 13, pos[1] - 13), 4)
            pygame.draw.circle(surface, (20, 80, 45), (pos[0] + 13, pos[1] - 13), 4, width=1)
        else:
            # Subtle environmental irregularity / faint chisel shimmer when lit and unexamined
            if is_lit:
                faint_shimmer = int(12 + 8 * math.sin(self.pulse))
                shimmer_surf = pygame.Surface((28, 28), pygame.SRCALPHA)
                pygame.draw.circle(shimmer_surf, (215, 195, 150, faint_shimmer), (14, 14), 12)
                surface.blit(shimmer_surf, (pos[0] - 14, pos[1] - 14))


def get_level1_clues() -> list[ClueObject]:
    """The canonical clue instances for Level 1.

    Each clue provides a distinct piece of indirect evidence pointing to key_gold:
    - Statue: warmth and untarnished metal (gold doesn't tarnish).
    - Plaque: explicitly mentions silver dulls and bronze rusts; only the metal that never fades passes.
    - Sun Sigil: connects the sun emblem to the gold key's hallmark.
    """
    return [
        ClueObject(
            clue_id="clue_statue",
            title="Ancient Guardian Statue",
            x=700, y=350,
            target_key_id="key_gold",
            prompt_text=(
                "An ancient stone sentinel overlooks the ruined corridor. An eroded "
                "inscription at its base warns: 'Beyond this threshold lies the Hall of Fate, "
                "where three great arches stand in silent trial. Only pure light will reveal "
                "the path that does not lead to ruin.'"
            ),
            clue_type="statue",
        ),
        ClueObject(
            clue_id="clue_stump",
            title="Gnarled Tree Stump",
            x=180, y=680,
            target_key_id="key_gold",
            prompt_text=(
                "Ancient runes are scored into the petrified tree rings: 'In the deep chambers, "
                "darkness is not merely an absence of light, but a prowling hunger. Guard your flame "
                "diligently, for when the light falters, the shadow awakens to claim what remains.'"
            ),
            clue_type="tree_stump",
        ),
        ClueObject(
            clue_id="clue_stone",
            title="Weathered Standing Stone",
            x=1400, y=680,
            target_key_id="key_gold",
            prompt_text=(
                "Carved glyphs wind down the ancient megalith: 'Three sacred keys exist in each "
                "domain of the temple. The first opens the passage; the second tests your resolve; "
                "the third preserves your soul. Trust your instincts when facing the seal.'"
            ),
            clue_type="standing_stone",
        ),
    ]
