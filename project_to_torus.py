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
    # rw is the radius of the wheel, rh the radius of the tube
    rw = (uv_width - 1) / (2 * math.pi)
    rh = (uv_height - 1) / (2 * math.pi)

    camera_matrix = translate(0, 0, z=(rh + rw) * 1.5) @ rotate_x(
        math.radians(30))
    render_matrix = NDC_to_raster_matrix(*output_size)

    # compute the relevant Z range in image space
    model_bbox = numpy.array(
        [[x, y, z, 1.0] for x in (- rw - rh, rw + rh)
         for y in (- rw - rh, rw + rh)
         for z in (-rh, rh)
         ]
    ).transpose()
    render_Zs = (camera_matrix @ model_bbox)[2, :]
    Z_min, Z_max = min(render_Zs), max(render_Zs)
    Zscale = 255 / (Z_max - Z_min)

    # output plane (X, Y)
    how, hoh = output_size[0] / 2, output_size[1] / 2
    layer = pygame.Surface(size=output_size, flags=pygame.SRCALPHA)
    layer.fill((255, 255, 255, 255))

    layer.unlock()
    plane.unlock()

    for theta in numpy.linspace(0, 2 * math.pi, 3 * max(*output_size)):
        progress = theta / (2 * math.pi) * 100  # Calculate progress percentage
        sys.stdout.write(
            f"\rTorus wrapping Progress: {progress:.0f}%")  # Overwrite the progress line
        sys.stdout.flush()  # Ensure the progress line gets updated immediately

        stheta, ctheta = math.sin(theta), math.cos(theta)
        u = round(rw * theta)
        for phi in numpy.linspace(0, 2 * math.pi, 3 * max(*output_size)):
            v = round(rh * phi)
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
            l = rw + rh * math.cos(phi)
            x = l * ctheta
            y = l * stheta
            z = rh * math.sin(phi)

            X, Y, Z = (camera_matrix @ [x, y, z, 1])[:3]
            if Z < 0:
                continue

            sx, sy = round(how + X * how / Z), round(hoh - Y * hoh / Z)
            if 0 <= sx < output_size[0] and 0 <= sy < output_size[1]:
                # encoding depth in the alpha channel.
                # Smaller numbers are closer
                Z_depth = int(clamp(round((Z - Z_min) * Zscale), 0, 255))
                # Set the pixel
                old_pixel = layer.get_at((sx, sy))
                if old_pixel.a > Z_depth:
                    pixel_colour.a = Z_depth
                    layer.set_at((sx, sy), pixel_colour)

        sys.stdout.write("\r")  # Clear the progress line
        sys.stdout.flush()  # Ensure the progress line gets updated immediately

    for i in range(output_size[0]):
        for j in range(output_size[1]):
            p = layer.get_at((i, j))
            p.a = 255
            layer.set_at((i, j), p)

    layer.lock()
    return layer


# Usage example
if __name__ == "__main__":
    def main():
        plane_file = "output.png" if len(sys.argv) <= 1 else sys.argv[1]
        radius = 1200 if len(sys.argv) <= 2 else int(sys.argv[2])
        shade = 0.3 if len(sys.argv) <= 3 else float(sys.argv[3])


    if 0:
        # plane_file = "leafy_plane_v3.png"
        plane_file = "amazon.jpg"
        plane = pygame.image.load(plane_file)

        torus = project_image_to_torus((400, 400), plane)
        pygame.image.save(torus, "torus.png")

    if 1:
        import brain_tile
        height = 250
        tiles = []
        for i in range(6):
            colours = ['0xfd8a8a', '0xffcbcb', '0x9ea1d4',
                       '0xf1f7b5', '0xa8d1d1', '0xdfebeb']
            tile, side, points = brain_tile.create_canvas(height + 1)
            pygame.draw.polygon(tile, pygame.Color(colours[i]), points, 0)
            tiles.append(tile)
            pygame.draw.polygon(tile, pygame.Color(colours[i]), points, 1)
            tiles.append(tile)


        import hextiles
        plane = hextiles.create_random_hexagonal_tiled_surface(
            tiles,
            (height * 19, height * 10),
            1.0,
            pygame.Color(0,0,0,255)
        )
        import show_canvas
        show_canvas.show_canvas(plane)

        torus = project_image_to_torus((400, 400), plane)
        pygame.image.save(torus, "torus.png")


