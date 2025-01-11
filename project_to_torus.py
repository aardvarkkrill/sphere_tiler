import sys
import math
from typing import Optional, Tuple

import pygame
from pygame.math import clamp
from sympy import ceiling
import numpy


def rotate_x(theta: float) -> numpy.ndarray:
    """ 4x4 matrix for rotating around the x-axis by theta radians."""
    return numpy.array([
        [1, 0, 0, 0],
        [0, math.cos(theta), -math.sin(theta), 0],
        [0, math.sin(theta), math.cos(theta), 0],
        [0, 0, 0, 1]
    ], dtype=numpy.float32)


def translate(x: float, y: float, z: float) -> numpy.ndarray:
    """ 4x4 matrix for translating the world."""
    return numpy.array([
        [1, 0, 0, x],
        [0, 1, 0, y],
        [0, 0, 1, z],
        [0, 0, 0, 1]
    ], dtype=numpy.float32)


def NDC_to_raster_matrix(width: int, height: int) -> numpy.ndarray:
    """ 2x3 projects [-1, 1] x [-1, 1] into the image region """
    return numpy.array([
        [width / 2, 0, width / 2],
        [0, -height / 2, height / 2]
    ], dtype=numpy.float32)


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
    uv_width, uv_height = plane.get_size()

    # torus (in model space, x,y,z)
    rw = (uv_width - 1) / (2 * math.pi)
    rh = (uv_height - 1) / (2 * math.pi)

    camera_matrix = translate(0, 0, z=(rh + rw)) @ rotate_x(math.radians(30))
    render_matrix = NDC_to_raster_matrix(*output_size)

    # output plane (X, Y)
    how, hoh = output_size[0] / 2, output_size[1] / 2
    layer = pygame.Surface(size=output_size, flags=pygame.SRCALPHA)
    layer.fill((255, 255, 255, 255))

    for theta in numpy.linspace(0, 2 * math.pi, max(*output_size) * 4):
        progress = theta / (2 * math.pi) * 100  # Calculate progress percentage
        sys.stdout.write(
            f"\rTorus wrapping Progress: {progress:.0f}%")  # Overwrite the progress line
        sys.stdout.flush()  # Ensure the progress line gets updated immediately

        stheta, ctheta = math.sin(theta), math.cos(theta)
        for phi in numpy.linspace(0, 2 * math.pi, max(*output_size) * 4):
            u, v = round(rw * theta), round(rh * phi)
            pixel_colour = plane.get_at((u, v))

            # pixel is fully transparent
            if pixel_colour[3] == 0:
                continue

            # position in model space
            #       _____
            #      /     \     z towards viewer
            #     |   O   |    ---> x
            #      \     /     |
            #       -----      v y
            cphi = math.cos(phi)
            x = (rw + rh * cphi) * ctheta
            y = (rw + rh * cphi) * stheta
            z = rh * math.sin(phi)

            X, Y, Z = (camera_matrix @ [x, y, z, 1])[:3]
            sx, sy = round(how + X * how / Z), round(hoh - Y * hoh)
            if 0 <= sx < output_size[0] and 0 <= sy < output_size[1]:
                # Set the pixel
                if pixel_colour[3] > 0:
                    layer.set_at((sx, sy), pixel_colour)

    sys.stdout.write("\r")  # Clear the progress line
    sys.stdout.flush()  # Ensure the progress line gets updated immediately
    return layer

# Usage example
if __name__ == "__main__":
    def main():
        plane_file = "output.png" if len(sys.argv) <= 1 else sys.argv[1]
        radius = 1200 if len(sys.argv) <= 2 else int(sys.argv[2])
        shade = 0.3 if len(sys.argv) <= 3 else float(sys.argv[3])


    # plane_file = "leafy_plane_v3.png"
    plane_file = "amazon_crop.jpg"
    plane = pygame.image.load(plane_file)

    torus = project_image_to_torus((400, 400), plane)
    pygame.image.save(torus, "torus.png")
