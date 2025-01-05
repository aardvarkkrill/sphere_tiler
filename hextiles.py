import math
from typing import Optional

import pygame
import random
import numpy
import sys

from pygame.math import clamp

import rainbow_tile


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


# Draw centered text at specified coordinates
def draw_centered_text(surface, text, font_path, font_size, color, x, y):
    font = pygame.font.Font(font_path, font_size)
    rendered_text = font.render(text, True, color)
    text_rect = rendered_text.get_rect(center=(x, y))
    surface.blit(rendered_text, text_rect)


def create_random_hexagonal_tiled_surface(
        tile_path, canvas_size=(6400, 6400), tile_scale=1.0,
        background_colour: Optional[pygame.Color]
        = pygame.Color(255, 255, 255, 255)
) -> pygame.Surface:
    """
    Generates a hexagonal tiled surface using a provided image or callable tile
    generator, or a list of these.  Chooses a random rotation and reflection for
    each tile position of (one of the) input tile(s).

    Parameters:
        tile_path (Union[str, Callable[[float, float], pygame.Surface], list]):
            The filepath to the tile image or a callable function that returns a tile 
            surface based on x and y fractional coordinates, or a non-empty list
            of these.
            If there's more than one tile, they must all evaluate to the same
            size, and if callable, also the same size for any parameter set.
        canvas_size (Tuple[int, int]): 
            The dimensions of the canvas to generate, defaults to (6400, 6400).
        tile_scale (float): 
            A scaling factor for resizing the tiles, defaults to 1.0.
        background_colour (Optional[pygame.Color]): 
            The background color to fill the canvas, defaults to white 
            (pygame.Color(255, 255, 255, 255)).

    Returns:
        pygame.Surface: 
            A pygame surface containing the hexagonal tiled pattern.
    """
    # Create canvas
    canvas = pygame.Surface(canvas_size, flags=pygame.SRCALPHA)

    # Canvas fill will be the colour we see through any transparency in the tile
    if background_colour is not None:
        canvas.fill(background_colour)
    # canvas.fill((255, 0, 255))  # Fill with pink
    # canvas.fill((179, 179, 179))  # Fill with grey 30% (0xB3)
    # canvas.fill((255,255,255))  # Fill with white

    if not isinstance(tile_path, list):
        tile_path = [tile_path]

    # Load image(s) if files
    full_tiles = [
        pygame.image.load(tile_path) if isinstance(tile_path, str) \
            else tile_path
        for tp in tile_path
    ]

    # a callable tile takes two [0,1] arguments (x and y fractions along the
    # plane.  In this case we'll get one tile just to measure it.
    if callable(full_tiles[0]):
        callable_full_tile = full_tiles[0]
        full_tile0 = callable_full_tile(0.0, 0.0)
    else:
        full_tile0 = full_tiles[0]
        callable_full_tile = None

    scaled_tile0 = pygame.transform.smoothscale_by(full_tile0, tile_scale)

    tile_height = scaled_tile0.get_height()
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

        progress = (
                           row + 1) / num_tiles_y * 100  # Calculate progress percentage
        sys.stdout.write(
            f"\rRandom-plane Progress: {progress:.0f}%")  # Overwrite the progress line
        sys.stdout.flush()  # Ensure the progress line gets updated immediately

        even_row = row % 2 == 0
        for col in range((0 if even_row else 1), num_tiles_x, 2):
            x = col * tile_radius * 3 / 2
            y = row * tile_height / 2

            if callable_full_tile is not None:
                scaled_tile = callable_full_tile(
                    clamp(x / canvas_size[0], 0, 1),
                    clamp(y / canvas_size[1], 0, 1))
                scaled_tile = pygame.transform.smoothscale_by(scaled_tile,
                                                              tile_scale)

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

    sys.stdout.write(f"\rRandom-plane Done.")  # Overwrite the progress line
    sys.stdout.flush()
    return canvas


def graded_colour_plane(
        colour1=pygame.Color(255, 0, 255, 255),  # pink
        colour2=pygame.Color(0, 255, 255, 255),  # cyan,
        canvas_size=(6400, 6400),  # default canvas size
        tile_scale=1.0
) -> pygame.Surface:
    """
    Generates a gradient-based hexagonal tiled image surface by blending two colors.
    The function creates a hexagonal tiled surface where tiles are painted with colors
    blended between `colour1` and `colour2`. The blending is determined by the distance
    of each tile and relative to a center. The resulting surface is saved as an image
    file named "output.png" and returned.

    Parameters:
        colour1 (pygame.Color): The starting color for the gradient, defaults
                                to pink pygame.Color(255, 0, 255, 255).
        colour2 (pygame.Color): The ending color for the gradient, defaults
                                to cyan pygame.Color(0, 255, 255, 255).
        tile_scale (float): A scaling factor for the size of the hexagonal tiles.
                            Higher values increase the tile size, defaults to 1.0.

    Returns:
        pygame.Surface: The generated hexagonal tiled surface with a gradient
                        based on the provided colors.
    """

    def tile(x, y) -> pygame.Surface:
        # colour1 in top left -> colour2 in bottom right
        d00 = abs(x) + abs(y)
        return rainbow_tile.pink_tile(
            rainbow_tile.blend_colours(colour1, colour2, d00 / 2))

    canvas = create_random_hexagonal_tiled_surface(tile,
                                                   background_colour=pygame.Color(
                                                       0, 0, 0, 0),
                                                   canvas_size=canvas_size,
                                                   tile_scale=tile_scale)
    pygame.image.save(canvas, "output.png")
    return canvas


# Usage example
if __name__ == "__main__":
    def main():
        tile = "tile.png" if len(sys.argv) <= 1 else sys.argv[1]
        tile_scale = 1.0 if len(sys.argv) <= 2 else float(sys.argv[2])
        canvas = create_random_hexagonal_tiled_surface(tile,
                                                       tile_scale=tile_scale)
        # Save canvas as image
        pygame.image.save(canvas, "output.png")


    main()
