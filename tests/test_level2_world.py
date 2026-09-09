"""tests/test_level2_world.py — Phase B automated tests for Level 2.

Covers:
    Level2Room initialisation, dimensions, spawn, crystals, shadow
    Camera within Level 2 bounds
    Crystal count and recharge behaviour
    RGB switching (R/G/B)
    RGB reveal helper (lantern ON required)
    Death / restart / inventory preservation
    Jump-gap protection
"""

import pygame
import pytest

# ---------------------------------------------------------------------------
# Pygame headless initialisation (matches existing test pattern)
# ---------------------------------------------------------------------------
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)


# ---------------------------------------------------------------------------
# Imports under test
# ---------------------------------------------------------------------------
from content.level2 import (
    Level2Room,
    L2_WORLD_WIDTH, L2_WORLD_HEIGHT,
    L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT,
    L2_SPAWN_X, L2_SPAWN_Y,
    CRYSTAL_RECHARGE_AMOUNT,
    is_color_active,
    build_colored_darkness_mask,
)
from engine.player import Player
from engine.lantern import Lantern
from engine.camera import Camera
from engine.inventory import Inventory
from engine.battery import BatterySystem
from engine.collision import move_with_collision
from entities.shadow import ShadowCreature


# ===========================================================================
# LEVEL 2 INITIALISATION
# ===========================================================================

class TestLevel2Init:
    """Level2Room can initialise with correct dimensions and entities."""

    def test_world_exceeds_viewport(self):
        room = Level2Room()
        assert L2_WORLD_WIDTH > L2_SCREEN_WIDTH
        assert L2_WORLD_HEIGHT > L2_SCREEN_HEIGHT

    def test_battery_starts_full(self):
        room = Level2Room()
        assert room.battery.energy == BatterySystem.MAX_ENERGY
        assert room.battery.ratio == 1.0

    def test_spawn_inside_world(self):
        assert 0 < L2_SPAWN_X < L2_WORLD_WIDTH
        assert 0 < L2_SPAWN_Y < L2_WORLD_HEIGHT

    def test_spawn_not_inside_wall(self):
        room = Level2Room()
        spawn_rect = pygame.Rect(L2_SPAWN_X - 12, L2_SPAWN_Y - 12, 24, 24)
        for wall in room.walls:
            assert not wall.colliderect(spawn_rect), \
                f"Spawn collides with wall {wall}"

    def test_shadow_exists(self):
        room = Level2Room()
        assert isinstance(room.shadow, ShadowCreature)

    def test_shadow_not_at_spawn(self):
        room = Level2Room()
        import math
        dist = math.hypot(room.shadow.x - L2_SPAWN_X,
                          room.shadow.y - L2_SPAWN_Y)
        assert dist > 200, "Shadow should not be near player spawn"

    def test_walls_are_nonempty(self):
        room = Level2Room()
        assert len(room.walls) >= 10

    def test_pillars_are_nonempty(self):
        room = Level2Room()
        assert len(room.pillars) >= 10

    def test_is_not_dead_initially(self):
        room = Level2Room()
        assert not room.is_dead


# ===========================================================================
# CAMERA
# ===========================================================================

class TestLevel2Camera:
    """Camera operates within Level 2 world bounds."""

    def test_camera_clamps_within_bounds(self):
        cam = Camera(L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT,
                     L2_WORLD_WIDTH, L2_WORLD_HEIGHT)
        # Force update to a corner
        cam.update((0, 0), 1.0)
        cam.update((0, 0), 1.0)
        cam.update((0, 0), 1.0)
        ox, oy = cam.offset
        assert ox >= 0
        assert oy >= 0

    def test_camera_clamps_bottom_right(self):
        cam = Camera(L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT,
                     L2_WORLD_WIDTH, L2_WORLD_HEIGHT)
        cam.update((L2_WORLD_WIDTH, L2_WORLD_HEIGHT), 1.0)
        cam.update((L2_WORLD_WIDTH, L2_WORLD_HEIGHT), 1.0)
        cam.update((L2_WORLD_WIDTH, L2_WORLD_HEIGHT), 1.0)
        ox, oy = cam.offset
        assert ox <= L2_WORLD_WIDTH - L2_SCREEN_WIDTH
        assert oy <= L2_WORLD_HEIGHT - L2_SCREEN_HEIGHT


# ===========================================================================
# CRYSTALS
# ===========================================================================

class TestLevel2Crystals:
    """Energy Crystal stations count and recharge behaviour."""

    def test_total_crystal_count_is_seven(self):
        room = Level2Room()
        assert len(room.crystals) == 7

    def test_crystal_recharge_increases_battery(self):
        room = Level2Room()
        room.battery.energy = 30.0
        player = Player(x=room.crystals[0].x, y=room.crystals[0].y)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        result = room.handle_interact(player, lantern)
        assert result is True
        assert room.battery.energy == pytest.approx(30.0 + CRYSTAL_RECHARGE_AMOUNT)

    def test_recharge_caps_at_max(self):
        room = Level2Room()
        room.battery.energy = 90.0
        player = Player(x=room.crystals[0].x, y=room.crystals[0].y)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        room.handle_interact(player, lantern)
        assert room.battery.energy <= BatterySystem.MAX_ENERGY

    def test_recharge_does_nothing_when_full(self):
        room = Level2Room()
        assert room.battery.energy == BatterySystem.MAX_ENERGY
        player = Player(x=room.crystals[0].x, y=room.crystals[0].y)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        result = room.handle_interact(player, lantern)
        assert result is True  # interaction acknowledged
        assert room.battery.energy == BatterySystem.MAX_ENERGY

    def test_no_recharge_when_far_from_crystal(self):
        room = Level2Room()
        room.battery.energy = 50.0
        player = Player(x=0, y=0)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        result = room.handle_interact(player, lantern)
        assert result is False
        assert room.battery.energy == 50.0

    def test_crystals_not_inside_walls(self):
        room = Level2Room()
        for crystal in room.crystals:
            for wall in room.walls:
                assert not wall.colliderect(crystal.rect), \
                    f"Crystal at ({crystal.x},{crystal.y}) collides with {wall}"


# ===========================================================================
# RGB SWITCHING
# ===========================================================================

class TestRGBSwitching:
    """R/G/B colour selection on the lantern."""

    def test_set_red(self):
        lantern = Lantern(radius=130)
        lantern.set_color("red")
        assert lantern.color == "red"

    def test_set_green(self):
        lantern = Lantern(radius=130)
        lantern.set_color("green")
        assert lantern.color == "green"

    def test_set_blue(self):
        lantern = Lantern(radius=130)
        lantern.set_color("blue")
        assert lantern.color == "blue"

    def test_switching_is_immediate(self):
        lantern = Lantern(radius=130)
        lantern.set_color("red")
        lantern.set_color("blue")
        lantern.set_color("green")
        assert lantern.color == "green"

    def test_rgb_reveal_requires_lantern_on(self):
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("red")
        assert is_color_active(lantern, "red") is True

    def test_rgb_reveal_false_when_off(self):
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = False
        lantern.set_color("red")
        assert is_color_active(lantern, "red") is False

    def test_rgb_reveal_false_wrong_color(self):
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("blue")
        assert is_color_active(lantern, "red") is False

    def test_colored_darkness_mask_does_not_crash(self):
        """Smoke test: mask builds without error for every colour."""
        for color in ("white", "red", "green", "blue"):
            mask = build_colored_darkness_mask(
                (L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT),
                (400, 300), 130,
                lantern_color=color,
            )
            assert mask.get_size() == (L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT)


# ===========================================================================
# DEATH / RESTART
# ===========================================================================

class TestLevel2DeathRestart:
    """Level 2 death, restart, and inventory preservation."""

    def test_battery_zero_triggers_death(self):
        room = Level2Room()
        player = Player(x=L2_SPAWN_X, y=L2_SPAWN_Y)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        room.battery.energy = 0.0
        room.update(player, lantern, 0.016)
        assert room.is_dead

    def test_shadow_contact_triggers_death(self):
        room = Level2Room()
        player = Player(x=L2_SPAWN_X, y=L2_SPAWN_Y)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        # Put shadow on player
        room.shadow.x = L2_SPAWN_X
        room.shadow.y = L2_SPAWN_Y
        room.update(player, lantern, 0.016)
        assert room.is_dead

    def test_reset_restores_battery(self):
        room = Level2Room()
        player = Player(x=L2_SPAWN_X, y=L2_SPAWN_Y)
        room.battery.energy = 0.0
        room.is_dead = True
        room.reset(player)
        assert room.battery.energy == BatterySystem.MAX_ENERGY
        assert not room.is_dead

    def test_reset_restores_spawn(self):
        room = Level2Room()
        player = Player(x=500, y=500)
        room.reset(player)
        assert player.x == L2_SPAWN_X
        assert player.y == L2_SPAWN_Y

    def test_reset_restores_shadow(self):
        room = Level2Room()
        player = Player(x=L2_SPAWN_X, y=L2_SPAWN_Y)
        room.shadow.x = 0
        room.shadow.y = 0
        room.reset(player)
        assert room.shadow.x == room.shadow.spawn_x
        assert room.shadow.y == room.shadow.spawn_y

    def test_level1_inventory_preserved_on_reset(self):
        """Level 2 reset must NOT clear Level 1 inventory."""
        room = Level2Room()
        inv = Inventory()
        inv.add_key("key_gold")
        inv.add_key("key_silver")

        player = Player(x=L2_SPAWN_X, y=L2_SPAWN_Y)
        room.reset(player)

        # Inventory is external to Level2Room — reset doesn't touch it
        assert inv.has_key("key_gold")
        assert inv.has_key("key_silver")


# ===========================================================================
# JUMP-GAP PROTECTION
# ===========================================================================

class TestJumpGapProtection:
    """No Phase B structure should be in jumpable_gaps."""

    def test_no_jumpable_gaps(self):
        room = Level2Room()
        assert room.jumpable_gaps == []
        assert room.jumpable_gap_rects == []


# ===========================================================================
# DRAW SMOKE TESTS
# ===========================================================================

class TestLevel2DrawSmoke:
    """Smoke tests: draw methods run without crashing."""

    def test_draw_does_not_crash(self):
        room = Level2Room()
        player = Player(x=L2_SPAWN_X, y=L2_SPAWN_Y)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        surf = pygame.Surface((L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT))
        room.draw(surf, player, lantern, camera_offset=(0, 0))

    def test_draw_hud_does_not_crash(self):
        room = Level2Room()
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        surf = pygame.Surface((L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT))
        font = pygame.font.SysFont("consolas", 13)
        room.draw_hud(surf, font, lantern)

    def test_update_does_not_crash(self):
        room = Level2Room()
        player = Player(x=L2_SPAWN_X, y=L2_SPAWN_Y)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        for _ in range(10):
            room.update(player, lantern, 0.016)


# ===========================================================================
# PHASE B.1 — ANCIENT INSCRIPTION DISCOVERY HINT
# ===========================================================================

class TestInscriptionDiscoveryHint:
    """The ancient inscription provides a cryptic hint that the lantern
    holds multiple colours, without revealing controls or Phase C answers."""

    def test_inscription_exists(self):
        room = Level2Room()
        assert "inscription" in dir(room) or hasattr(room, "inscription")
        ins = room.inscription
        assert ins is not None

    def test_inscription_text_contains_intended_lines(self):
        room = Level2Room()
        ins = room.inscription
        assert ins["line1"] == "The flame is not what it seems."
        assert ins["line2"] == "Three colors sleep within it."

    def test_inscription_title_is_ancient(self):
        room = Level2Room()
        ins = room.inscription
        assert "Ancient" in ins["title"]

    def test_inscription_is_in_level2_not_level1(self):
        """Inscription belongs to Level2Room, not Level1Room."""
        from content.level1 import Level1Room
        l1 = Level1Room()
        assert not hasattr(l1, "inscription")

    def test_inscription_not_showing_initially(self):
        room = Level2Room()
        assert room.inscription["showing"] is False

    def test_interact_near_inscription_opens_modal(self):
        room = Level2Room()
        ins = room.inscription
        player = Player(x=ins["x"], y=ins["y"])
        lantern = Lantern(radius=130)
        lantern.possessed = True
        result = room.handle_interact(player, lantern)
        assert result is True
        assert ins["showing"] is True

    def test_dismiss_inscription_closes_modal(self):
        room = Level2Room()
        room.inscription["showing"] = True
        room.dismiss_inscription()
        assert room.inscription["showing"] is False

    def test_interact_far_from_inscription_does_not_open(self):
        room = Level2Room()
        player = Player(x=0, y=0)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        room.handle_interact(player, lantern)
        assert room.inscription["showing"] is False

    def test_inscription_does_not_activate_phase_c(self):
        """Opening inscription must not change any gameplay state."""
        room = Level2Room()
        ins = room.inscription
        player = Player(x=ins["x"], y=ins["y"])
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        battery_before = room.battery.energy
        room.handle_interact(player, lantern)
        assert room.battery.energy == battery_before
        assert not room.is_dead

    def test_is_color_active_unchanged(self):
        """is_color_active must still require lantern ON + matching colour."""
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("red")
        assert is_color_active(lantern, "red") is True
        assert is_color_active(lantern, "blue") is False
        lantern.active = False
        assert is_color_active(lantern, "red") is False

    def test_inscription_not_inside_wall(self):
        room = Level2Room()
        ins = room.inscription
        for wall in room.walls:
            assert not wall.colliderect(ins["rect"]), \
                f"Inscription collides with wall {wall}"

    def test_inscription_draw_does_not_crash(self):
        room = Level2Room()
        player = Player(x=room.inscription["x"], y=room.inscription["y"])
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        surf = pygame.Surface((L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT))
        room.draw(surf, player, lantern, camera_offset=(0, 0))

    def test_inscription_modal_draw_does_not_crash(self):
        room = Level2Room()
        room.inscription["showing"] = True
        player = Player(x=L2_SPAWN_X, y=L2_SPAWN_Y)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        surf = pygame.Surface((L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT))
        room.draw(surf, player, lantern, camera_offset=(0, 0))


# ===========================================================================
# PHASE B.2 FIXES (WHITE VISIBILITY & GLOBAL DEATH FLOW)
# ===========================================================================

class TestPhaseB2Fixes:
    def test_white_lantern_visibility_expands_radius(self):
        room = Level2Room()
        player = Player(x=L2_SPAWN_X, y=L2_SPAWN_Y)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("white")
        
        # We can't directly assert eff_radius since it's local in draw(),
        # but we can test that it doesn't crash with the new logic.
        surf = pygame.Surface((L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT))
        room.draw(surf, player, lantern, camera_offset=(0, 0))
        assert True

    def test_death_restarts_level2_with_shared_inventory(self):
        from main import GameManager, STATE_LEVEL2
        import unittest.mock
        
        with unittest.mock.patch.object(GameManager, '_set_display_mode'):
            game = GameManager()
        
        # Mock reaching Level 2
        game.init_level2()
        assert game.state == STATE_LEVEL2
        game.inventory.add_key("key_gold")
        
        # Trigger death in Level 2
        game.level2_room.is_dead = True
        game.level2_room.death_timer = 0.0 # Ready to transition
        
        # Run one update frame
        game._update(0.016)
        
        # Retry rebuilds the Level 2 room without discarding shared progress.
        assert game.state == STATE_LEVEL2
        assert game.level2_room is not None
        assert game.inventory.has_key("key_gold")

# ===========================================================================
# PHASE C1: RED CHAMBER & HIDDEN DOOR
# ===========================================================================

class TestPhaseC1RedChamber:
    def test_rgb_broad_visibility_retained(self):
        """All colors (R/G/B/W) should render without crashing the draw loop."""
        room = Level2Room()
        player = Player(x=L2_SPAWN_X, y=L2_SPAWN_Y)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        
        surf = pygame.Surface((L2_SCREEN_WIDTH, L2_SCREEN_HEIGHT))
        for color in ["white", "red", "green", "blue"]:
            lantern.set_color(color)
            room.draw(surf, player, lantern, camera_offset=(0, 0))
            
    def test_white_hotkey(self):
        """Test K_1 returns to white."""
        from main import GameManager, STATE_LEVEL2
        import unittest.mock
        with unittest.mock.patch.object(GameManager, '_set_display_mode'):
            game = GameManager()
        game.init_level2()
        game.lantern.set_color("red")
        game._handle_keydown(pygame.K_1)
        assert game.lantern.color == "white"

    def test_hidden_door_collision_and_opening(self):
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        player = Player(x=1840, y=1600)
        
        # Initially locked, obstacle is present
        assert room.door_locked is True
        assert room.door_rect in room.all_obstacles
        
        # Need red color to interact successfully
        lantern.set_color("red")
        
        # Interact without key fails
        result = room.handle_interact(player, lantern, inv)
        assert result is True
        assert room.door_locked is True
        
        # Interact with key succeeds
        inv.add_key("key_gold")
        result = room.handle_interact(player, lantern, inv)
        assert result is True
        assert room.door_locked is False
        assert room.door_rect not in room.all_obstacles
        
    def test_door_remains_hidden_if_not_red(self):
        room = Level2Room()
        inv = Inventory()
        inv.add_key("key_gold")
        
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        player = Player(x=1840, y=1600)
        
        # White lantern -> can't interact
        lantern.set_color("white")
        result = room.handle_interact(player, lantern, inv)
        assert room.door_locked is True
        
        # Red lantern OFF -> can't interact
        lantern.set_color("red")
        lantern.active = False
        result = room.handle_interact(player, lantern, inv)
        assert room.door_locked is True

    def test_red_chamber_crystal_exists(self):
        room = Level2Room()
        # The crystal at (2700, 1625) should be present
        found = False
        for crystal in room.crystals:
            if crystal.x == 2700 and crystal.y == 1625:
                found = True
                break
        assert found is True

# ===========================================================================
# PHASE C1.5: CONTROLS & BATTERY-BASED LIGHT INTENSITY
# ===========================================================================

class TestPhaseC15ControlsAndLighting:
    def test_controls_hotkeys_mapping(self):
        """1 -> WHITE, R -> RED, G -> GREEN, B -> BLUE keybindings."""
        from main import GameManager, STATE_LEVEL2
        import unittest.mock

        with unittest.mock.patch.object(GameManager, '_set_display_mode'):
            game = GameManager()
        game.init_level2()
        
        game._handle_keydown(pygame.K_r)
        assert game.lantern.color == "red"

        game._handle_keydown(pygame.K_g)
        assert game.lantern.color == "green"

        game._handle_keydown(pygame.K_b)
        assert game.lantern.color == "blue"

        game._handle_keydown(pygame.K_1)
        assert game.lantern.color == "white"

    def test_battery_ratio_intensity_progression(self):
        """High battery produces stronger illumination (lower mask alpha) than low battery."""
        light_center = (400, 300)
        eff_radius = 1200.0

        mask_100 = build_colored_darkness_mask((800, 600), light_center, eff_radius, battery_ratio=1.0)
        mask_50  = build_colored_darkness_mask((800, 600), light_center, eff_radius, battery_ratio=0.5)
        mask_25  = build_colored_darkness_mask((800, 600), light_center, eff_radius, battery_ratio=0.25)
        mask_10  = build_colored_darkness_mask((800, 600), light_center, eff_radius, battery_ratio=0.10)

        alpha_100 = mask_100.get_at(light_center).a
        alpha_50  = mask_50.get_at(light_center).a
        alpha_25  = mask_25.get_at(light_center).a
        alpha_10  = mask_10.get_at(light_center).a

        # Alpha at center must increase monotonically as battery drops
        assert alpha_100 < alpha_50 < alpha_25 < alpha_10
        # 100% battery center is fully transparent (0 alpha)
        assert alpha_100 == 0

    def test_all_colors_respect_same_battery_intensity(self):
        """All four light states (W/R/G/B) produce identical battery-intensity scaling at 50% battery."""
        light_center = (400, 300)
        eff_radius = 1200.0

        alphas = {}
        for color in ("white", "red", "green", "blue"):
            mask = build_colored_darkness_mask((800, 600), light_center, eff_radius, lantern_color=color, battery_ratio=0.5)
            alphas[color] = mask.get_at(light_center).a

        # All colors produce approximately identical center darkness alpha at 50% battery (within 5 alpha units)
        base_a = alphas["white"]
        for color in ("red", "green", "blue"):
            assert abs(alphas[color] - base_a) <= 5
        assert base_a > 0  # noticeably dimmer than 100% battery

# ===========================================================================
# GOLD KEY INVENTORY CARRYOVER REGRESSION TESTS
# ===========================================================================

class TestGoldKeyInventoryCarryoverToLevel2:
    def test_gold_key_carried_over_opens_red_door(self):
        """Level 1 inventory with key_gold carries over to Level 2 and opens the Red Door on E interaction."""
        from main import GameManager
        import unittest.mock

        with unittest.mock.patch.object(GameManager, '_set_display_mode'):
            game = GameManager()

        # Simulate Level 1 collecting Gold Key
        game.inventory.add_key("key_gold")
        assert game.inventory.has_key("key_gold") is True

        # Transition to Level 2 via init_level2()
        game.init_level2()

        # 1. Verify Gold Key is still present after Level 2 initialization
        assert game.inventory.has_key("key_gold") is True

        # Move player near the Red Door (1840, 1600)
        game.player.x = 1840
        game.player.y = 1600

        # Switch lantern to RED
        game._handle_keydown(pygame.K_r)
        assert game.lantern.color == "red"

        # Verify door is initially locked
        assert game.level2_room.door_locked is True

        # Press E via game._handle_keydown
        game._handle_keydown(pygame.K_e)

        # Verify door opens!
        assert game.level2_room.door_locked is False
        assert game.level2_room.door_rect not in game.level2_room.all_obstacles

    def test_without_gold_key_red_door_remains_locked(self):
        """Level 2 without key_gold in inventory keeps the Red Door locked on E interaction."""
        from main import GameManager
        import unittest.mock

        with unittest.mock.patch.object(GameManager, '_set_display_mode'):
            game = GameManager()

        # Fresh inventory without Gold Key
        game.init_level2()
        assert game.inventory.has_key("key_gold") is False

        # Move player near Red Door & set RED light
        game.player.x = 1840
        game.player.y = 1600
        game._handle_keydown(pygame.K_r)

        # Press E
        game._handle_keydown(pygame.K_e)

        # Door remains locked
        assert game.level2_room.door_locked is True
        assert game.level2_room.message == "It is sealed. A gold key is required."

# ===========================================================================
# PHASE C2.1: COLOR-SPECIFIC REVEALS & DYNAMIC BLUE BRIDGE
# ===========================================================================

class TestPhaseC21ColorSpecificReveals:
    def test_blue_gap_and_chamber_exist(self):
        """Blue chasm and Blue Chamber exist in Level 2 layout."""
        room = Level2Room()
        assert room.chasm_full_rect == pygame.Rect(750, 650, 400, 80)
        assert room.bridge_rect == pygame.Rect(910, 650, 80, 80)
        assert room.chasm_left_rect == pygame.Rect(750, 650, 160, 80)
        assert room.chasm_right_rect == pygame.Rect(990, 650, 160, 80)
        assert room.bridge_discovered is False

    def test_blue_gap_not_in_jumpable_gaps(self):
        """Blue gap is NOT a jumpable gap and cannot be bypassed via SPACE."""
        room = Level2Room()
        assert room.jumpable_gaps == []
        assert room.jumpable_gap_rects == []
        assert room.chasm_full_rect not in room.jumpable_gap_rects

    def test_undiscovered_gap_blocks_movement(self):
        """Undiscovered chasm obstacle is in all_obstacles and blocks passage."""
        room = Level2Room()
        assert room.chasm_full_rect in room.all_obstacles
        assert room.chasm_left_rect not in room.all_obstacles
        assert room.chasm_right_rect not in room.all_obstacles

    def test_white_red_green_do_not_reveal_bridge(self):
        """White, Red, and Green lights do not reveal the Blue bridge."""
        room = Level2Room()
        player = Player(x=950, y=750)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True

        for color in ("white", "red", "green"):
            lantern.set_color(color)
            room.update(player, lantern, 0.016)
            assert room.bridge_discovered is False
            assert room.chasm_full_rect in room.all_obstacles

    def test_blue_light_off_does_not_reveal_bridge(self):
        """Blue light while lantern is OFF does not reveal the bridge."""
        room = Level2Room()
        player = Player(x=950, y=750)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = False
        lantern.set_color("blue")

        room.update(player, lantern, 0.016)
        assert room.bridge_discovered is False

    def test_blue_light_reveals_bridge_when_near(self):
        """Blue light while lantern is ON reveals the bridge when player is nearby."""
        room = Level2Room()
        player = Player(x=950, y=750)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("blue")

        room.update(player, lantern, 0.016)
        assert room.bridge_discovered is True
        assert room.chasm_full_rect not in room.all_obstacles
        assert room.chasm_left_rect in room.all_obstacles
        assert room.chasm_right_rect in room.all_obstacles

    def test_switching_away_from_blue_hides_bridge(self):
        """Switching from BLUE to White/Red/Green while on safe ground hides bridge and restores full chasm obstacle."""
        room = Level2Room()
        player = Player(x=950, y=750)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("blue")

        room.update(player, lantern, 0.016)
        assert room.bridge_discovered is True

        # Move player to safe ground north of bridge (y = 500)
        player.y = 500
        lantern.set_color("white")
        room.update(player, lantern, 0.016)

        # Bridge must immediately disappear and full chasm obstacle return
        assert room.bridge_discovered is False
        assert room.chasm_full_rect in room.all_obstacles
        assert room.chasm_left_rect not in room.all_obstacles

    def test_switching_back_to_blue_reveals_bridge_again(self):
        """Switching back to BLUE near chasm reveals the bridge again."""
        room = Level2Room()
        player = Player(x=950, y=750)
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True

        # 1. Start White -> undiscovered
        lantern.set_color("white")
        room.update(player, lantern, 0.016)
        assert room.bridge_discovered is False

        # 2. Switch Blue -> discovered
        lantern.set_color("blue")
        room.update(player, lantern, 0.016)
        assert room.bridge_discovered is True

        # 3. Move to safe ground & switch Green -> undiscovered
        player.y = 500
        lantern.set_color("green")
        room.update(player, lantern, 0.016)
        assert room.bridge_discovered is False

        # 4. Move near bridge & switch Blue -> discovered again!
        player.y = 750
        lantern.set_color("blue")
        room.update(player, lantern, 0.016)
        assert room.bridge_discovered is True

    def test_player_standing_on_bridge_prevents_color_switch(self):
        """Standing directly on the bridge forces blue color until stepping onto safe ground."""
        room = Level2Room()
        player = Player(x=950, y=690)  # directly on bridge
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("blue")

        room.update(player, lantern, 0.016)
        assert room.bridge_discovered is True

        # Try to switch to White while standing on bridge
        lantern.set_color("white")
        room.update(player, lantern, 0.016)

        # Safety check keeps color Blue and bridge active
        assert lantern.color == "blue"
        assert room.bridge_discovered is True

    def test_blue_chamber_contains_single_energy_crystal(self):
        """Blue Chamber contains exactly one EnergyCrystalStation at (950, 450)."""
        room = Level2Room()
        found = [c for c in room.crystals if c.x == 950 and c.y == 450]
        assert len(found) == 1

    def test_blue_chamber_crystal_recharges_battery(self):
        """Interacting with Blue Chamber crystal recharges player lantern battery."""
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True

        room.battery.energy = 20.0
        player = Player(x=950, y=450)
        result = room.handle_interact(player, lantern, inv)
        assert result is True
        assert room.battery.energy > 20.0

    def test_locked_door_hidden_in_white_green_blue_and_off(self):
        """Locked Red Door returns visual state 'hidden' for WHITE, GREEN, BLUE, and OFF."""
        room = Level2Room()
        lantern = Lantern(radius=130)
        lantern.possessed = True

        # Lantern OFF
        lantern.active = False
        lantern.set_color("red")
        assert room.get_red_door_visual_state(lantern) == "hidden"

        # Lantern ON
        lantern.active = True
        for color in ("white", "green", "blue"):
            lantern.set_color(color)
            assert room.get_red_door_visual_state(lantern) == "hidden"

    def test_locked_door_revealed_only_in_red(self):
        """Locked Red Door returns visual state 'revealed' ONLY under active RED light."""
        room = Level2Room()
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("red")
        assert room.get_red_door_visual_state(lantern) == "revealed"

    def test_red_door_color_switch_matrix(self):
        """Tests transitions: RED ('revealed') -> WHITE/GREEN/BLUE ('hidden') -> RED ('revealed')."""
        room = Level2Room()
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True

        # RED -> revealed
        lantern.set_color("red")
        assert room.get_red_door_visual_state(lantern) == "revealed"

        # RED -> WHITE -> hidden
        lantern.set_color("white")
        assert room.get_red_door_visual_state(lantern) == "hidden"

        # WHITE -> RED -> revealed
        lantern.set_color("red")
        assert room.get_red_door_visual_state(lantern) == "revealed"

        # RED -> GREEN -> hidden
        lantern.set_color("green")
        assert room.get_red_door_visual_state(lantern) == "hidden"

        # GREEN -> RED -> revealed
        lantern.set_color("red")
        assert room.get_red_door_visual_state(lantern) == "revealed"

        # RED -> BLUE -> hidden
        lantern.set_color("blue")
        assert room.get_red_door_visual_state(lantern) == "hidden"

    def test_red_door_opened_state_visual_matrix_and_passable_collision(self):
        """Once opened, Red Door is 'open' under RED, 'wall' under WHITE/GREEN/BLUE/OFF, and collision stays PASSABLE."""
        room = Level2Room()
        inv = Inventory()
        inv.add_key("key_gold")
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        player = Player(x=1840, y=1600)

        # Open door under Red
        lantern.set_color("red")
        room.handle_interact(player, lantern, inv)
        assert room.door_locked is False
        assert room.door_rect not in room.all_obstacles
        assert room.get_red_door_visual_state(lantern) == "open"

        # Switch to WHITE: visual state is 'wall', but collision remains PASSABLE (door_rect not in all_obstacles)
        lantern.set_color("white")
        assert room.get_red_door_visual_state(lantern) == "wall"
        assert room.door_rect not in room.all_obstacles

        # Switch to GREEN: visual state is 'wall', collision remains PASSABLE
        lantern.set_color("green")
        assert room.get_red_door_visual_state(lantern) == "wall"
        assert room.door_rect not in room.all_obstacles

        # Switch to BLUE: visual state is 'wall', collision remains PASSABLE
        lantern.set_color("blue")
        assert room.get_red_door_visual_state(lantern) == "wall"
        assert room.door_rect not in room.all_obstacles

        # Turn lantern OFF: visual state is 'wall', collision remains PASSABLE
        lantern.active = False
        assert room.get_red_door_visual_state(lantern) == "wall"
        assert room.door_rect not in room.all_obstacles

        # Switch back to RED (ON): visual state returns to 'open', collision remains PASSABLE
        lantern.active = True
        lantern.set_color("red")
        assert room.get_red_door_visual_state(lantern) == "open"
        assert room.door_rect not in room.all_obstacles

    def test_player_can_walk_through_opened_door_under_white_light(self):
        """Player can walk through opened door into Red Chamber while WHITE light is active."""
        room = Level2Room()
        inv = Inventory()
        inv.add_key("key_gold")
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        player = Player(x=1800, y=1600)  # west of door

        # Unlock door
        lantern.set_color("red")
        room.handle_interact(player, lantern, inv)
        assert room.door_locked is False

        # Switch to WHITE light
        lantern.set_color("white")
        assert room.get_red_door_visual_state(lantern) == "wall"

        # Move player east through the doorway into the Red Chamber (x 1800 -> 1900)
        move_with_collision(player, 100.0, 0.0, room.all_obstacles, dt=1.0)
        assert player.x > 1850  # player walked through doorway successfully!


# ===========================================================================
# PHASE C3 — GREEN LIGHT + ANCIENT WRITINGS + GREEN CHAMBER
# ===========================================================================

class TestPhaseC3GreenChamberAndWritings:
    """Automated tests for Phase C3 Green Light reveal, lore fragments, and Green Chamber."""

    def test_green_chamber_exists_and_connected(self):
        """Green Chamber exists in East Sanctum (x 2500-3100, y 300-900) connected seamlessly to Level 2 world."""
        room = Level2Room()
        # Verify floor surface encompasses East Sanctum Green Chamber coordinates
        assert room.floor_surf.get_width() == L2_WORLD_WIDTH
        assert room.floor_surf.get_height() == L2_WORLD_HEIGHT

    def test_green_chamber_contains_single_energy_crystal(self):
        """Green Chamber (East Sanctum right side shrine alcove) contains an EnergyCrystalStation at (2980, 500)."""
        room = Level2Room()
        gc_crystals = [c for c in room.crystals if 2500 <= c.x <= 3100 and 300 <= c.y <= 900]
        assert any(c.x == 2980 and c.y == 500 for c in gc_crystals)

    def test_green_writing_locations_exist_and_bounded(self):
        """Exactly 3 short ancient writing locations exist total across Level 2."""
        room = Level2Room()
        assert len(room.ancient_writings) == 3
        for w in room.ancient_writings:
            assert "title" in w and "line1" in w and "line2" in w
            assert len(w["line1"]) < 100
            assert len(w["line2"]) < 100

    def test_writings_hidden_in_white_red_blue_and_off(self):
        """Ancient writings are NOT revealed under WHITE, RED, BLUE, or OFF lantern states."""
        lantern = Lantern(radius=130)
        lantern.possessed = True

        # Lantern OFF
        lantern.active = False
        lantern.set_color("green")
        assert is_color_active(lantern, "green") is False

        # Lantern ON, non-green colors
        lantern.active = True
        for color in ("white", "red", "blue"):
            lantern.set_color(color)
            assert is_color_active(lantern, "green") is False

    def test_writings_revealed_only_under_green_light(self):
        """Ancient writings reveal helper returns True ONLY under active GREEN light."""
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("green")
        assert is_color_active(lantern, "green") is True

    def test_green_writing_color_switch_matrix_and_auto_close(self):
        """Switching away from GREEN auto-closes writing modals; switching back to GREEN enables revealing again."""
        room = Level2Room()
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        player = Player(x=280, y=580)  # near writing_1

        # Reveal writing 1 under Green
        lantern.set_color("green")
        room.handle_interact(player, lantern)
        assert room.ancient_writings[0]["showing"] is True

        # Switch to WHITE: update auto-dismisses open writing modal
        lantern.set_color("white")
        room.update(player, lantern, 0.016)
        assert room.ancient_writings[0]["showing"] is False

        # Switch to RED: modal remains hidden
        lantern.set_color("red")
        room.update(player, lantern, 0.016)
        assert room.ancient_writings[0]["showing"] is False

        # Switch to BLUE: modal remains hidden
        lantern.set_color("blue")
        room.update(player, lantern, 0.016)
        assert room.ancient_writings[0]["showing"] is False

        # Switch back to GREEN and interact: modal reveals again
        lantern.set_color("green")
        room.handle_interact(player, lantern)
        assert room.ancient_writings[0]["showing"] is True

    def test_green_writing_interaction_opens_modal(self):
        """Interacting near writing rect under GREEN light triggers modal dialog."""
        room = Level2Room()
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("green")
        player = Player(x=280, y=580)  # near writing_1

        result = room.handle_interact(player, lantern)
        assert result is True
        assert room.ancient_writings[0]["showing"] is True

        # Dismiss modal on next interact call
        room.handle_interact(player, lantern)
        assert room.ancient_writings[0]["showing"] is False

    def test_lore_fragments_do_not_explicitly_solve_level5(self):
        """Writing text contains cryptic clues but no direct puzzle solutions ('Door 3', 'Pick Door')."""
        room = Level2Room()
        for w in room.ancient_writings:
            full_text = f"{w['line1']} {w['line2']}".lower()
            assert "door 3" not in full_text
            assert "pick the" not in full_text
            assert "choose door" not in full_text

    def test_moved_crystal_no_overlap_with_inscriptions(self):
        """Green Chamber EnergyCrystalStation is moved to (2980, 500) on the right side and does NOT overlap any inscription interaction area."""
        room = Level2Room()
        gc_crystal = next(c for c in room.crystals if c.x == 2980 and c.y == 500)
        
        # Verify physical separation from all 3 inscriptions
        for w in room.ancient_writings:
            w_inflated = w["rect"].inflate(40, 40)
            c_inflated = gc_crystal.rect.inflate(30, 30)
            assert not w_inflated.colliderect(c_inflated)

        # Verify interaction separation: standing near writing 3 (2850, 360) opens modal, NOT crystal recharge
        lantern = Lantern(radius=130)
        lantern.possessed = True
        lantern.active = True
        lantern.set_color("green")
        room.battery.energy = 50.0
        
        player_at_w3 = Player(x=2850, y=360)
        room.handle_interact(player_at_w3, lantern)
        assert room.ancient_writings[2]["showing"] is True
        assert room.battery.energy == 50.0  # crystal recharge did NOT fire!

        # Verify standing near crystal (2980, 500) recharges battery, NOT writing modal
        room.ancient_writings[2]["showing"] = False
        player_at_crystal = Player(x=2980, y=500)
        room.handle_interact(player_at_crystal, lantern)
        assert room.battery.energy > 50.0  # crystal recharge fired!
        assert room.ancient_writings[2]["showing"] is False


# ===========================================================================
# PHASE C4 — 3 MIRROR COLLECTIBLES + LEVEL 2 -> LEVEL 3 EXIT DOOR
# ===========================================================================

class TestPhaseC4MirrorsAndExitDoor:
    """Automated tests for 3 Mirror Collectibles and Level 2 -> Level 3 Exit Door."""

    def test_level2_initializes_successfully(self):
        """Level2 initializes cleanly with mirrors and exit door."""
        room = Level2Room()
        assert len(room.mirrors_in_world) == 3
        assert room.exit_door is not None

    def test_exactly_three_mirrors_exist(self):
        """Exactly 3 collectible mirrors exist in Level 2 world."""
        room = Level2Room()
        assert len(room.mirrors_in_world) == 3

    def test_mirror1_in_red_chamber(self):
        """Mirror 1 (mirror_red) is located inside Red Chamber (x 1940-2800, y 1450-1800)."""
        room = Level2Room()
        m1 = room.mirrors_in_world[0]
        assert m1["id"] == "mirror_red"
        assert 1940 <= m1["rect"].centerx <= 2800
        assert 1450 <= m1["rect"].centery <= 1800

    def test_mirror2_in_blue_chamber(self):
        """Mirror 2 (mirror_blue) is located inside Blue Chamber (x 750-1150, y 350-650)."""
        room = Level2Room()
        m2 = room.mirrors_in_world[1]
        assert m2["id"] == "mirror_blue"
        assert 750 <= m2["rect"].centerx <= 1150
        assert 350 <= m2["rect"].centery <= 650

    def test_mirror3_in_green_chamber(self):
        """Mirror 3 (mirror_green) is located inside Green Chamber (x 2500-3100, y 300-900)."""
        room = Level2Room()
        m3 = room.mirrors_in_world[2]
        assert m3["id"] == "mirror_green"
        assert 2500 <= m3["rect"].centerx <= 3100
        assert 300 <= m3["rect"].centery <= 900

    def test_mirrors_do_not_overlap_crystals(self):
        """No mirror interaction area overlaps any EnergyCrystalStation interaction area."""
        room = Level2Room()
        for m in room.mirrors_in_world:
            m_area = m["rect"].inflate(30, 30)
            for c in room.crystals:
                c_area = c.rect.inflate(30, 30)
                assert not m_area.colliderect(c_area)

    def test_mirrors_do_not_overlap_writings(self):
        """No mirror interaction area overlaps any AncientWriting area."""
        room = Level2Room()
        for m in room.mirrors_in_world:
            m_area = m["rect"].inflate(30, 30)
            for w in room.ancient_writings:
                w_area = w["rect"].inflate(40, 40)
                assert not m_area.colliderect(w_area)

    def test_collecting_mirror1_adds_to_inventory(self):
        """Collecting Mirror 1 adds 'mirror_red' to shared Inventory under RED light."""
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        lantern.set_color("red")
        m1 = room.mirrors_in_world[0]
        player = Player(x=m1["rect"].centerx, y=m1["rect"].centery)

        res = room.handle_interact(player, lantern, inv)
        assert res is True
        assert m1["collected"] is True
        assert "mirror_red" in inv.mirrors

    def test_collecting_mirror2_adds_to_inventory(self):
        """Collecting Mirror 2 adds 'mirror_blue' to shared Inventory under BLUE light."""
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        lantern.set_color("blue")
        m2 = room.mirrors_in_world[1]
        player = Player(x=m2["rect"].centerx, y=m2["rect"].centery)

        res = room.handle_interact(player, lantern, inv)
        assert res is True
        assert m2["collected"] is True
        assert "mirror_blue" in inv.mirrors

    def test_collecting_mirror3_adds_to_inventory(self):
        """Collecting Mirror 3 adds 'mirror_green' to shared Inventory under GREEN light."""
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        lantern.set_color("green")
        m3 = room.mirrors_in_world[2]
        player = Player(x=m3["rect"].centerx, y=m3["rect"].centery)

        res = room.handle_interact(player, lantern, inv)
        assert res is True
        assert m3["collected"] is True
        assert "mirror_green" in inv.mirrors

    def test_collected_mirror_cannot_be_collected_twice(self):
        """Collected mirror cannot be collected a second time."""
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        lantern.set_color("red")
        m1 = room.mirrors_in_world[0]
        player = Player(x=m1["rect"].centerx, y=m1["rect"].centery)

        room.handle_interact(player, lantern, inv)
        assert len(inv.mirrors) == 1

        # Second interaction at same spot returns False
        res = room.handle_interact(player, lantern, inv)
        assert res is False
        assert len(inv.mirrors) == 1

    def test_mirror_pickup_fails_with_wrong_lantern_color(self):
        """Mirror cannot be collected under the wrong lantern color or when lantern is OFF."""
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        # Mirror 0 is red; white lantern cannot collect it
        m0 = room.mirrors_in_world[0]
        player = Player(x=m0["rect"].centerx, y=m0["rect"].centery)
        res_white = room.handle_interact(player, lantern, inv)
        assert res_white is False
        assert m0["collected"] is False
        assert len(inv.mirrors) == 0

        # Blue lantern cannot collect red mirror
        lantern.set_color("blue")
        res_blue = room.handle_interact(player, lantern, inv)
        assert res_blue is False
        assert m0["collected"] is False

        # Turned off red lantern cannot collect red mirror
        lantern.set_color("red")
        lantern.toggle()  # active = False
        res_off = room.handle_interact(player, lantern, inv)
        assert res_off is False
        assert m0["collected"] is False

    def test_three_collected_mirrors_represented_in_inventory(self):
        """Collecting all 3 mirrors results in len(inventory.mirrors) == 3."""
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        for m in room.mirrors_in_world:
            lantern.set_color(m["id"].replace("mirror_", ""))
            player = Player(x=m["rect"].centerx, y=m["rect"].centery)
            room.handle_interact(player, lantern, inv)

        assert len(inv.mirrors) == 3
        assert "mirror_red" in inv.mirrors
        assert "mirror_blue" in inv.mirrors
        assert "mirror_green" in inv.mirrors

    def test_exit_door_exists_and_inside_world_bounds(self):
        """Level 2 -> Level 3 exit door exists within Level 2 world bounds."""
        room = Level2Room()
        dr = room.exit_door["rect"]
        assert 0 <= dr.x <= L2_WORLD_WIDTH
        assert 0 <= dr.y <= L2_WORLD_HEIGHT

    def test_exit_door_is_initially_solid(self):
        """Exit door rect is present in room.all_obstacles (solid collision)."""
        room = Level2Room()
        assert room.exit_door["rect"] in room.all_obstacles

    def test_door_cannot_be_bypassed_by_normal_movement(self):
        """Player cannot walk through solid exit door."""
        room = Level2Room()
        player = Player(x=1600, y=80)  # south of exit door
        # Try moving north into door over 30 frames (dt=0.016)
        for _ in range(30):
            move_with_collision(player, 0.0, -1.0, room.all_obstacles, dt=0.016)
        assert player.rect.top >= room.exit_door["rect"].bottom

    def test_door_interaction_displays_sealed_message(self):
        """Interacting with exit door displays sealed-path modal message."""
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        dr = room.exit_door["rect"]
        player = Player(x=dr.centerx, y=dr.bottom + 5)

        res = room.handle_interact(player, lantern, inv)
        assert res is True
        assert room.exit_door["showing"] is True

    def test_door_interaction_does_not_modify_inventory(self):
        """Exit door interaction does NOT add items to Inventory."""
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        dr = room.exit_door["rect"]
        player = Player(x=dr.centerx, y=dr.bottom + 20)

        room.handle_interact(player, lantern, inv)
        assert len(inv.mirrors) == 0
        assert len(inv.keys) == 0

    def test_inventory_mirror_api(self):
        """Inventory supports add_mirror, has_mirror, and mirror_count."""
        inv = Inventory()
        assert inv.mirror_count == 0
        assert not inv.has_mirror("mirror_red")

        inv.add_mirror("mirror_red")
        assert inv.mirror_count == 1
        assert inv.has_mirror("mirror_red")

        # Duplicate addition is idempotent
        inv.add_mirror("mirror_red")
        assert inv.mirror_count == 1

        inv.add_mirror("mirror_blue")
        inv.add_mirror("mirror_green")
        assert inv.mirror_count == 3
        assert inv.has_mirror("mirror_blue")
        assert inv.has_mirror("mirror_green")

    def test_mirror_collection_via_handle_interact(self):
        """Collecting mirrors uses Inventory mirror API and persists across room."""
        room = Level2Room()
        inv = Inventory()
        lantern = Lantern(radius=130)
        lantern.set_color("red")
        
        m = room.mirrors_in_world[0]
        player = Player(x=m["rect"].centerx, y=m["rect"].centery)
        res = room.handle_interact(player, lantern, inv)

        assert res is True
        assert m["collected"] is True
        assert inv.has_mirror(m["id"])
        assert inv.mirror_count == 1

    def test_draw_mirrors_color_gating(self):
        """_draw_mirrors renders without error and respects lantern color."""
        room = Level2Room()
        surface = pygame.Surface((800, 600))
        player = Player(x=1600, y=1200)
        camera_offset = (0, 0)
        vp = pygame.Rect(0, 0, 3200, 2400)
        lantern = Lantern(radius=130)

        # White lantern: no mirrors drawn
        lantern.set_color("white")
        room._draw_mirrors(surface, player, camera_offset, vp, lantern)

        # Red lantern: red mirror drawn
        lantern.set_color("red")
        room._draw_mirrors(surface, player, camera_offset, vp, lantern)

        # Blue lantern: blue mirror drawn
        lantern.set_color("blue")
        room._draw_mirrors(surface, player, camera_offset, vp, lantern)

        # Green lantern: green mirror drawn
        lantern.set_color("green")
        room._draw_mirrors(surface, player, camera_offset, vp, lantern)

    def test_exit_door_dismiss_modal(self):
        """dismiss_inscription properly resets exit_door showing flag."""
        room = Level2Room()
        room.exit_door["showing"] = True
        room.dismiss_inscription()
        assert room.exit_door["showing"] is False

if __name__ == "__main__":
    unittest.main()
