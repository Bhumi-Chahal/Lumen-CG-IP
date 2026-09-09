"""tests/test_level3.py — Unit and system tests for Level 3 mechanics and entities.

Tests cover:
- Pure reflection mathematics (cardinal & diagonal preservation, discrete normals, 45° mappings)
- Mirror entity ownership, discrete 8-orientation states, 45° rotation
- Trial Mirror vs Player Mirror properties and Inventory isolation safeguards
- PuzzleCrystal color requirements, non-punishing wrong color, and 0.5s grace sustain
"""

import math
import unittest
import pygame

# Initialize pygame headless
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from engine.inventory import Inventory
from engine.reflection import (
    calculate_reflection,
    get_orientation_normal,
    dot_product,
    normalize_vector,
    ORIENTATION_NORMALS,
    SQRT2_2,
)
from entities.mirror import Mirror
from entities.puzzle_crystal import PuzzleCrystal


class TestReflectionMath(unittest.TestCase):
    """Pure, Pygame-independent reflection mathematics tests."""

    def test_horizontal_reflection_cardinal(self):
        """Horizontal beam hitting a vertical mirror (normal facing West)."""
        incoming = (1.0, 0.0)    # moving East (right)
        normal = (-1.0, 0.0)      # mirror facing West
        reflected = calculate_reflection(incoming, normal)
        self.assertAlmostEqual(reflected[0], -1.0, places=4)
        self.assertAlmostEqual(reflected[1], 0.0, places=4)

    def test_vertical_reflection_cardinal(self):
        """Vertical beam hitting a horizontal mirror (normal facing North)."""
        incoming = (0.0, 1.0)     # moving South (down)
        normal = (0.0, -1.0)      # mirror facing North
        reflected = calculate_reflection(incoming, normal)
        self.assertAlmostEqual(reflected[0], 0.0, places=4)
        self.assertAlmostEqual(reflected[1], -1.0, places=4)

    def test_45_degree_reflection_right_to_up(self):
        """Horizontal beam moving right reflected 90 degrees upward by a 45-degree mirror."""
        incoming = (1.0, 0.0)
        # Mirror tilted 45 degrees, normal pointing North-West (-SQRT2_2, -SQRT2_2)
        normal = (-SQRT2_2, -SQRT2_2)
        reflected = calculate_reflection(incoming, normal)
        self.assertAlmostEqual(reflected[0], 0.0, places=4)
        self.assertAlmostEqual(reflected[1], -1.0, places=4)

    def test_45_degree_reflection_right_to_down(self):
        """Horizontal beam moving right reflected 90 degrees downward."""
        incoming = (1.0, 0.0)
        # Mirror normal pointing South-West (-SQRT2_2, SQRT2_2)
        normal = (-SQRT2_2, SQRT2_2)
        reflected = calculate_reflection(incoming, normal)
        self.assertAlmostEqual(reflected[0], 0.0, places=4)
        self.assertAlmostEqual(reflected[1], 1.0, places=4)

    def test_45_degree_reflection_down_to_right(self):
        """Vertical beam moving down reflected 90 degrees rightward."""
        incoming = (0.0, 1.0)
        # Mirror normal pointing North-West (-SQRT2_2, -SQRT2_2)
        normal = (-SQRT2_2, -SQRT2_2)
        reflected = calculate_reflection(incoming, normal)
        self.assertAlmostEqual(reflected[0], -1.0, places=4)
        self.assertAlmostEqual(reflected[1], 0.0, places=4)

    def test_diagonal_beam_reflection(self):
        """Diagonal beam hitting a flat vertical wall/mirror."""
        incoming = (SQRT2_2, SQRT2_2)  # moving South-East
        normal = (-1.0, 0.0)           # vertical mirror facing West
        reflected = calculate_reflection(incoming, normal)
        # X reflects, Y stays same
        self.assertAlmostEqual(reflected[0], -SQRT2_2, places=4)
        self.assertAlmostEqual(reflected[1], SQRT2_2, places=4)

    def test_deterministic_output_stability(self):
        """Calling calculate_reflection multiple times produces bit-exact deterministic results."""
        incoming = (1.0, 0.0)
        normal = get_orientation_normal(5)
        first = calculate_reflection(incoming, normal)
        for _ in range(50):
            repeated = calculate_reflection(incoming, normal)
            self.assertEqual(first, repeated)

    def test_orientation_normals_count_and_magnitude(self):
        """There must be exactly 8 discrete orientation normals, all unit length."""
        self.assertEqual(len(ORIENTATION_NORMALS), 8)
        for i, n in enumerate(ORIENTATION_NORMALS):
            mag = math.hypot(n[0], n[1])
            self.assertAlmostEqual(mag, 1.0, places=4)
            retrieved = get_orientation_normal(i)
            self.assertEqual(n, retrieved)

    def test_cardinal_input_produces_cardinal_output(self):
        """Important mathematical rule: cardinal input ALWAYS produces cardinal output."""
        cardinals = [(1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)]
        for incoming in cardinals:
            for orientation in range(8):
                normal = get_orientation_normal(orientation)
                reflected = calculate_reflection(incoming, normal)
                # Must be one of the cardinal directions
                is_cardinal = any(
                    math.isclose(reflected[0], c[0], abs_tol=1e-4) and
                    math.isclose(reflected[1], c[1], abs_tol=1e-4)
                    for c in cardinals
                )
                self.assertTrue(
                    is_cardinal,
                    f"Expected cardinal output for incoming {incoming} with orientation {orientation}, got {reflected}"
                )

    def test_diagonal_input_produces_diagonal_output(self):
        """Important mathematical rule: diagonal input ALWAYS produces diagonal output."""
        diagonals = [
            (SQRT2_2, SQRT2_2),
            (-SQRT2_2, SQRT2_2),
            (SQRT2_2, -SQRT2_2),
            (-SQRT2_2, -SQRT2_2),
        ]
        for incoming in diagonals:
            for orientation in range(8):
                normal = get_orientation_normal(orientation)
                reflected = calculate_reflection(incoming, normal)
                # Must be one of the diagonal directions
                is_diagonal = any(
                    math.isclose(reflected[0], d[0], abs_tol=1e-4) and
                    math.isclose(reflected[1], d[1], abs_tol=1e-4)
                    for d in diagonals
                )
                self.assertTrue(
                    is_diagonal,
                    f"Expected diagonal output for incoming {incoming} with orientation {orientation}, got {reflected}"
                )

    def test_cardinal_to_cardinal_specific_mappings(self):
        """Verify exact cardinal reflection mappings for the key 45-degree orientations."""
        # Moving North (0, -1) hitting NW mirror (orientation 5: -SQRT2_2, -SQRT2_2) -> East (1, 0)
        r1 = calculate_reflection((0.0, -1.0), get_orientation_normal(5))
        self.assertAlmostEqual(r1[0], 1.0, places=4)
        self.assertAlmostEqual(r1[1], 0.0, places=4)

        # Moving North (0, -1) hitting NE mirror (orientation 7: SQRT2_2, -SQRT2_2) -> West (-1, 0)
        r2 = calculate_reflection((0.0, -1.0), get_orientation_normal(7))
        self.assertAlmostEqual(r2[0], -1.0, places=4)
        self.assertAlmostEqual(r2[1], 0.0, places=4)

        # Moving East (1, 0) hitting NW mirror (orientation 5: -SQRT2_2, -SQRT2_2) -> North (0, -1)
        r3 = calculate_reflection((1.0, 0.0), get_orientation_normal(5))
        self.assertAlmostEqual(r3[0], 0.0, places=4)
        self.assertAlmostEqual(r3[1], -1.0, places=4)

        # Moving East (1, 0) hitting SW mirror (orientation 3: -SQRT2_2, SQRT2_2) -> South (0, 1)
        r4 = calculate_reflection((1.0, 0.0), get_orientation_normal(3))
        self.assertAlmostEqual(r4[0], 0.0, places=4)
        self.assertAlmostEqual(r4[1], 1.0, places=4)


class TestMirrorEntity(unittest.TestCase):
    """Unit tests for the Mirror entity and inventory interactions."""

    def setUp(self):
        self.mirror = Mirror(
            mirror_id="mirror_red",
            socket_id="socket_1",
            x=500.0,
            y=400.0,
            orientation=0,
            name="Crimson Refractor"
        )

    def test_mirror_ownership_attributes(self):
        """Mirror properly owns id, socket_id, position, orientation, and name."""
        self.assertEqual(self.mirror.id, "mirror_red")
        self.assertEqual(self.mirror.socket_id, "socket_1")
        self.assertEqual(self.mirror.x, 500.0)
        self.assertEqual(self.mirror.y, 400.0)
        self.assertEqual(self.mirror.orientation, 0)
        self.assertEqual(self.mirror.name, "Crimson Refractor")

    def test_rotation_is_discrete_and_modulo_8(self):
        """Rotating increments orientation through exactly 8 states and wraps cleanly."""
        for expected in range(1, 8):
            self.mirror.rotate(1)
            self.assertEqual(self.mirror.orientation, expected)
        # 8th rotation wraps back to 0
        self.mirror.rotate(1)
        self.assertEqual(self.mirror.orientation, 0)

    def test_multi_step_rotation(self):
        """Rotating by multiple steps wraps modulo 8."""
        self.mirror.rotate(10)  # 10 % 8 = 2
        self.assertEqual(self.mirror.orientation, 2)
        self.mirror.rotate(-3)  # (2 - 3) % 8 = 7
        self.assertEqual(self.mirror.orientation, 7)

    def test_mirror_normal_reflects_current_orientation(self):
        """Mirror.normal returns the precomputed unit normal matching orientation."""
        self.mirror.orientation = 0
        self.assertEqual(self.mirror.normal, (1.0, 0.0))
        self.mirror.orientation = 2
        self.assertEqual(self.mirror.normal, (0.0, 1.0))
        self.mirror.orientation = 4
        self.assertEqual(self.mirror.normal, (-1.0, 0.0))
        self.mirror.orientation = 6
        self.assertEqual(self.mirror.normal, (0.0, -1.0))

    def test_mirror_reflect_beam(self):
        """Mirror.reflect_beam returns the correct reflected direction vector."""
        # Set mirror to orientation 5 (normal pointing North-West: -SQRT2_2, -SQRT2_2)
        self.mirror.orientation = 5
        incoming = (1.0, 0.0)
        reflected = self.mirror.reflect_beam(incoming)
        self.assertAlmostEqual(reflected[0], 0.0, places=4)
        self.assertAlmostEqual(reflected[1], -1.0, places=4)

    def test_all_8_mirror_orientations_and_normals(self):
        """All 8 discrete orientations (45-degree intervals) return the correct unit normal."""
        expected_normals = [
            (1.0, 0.0),           # 0: 0° East
            (SQRT2_2, SQRT2_2),   # 1: 45° South-East
            (0.0, 1.0),           # 2: 90° South
            (-SQRT2_2, SQRT2_2),  # 3: 135° South-West
            (-1.0, 0.0),          # 4: 180° West
            (-SQRT2_2, -SQRT2_2), # 5: 225° North-West
            (0.0, -1.0),          # 6: 270° North
            (SQRT2_2, -SQRT2_2),  # 7: 315° North-East
        ]
        for i, expected in enumerate(expected_normals):
            self.mirror.orientation = i
            norm = self.mirror.normal
            self.assertAlmostEqual(norm[0], expected[0], places=5)
            self.assertAlmostEqual(norm[1], expected[1], places=5)

    def test_trial_mirror_vs_player_mirror_properties(self):
        """Trial mirrors are identified as trial and neither mirror type is collectible in Level 3."""
        trial = Mirror("trial_m1", "trial_socket_1", 300.0, 300.0, orientation=2, is_trial=True)
        player = Mirror("mirror_red", "socket_1", 500.0, 500.0, orientation=0, is_trial=False)

        self.assertTrue(trial.is_trial)
        self.assertTrue(trial.is_trial_mirror)
        self.assertFalse(trial.is_collectible)

        self.assertFalse(player.is_trial)
        self.assertFalse(player.is_trial_mirror)
        self.assertFalse(player.is_collectible)

    def test_trial_mirror_cannot_enter_inventory(self):
        """Trial mirrors are environmental teaching objects and NEVER enter player inventory."""
        inv = Inventory()
        trial = Mirror("trial_mirror_1", "ts1", 200.0, 200.0, orientation=1, is_trial=True)

        res1 = inv.add_mirror(trial)
        self.assertFalse(res1)
        self.assertEqual(inv.mirror_count, 0)
        self.assertFalse(inv.has_mirror("trial_mirror_1"))

        # String ID attempt with "trial" also blocked
        res2 = inv.add_mirror("trial_mirror_chamber_2")
        self.assertFalse(res2)
        self.assertEqual(inv.mirror_count, 0)

    def test_player_mirror_enters_and_uses_inventory_correctly(self):
        """Player mirrors (M1, M2, M3 from Level 2) enter and query inventory correctly."""
        inv = Inventory()

        res1 = inv.add_mirror("mirror_red")
        res2 = inv.add_mirror("mirror_blue")
        res3 = inv.add_mirror("mirror_green")

        self.assertTrue(res1)
        self.assertTrue(res2)
        self.assertTrue(res3)
        self.assertEqual(inv.mirror_count, 3)
        self.assertTrue(inv.has_mirror("mirror_red"))
        self.assertTrue(inv.has_mirror("mirror_blue"))
        self.assertTrue(inv.has_mirror("mirror_green"))

    def test_mirror_hitbox_rect(self):
        """Mirror rect is centered at (x, y) with width/height 2*radius."""
        r = self.mirror.rect
        self.assertEqual(r.centerx, 500)
        self.assertEqual(r.centery, 400)
        self.assertEqual(r.width, 48)
        self.assertEqual(r.height, 48)


class TestPuzzleCrystalMechanics(unittest.TestCase):
    """Unit tests for PuzzleCrystal color gating and sustain grace."""

    def test_crystal_activation_requires_matching_color(self):
        """PuzzleCrystal only activates when struck by its required_color."""
        crystal_red = PuzzleCrystal("c_red", 600.0, 300.0, required_color="red")
        crystal_any = PuzzleCrystal("c_any", 600.0, 400.0, required_color=None)

        # 1. Matching color activates
        self.assertTrue(crystal_red.check_activation(hit_by_beam=True, beam_color="red"))
        # 2. Wrong color does NOT activate
        self.assertFalse(crystal_red.check_activation(hit_by_beam=True, beam_color="blue"))
        self.assertFalse(crystal_red.check_activation(hit_by_beam=True, beam_color="white"))
        # 3. Neutral crystal activates on any color
        self.assertTrue(crystal_any.check_activation(hit_by_beam=True, beam_color="blue"))
        self.assertTrue(crystal_any.check_activation(hit_by_beam=True, beam_color="white"))

    def test_crystal_grace_sustain(self):
        """Crystal stays active during 0.5s grace period when beam flickers or unaligns momentarily."""
        crystal = PuzzleCrystal("c1", 500.0, 300.0, required_color="green")

        # Hit crystal
        just_activated = crystal.update(dt=0.016, is_hit=True, hit_color="green")
        self.assertTrue(just_activated)
        self.assertTrue(crystal.active)

        # Beam moves away for 0.2s: crystal should sustain activation
        crystal.update(dt=0.2, is_hit=False)
        self.assertTrue(crystal.active)

        # After grace period expires (>0.5s total), crystal deactivates
        crystal.update(dt=0.35, is_hit=False)
        self.assertFalse(crystal.active)


if __name__ == "__main__":
    unittest.main()
