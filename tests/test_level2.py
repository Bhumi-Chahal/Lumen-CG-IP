"""Unit tests for Lumen Level 2 — Phase A (battery, shadow, death conditions, HUD meter).

Phase A scope only: these tests validate the standalone systems in isolation
(BatterySystem, LanternMeter, ShadowCreature, level2_death_triggered). Level 2
room/world integration (camera, crystals, RGB reveal, hidden door/bridge/
writings) is Phase B/C and is not covered here.
"""

import math
import unittest
import pygame

# Initialize pygame headless for unit test execution
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from engine.battery import BatterySystem, LanternMeter
from entities.shadow import ShadowCreature, level2_death_triggered


class TestBatterySystem(unittest.TestCase):
    def setUp(self):
        self.battery = BatterySystem()

    def test_starts_full(self):
        self.assertEqual(self.battery.energy, 100.0)
        self.assertEqual(self.battery.ratio, 1.0)
        self.assertFalse(self.battery.is_depleted)

    def test_drains_only_while_lantern_active(self):
        self.battery.update(dt=5.0, is_lantern_active=False)
        self.assertEqual(self.battery.energy, 100.0)

        self.battery.update(dt=1.0, is_lantern_active=True)
        expected = 100.0 - BatterySystem.ACTIVE_DRAIN_RATE
        self.assertAlmostEqual(self.battery.energy, expected, places=4)

    def test_does_not_go_below_zero(self):
        self.battery.update(dt=1000.0, is_lantern_active=True)
        self.assertEqual(self.battery.energy, 0.0)
        self.assertTrue(self.battery.is_depleted)

    def test_recharge_caps_at_max(self):
        self.battery.energy = 50.0
        self.battery.recharge(1000.0)
        self.assertEqual(self.battery.energy, BatterySystem.MAX_ENERGY)

    def test_reset_restores_full(self):
        self.battery.energy = 3.0
        self.battery.reset()
        self.assertEqual(self.battery.energy, 100.0)
        self.assertFalse(self.battery.is_depleted)

    def test_low_and_critical_thresholds(self):
        self.battery.energy = 25.0
        self.assertTrue(self.battery.is_low)
        self.assertFalse(self.battery.is_critical)

        self.battery.energy = 5.0
        self.assertTrue(self.battery.is_low)
        self.assertTrue(self.battery.is_critical)


class TestLanternMeter(unittest.TestCase):
    def setUp(self):
        self.meter = LanternMeter()
        self.surface = pygame.Surface((400, 100))

    def test_update_advances_phases_without_error(self):
        self.meter.update(dt=0.1, energy_ratio=0.8)
        self.meter.update(dt=0.1, energy_ratio=0.05)
        self.assertGreaterEqual(self.meter.flicker_phase, 0.0)
        self.assertGreaterEqual(self.meter.pulse_phase, 0.0)

    def test_draw_smoke_test_all_ratio_bands(self):
        for ratio in (
            1.0,
            0.5,
            LanternMeter.WARN_RATIO - 0.01,
            LanternMeter.CRITICAL_RATIO - 0.01,
            0.0,
        ):
            self.meter.update(dt=0.05, energy_ratio=ratio)
            self.meter.draw(self.surface, 10, 10, ratio)

    def test_fill_color_shifts_from_amber_to_red_as_ratio_drops(self):
        healthy = self.meter._fill_color(1.0)
        critical = self.meter._fill_color(0.02)
        self.assertGreater(healthy[1], critical[1])


class TestShadowDistanceCurve(unittest.TestCase):
    def test_checkpoints_match_locked_spec(self):
        self.assertEqual(
            ShadowCreature.target_distance_for_battery(1.00),
            ShadowCreature.DIST_FAR
        )
        self.assertEqual(
            ShadowCreature.target_distance_for_battery(0.75),
            ShadowCreature.DIST_CLOSE
        )
        self.assertEqual(
            ShadowCreature.target_distance_for_battery(0.50),
            ShadowCreature.DIST_DANGEROUS
        )
        self.assertEqual(
            ShadowCreature.target_distance_for_battery(0.25),
            ShadowCreature.DIST_VERY_CLOSE
        )
        self.assertEqual(
            ShadowCreature.target_distance_for_battery(0.00),
            ShadowCreature.DIST_CRITICAL
        )

    def test_interpolates_smoothly_between_checkpoints(self):
        mid_ratio = 0.625
        expected_mid = (
            ShadowCreature.DIST_CLOSE +
            ShadowCreature.DIST_DANGEROUS
        ) / 2.0

        self.assertAlmostEqual(
            ShadowCreature.target_distance_for_battery(mid_ratio),
            expected_mid,
            places=4
        )

    def test_distance_decreases_monotonically_as_battery_drops(self):
        ratios = [
            1.0,
            0.9,
            0.8,
            0.75,
            0.6,
            0.5,
            0.4,
            0.25,
            0.1,
            0.0,
        ]

        distances = [
            ShadowCreature.target_distance_for_battery(r)
            for r in ratios
        ]

        for a, b in zip(distances, distances[1:]):
            self.assertGreaterEqual(a, b)

    def test_ratio_is_clamped_outside_0_1(self):
        self.assertEqual(
            ShadowCreature.target_distance_for_battery(1.5),
            ShadowCreature.target_distance_for_battery(1.0)
        )

        self.assertEqual(
            ShadowCreature.target_distance_for_battery(-0.5),
            ShadowCreature.target_distance_for_battery(0.0)
        )


class TestShadowVisibilityAlpha(unittest.TestCase):
    def test_far_distance_still_faintly_visible_not_zero(self):
        alpha = ShadowCreature.visibility_alpha_for_distance(
            ShadowCreature.DIST_FAR
        )
        self.assertGreater(alpha, 0.0)
        self.assertLess(alpha, 0.3)

    def test_contact_range_fully_visible(self):
        alpha = ShadowCreature.visibility_alpha_for_distance(
            ShadowCreature.DIST_CRITICAL
        )
        self.assertEqual(alpha, 1.0)

    def test_alpha_increases_as_distance_shrinks(self):
        far_alpha = ShadowCreature.visibility_alpha_for_distance(
            ShadowCreature.DIST_FAR
        )
        close_alpha = ShadowCreature.visibility_alpha_for_distance(
            ShadowCreature.DIST_VERY_CLOSE
        )
        self.assertLess(far_alpha, close_alpha)


class TestShadowMovement(unittest.TestCase):
    def setUp(self):
        self.shadow = ShadowCreature(x=0.0, y=0.0)

    def test_moves_toward_target_distance_without_teleporting(self):
        player_pos = (1000.0, 0.0)
        dt = 1.0 / 60.0

        start_x = self.shadow.x

        self.shadow.update(
            dt,
            player_pos,
            battery_ratio=1.0
        )

        moved = math.hypot(
            self.shadow.x - start_x,
            self.shadow.y - 0.0
        )

        self.assertLessEqual(
            moved,
            ShadowCreature.MAX_SPEED * dt + 1e-6
        )

    def test_approaches_player_as_battery_drops_over_many_frames(self):
        player_pos = (0.0, 0.0)

        self.shadow.x = 600.0
        self.shadow.y = 0.0

        dt = 1.0 / 60.0

        for _ in range(600):
            prev_dist = self.shadow.distance_to(player_pos)

            self.shadow.update(
                dt,
                player_pos,
                battery_ratio=0.0
            )

            new_dist = self.shadow.distance_to(player_pos)

            step = abs(prev_dist - new_dist)

            self.assertLessEqual(
                step,
                ShadowCreature.MAX_SPEED * dt + 1e-6
            )

        final_dist = self.shadow.distance_to(player_pos)

        self.assertAlmostEqual(
            final_dist,
            ShadowCreature.DIST_CRITICAL,
            delta=2.0
        )

    def test_reset_returns_to_spawn(self):
        self.shadow.x = 999.0
        self.shadow.y = -999.0

        self.shadow.reset()

        self.assertEqual(
            self.shadow.x,
            self.shadow.spawn_x
        )
        self.assertEqual(
            self.shadow.y,
            self.shadow.spawn_y
        )

    def test_degenerate_zero_distance_does_not_crash(self):
        self.shadow.x = 50.0
        self.shadow.y = 50.0

        player_pos = (50.0, 50.0)

        try:
            self.shadow.update(
                1.0 / 60.0,
                player_pos,
                battery_ratio=0.5
            )
        except ZeroDivisionError:
            self.fail(
                "ShadowCreature.update raised ZeroDivisionError "
                "on zero distance"
            )


class TestShadowContactDeath(unittest.TestCase):
    def setUp(self):
        self.shadow = ShadowCreature(x=0.0, y=0.0)

    def test_not_touching_when_far(self):
        self.assertFalse(
            self.shadow.is_touching_player((500.0, 0.0))
        )

    def test_touching_within_contact_radius(self):
        self.shadow.x = 10.0
        self.shadow.y = 0.0

        self.assertTrue(
            self.shadow.is_touching_player((0.0, 0.0))
        )

    def test_touching_boundary_is_inclusive(self):
        self.shadow.x = ShadowCreature.CONTACT_RADIUS
        self.shadow.y = 0.0

        self.assertTrue(
            self.shadow.is_touching_player((0.0, 0.0))
        )


class TestLevel2DeathConditionsAreIndependent(unittest.TestCase):
    def setUp(self):
        self.battery = BatterySystem()

        self.shadow = ShadowCreature(
            x=10000.0,
            y=10000.0
        )

        self.player_pos = (0.0, 0.0)

    def test_battery_depleted_alone_triggers_death(self):
        self.battery.energy = 0.0

        self.assertTrue(self.battery.is_depleted)

        self.assertFalse(
            self.shadow.is_touching_player(
                self.player_pos
            )
        )

        self.assertTrue(
            level2_death_triggered(
                self.battery,
                self.shadow,
                self.player_pos
            )
        )

    def test_shadow_contact_alone_triggers_death_even_at_full_battery(self):
        self.battery.energy = 100.0

        self.shadow.x = 0.0
        self.shadow.y = 0.0

        self.assertFalse(self.battery.is_depleted)

        self.assertTrue(
            self.shadow.is_touching_player(
                self.player_pos
            )
        )

        self.assertTrue(
            level2_death_triggered(
                self.battery,
                self.shadow,
                self.player_pos
            )
        )

    def test_no_death_when_neither_condition_met(self):
        self.battery.energy = 50.0

        self.shadow.x = 10000.0
        self.shadow.y = 10000.0

        self.assertFalse(
            level2_death_triggered(
                self.battery,
                self.shadow,
                self.player_pos
            )
        )


class TestShadowDrawSmokeTest(unittest.TestCase):
    def setUp(self):
        self.surface = pygame.Surface((800, 600))

        self.shadow = ShadowCreature(
            x=400.0,
            y=300.0
        )

    def test_draw_at_various_distances(self):
        player_center = (400.0, 300.0)

        for offset in (
            0.0,
            ShadowCreature.DIST_VERY_CLOSE,
            ShadowCreature.DIST_DANGEROUS,
            ShadowCreature.DIST_CLOSE,
            ShadowCreature.DIST_FAR,
            ShadowCreature.DIST_FAR + 400,
        ):
            self.shadow.x = 400.0 + offset
            self.shadow.y = 300.0

            self.shadow.draw(
                self.surface,
                player_center
            )


if __name__ == "__main__":
    unittest.main()
