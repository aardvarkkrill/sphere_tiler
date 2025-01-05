import math
from itertools import count

import pygame
from typing import Tuple, Optional, List
from collections.abc import Callable

from sympy.core.numbers import Infinity

from brain_tile import create_canvas, create_hexagonal_mask, show_canvas

#        2___1      ^
#       /     \     |
#     3/       \0    | h
#      \       /    |
#       \4___5/     v
#        <--->
#        side

Point = pygame.math.Vector2
Vertices = list[Point]

# maps [0,1] to some kind of rainbow
ColourFunction = Callable[[float], pygame.Color]


class Polygon(object):
    def __init__(self, points: Vertices, height: float, side: float):
        self.N = len(points)
        self.points = points
        self.height = height
        self.side = side


class PerimeterPoint(object):
    def __init__(self, index: int, fraction: float):
        self.index = index
        self.fraction = fraction

    def to_point(self, polygon: Polygon) -> Point:
        index = self.index % polygon.N
        return polygon.points[index] + (
                polygon.points[(index + 1) % polygon.N] - polygon.points[
            index]) * self.fraction


def angle(a: Point, b: Point) -> float:
    return math.atan2(- b.y + a.y, b.x - a.x)

def arc(surface: pygame.Surface, cxy: Point, radius: float, theta0, theta1,
        colour: pygame.Color, width:int):

    # cxy = pygame.math.Vector2(*surface.get_size()) / 2

    if theta0 > theta1:
        theta1 += 2 * math.pi

    def point(theta):
        return cxy + radius * pygame.math.Vector2(math.cos(theta), -math.sin(theta))

    p0 = point(theta0)
    for i in range(101):
        theta = theta0 + (theta1 - theta0) * i / 100
        p1 = point(theta)
        pygame.draw.line(surface, colour, p0, p1, width)
        p0 = p1


def rainbow_arc(surface: pygame.Surface, polygon: Polygon,
                start: int, finish: int,
                colourfun: ColourFunction,
                extent: float = 0.6) -> None:
    """ Draws a ribbon of arcs between polygon sides of index start and finish,
        covering a fraction "extent" [0,1], and centered on each edge.  The
        arcs meet the edges perpendicularly.
        ColourFunction is called with parameter 0 at the outsides of the ribbon,
             1 at the centre (so the ribbon colours are symmetric.)
        NOTE: currently implemented only for hexagons
    """
    N = polygon.N
    assert N == 6
    count = round(polygon.side * extent)

    distance = (finish - start) % N
    even = distance % 2 == 0

    line = distance == 3
    centre = PerimeterPoint(start + [0,1,0,2,5,0][distance],
                            [0.5, 0, 2, 0, 0.5, 0][distance]).to_point(polygon)
    for i in range(count):
        fraction = i / count
        p1 = extent * (i / count - 0.5) + 0.5
        p2 = 1 - p1
        point_a = PerimeterPoint(start, p1).to_point(polygon)
        point_b = PerimeterPoint(finish, p2).to_point(polygon)
        colour = colourfun(
            fraction * 2 if fraction < 0.5 else (1 - fraction) * 2)
        if line:
            pygame.draw.line(surface, colour, point_a, point_b, 2)
        else:
            theta_a = angle(centre, point_a)
            theta_b = angle(centre, point_b)
            radius = (point_a - centre).length()
            arc(surface, centre, radius, theta_b, theta_a, colour, 3)

def rainbow_tile() -> pygame.Surface:
    """ creates the rainbow tile"""
    pygame.init()
    height = 800
    tile, side, points = create_canvas(height=height)

    polygon = Polygon(points, height, side)

    # for p in points:
    #     pygame.draw.circle(tile, pygame.color.THECOLORS["black"], p, 5)
    # show_canvas.show_canvas(tile)

    def rainbow(fraction: float) -> pygame.Color:
        c = pygame.Color(0)
        c.hsva = (
            fraction * 360, 100, 100,
            100)  # HSV: hue, saturation, value, alpha
        return c

    rainbow_arc(tile, polygon, 1, 2, rainbow)
    rainbow_arc(tile, polygon, 4, 5, rainbow)
    rainbow_arc(tile, polygon, 0, 3, rainbow)
    return tile

def pink_tile() -> pygame.Surface:
    """ creates the pink tile and saves it to xxx"""
    pygame.init()
    height = 800
    tile, side, points = create_canvas(height=height)

    polygon = Polygon(points, height, side)

    # for p in points:
    #     pygame.draw.circle(tile, pygame.color.THECOLORS["black"], p, 5)
    # show_canvas.show_canvas(tile)

    def rainbow(fraction: float) -> pygame.Color:
        c = pygame.Color(0)
        c.hsva = (
            fraction * 360, 100, 100,
            100)  # HSV: hue, saturation, value, alpha
        return c

    rainbow_arc(tile, polygon, 1, 2, rainbow)
    rainbow_arc(tile, polygon, 4, 5, rainbow)
    rainbow_arc(tile, polygon, 0, 3, rainbow)

    show_canvas.show_canvas(tile)
    pygame.image.save(tile, "rainbow_tile.png")

    return tile


if __name__ == "__main__":
    tile = rainbow_tile()
    pygame.image.save(tile, "rainbow_tile.png")
    show_canvas.show_canvas(tile)
