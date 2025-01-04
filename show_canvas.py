from typing import Optional, Tuple

import pygame

# Show canvas in a window until ESC is pressed.
def show_canvas(canvas: pygame.Surface,
                size: Optional[Tuple[int, int]] = None,
                title: Optional[str] = None) -> None:
    # Create a window to display the canvas
    screen = pygame.display.set_mode(
        (canvas.get_width(), canvas.get_height()) if size is None else size)
    if title is not None:
        pygame.display.set_caption(title=title)
    if (canvas.get_width() > screen.get_width() or
            canvas.get_height() > screen.get_height()):
        canvas = pygame.transform.smoothscale(canvas, screen.get_size())

    # Clear the screen and draw the canvas
    screen.fill((255, 192, 255))
    screen.blit(canvas, (0, 0))
    pygame.display.flip()

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

    pygame.quit()
