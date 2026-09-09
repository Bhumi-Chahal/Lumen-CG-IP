"""Runnable Level 1 milestone, imported from the existing local prototype."""
import pygame
from engine.player import Player
from content.level1 import Level1Room

def main(max_frames=None):
    pygame.init()
    screen=pygame.display.set_mode((800,600))
    pygame.display.set_caption("Lumen — Level 1")
    clock=pygame.time.Clock()
    running=True
    frames=0
    player=Player(780,1100)
    room=Level1Room()
    while running:
        dt=min(clock.tick(60)/1000,.05)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:running=False
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:running=False
        screen.fill((17,14,24))
        room.update(player,dt)
        room.draw(screen,player,(400,600))
        pygame.display.flip()
        frames+=1
        if max_frames is not None and frames>=max_frames:running=False
    pygame.quit()

if __name__=="__main__":main()
