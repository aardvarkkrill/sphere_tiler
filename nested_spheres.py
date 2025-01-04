import sys
import os

import pygame

import hextiles
import project_to_sphere
import make_tile


def main():
    if os.path.exists("brain_plane.png"):
        brain_plane = pygame.image.load("brain_plane.png")
    else:
        brain_plane = hextiles.create_random_hexagonal_tiled_surface(
            "brain_tile.png", (6400, 6400), 1.0,
            pygame.Color(0, 0, 0, 0)
        )
        pygame.image.save(brain_plane, "brain_plane.png")

    if os.path.exists("rainbow_plane.png"):
        rainbow_plane = pygame.image.load("rainbow_plane.png")
    else:
        rainbow_plane = hextiles.create_random_hexagonal_tiled_surface(
            "rainbow_tile.png", (6400, 6400), 0.5,
            pygame.Color(0, 0, 0, 0)
        )
        pygame.image.save(rainbow_plane, "rainbow_plane.png")

    if os.path.exists("pink_plane.png"):
        pink_plane = pygame.image.load("pink_plane.png")
    else:
        pink_plane = hextiles.create_random_hexagonal_tiled_surface(
            "pink_tile.png", (6400, 6400), 1.0,
            pygame.Color(0, 0, 0, 0)
        )
        pygame.image.save(pink_plane, "pink_plane.png")

    radius = 1200
    sphere_surface = pygame.Surface((2 * radius, 2 * radius),
                                    pygame.SRCALPHA)
    sphere_surface.fill(pygame.Color(255, 255, 255, 255))
    pygame.draw.circle(sphere_surface, pygame.Color(50, 50, 50, 255),
                       center=(radius, radius), radius=radius, width=0)

    # sphere_surface = project_to_sphere.project_image_to_sphere(
    #     sphere_surface, brain_plane, round(radius * 0.9**2), 0.7)
    #
    # sphere_surface = project_to_sphere.project_image_to_sphere(
    #     sphere_surface, rainbow_plane, round(radius * 0.9**1), 0.5)

    pw, ph = pink_plane.get_size()
    shrink = 0.9

    # sphere_surface = project_to_sphere.project_image_to_sphere(
    #     sphere_surface, pink_plane, round(radius * shrink ** 3), 0.9,
    #     sphere_centre_xy=(pw * 3/4, ph * 3/4), sphere_centre_z=radius * shrink ** 2)
    sphere_surface = project_to_sphere.project_image_to_sphere(
        sphere_surface, pink_plane, round(radius * shrink ** 2), 0.7,
        sphere_centre_xy=(pw * 3/4, ph * 3/4), sphere_centre_z=radius * shrink ** 2)
    sphere_surface = project_to_sphere.project_image_to_sphere(
        sphere_surface, pink_plane, round(radius * shrink ** 1), 0.5,
        sphere_centre_xy=(pw*1/4, ph*1/4), sphere_centre_z=radius * shrink ** 1)
    sphere_surface = project_to_sphere.project_image_to_sphere(
        sphere_surface, pink_plane, round(radius * shrink ** 0), 0.3)

    pygame.image.save(sphere_surface, "nested_spheres.png")
    make_tile.show_canvas(sphere_surface, (600, 600))


main()
