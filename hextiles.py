import math
import pygame
import random
import numpy

from pygame.math import clamp


# Take a hexagonal tile and repeat it over the plane, with random orientation.

# randomised rotations
def create_canvas_and_save_output1(image_path, output_path,
                                   canvas_size=(1600, 1600)):
    # Initialize pygame
    pygame.init()

    # Create canvas
    canvas = pygame.Surface(canvas_size)
    canvas.fill((255, 255, 255))  # Fill with white

    # Load image
    full_tile = pygame.image.load("tile.png")
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


# randomised rotations avoiding dots
def create_canvas_and_save_output2(image_path, output_path,
                                   canvas_size=(6400, 6400),
                                   tile_scale = 1.0):
    # Initialize pygame
    pygame.init()

    # Create canvas
    canvas = pygame.Surface(canvas_size)

    # Canvas fill will be the colour we see through any transparency in the tile
    #canvas.fill((255, 0, 255))  # Fill with pink
    #canvas.fill((179, 179, 179))  # Fill with grey 30% (0xB3)
    canvas.fill((255,255,255))  # Fill with white

    # Load image
    full_tile = pygame.image.load(image_path)
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

    # Save canvas as image
    pygame.image.save(canvas, output_path)

    p = project_image_to_sphere(canvas, 1200)
    pygame.image.save(p, "sphere.png")
    pygame.quit()


def project_image_to_sphere(image: pygame.Surface,
                            radius: int) -> pygame.Surface:
    """ Given an image on a surface, wrap it around a sphere and project that
    orthogonally and centrally on a square plane of side 2 * radius.
    The wrapping should be a stereographic projection of the southern hemisphere."""

    width, height = image.get_size()
    sphere_surface = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
    sphere_surface.fill(pygame.Color(255, 255, 255, 255))

    # looping over projected image
    for y in range(2 * radius):
        for x in range(2 * radius):
            dx = x - radius
            dy = y - radius
            # distance from projected point to centre of projected image
            distance_squared = dx * dx + dy * dy
            if distance_squared > radius * radius:
                continue

            s = math.sqrt(distance_squared)
            if distance_squared < 1e-6:
                u, v = radius, radius
            else:
                # angle subtended at north pole
                theta = 0.5 * math.asin(s / radius)
                # distance to original point
                d = 2 * radius * math.tan(theta)
                # original point
                u = width / 2 + dx * d / s
                v = height / 2 + dy * d / s
            uu = math.floor((0.5 + u) % width)
            vv = math.floor((0.5 + v) % height)
            pixel_colour = image.get_at((uu, vv))

            # Attached Shadow
            # to calculate shadows, assume the north pole is towards us (this is
            # a different parametrisation to the above)
            light_lat = - math.pi / 4
            light_lon = - math.pi / 4
            latitude = math.acos(s / radius)
            longitude = math.atan2(dx, dy)

            # See https://en.wikipedia.org/wiki/Haversine_formula
            def hav(angle):
                return 0.5 * (1 - math.cos(angle))

            def ahav(x):
                return math.acos(clamp(1 - 2 * x, -1, 1))

            hav_theta = hav(light_lat - latitude) + math.cos(
                latitude) * math.cos(light_lat) * hav(light_lon - longitude)
            ang_diff = ahav(hav_theta)
            brighten = 3
            shade = clamp(brighten * ang_diff / (2 * math.pi), 0, 1)

            pixel_colour.r = round(pixel_colour.r * shade)
            pixel_colour.g = round(pixel_colour.g * shade)
            pixel_colour.b = round(pixel_colour.b * shade)

            # Set the pixel
            sphere_surface.set_at((x, y), pixel_colour)

    return sphere_surface


# Usage example
if __name__ == "__main__":
    # create_canvas_and_save_output1("input.png", "output.png")
    create_canvas_and_save_output2("tile.png", "output.png")
