"""Runnable Level 1 milestone, imported from the existing local prototype."""
import pygame

def main(max_frames=None):
    pygame.init()
    screen=pygame.display.set_mode((800,600))
    pygame.display.set_caption("Lumen — Level 1")
    clock=pygame.time.Clock()
    running=True
    frames=0
    while running:
        dt=min(clock.tick(60)/1000,.05)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:running=False
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:running=False
        screen.fill((17,14,24))
        pygame.display.flip()
        frames+=1
        if max_frames is not None and frames>=max_frames:running=False
    pygame.quit()

if __name__=="__main__":main()
