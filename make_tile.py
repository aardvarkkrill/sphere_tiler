import math
import copy

import pygame
from typing import Callable, Tuple, Optional, List


# Create a hexagonal tile of given height.  The vertices are numbered as shown.
#        2___1      ^
#       /     \     |
#     3/       \0    | h
#      \       /    |
#       \4___5/     v
#        <--->
#        side

# returns surface of given height, side length and vertex positions as a 6
# element list of Vector2
def create_canvas(height: int) -> (pygame.Surface, float, list):
    side = height / math.sqrt(3)
    width = round(side * 2)

    points = list(map(pygame.math.Vector2, [
        (2 * side, height / 2),
        (side * 3 / 2, 0),
        (side / 2, 0),
        (0, height / 2),
        (side / 2, height),
        (side * 3 / 2, height)]))

    return pygame.Surface((width, height), pygame.SRCALPHA), side, points


# creates a surface with non-zero value just inside the hexagonal area
def create_hexagonal_mask(height: int) -> pygame.Surface:
    mask, side, points = create_canvas(height)
    pygame.draw.polygon(mask, (255, 255, 255, 255), list(points))
    return mask


# evaluates f(theta)->(x,y,colour) from theta0 to theta1 at pixel density, and
# finds the first theta>=theta0 for which either > theta1 or the condition fails
def find_limit(f, condition, theta0: float, theta1: float) -> float:
    x, y = f(theta0)
    if not condition(x, y):
        return theta0
    previous_xy = round(x), round(y)

    def travel(x, y):
        return abs(round(x) - previous_xy[0]) + abs(
            round(y) - previous_xy[1])

    delta = (theta1 - theta0) / 16  # why not
    theta = theta0
    while theta <= theta1:
        x, y = f(theta + delta)
        dist = travel(x, y)
        if dist < 1:
            delta = delta * 1.1
            continue
        if dist > 1:
            delta = delta * 0.9
            continue
        if not condition(x, y):
            return theta
        previous_xy = round(x), round(y)
        theta += delta
    return theta


DrawFunctionType = Callable[
    [float], Tuple[float, float]]


# plot a parameterised function onto the surface, from theta0 to theta1.
# If condition is not None, stops prematurely (before plotting (x,y)) if
# condition(x, y) returns false.  Ensures that condition is called at pixel
# density to find an accurate end point.
#  f : theta |-> (x, y)
def draw_function(canvas: pygame.Surface, f: DrawFunctionType,
                  thickness: int,
                  colour: pygame.Color,
                  condition: Optional[Callable[[float, float], bool]],
                  theta0: float, theta1: float) -> None:
    x, y = f(theta0)
    if condition is not None:
        limit = find_limit(f, condition, theta0, theta1)
        if limit < theta1:
            theta1 = limit
    previous_xy = round(x), round(y)

    def travel(x, y):
        return abs(round(x) - round(previous_xy[0])) + abs(
            round(y) - round(previous_xy[1]))

    delta = (theta1 - theta0) / 16  # why not
    if delta == 0:
        return
    theta = theta0
    while theta <= theta1:
        x, y = f(theta + delta)
        dist = travel(x, y)
        if dist < 1:
            delta = delta * 1.1
            continue
        if dist > 1:
            delta = delta * 0.9
            continue
        pygame.draw.line(canvas, colour, previous_xy, (x, y), thickness)
        previous_xy = x, y
        theta += delta


# Show canvas in a window until ESC is pressed.
def show_canvas(canvas: pygame.Surface,
                size: Optional[Tuple[int, int]] = None,
                title: Optional[str] = None) -> None:
    # Create a window to display the canvas
    screen = pygame.display.set_mode(
        (canvas.get_width(), canvas.get_height()) if size is None else size)
    if title is not None:
        pygame.display.set_caption(title=title)
    if (canvas.get_width() > screen.get_width() or
            canvas.get_height() > screen.get_height()):
        canvas = pygame.transform.smoothscale(canvas, screen.get_size())

    # Clear the screen and draw the canvas
    screen.fill((255, 192, 255))
    screen.blit(canvas, (0, 0))
    pygame.display.flip()

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

    pygame.quit()


class Arc(object):
    def __init__(self, cxy, radius, theta0, theta1, amplitude, frequency,
                 stop_condition):
        self.cxy = cxy
        self.radius = radius
        self.theta0 = theta0
        self.theta1 = theta1
        self.amplitude = amplitude
        self.frequency = frequency
        self.stop_condition = stop_condition

    def _normalised_theta(self, theta):
        return (theta - self.theta0) / (self.theta1 - self.theta0)

    # function that's 0 at the endpoints but rises to maximum of 1 at the
    # centre
    def _fade_in(self, normalised_theta):
        return normalised_theta * (1 - normalised_theta) * 4

    # Gets the cartesian point on the circle of given centre, radius and angle
    @staticmethod
    def _circle(cxy: tuple[float, float], radius: float, theta: float) -> tuple[
        float, float]:
        return cxy[0] + radius * math.cos(theta), cxy[1] + radius * math.sin(
            theta)

    # boundary position, grown by up to a factor of grow (at centre, 0 at ends)
    def f(self, theta, grow):
        fade = self._fade_in(self._normalised_theta(theta))
        radius_shape_boost = fade * self.amplitude * (abs(
            math.sin(
                (theta - self.theta0) * 2 * math.pi * self.frequency)) - 0.5)
        radius_grow_boost = fade * grow
        return self._circle(self.cxy,
                            self.radius * (1 + radius_shape_boost)
                            * (1 + radius_grow_boost),
                            theta)

    def draw_boundary(self, canvas, colour, thickness):
        draw_function(canvas,
                      lambda theta: self.f(theta, 0),
                      thickness, colour,
                      self.stop_condition,
                      self.theta0, self.theta1)

    def draw_shading(self, tile, colour, thickness, steps):
        rgba = copy.copy(colour)
        for i in range(1, steps):  # omitting both 0 and 'steps'
            t = i / steps
            rgba.a = round(255 * (1 - t))
            draw_function(tile,
                          lambda theta: self.f(theta, t * self.amplitude * 3),
                          thickness, rgba,
                          self.stop_condition,
                          self.theta0, self.theta1)


if __name__ == "__main__":
    pygame.init()
    height = 400
    tile, side, points = create_canvas(height=height)

    arc1 = Arc(points[5], side, math.pi, 5 * 2 * math.pi / 6, 0.08, 1, None)
    arc2 = Arc((-side / 2, 0), side, 0, 1 * 2 * math.pi / 6, -0.08, 1, None)

    colour = pygame.Color(0, 0, 0, 255)
    arc1.draw_boundary(tile, colour, 4)
    arc2.draw_boundary(tile, colour, 4)

    # image containing the boundary arcs 1 and 2, but no shading.  This is what
    # we use to limit the extent of arc 3 (which runs underneath arc 1)
    mask = tile.copy()


    # returns true if (x,y) is inside the mask, and its alpha is 0
    def check_alpha(x, y):
        try:
            return mask.get_at((round(x), round(y))).a == 0
        except IndexError:
            return False


    arc3 = Arc((-side / 2, 0), 2 * side, 0, 1 * 2 * math.pi / 6, 0.04, 2,
               check_alpha)
    arc3.draw_boundary(tile, colour, 4)

    # draw each gradient onto a new tile, so that we can blend it with the blit
    shading_tile = create_canvas(height)[0]
    arc3.draw_shading(tile, colour, 4, 20)
    tile.blit(shading_tile, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    # draw each gradient onto a new tile, so that we can blend it with the blit
    shading_tile = create_canvas(height)[0]
    arc1.draw_shading(shading_tile, colour, 4, 20)
    arc2.draw_shading(shading_tile, colour, 4, 20)
    tile.blit(shading_tile, (0, 0), special_flags=pygame.BLEND_ALPHA_SDL2)

    show_canvas(tile)
    pygame.image.save(tile, "tile.png")
