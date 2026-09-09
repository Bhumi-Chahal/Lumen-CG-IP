"""Runnable Level 1 milestone, imported from the existing local prototype."""
import pygame
from engine.player import Player
from content.level1 import Level1Room
from engine.camera import Camera
from engine.lantern import Lantern
from engine.inventory import Inventory
from systems.ui import ClueModal

def main(max_frames=None):
    pygame.init()
    window=pygame.display.set_mode((800,600))
    screen=pygame.Surface((800,600))
    fullscreen=False
    pygame.display.set_caption("Lumen â€” Level 1")
    clock=pygame.time.Clock()
    running=True
    frames=0
    player=Player(780,1100)
    room=Level1Room()
    camera=Camera(800,600,1600,1200)
    camera.update(player.center,1)
    lantern=Lantern()
    inventory=Inventory()
    clue_modal=ClueModal(800,600)
    font=pygame.font.SysFont("georgia",16)
    while running:
        dt=min(clock.tick(60)/1000,.05)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:running=False
            elif event.type==pygame.KEYDOWN and clue_modal.is_open:
                if event.key in (pygame.K_e,pygame.K_ESCAPE,pygame.K_SPACE):clue_modal.close()
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:running=False
                elif event.key==pygame.K_F11:
                    fullscreen=not fullscreen
                    window=pygame.display.set_mode((0,0) if fullscreen else (800,600),pygame.FULLSCREEN if fullscreen else 0)
                elif event.key in (pygame.K_1,pygame.K_2,pygame.K_3) and player.rect.colliderect(room.exit_rect.inflate(36,36)):
                    room.select_and_try_key(inventory,{pygame.K_1:1,pygame.K_2:2,pygame.K_3:3}[event.key],camera)
                elif event.key==pygame.K_l and lantern.possessed:lantern.toggle()
                elif event.key==pygame.K_e:room.handle_interact(player,inventory,clue_modal,lantern=lantern)
        screen.fill((17,14,24))
        if not clue_modal.is_open:room.update(player,inventory,lantern,dt,camera)
        camera.update(player.center,dt)
        room.draw(screen,player,lantern,camera_offset=camera.offset)
        if clue_modal.is_open:clue_modal.draw(screen,font,font)
        window.blit(pygame.transform.scale(screen,window.get_size()),(0,0))
        if room.is_complete:screen.blit(font.render("Level 1 complete - Esc exits",True,(240,210,150)),(200,40))
        pygame.display.flip()
        frames+=1
        if max_frames is not None and frames>=max_frames:running=False
    pygame.quit()

if __name__=="__main__":main()
