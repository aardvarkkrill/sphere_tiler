import sys
import math
from typing import Optional, Tuple

import pygame
from pygame.math import clamp
from sympy import ceiling
import numpy


def project_image_to_torus(
        output_size: Tuple[int, int],
        plane: pygame.Surface,
        shadow_amount: float = 0.3,
        sphere_centre_xy: Optional[Tuple[float, float]] = None,
        sphere_centre_z: Optional[float] = None) -> pygame.Surface:
    """ Given an image on a surface, wrap it around a torus and project that
        onto an output plane (in a way yet to be determined)
        If shadow_amount > 0, it will add shadow (larger values are darker.)
    """

    # input plane (u, v)
    u_width, u_height = plane.get_size()

    # torus (in model space, x,y,z)
    rh = (u_height - 1) / (2 * math.pi)
    rw = (u_width - 1) / (2 * math.pi)

    # output plane (X, Y)
    layer = pygame.Surface(size=output_size, flags=pygame.SRCALPHA)
    layer.fill((255, 255, 255, 255))
    ow, oh = output_size
    scale = min(ow, oh) / 2
    ocx, ocy = ow / 2, oh / 2

    for theta in numpy.linspace(0, 2 * math.pi, max(*output_size) * 4):
        progress = theta / (2 * math.pi) * 100  # Calculate progress percentage
        sys.stdout.write(
            f"\rToruse wrapping Progress: {progress:.0f}%")  # Overwrite the progress line
        sys.stdout.flush()  # Ensure the progress line gets updated immediately

        for phi in numpy.linspace(0, 2 * math.pi, max(*output_size) * 4):
            u, v = round(rh * phi), round(rw * theta)
            pixel_colour = plane.get_at((u, v))

            # position in model space [-1, +1]^3
            #       _____
            #      /     \     y towards viewer
            #     |   O   |    ---> x
            #      \     /     |
            #       -----      v z
            x = ((rw + rh * math.cos(phi) * math.cos(theta)) - rw) / (
                        2 * (rh + rw))
            y = ((rw + rh * math.cos(phi) * math.sin(theta)) - rw) / (
                        2 * (rh + rw))
            z = - math.sin(phi)

            # Viewer distance and tilt angle
            viewer = 2.0  # Distance of viewer (y-coordinate) from the origin
            alpha = math.radians(30)  # Tilt angle in radians

            # Apply tilt by rotating around the x-axis
            z_tilted = z * math.cos(alpha) - y * math.sin(alpha)
            y_tilted = z * math.sin(alpha) + y * math.cos(alpha)

            # Compute the perspective projection for the X, Y plane
            fn = scale * viewer / (viewer + y_tilted)  # Perspective factor
            X = int(clamp(ocx + x * fn, 0, ow - 1))  # Map to [0, ow]
            Y = int(clamp(ocy + z_tilted * fn, 0, oh - 1))  # Map to [0, oh]

            # Set the pixel
            if pixel_colour[3] > 0:
                layer.set_at((X, Y), pixel_colour)

    sys.stdout.write("\r")  # Clear the progress line
    sys.stdout.flush()  # Ensure the progress line gets updated immediately
    return layer


# Usage example
if __name__ == "__main__":
    def main():
        plane_file = "output.png" if len(sys.argv) <= 1 else sys.argv[1]
        radius = 1200 if len(sys.argv) <= 2 else int(sys.argv[2])
        shade = 0.3 if len(sys.argv) <= 3 else float(sys.argv[3])


    plane_file = "leafy_plane_v3.png"
    plane = pygame.image.load(plane_file)

    torus = project_image_to_torus((400, 400), plane)
    pygame.image.save(torus, "torus.png")
