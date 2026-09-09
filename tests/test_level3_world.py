"""Integration tests for the Python-drawn Level 3 world and Level 2 handoff."""

import json

import pygame

from content.level3 import Level3Room, SourceCrystal, is_light_active
from engine.inventory import Inventory
from engine.lantern import Lantern
from engine.player import Player
from main import GameManager, STATE_LEVEL2, STATE_LEVEL3


MIRRORS = ("mirror_red", "mirror_blue", "mirror_green")


def make_room():
    inventory = Inventory()
    for mirror_id in MIRRORS:
        inventory.add_mirror(mirror_id)
    return Level3Room(inventory), inventory, Player(650, 1850), Lantern()


def test_level2_exit_enters_level3_with_the_same_inventory():
    game = GameManager()
    game.init_level2()
    assert game.state == STATE_LEVEL2
    for mirror_id in MIRRORS:
        game.inventory.add_mirror(mirror_id)

    carried_inventory = game.inventory
    game.level2_room.trigger_level3_transition = True
    game._update(0.01)

    assert game.state == STATE_LEVEL3
    assert game.inventory is carried_inventory
    assert tuple(game.level3_room.inventory.mirrors) == MIRRORS
    assert {mirror.id for mirror in game.level3_room.player_mirrors} == set(MIRRORS)


def test_crystals_are_gray_until_the_matching_light_is_active():
    crystal = SourceCrystal("source", 60, 60, color="red")
    hidden = pygame.Surface((120, 120), pygame.SRCALPHA)
    shown = pygame.Surface((120, 120), pygame.SRCALPHA)
    crystal.draw(hidden, is_revealed=False)
    crystal.draw(shown, is_revealed=True)

    hidden_colors = {hidden.get_at((x, y))[:3] for x in range(120) for y in range(120)}
    shown_colors = {shown.get_at((x, y))[:3] for x in range(120) for y in range(120)}
    assert (165, 165, 165) in hidden_colors
    assert (255, 125, 150) in shown_colors

    lantern = Lantern()
    lantern.possessed = True
    lantern.active = False
    lantern.set_color("red")
    assert not is_light_active(lantern, "red")
    lantern.active = True
    assert is_light_active(lantern, "red")


def test_every_carried_mirror_can_be_installed_rotated_and_retrieved():
    room, inventory, player, _ = make_room()
    socket = room.sockets[0]
    for mirror_id in MIRRORS:
        assert room.install_mirror(mirror_id, socket["id"])
        placed = socket["mirror"]
        assert placed.id == mirror_id
        before = placed.orientation
        room.focused_socket = socket["id"]
        assert room.handle_rotate_mirror(player, 1)
        assert placed.orientation == (before + 1) % 4
        assert room.handle_retrieve_mirror(player)
        assert socket["mirror"] is None
        assert inventory.has_mirror(mirror_id)


def test_checkpoint_restores_progress_without_changing_incoming_mirrors(tmp_path, monkeypatch):
    monkeypatch.setenv("LUMEN_LEVEL3_SAVE", str(tmp_path / "level3.json"))
    room, inventory, player, lantern = make_room()
    room.doors["entrance_door"]["open"] = True
    room.doors["entrance_door"]["unlocked"] = True
    room.puzzles[0]["solved"] = True
    room.player_crystals[0].charged = True
    inventory.add_crystal("crystal_2")
    player.x, player.y = 650, 700
    lantern.active = True
    lantern.set_color("blue")
    assert room.save_checkpoint(player, lantern)

    player.x, player.y = 650, 1850
    room.puzzles[0]["solved"] = False
    room.player_crystals[0].charged = False
    inventory.crystals.clear()
    assert room.load_checkpoint(player, lantern)
    assert room.puzzles[0]["solved"]
    assert inventory.has_crystal("crystal_2")
    assert tuple(inventory.mirrors) == MIRRORS


def test_invalid_checkpoint_leaves_current_progress_unchanged(tmp_path, monkeypatch):
    checkpoint = tmp_path / "level3.json"
    monkeypatch.setenv("LUMEN_LEVEL3_SAVE", str(checkpoint))
    room, _, player, lantern = make_room()
    checkpoint.write_text(json.dumps({"version": 99}), encoding="utf-8")
    before = (player.x, player.y, tuple(p["solved"] for p in room.puzzles))
    assert not room.load_checkpoint(player, lantern)
    assert (player.x, player.y, tuple(p["solved"] for p in room.puzzles)) == before
