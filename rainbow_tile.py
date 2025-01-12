import sys
import math

import pygame
from typing import Union
from collections.abc import Callable

from sympy import ceiling
from brain_tile import create_canvas
import show_canvas

#        2___1      ^
#       /     \     |
#     3/       \0    | h
#      \       /    |
#       \4___5/     v
#        <--->
#        side

Point = pygame.math.Vector2
Vertices = list[Point]

# a colour, or [0,1]->colour
ColourFunction = Union[pygame.Color, Callable[[float], pygame.Color]]
# a colour, or [0,1]->colour, or [0,1]->[0,1]->colour
MetaColourFunction = Union[ColourFunction, Callable[[float], ColourFunction]]


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
        colour: ColourFunction, width: int):
    """ draws an arc of a circle of given centre and radius between two angles.
        The drawing is always anti-clockwise from theta0 to theta1.
        If a colour function is given, its parameter is the fraction of the arc
            being drawn.
    """

    if theta0 > theta1:
        theta1 += 2 * math.pi

    def point(theta_):
        return cxy + radius * pygame.math.Vector2(math.cos(theta_),
                                                  -math.sin(theta_))

    if radius < 3:
        # approx 1 step per 45 degrees.
        steps = int(ceiling((theta1 - theta0) / (math.pi / 4) + 1))
    else:
        # approx 2 pixels per step
        steps = max(2, int(ceiling((theta1 - theta0) * radius / 2)))
    delta = (theta1 - theta0) / (steps - 1)
    p0 = point(theta0)
    for i in range(steps):
        theta = theta0 + i * delta
        p1 = point(theta)
        if callable(colour):
            pygame.draw.line(surface, colour(i / steps), p0, p1, width)
        else:
            pygame.draw.line(surface, colour, p0, p1, width)
        p0 = p1


def rainbow_arc(surface: pygame.Surface, polygon: Polygon,
                start: int, finish: int,
                colourfun: MetaColourFunction,
                extent: float = 0.6,
                overshoot: float = 0.01) -> None:
    """ Draws a ribbon of arcs between polygon sides of index start and finish,
        covering a centred fraction "extent" [0,1] of each edge.
        The arcs meet the edges perpendicularly.
        ColourFunction is called with parameter 0 at the outsides of the ribbon,
             1 at the centre (so the ribbon colours are symmetric.)
             Additionally, a MetaColourFunction is called with a parameter
             denoting fraction along the arc being drawn
        The arc overshoots the edges by overshoot radians.
        NOTE: currently implemented only for hexagons
    """
    N = polygon.N
    assert N == 6
    count = round(polygon.side * extent)

    distance = (finish - start) % N

    line = (distance == 3)
    centre = PerimeterPoint(start + [0, 1, 0, 2, 5, 0][distance],
                            [0.5, 0, 2, 0, 0.5, 0][distance]).to_point(polygon)
    for i in range(count):
        fraction = i / count
        p1 = extent * (i / count - 0.5) + 0.5
        p2 = 1 - p1
        point_a = PerimeterPoint(start, p1).to_point(polygon)
        point_b = PerimeterPoint(finish, p2).to_point(polygon)

        if callable(colourfun):
            colour = colourfun(
                fraction * 2 if fraction < 0.5 else (1 - fraction) * 2)
        else:
            colour = colourfun

        if line:
            pygame.draw.line(surface, colour, point_a, point_b, 2)
        else:
            theta_a = angle(centre, point_a)
            theta_b = angle(centre, point_b)
            radius = (point_a - centre).length()
            arc(surface, centre, radius,
                theta_b - overshoot, theta_a + overshoot,
                colour, width=3)


def rainbow_tile(extent: float = 0.6) -> pygame.Surface:
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

    rainbow_arc(tile, polygon, 1, 2, rainbow, extent=extent)
    rainbow_arc(tile, polygon, 4, 5, rainbow, extent=extent)
    rainbow_arc(tile, polygon, 0, 3, rainbow, extent=extent)
    return tile


def blend_colours(a: pygame.Color, b: pygame.Color,
                  alpha: float) -> pygame.Color:
    def blend(c1, c2): return round(c1 * (1 - alpha) + c2 * alpha)

    return pygame.Color(blend(a.r, b.r),
                        blend(a.g, b.g),
                        blend(a.b, b.b),
                        blend(a.a, b.a))


# Blends two colours (or colour functions, or meta-colour-functions),
# returning a meta-colour-function that blends more of the first colour
# around a certain part of each arc when passed to rainbow_arc
# (used eg for drawing shadows.)
# Note: peak and spread are analogous to mean and variance of a gaussian.
def blend_colours_dynamic(colour1: MetaColourFunction,
                          colour2: MetaColourFunction,
                          peak: float, spread: float) -> MetaColourFunction:
    def f(edge_fraction: float) -> ColourFunction:
        c1 = colour1(edge_fraction) if callable(colour1) else colour1
        c2 = colour2(edge_fraction) if callable(colour2) else colour2

        def g(arc_fraction: float) -> pygame.Color:
            cc1 = c1(arc_fraction) if callable(c1) else c1
            cc2 = c2(arc_fraction) if callable(c2) else c2
            amount = math.exp((- (arc_fraction - peak) ** 2) / spread) * 16 * (
                    arc_fraction * (1 - arc_fraction)) ** 2
            return blend_colours(cc1, cc2, amount)

        return g

    return f


def pink_tile(base_colour : pygame.Color = pygame.Color(255, 0, 255, 255),
              extent: float = 0.3,
              shade_overlap: bool = True,
              height = 800) -> pygame.Surface:
    """ builds the pink hexagonal tile (or, base it on any other colour)
        "Extent" determines the thickness of the branches
        "height" is the height of the tile in pixels.
    """
    pygame.init()
    tile, side, points = create_canvas(height=height)

    polygon = Polygon(points, height, side)

    pink = base_colour
    if shade_overlap:
        black = pygame.Color(0, 0, 0, 255)
        pink_shade = blend_colours_dynamic(pink, black, peak=0.35, spread=extent/3)
    else:
        pink_shade = pink

    rainbow_arc(tile, polygon, 0, 2, pink_shade, extent=extent)
    rainbow_arc(tile, polygon, 1, 3, pink, extent=extent)
    rainbow_arc(tile, polygon, 4, 5, pink, extent=extent)

    return tile


if __name__ == "__main__":

    def main():
        tile_name = sys.argv[1] if len(sys.argv) > 1 else "pink"

        if tile_name == "rainbow":
            tile = rainbow_tile()
            pygame.image.save(tile, "rainbow_tile.png")
        elif tile_name == "pink":
            tile = pink_tile()
            pygame.image.save(tile, "pink_tile.png")
        else:
            print(f"""I don't know how to make tile \"{tile_name}\"\n
                      Known tiles: rainbow, pink.""", file=sys.stderr)
            exit(1)

        show_canvas.show_canvas(tile)


    main()
