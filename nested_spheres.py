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
        brain_plane = hextiles.create_canvas_and_save_output2(
            "brain_tile.png", "brain_plane.png", (6400, 6400), 1.0,
            pygame.Color(0, 0, 0, 0)
        )

    if os.path.exists("rainbow_plane.png"):
        rainbow_plane = pygame.image.load("rainbow_plane.png")
    else:
        rainbow_plane = hextiles.create_canvas_and_save_output2(
            "rainbow_tile.png", "rainbow_plane.png", (6400, 6400), 0.5,
            pygame.Color(0, 0, 0, 0)
        )

    if os.path.exists("pink_plane.png"):
        pink_plane = pygame.image.load("pink_plane.png")
    else:
        pink_plane = hextiles.create_canvas_and_save_output2(
            "pink_tile.png", "pink_plane.png", (6400, 6400), 1.0,
            pygame.Color(0, 0, 0, 0)
        )

    max_radius = 1200
    sphere_surface = pygame.Surface((2 * max_radius, 2 * max_radius),
                                    pygame.SRCALPHA)
    sphere_surface.fill(pygame.Color(255, 255, 255, 255))

    make_tile.show_canvas(sphere_surface, (600,600))

    sphere_surface = project_to_sphere.project_image_to_sphere(
        sphere_surface, pink_plane, round(max_radius * 0.8), 0.3)

    for i in range(sphere_surface.get_width()//2 - 100, sphere_surface.get_width()//2 + 100, 5):
        print(sphere_surface.get_at((i, sphere_surface.get_height()//2)))
    make_tile.show_canvas(sphere_surface, (600,600))

    sphere_surface = project_to_sphere.project_image_to_sphere(
        sphere_surface, rainbow_plane, round(max_radius * 0.9), 0.3)

    make_tile.show_canvas(sphere_surface, (600,600))

    sphere_surface = project_to_sphere.project_image_to_sphere(
        sphere_surface, brain_plane, round(max_radius * 1.0), 0.3)

    pygame.image.save(sphere_surface, "nested_spheres.png")
    make_tile.show_canvas(sphere_surface, (600, 600))


main()
