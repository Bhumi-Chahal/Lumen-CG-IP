"""End-to-end Level 1 controls, import boundaries and fresh-session checks."""
import heapq
from pathlib import Path
from unittest.mock import patch
import pygame
import pytest
from main import GameManager,STATE_PLAYING,STATE_LEVEL1_COMPLETE,STATE_LEVEL2,STATE_MENU
from content.level1 import has_line_of_sight

@pytest.fixture
def game():
    g=GameManager();g.reset_level1();g.story_modal.close();g.state=STATE_PLAYING
    return g

def walk_to(game,target):
    """Find a path through real collision footprints, then move along it."""
    p=game.player;room=game.room;start=(round(p.x/10),round(p.y/10))
    queue=[(0,start)];cost={start:0};parent={start:None};goal=None
    while queue:
        _,cell=heapq.heappop(queue);x,y=cell[0]*10,cell[1]*10
        rect=pygame.Rect(x,y,p.width,p.height)
        if rect.colliderect(target.inflate(20,20)) and has_line_of_sight(rect.center,target.center,room.walls):goal=cell;break
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nxt=(cell[0]+dx,cell[1]+dy)
            if not (3<=nxt[0]<=154 and 3<=nxt[1]<=114):continue
            swept=pygame.Rect(min(x,nxt[0]*10),min(y,nxt[1]*10),p.width+10*abs(dx),p.height+10*abs(dy))
            if swept.collidelist(room.all_obstacles)!=-1:continue
            distance=cost[cell]+1
            if distance>=cost.get(nxt,float('inf')):continue
            cost[nxt]=distance;parent[nxt]=cell
            heuristic=(abs(nxt[0]*10-target.centerx)+abs(nxt[1]*10-target.centery))/10
            heapq.heappush(queue,(distance+heuristic,nxt))
    assert goal is not None,f'No route to {target}'
    route=[]
    while parent[goal] is not None:route.append(goal);goal=parent[goal]
    for cell in reversed(route):
        tx,ty=cell[0]*10,cell[1]*10
        for _ in range(2):
            dx,dy=(tx-p.x)/2,(ty-p.y)/2
            # Split each grid move below a normal game's frame distance.
            dt=1/p.speed
            with patch.object(p,'get_input_vector',return_value=(dx,dy)):
                room.update(p,game.inventory,game.lantern,dt,game.camera)
        dx,dy=tx-p.x,ty-p.y
        with patch.object(p,'get_input_vector',return_value=(dx,dy)):
            room.update(p,game.inventory,game.lantern,1/p.speed,game.camera)
        assert abs(p.x-tx)<.01 and abs(p.y-ty)<.01

def test_walk_collect_read_unlock_complete_and_enter_level2(game):
    walk_to(game,game.room.lantern_pickup.rect)
    game._handle_keydown(pygame.K_e);assert game.lantern.possessed
    for key in game.room.keys:
        walk_to(game,key.rect);game._handle_keydown(pygame.K_e)
        assert game.inventory.has_key(key.id)
        game.story_modal.close()
    for clue in game.room.clue_objects:
        walk_to(game,clue.rect);game._handle_keydown(pygame.K_e)
        assert game.inventory.has_clue(clue.id)
        game.clue_modal.close();game.story_modal.close()
    assert game.inventory.key_count==3 and game.inventory.clue_count==3
    game.room.pending_story_modal=None
    walk_to(game,game.room.exit_rect)
    game._handle_keydown(pygame.K_e);assert game.door_modal.is_open
    game._handle_keydown(pygame.K_1);assert not game.room.is_complete
    game._handle_keydown(pygame.K_3);assert game.room.is_complete
    for _ in range(25):game._update(.05)
    assert game.state==STATE_LEVEL1_COMPLETE
    game._draw()
    game._handle_keydown(pygame.K_SPACE)
    assert game.state==STATE_LEVEL2 and game.inventory.key_count==3
    assert game.inventory.has_key('key_gold')
    assert game.lantern.possessed

@pytest.mark.parametrize('panel',['story_modal','clue_modal','inventory_modal'])
def test_modal_blocks_world_movement(game,panel):
    modal=getattr(game,panel)
    if panel=='story_modal':modal.open('Story','Text')
    elif panel=='clue_modal':modal.open('Clue','Text')
    else:modal.open()
    before=game.player.center
    with patch.object(game.player,'get_input_vector',return_value=(1,0)):game._update(.05)
    assert game.player.center==before

def test_two_wrong_keys_return_to_menu(game):
    for key in ('key_bronze','key_silver'):game.inventory.add_key(key)
    game.door_modal.open(game.inventory)
    game._handle_keydown(pygame.K_1);game._handle_keydown(pygame.K_2)
    assert game.door_modal.failed
    game._update(2.1)
    assert game.state==STATE_MENU and game.inventory.key_count==0

def test_level3_foundation_uses_the_expected_file_layout():
    root=Path(__file__).resolve().parents[1]
    assert sorted(file.name for file in (root/'src'/'content').glob('level3*.py')) == [
        'level3.py', 'level3_helpers.py',
    ]
    assert (root/'src'/'engine'/'reflection.py').exists()
    assert (root/'src'/'entities'/'mirror.py').exists()
    assert (root/'src'/'entities'/'puzzle_crystal.py').exists()
    assert (root/'tests'/'test_level3.py').exists()
    assert not (root/'saves').exists()

def test_inventory_has_keys_mirrors_and_clues(game):
    for key in ('key_bronze','key_silver','key_gold'):game.inventory.add_key(key)
    game.inventory.add_clue('example','Example','A discovered clue.')
    modal=game.inventory_modal;modal.open()
    for i,category in enumerate(('KEYS','MIRRORS','CLUES')):
        modal.active_tab_index=i
        items=modal._get_category_items(game.inventory)
        assert len(items)==(3 if category in ('KEYS','MIRRORS') else 1)
        game._draw()
    assert modal.CATEGORIES==['KEYS','MIRRORS','CLUES']
