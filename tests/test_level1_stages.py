from pathlib import Path

def test_project_dependencies_and_package_layout():
    root=Path(__file__).resolve().parents[1]
    assert "pygame" in (root/"requirements.txt").read_text()
    for name in ("content","engine","systems"):
        assert (root/"src"/name/"__init__.py").is_file()


def test_application_loop_exits_after_smoke_frame():
    import main
    main.main(max_frames=1)


def test_player_geometry_and_directional_animation():
    from engine.player import Player
    p=Player(100,200)
    assert p.center==(113,215)
    p.update_animation(True,.1)
    assert p.width==26 and p.height==30


def test_world_collision_stops_at_wall():
    import pygame
    from engine.player import Player
    from engine.collision import move_with_collision
    from content.level1 import Level1Room
    pygame.init()
    room=Level1Room();assert len(room.walls)>4
    p=Player(80,80)
    move_with_collision(p,1,0,[pygame.Rect(120,0,20,300)],.1)
    assert p.rect.right==120


def test_camera_clamps_both_world_edges():
    from engine.camera import Camera
    c=Camera(800,600,1600,1200)
    c.update((0,0),1);assert c.offset==(0,0)
    c.update((1600,1200),1);assert c.offset==(800,600)


def test_lantern_pickup_and_toggle():
    import pygame
    from content.level1 import Level1Room
    from engine.player import Player
    from engine.lantern import Lantern
    pygame.init();r=Level1Room();p=Player(667,1075);l=Lantern()
    assert r.handle_interact(p,None,lantern=l)
    assert l.possessed and l.active
    l.toggle();assert not l.active and l.radius==0


def test_key_pickup_records_each_key_once():
    import pygame
    from content.level1 import Level1Room
    from engine.player import Player
    from engine.inventory import Inventory
    pygame.init();r=Level1Room();inv=Inventory();key=r.keys[0]
    p=Player(key.rect.centerx-13,key.rect.centery-15)
    r.update(p,inv,__import__("engine.lantern",fromlist=["Lantern"]).Lantern(),.01);r.update(p,inv,__import__("engine.lantern",fromlist=["Lantern"]).Lantern(),.01)
    assert key.collected and inv.keys==[key.id]


def test_clue_inspection_populates_journal():
    import pygame
    from content.level1 import Level1Room
    from engine.player import Player
    from engine.inventory import Inventory
    from engine.lantern import Lantern
    pygame.init();r=Level1Room();inv=Inventory();clue=r.clue_objects[0]
    p=Player(clue.rect.centerx-13,clue.rect.bottom+1)
    assert r.handle_interact(p,inv,lantern=Lantern())
    assert inv.has_clue(clue.id)


def test_only_gold_key_opens_sanctum():
    import pygame
    from content.level1 import Level1Room
    from engine.inventory import Inventory
    pygame.init();r=Level1Room();inv=Inventory()
    for name in ('key_bronze','key_silver','key_gold'):inv.add_key(name)
    r.select_and_try_key(inv,1);assert not r.is_complete
    r.select_and_try_key(inv,2);assert not r.is_complete
    r.select_and_try_key(inv,3);assert r.is_complete


def test_completion_replays_only_level1():
    import pygame
    from main import GameManager,STATE_LEVEL1_COMPLETE,STATE_PLAYING
    game=GameManager();game.state=STATE_LEVEL1_COMPLETE
    game._handle_keydown(pygame.K_SPACE)
    assert game.state==STATE_PLAYING
    assert not hasattr(game,'level2_room') and not hasattr(game,'level3_room')
    game.story_modal.close();game._draw()
    game.inventory_modal.open();game._draw()
    assert game.inventory_modal.CATEGORIES==['KEYS','CLUES']
