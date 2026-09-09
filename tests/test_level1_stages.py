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
