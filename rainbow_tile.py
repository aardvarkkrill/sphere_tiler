import math
from itertools import count

import pygame
from typing import Tuple, Optional, List
from collections.abc import Callable

from sympy.core.numbers import Infinity

from make_tile import create_canvas, create_hexagonal_mask, show_canvas

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


def rainbow_arc(surface: pygame.Surface, polygon: Polygon, start: int,
                finish: int, colourfun: ColourFunction) -> None:
    N = polygon.N
    size = 0.6 # fraction of side covered
    count = round(polygon.side * size)

    distance = (finish - start) % N
    even = distance % 2 == 0

    line = distance == 3
    centre = PerimeterPoint(start + [0,1,0,2,5,0][distance],
                            [0.5, 0, 2, 0, 0.5, 0][distance]).to_point(polygon)
    # pygame.draw.circle(surface, pygame.color.THECOLORS["green"], centre, 5)
    for i in range(count):
        fraction = i / count
        p1 = size * (i / count - 0.5) + 0.5
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
            # pygame.draw.arc(surface, colour,
            #                 pygame.Rect(centre.x - radius, centre.y - radius,
            #                             2 * radius, 2 * radius),
            #                 theta_b, theta_a, 4)
            # pygame.draw.circle(surface, pygame.color.THECOLORS["black"], point_a, 5)
            # pygame.draw.circle(surface, pygame.color.THECOLORS["white"], point_b, 5)
            # pygame.draw.circle(surface, pygame.color.THECOLORS["green"], centre, 5)
            # pygame.draw.line(surface, pygame.color.THECOLORS["cyan"], point_a, point_b, 2)
        # show_canvas(surface)


if __name__ == "__main__":
    # create a tile with rainbow curves

    def main() -> None:
        pygame.init()
        height = 800
        tile, side, points = create_canvas(height=height)

        polygon = Polygon(points, height, side)

        # for p in points:
        #     pygame.draw.circle(tile, pygame.color.THECOLORS["black"], p, 5)
        # show_canvas(tile)

        def rainbow(fraction: float) -> pygame.Color:
            c = pygame.Color(0)
            c.hsva = (
                fraction * 360, 100, 100,
                100)  # HSV: hue, saturation, value, alpha
            return c

        rainbow_arc(tile, polygon, 1, 2, rainbow)
        rainbow_arc(tile, polygon, 4, 5, rainbow)
        rainbow_arc(tile, polygon, 0, 3, rainbow)

        # Remove redundant/referenced code for undefined arcs
        pass

        show_canvas(tile)
        pygame.image.save(tile, "rainbow.png")

        pygame.quit()


    main()
