import sys
import os
import random

import pygame

import hextiles
import project_to_sphere
import brain_tile
import rainbow_tile
import show_canvas


def main():
    # if os.path.exists("brain_plane.png"):
    #     brain_plane = pygame.image.load("brain_plane.png")
    # else:
    #     brain_plane = hextiles.create_random_hexagonal_tiled_surface(
    #         "brain_tile.png", (6400, 6400), 1.0,
    #         pygame.Color(0, 0, 0, 0)
    #     )
    #     pygame.image.save(brain_plane, "brain_plane.png")
    #
    # if os.path.exists("rainbow_plane.png"):
    #     rainbow_plane = pygame.image.load("rainbow_plane.png")
    # else:
    #     rainbow_plane = hextiles.create_random_hexagonal_tiled_surface(
    #         "rainbow_tile.png", (6400, 6400), 0.5,
    #         pygame.Color(0, 0, 0, 0)
    #     )
    #     pygame.image.save(rainbow_plane, "rainbow_plane.png")

    # create pink_tile.png if it doesn't already exist
    if not os.path.exists("pink_tile.png"):
        tile = rainbow_tile.pink_tile()
        pygame.image.save(tile, "pink_tile.png")
        os.remove("pink_plane.png")

    # create pink_plane.png if it doesn't already exist, or is older than
    # the pink_tile.pnk
    if (not os.path.exists("pink_plane.png") or
            os.path.getmtime("pink_plane.png") <
            os.path.getmtime("pink_tile.png")):
        pink_plane = hextiles.create_random_hexagonal_tiled_surface(
            "pink_tile.png", (6400, 6400), 1.0,
            pygame.Color(0, 0, 0, 0)
        )
        pygame.image.save(pink_plane, "pink_plane.png")
    else:
        pink_plane = pygame.image.load("pink_plane.png")

    radius = 1200
    sphere_surface = pygame.Surface((2 * radius, 2 * radius),
                                    pygame.SRCALPHA)
    sphere_surface.fill(pygame.Color(255, 255, 255, 255))
    pygame.draw.circle(sphere_surface, pygame.Color(50, 50, 50, 255),
                       center=(radius, radius), radius=radius, width=0)

    # assume we need 4*radius pixels of the plane for each projection, choose
    # a random point in the surface to centre the sphere
    def random_point(surface) -> (float, float):
        pw, ph = surface.get_size()
        return (
            (pw - radius * 4) * random.random() + radius * 2,
            (pw - radius * 4) * random.random() + radius * 2)

    # how much smaller is the radius of each nested layer than its parent
    shrink = 0.9
    num_layers = 4
    base_shadow = 0.3
    shadow_factor = 1.5

    for i in range(num_layers-1, 0, -1):
        sphere_surface = project_to_sphere.project_image_to_sphere(
            sphere_surface, pink_plane, round(radius * shrink ** i),
            base_shadow * shadow_factor**i,
            sphere_centre_xy=random_point(pink_plane),
            sphere_centre_z=radius * shrink ** i)

    sphere_surface = project_to_sphere.project_image_to_sphere(
        sphere_surface, pink_plane, round(radius * shrink ** 0), base_shadow)

    pygame.image.save(sphere_surface, "nested_spheres.png")
    show_canvas.show_canvas(sphere_surface, (600, 600))


main()
