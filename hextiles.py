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
    pygame.font.init()
    font = pygame.font.Font(font_path, font_size)
    rendered_text = font.render(text, True, color)
    text_rect = rendered_text.get_rect(center=(x, y))
    surface.blit(rendered_text, text_rect)


def create_random_hexagonal_tiled_surface(
        tile_paths, canvas_size=(6400, 6400), tile_scale=1.0,
        background_colour: Optional[pygame.Color]
        = pygame.Color(255, 255, 255, 255),
        toroidal = False
) -> pygame.Surface:
    """
    Generates a hexagonal tiled surface using a provided image or callable tile
    generator, or a list of these.  Chooses a random rotation and reflection for
    each tile position of (one of the) input tile(s).

    Parameters:
        tile_paths (Union[str, Callable[[float, float], pygame.Surface], list]):
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
        toroidal (bool): False by default.  If true, the tiles on the left/right
            and top/bottom edges will be the same.  It's up to the caller to
            make sure that the repeats match an integral number of tiles.  To do
            this, set the size to (height*m, height*n) where m is odd and n is
            even.

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

    if not isinstance(tile_paths, list):
        tile_paths = [tile_paths]

    # Load image(s) if files
    full_tiles = [
        pygame.image.load(tp) if isinstance(tp, str) else tp
        for tp in tile_paths
    ]

    # a callable tile takes two [0,1] arguments (x and y fractions along the
    # plane.  In this case we'll get one tile just to measure it.
    if callable(full_tiles[0]):
        full_tile0 = full_tiles[0](0.0, 0.0)
    else:
        full_tile0 = full_tiles[0]

    scaled_tile0 = pygame.transform.smoothscale_by(full_tile0, tile_scale)

    # subtracting 1 puts the tiles a bit closer together, avoiding ugly gaps.
    # but it is a hack.  ideally this would be factored in to the tile design
    # which would have some bleed.
    tile_height = scaled_tile0.get_height() - 1
    tile_radius = tile_height / math.sqrt(3)
    tile_diameter = tile_height * 2 / math.sqrt(3)
    num_tiles_x = 1 + math.ceil(canvas_size[0] * 2 / (3 * tile_radius))
    num_tiles_y = 1 + math.ceil(canvas_size[1] * 2 / tile_height)

    # Build a list of either scaled tiles (so we only have to scale them once)
    # or else just the callable
    scaled_tiles = []
    for full_tile in full_tiles:
        if callable(full_tile):
            scaled_tiles.append(full_tile)
        else:
            scaled_tiles.append(
                pygame.transform.smoothscale_by(full_tile, tile_scale))

    # an array to hold the decisions on tile selection and rotation (negative
    # for reflections)
    selections = numpy.zeros((num_tiles_y, num_tiles_x * 2), dtype=numpy.int32)
    selections[:] = numpy.iinfo(numpy.int32).min
    rotations = numpy.zeros((num_tiles_y, num_tiles_x * 2), dtype=numpy.int32)
    rotations[:] = numpy.iinfo(numpy.int32).min

    # we'll use a negative rotation to code a reflection
    allow_reflections = True

    # Place random copies with random rotations
    for row in range(num_tiles_y):

        progress = (row + 1) / num_tiles_y * 100  # Calculate progress percentage
        sys.stdout.write(
            f"\rRandom-plane Progress: {progress:.0f}%")  # Overwrite the progress line
        sys.stdout.flush()  # Ensure the progress line gets updated immediately

        even_row = row % 2
        for col in range(even_row, num_tiles_x, 2):
            x = col * tile_radius * 3 / 2
            y = row * tile_height / 2

            if toroidal:
                last_col = (col == num_tiles_x - 1)
                last_row = (row == num_tiles_y - 1)
                if last_col and last_row:
                    chosen_tile = selections[0, 0]
                    chosen_rotation = rotations[0, 0]
                elif last_col:
                    chosen_tile = selections[row, 0]
                    chosen_rotation = rotations[row, 0]
                elif last_row:
                    chosen_tile = selections[0, col]
                    chosen_rotation = rotations[0, col]
                else:
                    chosen_tile = random.randint(0, len(scaled_tiles) - 1)
                    chosen_rotation = random.choice(range(-6, 6))
            else:
                chosen_tile = random.randint(0, len(scaled_tiles) - 1)
                chosen_rotation = random.choice(range(-6, 6))

            selections[row, col] = chosen_tile
            scaled_tile = scaled_tiles[chosen_tile]
            rotations[row, col] = chosen_rotation

            if callable(scaled_tile):
                full_tile = scaled_tile(
                    clamp(x / canvas_size[0], 0, 1),
                    clamp(y / canvas_size[1], 0, 1))
                scaled_tile = pygame.transform.smoothscale_by(full_tile,
                                                              tile_scale)

            if chosen_rotation < 0:
                chosen_rotation = -chosen_rotation
                scaled_tile = pygame.transform.flip(scaled_tile, True, False)

            angle = chosen_rotation * 360 / 6
            rotated_image = pygame.transform.rotate(scaled_tile, angle)

            # Blit to canvas (adjust to ensure center alignment)
            canvas.blit(rotated_image,
                        (round(x - rotated_image.get_width() / 2),
                         round(y - rotated_image.get_height() / 2)))

            # draw_centered_text(canvas, f"r{row},c{col}",
            #                    pygame.font.get_default_font(), 48, (0, 0, 0),
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
