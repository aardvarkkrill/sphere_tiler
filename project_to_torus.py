import random
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
        shadow_amount: float = 0.6,
        parallel_light: (float, float, float) = (-1, -1, 1),
        shading_model: str = 'halflambertian'
) -> pygame.Surface:
    """ Given an image on a surface, wrap it around a torus and project that
        onto an output plane (in a way yet to be determined)
        If shadow_amount > 0, it will add shadow (larger values are darker.)
        We assume that the light comes from a parallel source, parallel to the
        vector given in model (world) space.
        shading_model can be 'halflambertian', 'lambertian' or 'simple'
    """

    # input plane (u, v)
    uv_width, uv_height = plane.get_size()

    # torus (in model space, x,y,z)
    # rw is the radius of the wheel, rh the radius of the tube
    rw = (uv_width - 1) / (2 * math.pi)
    rh = (uv_height - 1) / (2 * math.pi)

    parallel_light = numpy.array(parallel_light, dtype=numpy.float32)
    parallel_light /= numpy.linalg.norm(parallel_light)

    camera_matrix = translate(0, 0, z=(rh + rw) * 1.5) @ rotate_x(
        math.radians(50))
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
    # note: alpha=255 codes for Z_max, so will be overwritten by any
    # non-transparent pixel
    layer.fill((255, 255, 255, 255))

    layer.unlock()
    plane.unlock()

    # bigger is smoother, but takes longer, and repeats pixels.
    # TODO: dynamically modify the sampling rate depending on the projection
    #       (probably the derivative in the image space?)  We're aiming to get
    #       one sample per pixel.
    sampling = 4.5

    for theta in numpy.linspace(0, 2 * math.pi,
                                round(sampling * max(*output_size))):
        progress = theta / (2 * math.pi) * 100  # Calculate progress percentage
        print(f"\rTorus wrapping: {progress:.0f}%", end="",
              flush=True)  # Overwrite the progress line

        stheta, ctheta = math.sin(theta), math.cos(theta)
        u = round(rw * theta)
        for phi in numpy.linspace(0, 2 * math.pi,
                                  round(sampling * max(*output_size))):
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
            cphi, sphi = math.cos(phi), math.sin(phi)

            # calculate the surface normal in model space
            normed_dxyz_by_dtheta = numpy.array((-stheta, ctheta, 0))
            normed_dxyz_by_dphi = numpy.array(
                (-sphi * ctheta, -sphi * stheta, cphi))
            normal = numpy.cross(normed_dxyz_by_dtheta, normed_dxyz_by_dphi)

            # surface pointing away from the camera is skipped.  For this,
            # transform the normal with the rotation part of the camera matrix.
            # normal_in_camera_space = camera_matrix[:3, :3] @ normal
            # if normal_in_camera_space[2] < 1e-3:
            #     continue

            # shading just depends on the angle between the normal and the light
            # Our backwards model means that larger = darker
            if shading_model == 'simple':
                shade = parallel_light.dot(normal) * shadow_amount
                if shade > 0:
                    pixel_colour = pixel_colour.lerp(
                        pygame.Color(0, 0, 0, pixel_colour.a),
                        shade)
                else:
                    pixel_colour = pixel_colour.lerp(
                        pygame.Color(255, 255, 255, pixel_colour.a),
                        -shade)
            elif shading_model == 'halflambertian':
                light = (0.5 - 0.5 * parallel_light.dot(normal))
                pixel_colour = pygame.Color(0, 0, 0, pixel_colour.a).lerp(
                    pixel_colour, light)

            # surface of model in model space
            l = rw + rh * cphi
            x = l * ctheta
            y = l * stheta
            z = rh * sphi

            X, Y, Z = (camera_matrix @ [x, y, z, 1])[:3]
            if Z < 0:
                # Behind camera
                continue

            sx, sy = round(how + X * how / Z), round(hoh - Y * hoh / Z)
            if 0 <= sx < output_size[0] and 0 <= sy < output_size[1]:

                # # draw 1% of normals
                # if random.randint(0, 10000) < 10:
                #     NX, NY, NZ = normal_in_camera_space * rh/2 + numpy.array([X, Y, Z])
                #     snx, sny = round(how + NX * how / NZ), round(hoh - NY * hoh / NZ)
                #     if 0 <= snx < output_size[0] and 0 <= sny < output_size[1]:
                #         pygame.draw.circle(layer, pygame.Color(255, 0, 0, 255), (sx, sy), 2)
                #         pygame.draw.line(layer, pygame.Color(0, 0, 0, 255), (sx, sy),
                #             (snx, sny), 1)
                #
                # continue

                # encoding depth in the alpha channel.
                # Smaller numbers are closer
                Z_depth = int(clamp(round((Z - Z_min) * Zscale), 0, 255))
                # Set the pixel
                old_pixel = layer.get_at((sx, sy))
                if old_pixel.a > Z_depth:
                    # fully opaque pixels just overwrite
                    if pixel_colour.a == 255:
                        pixel_colour.a = Z_depth
                        layer.set_at((sx, sy), pixel_colour)
                    else:
                        # partially transparent colour is a lerp
                        new_colour = pixel_colour.lerp(old_pixel,
                                                       pixel_colour.a / 255)
                        new_colour.a = Z_depth
                        layer.set_at((sx, sy), new_colour)

        print("\r", end="", flush=True)  # Clear the progress line

    # convert Z field of each pixel back to solid colour
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
        pass
