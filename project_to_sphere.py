import sys
import math
from typing import Optional

import pygame
from pygame.math import clamp

def project_image_to_sphere(surface: Optional[pygame.Surface],
                            plane: pygame.Surface,
                            radius: int,
                            shadow_amount: float = 0.3) -> pygame.Surface:
    """ Given an image on a surface, wrap it around a sphere and project that
    orthogonally and centrally on a square plane of side 2 * radius.
    The wrapping should be a stereographic projection of the southern hemisphere.
    If surface is none, a white, minimum size (2*radius square) surface will be
    created.  If shadow_amount > 0, it will add shadow.  """

    width, height = plane.get_size()

    if surface is None:
        sphere_surface = pygame.Surface((2 * radius, 2 * radius),
                                        pygame.SRCALPHA)
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
            pixel_colour = plane.get_at((uu, vv))

            # Attached Shadow
            # to calculate shadows, assume the north pole is towards us (this is
            # a different parametrisation to the above)
            light_lat = - math.pi / 4
            light_lon = - math.pi / 4
            latitude = math.acos(s / radius)
            longitude = math.atan2(dx, dy)

            if shadow_amount > 0:
                # See https://en.wikipedia.org/wiki/Haversine_formula
                def hav(angle):
                    return 0.5 * (1 - math.cos(angle))

                def ahav(x):
                    return math.acos(clamp(1 - 2 * x, -1, 1))

                hav_theta = hav(light_lat - latitude) + math.cos(
                    latitude) * math.cos(light_lat) * hav(light_lon - longitude)
                ang_diff = ahav(hav_theta)
                shade = clamp(ang_diff / (2 * math.pi * shadow_amount), 0, 1)

                pixel_colour.r = round(pixel_colour.r * shade)
                pixel_colour.g = round(pixel_colour.g * shade)
                pixel_colour.b = round(pixel_colour.b * shade)

            # Set the pixel
            sphere_surface.set_at((x, y), pixel_colour)

    return sphere_surface


# Usage example
if __name__ == "__main__":
    def main():
        plane_file = "output.png" if len(sys.argv) <= 1 else sys.argv[1]
        radius = 1200 if len(sys.argv) <= 2 else int(sys.argv[2])
        shade = 0.3 if len(sys.argv) <= 3 else float(sys.argv[3])

        plane = pygame.image.load(plane_file)

        p = project_image_to_sphere(surface=None, plane=plane,
                                    radius=radius, shadow_amount=shade)
        pygame.image.save(p, "sphere.png")
        pygame.quit()


    main()
