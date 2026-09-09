"""Level 3 helpers: finite beam reflection and the code-drawn mural.

Level 3 has two implementation files, together in content/:
- level3.py: chambers, gameplay, controls, checkpoints and world rendering.
- level3_helpers.py: beam mathematics and mural drawing/image processing.

Shared player, inventory and engine modules remain shared with other levels.
"""
import math
import pygame
from engine.reflection import (
    BeamSegment, calculate_reflection, ray_intersect_rect, ray_intersect_circle,
)

# ---------------------------------------------------------------------------
# Beam reflection
# ---------------------------------------------------------------------------

def mirror_face(mirror):
    nx,ny=mirror.normal
    return ((mirror.x+ny*16,mirror.y-nx*16),(mirror.x-ny*16,mirror.y+nx*16))


def ray_segment(origin,direction,a,b):
    vx,vy=b[0]-a[0],b[1]-a[1]
    denominator=direction[0]*vy-direction[1]*vx
    if abs(denominator)<1e-9:return None
    qx,qy=a[0]-origin[0],a[1]-origin[1]
    t=(qx*vy-qy*vx)/denominator
    u=(qx*direction[1]-qy*direction[0])/denominator
    return t if t>.001 and -.000001<=u<=1.000001 else None


def trace_source(origin,direction,color,mirrors,obstacles,receiver,max_bounces=6):
    length=math.hypot(*direction)
    direction=(direction[0]/length,direction[1]/length)
    segments=[]
    previous=None
    for _ in range(max_bounces+1):
        hits=[(2400.,'none',None)]
        for wall in obstacles:
            distance=ray_intersect_rect(origin,direction,wall)
            if distance is not None:hits.append((distance,'wall',wall))
        distance=ray_intersect_circle(origin,direction,receiver,18)
        if distance is not None:hits.append((distance,'receiver',receiver))
        for mirror in mirrors:
            if mirror is previous:continue
            distance=ray_segment(origin,direction,*mirror_face(mirror))
            if distance is not None:hits.append((distance,'mirror',mirror))
        distance,kind,obj=min(hits,key=lambda item:item[0])
        end=(origin[0]+direction[0]*distance,origin[1]+direction[1]*distance)
        segments.append(BeamSegment(origin,end,direction,color,kind,obj))
        if kind!='mirror':return segments
        direction=calculate_reflection(direction,obj.normal)
        origin=(end[0]+direction[0]*.01,end[1]+direction[1]*.01)
        previous=obj
    return segments


# ---------------------------------------------------------------------------
# Mural drawing and processing
# ---------------------------------------------------------------------------

def contrast_stretch(values):
    lo,hi=min(values,default=0),max(values,default=0)
    return [round((v-lo)*255/(hi-lo)) if hi>lo else 0 for v in values]


class Mural:
    def __init__(self):
        self.clarity=0
        source=pygame.Surface((480,180))
        source.fill((116,112,102))
        ink=(103,101,94)
        pygame.draw.rect(source,ink,(8,8,464,164),2)
        for x in (85,135,345,395):
            pygame.draw.circle(source,ink,(x,53),7,2)
            pygame.draw.lines(source,ink,False,[(x-11,100),(x,73),(x+11,100)],3)
            pygame.draw.line(source,ink,(x,61),(x,82),3)
        pygame.draw.polygon(source,ink,[(240,28),(260,58),(240,88),(220,58)],2)
        for x in (95,145,335,385):pygame.draw.line(source,ink,(240,58),(x,82),1)
        f=pygame.font.SysFont('consolas',18,bold=True)
        for text,y in [('LIGHT ONCE GUIDED OUR PEOPLE',115),('TURN THE MIRRORS. WAKE THE RECEIVER.',141)]:
            label=f.render(text,False,ink)
            source.blit(label,((480-label.get_width())//2,y))
        gray=[]
        for y in range(180):
            for x in range(480):
                c=source.get_at((x,y))
                gray.append(round(.299*c.r+.587*c.g+.114*c.b))
        stretched=contrast_stretch(gray)
        self.stages=[source]
        for values in (gray,stretched,[255 if v>=128 else 0 for v in stretched]):
            s=pygame.Surface((480,180))
            for i,value in enumerate(values):s.set_at((i%480,i//480),(value,value,value))
            self.stages.append(s)

    def draw(self,surface,debug=False):
        pygame.draw.rect(surface,(18,15,25),(90,92,620,415))
        pygame.draw.rect(surface,(175,145,75),(90,92,620,415),2)
        font=pygame.font.SysFont('consolas',16,bold=True)
        surface.blit(font.render('THE FADED MURAL',True,(245,220,155)),(118,112))
        if debug:
            for i,stage in enumerate(self.stages):
                x,y=120+(i%2)*280,159+(i//2)*122
                surface.blit(pygame.transform.scale(stage,(240,90)),(x,y))
                text=('Original','Grayscale','Contrast stretch','Threshold')[i]
                surface.blit(font.render(text,True,(210,195,160)),(x,y+94))
        else:
            surface.blit(self.stages[self.clarity],(160,195))
        for text,y in [(f'Clarity {self.clarity}/3   [Left/Right] Adjust   [E] Clarify',433),
                       ('[Esc] Close   [F3] Processing stages',468)]:
            surface.blit(font.render(text,True,(230,215,180)),(118,y))
