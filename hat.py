# exploring the aperiodic hat monotile


import math
import numpy
import pygame.color

import exetile
from show_canvas import show_canvas

h = math.sqrt(3)

vertices = list(v for v in numpy.array(
    [[0, 0], [1, 0], [5 / 4, h / 4], [2, 0], [11 / 4, h / 4], [5 / 2, h / 2],
     [2, h / 2], [2, h], [5 / 4, 5 * h / 4], [1, h], [1 / 2, h], [1 / 2, h / 2],
     [-1 / 4, h / 4]]))

hat = exetile.Tile(vertices=vertices,
                   branch_points=[],
                   ribbons=[],
                   background=pygame.Color(pygame.color.THECOLORS['blue']),
                   )

s = pygame.Surface((500, 500))
s.fill(color=pygame.Color(pygame.color.THECOLORS['black']))


def scale(s: float):
    return numpy.diag([s,s,1.0])


def rotate(theta: float):
    s, c = math.sin(theta), math.cos(theta)
    return numpy.array([[c, -s, 0.0], [s, c, 0.0], [0, 0, 1]])

def translate(tx: float, ty: float):
    return numpy.array([[1.0,0,tx],[0,1.0,ty],[0,0,1]])

def hflip():
    return numpy.diag([-1.0,1.0,1.0])

hat.draw(exetile.PlaneLineArtist(s),
         transform=scale(0.2) @ translate(-3/2,3*h/2) @ rotate(4 * math.pi / 3.0))

hat.draw(exetile.PlaneLineArtist(s),
         override_bg=pygame.Color(255,0,0),
         transform=scale(0.2) @ hflip() @ rotate(math.pi / 3.0))

hat.draw(exetile.PlaneLineArtist(s),
         transform=scale(0.2) @ translate(3/2,3*h/2) @ rotate(4 * math.pi / 3.0))

hat.draw(exetile.PlaneLineArtist(s),
         transform=scale(0.2) @ translate(3/2,3*h/2) @ rotate(4 * math.pi / 6.0))

show_canvas(s)
