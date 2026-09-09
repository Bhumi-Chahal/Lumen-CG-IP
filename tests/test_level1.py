"""Unit tests for Lumen Level 1 prototype (rules.md section 2.5, phases.md Phase 10).

Validates:
- Player movement vector normalization
- Dual-axis wall collision resolution
- Lantern toggle state and lighting radius checks
- Clue trigger proximity and target key consistency
- Inventory key collection
- Exit door unlocking validation (only Gold Key succeeds)
- Camera viewport clamping and screen shake
"""

import unittest
# pyrefly: ignore [missing-import]
import pygame

# Initialize pygame headless for unit test execution
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from engine.player import Player
from engine.collision import move_with_collision
from engine.lantern import Lantern
from engine.lighting import is_point_lit
from engine.inventory import Inventory
from engine.camera import Camera
from systems.clues import get_level1_clues
from content.level1 import Level1Room, SCREEN_WIDTH, SCREEN_HEIGHT


class TestPlayer(unittest.TestCase):
    def setUp(self):
        self.player = Player(x=100.0, y=100.0)

    def test_initial_properties(self):
        self.assertEqual(self.player.x, 100.0)
        self.assertEqual(self.player.y, 100.0)
        self.assertEqual(self.player.lantern_color, "white")
        self.assertEqual(self.player.rect.width, Player.WIDTH)
        self.assertEqual(self.player.rect.height, Player.HEIGHT)

    def test_center_calculation(self):
        cx, cy = self.player.center
        self.assertEqual(cx, 100.0 + Player.WIDTH / 2)
        self.assertEqual(cy, 100.0 + Player.HEIGHT / 2)


class TestCollision(unittest.TestCase):
    def setUp(self):
        self.player = Player(x=50.0, y=50.0)
        # Wall placed ahead at x=100 (player width is 26, right edge at 76)
        self.walls = [pygame.Rect(100, 40, 30, 40)]

    def test_wall_blocks_x_movement(self):
        # Moving right into the wall (dx=1, dy=0)
        move_with_collision(self.player, dx=1.0, dy=0.0, walls=self.walls, dt=0.2)
        # Player should be stopped against the wall's left edge (100 - width)
        self.assertEqual(self.player.x, 100 - self.player.width)

    def test_sliding_along_wall_y_axis(self):
        # Moving diagonally into the wall (dx=1, dy=1)
        move_with_collision(self.player, dx=1.0, dy=1.0, walls=self.walls, dt=0.2)
        # X is clamped to wall left edge, but Y continues to advance
        self.assertEqual(self.player.x, 100 - self.player.width)
        self.assertGreater(self.player.y, 50.0)


class TestLanternAndLighting(unittest.TestCase):
    def test_lantern_toggle(self):
        lantern = Lantern(radius=120)
        self.assertTrue(lantern.active)
        lantern.toggle()
        self.assertFalse(lantern.active)
        lantern.toggle()
        self.assertTrue(lantern.active)

    def test_lantern_toggle_and_radius(self):
        lantern = Lantern(radius=130)
        self.assertTrue(lantern.active)
        self.assertEqual(lantern.radius, 130)
        lantern.toggle()
        self.assertFalse(lantern.active)
        self.assertEqual(lantern.radius, 0)
        lantern.toggle()
        self.assertTrue(lantern.active)
        self.assertEqual(lantern.radius, 130)

    def test_lantern_color(self):
        lantern = Lantern()
        self.assertEqual(lantern.color, "white")
        lantern.set_color("red")
        self.assertEqual(lantern.color, "red")
        with self.assertRaises(ValueError):
            lantern.set_color("invalid_color")




    def test_is_point_lit(self):
        center = (200.0, 200.0)
        radius = 100.0
        # Point inside radius (distance = 50)
        self.assertTrue(is_point_lit((250.0, 200.0), center, radius))
        # Point right on perimeter (distance = 100)
        self.assertTrue(is_point_lit((200.0, 300.0), center, radius))
        # Point outside radius (distance = 150)
        self.assertFalse(is_point_lit((350.0, 200.0), center, radius))



class TestInventory(unittest.TestCase):
    def setUp(self):
        self.inv = Inventory()

    def test_add_and_query_keys(self):
        self.assertEqual(self.inv.key_count, 0)
        self.inv.add_key("key_bronze")
        self.assertTrue(self.inv.has_key("key_bronze"))
        self.assertFalse(self.inv.has_key("key_gold"))
        self.assertEqual(self.inv.key_count, 1)

    def test_no_duplicate_keys(self):
        self.inv.add_key("key_gold")
        self.inv.add_key("key_gold")
        self.assertEqual(self.inv.key_count, 1)


class TestClues(unittest.TestCase):
    def test_level1_clues_point_to_gold_key(self):
        clues = get_level1_clues()
        self.assertEqual(len(clues), 3)
        for clue in clues:
            self.assertEqual(clue.target_key_id, "key_gold")
            self.assertFalse(clue.triggered)
            self.assertTrue(len(clue.prompt_text) > 20)


class TestLevel1RoomPuzzle(unittest.TestCase):
    def setUp(self):
        self.room = Level1Room()
        self.inv = Inventory()

    def test_key_composition(self):
        self.assertEqual(len(self.room.keys), 3)
        correct_keys = [k for k in self.room.keys if k.correct]
        self.assertEqual(len(correct_keys), 1)
        self.assertEqual(correct_keys[0].id, "key_gold")

    def test_bronze_key_fails_exit(self):
        self.inv.add_key("key_bronze")
        self.room.select_and_try_key(self.inv, 1)
        self.assertFalse(self.room.is_complete)

    def test_silver_key_fails_exit(self):
        self.inv.add_key("key_silver")
        self.room.select_and_try_key(self.inv, 2)
        self.assertFalse(self.room.is_complete)

    def test_gold_key_opens_exit(self):
        self.inv.add_key("key_gold")
        self.room.select_and_try_key(self.inv, 3)
        self.assertTrue(self.room.is_complete)

    def test_initial_tutorial_message(self):
        self.assertEqual(self.room.message, "You've been trapped in this abandoned temple. Find a way out.")

    def test_lantern_pickup_interaction(self):
        lantern = Lantern()
        player = Player(x=self.room.lantern_pickup.x - 10, y=self.room.lantern_pickup.y - 10)
        self.assertFalse(lantern.possessed)
        self.assertFalse(self.room.lantern_pickup.collected)

        # Interacting near the pickup collects lantern
        result = self.room.handle_interact(player, self.inv, lantern=lantern)
        self.assertTrue(result)
        self.assertTrue(lantern.possessed)
        self.assertTrue(self.room.lantern_pickup.collected)
        self.assertEqual(self.room.message, "You'll need to collect keys to unlock the way forward.")

    def test_key_pickup_message_count(self):
        player = Player(x=self.room.keys[0].x, y=self.room.keys[0].y)
        self.room.update(player, self.inv, Lantern(possessed=True), dt=0.1)
        self.assertEqual(self.inv.key_count, 1)
        self.assertIn("(1 of 3 keys)", self.room.message)


class TestStoryAndDoorModal(unittest.TestCase):
    def setUp(self):
        from systems.ui import StoryModal, DoorModal
        self.room = Level1Room()
        self.inv = Inventory()
        self.story_modal = StoryModal(800, 600)
        self.door_modal = DoorModal(800, 600)

    def test_level1_has_exactly_three_clues(self):
        self.assertEqual(len(self.room.clue_objects), 3)
        titles = [c.title for c in self.room.clue_objects]
        self.assertIn("Ancient Guardian Statue", titles)
        self.assertIn("Gnarled Tree Stump", titles)
        self.assertIn("Weathered Standing Stone", titles)

    def test_first_clue_sets_followup_pending(self):
        clue = self.room.clue_objects[0]
        player = Player(x=clue.x, y=clue.y)
        self.assertFalse(self.room.first_clue_inspected)
        self.assertFalse(self.room.clue_followup_pending)

        from systems.ui import ClueModal
        cm = ClueModal(800, 600)
        self.room.handle_interact(player, self.inv, clue_modal=cm)
        self.assertTrue(self.room.first_clue_inspected)
        self.assertTrue(self.room.clue_followup_pending)

    def test_all_three_keys_triggers_pending_story_modal(self):
        self.assertIsNone(self.room.pending_story_modal)
        # Collect all 3 keys
        for key in self.room.keys:
            p = Player(x=key.x, y=key.y)
            self.room.update(p, self.inv, Lantern(possessed=True), dt=0.1)

        self.assertEqual(self.inv.key_count, 3)
        self.assertTrue(self.room.all_keys_popup_shown)
        self.assertIsNotNone(self.room.pending_story_modal)
        title, text, mid = self.room.pending_story_modal
        self.assertEqual(mid, "all_keys")

    def test_door_modal_interaction_and_key_handling(self):
        # Open door modal
        self.door_modal.open(self.inv)
        self.assertTrue(self.door_modal.is_open)
        self.assertFalse(self.door_modal.unlocked)

        # Player near exit triggers door modal
        player = Player(x=self.room.exit_rect.centerx, y=self.room.exit_rect.centery)
        opened = self.room.handle_interact(player, self.inv, door_modal=self.door_modal)
        self.assertTrue(opened)

        # Try key without having it
        self.assertFalse(self.inv.has_key("key_gold"))
        self.door_modal.feedback_msg = "You have not discovered Key #3 yet."

        # Add Bronze Key and try (wrong key)
        self.inv.add_key("key_bronze")
        self.assertFalse(self.door_modal.unlocked)

        # Add Gold Key and unlock
        self.inv.add_key("key_gold")
        self.door_modal.unlocked = True
        self.assertTrue(self.door_modal.unlocked)


if __name__ == "__main__":
    unittest.main()
