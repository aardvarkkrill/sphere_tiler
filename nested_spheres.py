import sys
import os
import random

import pygame

import hextiles
import project_to_sphere
import brain_tile
import rainbow_tile
import show_canvas


def make_nest(plane, # plane to be wrapped on each shell
              radius = 1200, # radius of the outermost shell
              num_layers=4, # there are this many layers of spherical shell
              shrink=0.9, # each layer is this much smaller
              base_shadow=0.3,  # outer layer has this much shade
              shadow_factor=1.5  # each shadow darkens by this amount
              ):
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

    for i in range(num_layers - 1, 0, -1):
        print(f"Layer {num_layers - i} of {num_layers}")
        sphere_surface = project_to_sphere.project_image_to_sphere(
            sphere_surface, plane, round(radius * shrink ** i),
            base_shadow * shadow_factor ** i,
            sphere_centre_xy=random_point(plane),
            sphere_centre_z=radius * shrink ** i)

    print(f"Final Layer of {num_layers}")
    sphere_surface = project_to_sphere.project_image_to_sphere(
        sphere_surface, plane, round(radius * shrink ** 0), base_shadow)

    return sphere_surface


def pink_sphere():
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
            "pink_tile.png", (6400, 6400), 0.25,
            pygame.Color(0, 0, 0, 0)
        )
        pygame.image.save(pink_plane, "pink_plane.png")
    else:
        pink_plane = pygame.image.load("pink_plane.png")

    sphere = make_nest(pink_plane)
    pygame.image.save(sphere, "pink_sphere.png")
    show_canvas.show_canvas(sphere, (600, 600))

def yellow_cyan_sphere():
    # yellow -> cyan plane
    if not os.path.exists("yellow-cyan_plane.png"):
        plane = hextiles.graded_colour_plane(colour1=pygame.Color(255, 255, 0, 255),
                                 tile_scale=0.25)
        pygame.image.save(plane, "yellow-cyan_plane.png")
    plane = pygame.image.load("yellow-cyan_plane.png")

    sphere = make_nest(plane)
    pygame.image.save(sphere, "yellow_cyan_spheres.png")
    show_canvas.show_canvas(sphere, (600, 600))

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
    pass


# pink_sphere()
yellow_cyan_sphere()
