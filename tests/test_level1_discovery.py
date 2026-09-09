"""Original Level 1 discovery and line-of-sight regression checks."""
import pygame
import pytest
from content.level1 import Level1Room, has_line_of_sight as l1_has_los
from engine.inventory import Inventory
from engine.player import Player
from engine.lantern import Lantern

class TestLevel1EnvironmentalDiscovery:
    def test_keys_have_environmental_containers(self):
        """Keys are embedded within believable environmental containers rather than floating in the open."""
        room = Level1Room()
        key_map = {k.id: k for k in room.keys}

        assert "key_bronze" in key_map
        assert key_map["key_bronze"].container_type == "roots"
        assert "Root" in key_map["key_bronze"].container_name

        assert "key_silver" in key_map
        assert key_map["key_silver"].container_type == "cracked_boulder"
        assert ("Boulder" in key_map["key_silver"].container_name or
                "Stone" in key_map["key_silver"].container_name or
                "Pillar" in key_map["key_silver"].container_name)

        assert "key_gold" in key_map
        assert key_map["key_gold"].container_type == "masonry_debris"
        assert "Masonry" in key_map["key_gold"].container_name or "Ruin" in key_map["key_gold"].container_name

    def test_dummy_obstacles_exist_with_matching_types(self):
        """Visually similar dummy environmental objects exist with empty atmospheric text."""
        room = Level1Room()
        dummy_types = {obs.obs_type for obs in room.obstacles}
        assert "roots" in dummy_types
        assert "cracked_boulder" in dummy_types
        assert "masonry_debris" in dummy_types

        # Verify dummy obstacles have descriptive empty-investigation text
        for obs in room.obstacles:
            if obs.obs_type in ("roots", "cracked_boulder", "masonry_debris"):
                assert len(obs.inspect_text) > 10
                assert ("nothing" in obs.inspect_text.lower() or
                        "empty" in obs.inspect_text.lower() or
                        "no hidden" in obs.inspect_text.lower() or
                        "only" in obs.inspect_text.lower())

    def test_key_pickup_via_interact(self):
        """Keys can be investigated and collected via [E] interaction."""
        room = Level1Room()
        inv = Inventory()
        key = room.keys[0]

        player = Player(x=key.rect.centerx, y=key.rect.centery)
        res = room.handle_interact(player, inv)

        assert res is True
        assert key.collected is True
        assert inv.has_key(key.id)
        assert inv.key_count == 1

        # Duplicate pickup attempt returns False
        res_dup = room.handle_interact(player, inv)
        assert res_dup is False
        assert inv.key_count == 1

    def test_dummy_object_inspection_yields_no_items(self):
        """Inspecting a dummy environmental object gives feedback but grants no keys or items."""
        room = Level1Room()
        inv = Inventory()
        dummy = next(obs for obs in room.obstacles if obs.obs_type == "roots")

        player = Player(x=dummy.rect.centerx, y=dummy.rect.centery)
        res = room.handle_interact(player, inv)

        assert res is True
        assert inv.key_count == 0
        assert inv.clue_count == 0
        assert room.message == dummy.inspect_text

    def test_cannot_collect_key_through_wall(self):
        """Line-of-sight check prevents key collection when a wall occludes the player."""
        room = Level1Room()
        inv = Inventory()
        key = room.keys[0]

        # Put player at key location, but inject a solid blocking wall directly between player and key
        blocking_wall = pygame.Rect(key.rect.centerx - 10, key.rect.centery - 10, 20, 20)
        room.walls.append(blocking_wall)
        room.wall_rects = room.walls

        player = Player(x=key.rect.centerx + 15, y=key.rect.centery)
        res = room.handle_interact(player, inv)

        assert res is False
        assert key.collected is False
        assert inv.key_count == 0

    def test_cannot_inspect_dummy_through_wall(self):
        """Line-of-sight check prevents inspecting dummy objects through solid walls."""
        room = Level1Room()
        inv = Inventory()
        dummy = room.obstacles[0]

        blocking_wall = pygame.Rect(dummy.rect.centerx - 10, dummy.rect.centery - 10, 20, 20)
        room.walls.append(blocking_wall)
        room.wall_rects = room.walls

        player = Player(x=dummy.rect.centerx + 15, y=dummy.rect.centery)
        res = room.handle_interact(player, inv)

        assert res is False
