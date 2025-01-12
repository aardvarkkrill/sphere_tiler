import brain_tile
import pygame
import project_to_torus
import rainbow_tile
import show_canvas
import hextiles


def pastel_torus(size: int = 1200):
    # makes a torus out of solid pastel hexagons
    # 1200 takes ~5 minutes, use 400 for a quick look
    height = 250
    tiles = []
    for i in range(6):
        # pastel colours
        colours = ['0xfd8a8a', '0xffcbcb', '0x9ea1d4',
                   '0xf1f7b5', '0xa8d1d1', '0xdfebeb']
        # solid tiles
        tile, side, points = brain_tile.create_canvas(height + 1)
        pygame.draw.polygon(tile, pygame.Color(colours[i]), points, 0)
        pygame.draw.polygon(tile, pygame.Color(colours[i]), points, 1)
        tiles.append(tile)

    plane = hextiles.create_random_hexagonal_tiled_surface(
        tiles,
        (height * 19, height * 10),
        1.0,
        pygame.Color(0, 0, 0, 255),
        toroidal=True
    )

    # four = pygame.Surface((plane.get_width()*2, plane.get_height()*2))
    # four.fill(pygame.Color(0, 0, 0, 255))
    # four.blit(plane, (0, 0))
    # four.blit(plane, (plane.get_width(), 0))
    # four.blit(plane, (0, plane.get_height()))
    # four.blit(plane, (plane.get_width(), plane.get_height()))
    # show_canvas.show_canvas(four, (850, 500))

    # show_canvas.show_canvas(plane)
    pygame.image.save(plane, f"pastel_plane.png")

    torus = project_to_torus.project_image_to_torus((size, size), plane)
    pygame.image.save(torus, f"pastel_torus_{size}.png")


def ribbon_torus(size: int = 1200,
                 colour: pygame.Color = pygame.Color(255, 0, 255, 255)):
    # makes a torus out of hexagonal tiles with pink ribbon
    # 1200 takes ~5 minutes, use 400 for a quick look
    height = 250
    tile = rainbow_tile.pink_tile(height=height+1, extent=0.5)
    plane = hextiles.create_random_hexagonal_tiled_surface(
        tile,
        (height * 19, height * 10),
        1.0,
        pygame.Color(0, 0, 0, 255),
        toroidal=True
    )

    pygame.image.save(plane, f"ribbon_plane.png")

    torus = project_to_torus.project_image_to_torus((size, size), plane)
    pygame.image.save(torus, f"ribbon_torus_{size}.png")

def bagel_torus(size: int = 1200,
                bg_colour: pygame.Color = pygame.Color(179,155,133,255)):
    # makes a torus out of hexagonal tiles with pink ribbon
    # 1200 takes ~5 minutes, use 400 for a quick look
    tile = pygame.image.load("bagel_tile_250.png")
    height = tile.get_height() - 1
    plane = hextiles.create_random_hexagonal_tiled_surface(
        tile,
        (height * 19, height * 10),
        1.0,
        background_colour=bg_colour,
        toroidal=True
    )

    pygame.image.save(plane, f"bagel_plane.png")

    torus = project_to_torus.project_image_to_torus((size, size), plane)
    pygame.image.save(torus, f"bagel_torus_{size}.jpg")

# fast = True
fast = False
# pastel_torus(400 if fast else 1200)
# ribbon_torus(400 if fast else 1200)
bagel_torus(200 if fast else 1200)
