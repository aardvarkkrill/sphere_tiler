import math
from typing import Optional

import pygame
import random
import numpy
import sys

from pygame.math import clamp


# Take a hexagonal tile and repeat it over the plane, with random orientation.
# Argument: name of tile file (default tile.png)

# randomised rotations
def create_canvas_and_save_output1(tile_path: str, output_path: str,
                                   canvas_size=(1600, 1600)):
    # Initialize pygame
    pygame.init()

    # Create canvas
    canvas = pygame.Surface(canvas_size)
    canvas.fill((255, 255, 255))  # Fill with white

    # Load image
    full_tile = pygame.image.load(tile_path)
    scaled_tile = pygame.transform.scale_by(full_tile, 0.5)

    tile_height = scaled_tile.get_height()
    tile_radius = tile_height / math.sqrt(3)
    tile_diameter = tile_height * 2 / math.sqrt(3)

    num_tiles_x = math.ceil(canvas_size[0] / (3 * tile_radius))
    num_tiles_y = math.ceil(canvas_size[1] * 2 / tile_height)

    # Place random copies with random rotations
    for row in range(num_tiles_y):
        for col in range(num_tiles_x):
            even_row = row % 2 == 0
            x = col * tile_radius * 3 + (0 if even_row else 3 * tile_radius / 2)
            y = row * tile_height / 2

            # Random rotation
            angle = random.randint(0, 5) * 360 / 6
            angle = (col % 6) * 360 / 6
            rotated_image = pygame.transform.rotate(scaled_tile, angle)

            # Blit to canvas (adjust to ensure center alignment)
            canvas.blit(rotated_image,
                        (round(x - rotated_image.get_width() / 2),
                         round(y - rotated_image.get_height() / 2)))

    # Save canvas as image
    pygame.image.save(canvas, output_path)
    pygame.quit()


# Draw centered text at specified coordinates
def draw_centered_text(surface, text, font_path, font_size, color, x, y):
    font = pygame.font.Font(font_path, font_size)
    rendered_text = font.render(text, True, color)
    text_rect = rendered_text.get_rect(center=(x, y))
    surface.blit(rendered_text, text_rect)


# randomised rotations of a tile
def create_random_hexagonal_tiled_surface(
        tile_path, canvas_size=(6400, 6400), tile_scale=1.0,
        background_colour: Optional[pygame.Color] = pygame.Color(255, 255, 255, 255)
) -> pygame.Surface:
    # Create canvas
    canvas = pygame.Surface(canvas_size, flags=pygame.SRCALPHA)

    # Canvas fill will be the colour we see through any transparency in the tile
    if background_colour is not None:
        canvas.fill(background_colour)
    # canvas.fill((255, 0, 255))  # Fill with pink
    # canvas.fill((179, 179, 179))  # Fill with grey 30% (0xB3)
    # canvas.fill((255,255,255))  # Fill with white

    # Load image
    full_tile = pygame.image.load(tile_path)
    scaled_tile = pygame.transform.smoothscale_by(full_tile, tile_scale)

    tile_height = scaled_tile.get_height()
    tile_radius = tile_height / math.sqrt(3)
    tile_diameter = tile_height * 2 / math.sqrt(3)

    num_tiles_x = 1 + math.ceil(canvas_size[0] * 2 / (3 * tile_radius))
    num_tiles_y = 1 + math.ceil(canvas_size[1] * 2 / tile_height)

    rotations = numpy.zeros((num_tiles_y, num_tiles_x * 2), dtype=numpy.int32)
    rotations[:] = numpy.iinfo(numpy.int32).min

    # we'll use a negative rotation to code a reflection
    allow_reflections = True

    # Place random copies with random rotations
    for row in range(num_tiles_y):
        even_row = row % 2 == 0
        for col in range((0 if even_row else 1), num_tiles_x, 2):
            x = col * tile_radius * 3 / 2
            y = row * tile_height / 2

            # this is for the tile with the isolated dot
            has_isolated_dot = False
            if has_isolated_dot:
                allowed_rotations = [0, 1, 2, 3, 4, 5]
                allow_reflections = False
                if row > 0 and col > 0 and rotations[row - 1, col - 1] == 3:
                    allowed_rotations.remove(0)
                if row > 0 and col < num_tiles_x * 2 - 1 and rotations[
                    row - 1, col + 1] == 1:
                    allowed_rotations.remove(4)
                if row > 1 and rotations[row - 2, col] == 2:
                    allowed_rotations.remove(5)
            else:
                allowed_rotations = list(range(-5, 6))

            # Random rotation
            choice = random.choice(allowed_rotations)
            rotations[row, col] = choice

            if choice < 0:
                choice = -choice
                scaled_tile = pygame.transform.flip(scaled_tile, True, False)

            angle = choice * 360 / 6
            rotated_image = pygame.transform.rotate(scaled_tile, angle)

            # Blit to canvas (adjust to ensure center alignment)
            canvas.blit(rotated_image,
                        (round(x - rotated_image.get_width() / 2),
                         round(y - rotated_image.get_height() / 2)))

            # draw_centered_text(canvas, str(choice),
            #                    pygame.font.get_default_font(), 48, (0, 255, 128),
            #                    x, y)

    return canvas


# Usage example
if __name__ == "__main__":
    tile = "tile.png" if len(sys.argv) <= 1 else sys.argv[1]
    tile_scale = 1.0 if len(sys.argv) <= 2 else float(sys.argv[2])
    canvas = create_random_hexagonal_tiled_surface(tile, tile_scale=tile_scale)
    # Save canvas as image
    pygame.image.save(canvas, "output.png")
