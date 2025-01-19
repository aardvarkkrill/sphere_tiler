import random
from typing import Union, List, Tuple, Optional
import math

import numpy
import pygame

import show_canvas

Point2 = numpy.ndarray  # must be 2x1 element column vector.
Vertices = list[Point2]


def expand_colour(colourspec, *params):
    if isinstance(colourspec, pygame.Color) or len(params) == 0:
        return colourspec
    else:
        return expand_colour(colourspec(params[0]), *params[1:])


class LineArtist(object):
    def stroke(self, a: Point2, b: Point2, colour: pygame.Color, width: int):
        pass

    def fill(self, points: List[Point2], colour: pygame.Color):
        pass

    # given 2D points as row vectors, converts each one in to camera space as
    # 3D row vectors
    def model_to_camera_space(self, points2d: numpy.ndarray) -> numpy.ndarray:
        pass

    # given 3D points in camera space, converts each one in to image space as
    # 2D row vectors of pixel coordinates
    def camera_to_image_space(self, points3d: numpy.ndarray) -> numpy.ndarray:
        pass


class PlaneLineArtist(LineArtist):
    """ An artist which maps 2D model space to the Euclidean plane.
        Model space is assumed to be [-1,1] x [-1,1]
        Fits the model space to the width of the surface.
    """

    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.centre = numpy.array((surface.get_width() / 2,
                                   surface.get_height() / 2))
        # y points down, so invert
        # NOTE: still scale by half width, not half height!
        self.scalexy = numpy.array([self.centre[0], -self.centre[0]])

    def stroke(self, a: Point2, b: Point2, colour: pygame.Color, width: int):
        ai = self.camera_to_image_space(self.model_to_camera_space(a))
        bi = self.camera_to_image_space(self.model_to_camera_space(b))
        pygame.draw.line(self.surface, colour, ai, bi, width)

    def fill(self, points: List[Point2], colour: pygame.Color):
        ps = list(self.camera_to_image_space(self.model_to_camera_space(p))
                  for p in points)
        pygame.draw.polygon(self.surface, colour, ps, 0)

    def model_to_camera_space(self, points2d: numpy.ndarray) -> numpy.ndarray:
        if points2d.ndim == 1:
            return numpy.array((*points2d, 1.0))
        else:
            return numpy.hstack((points2d, numpy.ones((points2d.shape[0], 1))))

    def camera_to_image_space(self, points3d: numpy.ndarray) -> numpy.ndarray:
        if points3d.ndim == 1:
            return points3d[:-1] * self.scalexy + self.centre
        else:
            return points3d[:, :-1] * self.scalexy + self.centre


BMatrix = numpy.array([[1, 0, 0, 0],
                       [-3, 3, 0, 0],
                       [3, -6, 3, 0],
                       [-1, 3, -3, 1]], dtype=float)


def bezier(P1, N1, N2, P2, ts):
    # numpy treats 1-axis vectors as row vectors.
    tsquareds = ts * ts
    T = numpy.vstack(
        [numpy.ones(ts.shape), ts, tsquareds, tsquareds * ts]).transpose()
    P = numpy.vstack((P1, N1, N2, P2))
    B = T @ BMatrix @ P
    return B


class Tile(object):
    def __init__(self,
                 vertices: Vertices,
                 branch_points: List[Tuple[float, float]],
                 ribbons: List[Tuple[int, int, int, int]],
                 background: pygame.Color = None,
                 normal_scale: float = 0.5
                 ):
        """ Builds a polygonal tile that can draw itself.
        vertices: the vertices in anti-clockwise order.  These are in some
                  model space [-1,1]^2 with a right-handed coordinate system.
        branch_points: each edge of the tile has a number of sites where
                  ribbons begin.  These are centred at the given fractions of
                  distance along the edges, and width a given fraction of the
                  distance along the edge.  If there are n branch points they
                  are indexed as 0...n-1
        ribbons: a list of tuplss (from_edge, from_branch_index,
                                   to_edge, to_branch_index)
        normal_scale = fraction of the normal to the separation between the
                endpoints.  Affects the curviness of the ribbons.  Large
                values can cause the ribbon to extend outside the polygon.
                Small values make the curves too floppy.
        """
        self.background = background
        self.vertices = vertices
        self.ribbons = ribbons
        self.branch_points = branch_points
        self.N = len(vertices)
        self.normal_scale = normal_scale

    @staticmethod
    def do_transform(point, transform):
        return point if transform is None else ([*point, 1.0] @ transform)[:-1]

    def draw(self,
             line_artist: LineArtist,
             colourspec=pygame.color.THECOLORS['white'],
             transform: numpy.ndarray = None,
             ):
        """ draw the tile given a projection matrix to image space.
        """
        for i in range(self.N):
            line_artist.stroke(a=self.do_transform(self.vertices[i], transform),
                               b=self.do_transform(
                                   self.vertices[(i + 1) % self.N], transform),
                               colour=pygame.Color(
                                   pygame.color.THECOLORS['green']),
                               width=1)
        if self.background is not None:
            line_artist.fill(
                list(self.do_transform(p, transform) for p in self.vertices),
                self.background)

        for ribbon in self.ribbons:
            from_edge, from_branch_index, to_edge, to_branch_index = ribbon
            a1, b1 = self.endpoints(from_edge, transform)
            a2, b2 = self.endpoints(to_edge, transform)
            n1 = self.edge_normal(a1, b1)
            n2 = self.edge_normal(a2, b2)
            branch_centre1 = self.branch_points[from_branch_index][0]
            branch_centre2 = self.branch_points[to_branch_index][0]
            halfwidth1 = self.branch_points[from_branch_index][1] * 0.5
            halfwidth2 = self.branch_points[to_branch_index][1] * 0.5

            def fraction_to_control_points_model(branch_fraction1_: float,
                                                 branch_fraction2_: float):
                P1 = a1 + (b1 - a1) * branch_fraction1_
                P2 = a2 + (b2 - a2) * branch_fraction2_
                normal_size = numpy.linalg.norm(P2 - P1) * self.normal_scale
                N1, N2 = P1 + n1 * normal_size, P2 + n2 * normal_size
                return P1, N1, N2, P2

            def image_pixel_positions_at_branch_fraction(
                    branch_fraction1_: float,
                    branch_fraction2_: float,
                    ts_: numpy.ndarray):
                controls = fraction_to_control_points_model(branch_fraction1_,
                                                            branch_fraction2_)
                interpolate = bezier(*controls, ts_)
                pixels = line_artist.camera_to_image_space(
                    line_artist.model_to_camera_space(interpolate))
                return pixels

            # find the length of the base lines in pixels, and choose the max,
            # to estimate the number of samples required across the ribbon
            pixels_at_ribbon_edge0 = image_pixel_positions_at_branch_fraction(
                branch_centre1 - halfwidth1,
                branch_centre2 + halfwidth2,
                numpy.array([0.0, 0.5, 1.0])
            )
            pixels_at_ribbon_edge1 = image_pixel_positions_at_branch_fraction(
                branch_centre1 + halfwidth1,
                branch_centre2 - halfwidth2,
                numpy.array([0.0, 0.5, 1.0])
            )
            est_max_distance = max([numpy.linalg.norm(p0 - p1) for (p0, p1) in
                                    zip(pixels_at_ribbon_edge0,
                                        pixels_at_ribbon_edge1)])
            samples = round(2 + 2 * est_max_distance)
            for frac in numpy.linspace(-1.0, 1.0, samples):
                branch_fraction1 = branch_centre1 + frac * halfwidth1
                branch_fraction2 = branch_centre2 - frac * halfwidth2
                control_points = fraction_to_control_points_model(
                    branch_fraction1, branch_fraction2)
                ts = numpy.linspace(0.0, 1.0, 50)
                bs = bezier(*control_points, ts)
                b0 = bs[0]
                for i in range(1, len(ts)):
                    b = bs[i]
                    line_artist.stroke(
                        b0, b, expand_colour(colourspec, frac, ts[i]), 1)
                    b0 = b

    def endpoints(self, edge_index: int,
                  transform: Optional[numpy.ndarray] = None) -> Tuple[
        Point2, Point2]:
        """ the points defining the edge of given index [0..N-1] """
        a, b = self.vertices[edge_index], self.vertices[
            (edge_index + 1) % self.N]
        if transform is None:
            return a, b
        else:
            # we're doing (transform @ ([a,1][b,1]).transpose).transpose:
            ta, tb = numpy.array([[*a, 1], [*b, 1]]) @ transform
            return ta[:-1], tb[:-1]

    def edge_normal(self, a: Point2, b: Point2):
        """ get the unit normal of an edge """
        normal = numpy.array([(a - b)[1], (b - a)[0]])
        return normal / numpy.linalg.norm(normal)


def rainbow(fraction: float) -> pygame.Color:
    c = pygame.Color(0)
    c.hsva = (
        abs(fraction) * 360, 100, 100,
        100)  # HSV: hue, saturation, value, alpha
    return c


def rainbow_length(fraction: float):
    def f(ribbon_fraction: float) -> pygame.Color:
        c = pygame.Color(0)
        c.hsva = (
            abs(ribbon_fraction) * 360, 100, 100,
            100)  # HSV: hue, saturation, value, alpha
        return c

    return f


def regular_tile_maker(N: int, centre: Point2, scale: float, rotate: int,
                       reflect: bool,
                       background=None,
                       branch_points=None,
                       ribbons=None
                       ) -> Tile:
    vertices = []
    flip = -1 if reflect else +1
    for i in range(N):
        theta = 2 * (i + rotate) * math.pi / N
        vertices.append(
            centre + scale * numpy.array((math.cos(theta),
                                          flip * math.sin(theta))))
    if reflect:
        vertices.reverse()

    if branch_points is None:
        branch_points = [(1 / 4, 1 / 4), (3 / 4, 1 / 4)]
    if ribbons is None:
        ribbons = list((i, 0, (i + 1) % N, 1) for i in range(N))
    return Tile(vertices=vertices,
                branch_points=branch_points,
                ribbons=ribbons,
                background=background)


def diamond_tile_maker(centre: Point2, scale: float, rotate: int,
                       reflect: bool,
                       background=None,
                       branch_points=None,
                       ribbons=None) -> Tile:
    half_height = scale * math.sqrt(3) / 2
    half_width = scale / 2
    flipx = -1 if reflect else +1
    vertices = numpy.array([
        [flipx * half_width, 0],
        [0, half_height],
        [- flipx * half_width, 0],
        [0, -half_height]
    ])
    vertices = vertices + centre
    # diamond tiles have only 2 rotations
    vertices = numpy.roll(vertices, rotate * 2, 0)
    if reflect:
        # put vertices in positive orientation
        vertices = numpy.flip(vertices, 0)

    if branch_points is None:
        branch_points = [(1 / 4, 1 / 4), (3 / 4, 1 / 4)]
    if ribbons is None:
        ribbons = [(0, 0, 2, 1), (0, 1, 1, 0), (1, 1, 3, 0), (2, 0, 3, 1)]
    return Tile(vertices=list(vertices),
                branch_points=branch_points,
                ribbons=ribbons,
                background=background,
                normal_scale=0.3)


###############################################################################
# Examples

def rainbow_hex_tile():
    N = 6
    vertices = []
    for i in range(N):
        theta = 2 * i * math.pi / N
        vertices.append(numpy.array((math.cos(theta), math.sin(theta))))

    T1 = Tile(vertices=vertices,
              branch_points=[(0.5, 1.0)],
              ribbons=[(0, 0, 1, 0), (2, 0, 4, 0), (3, 0, 5, 0)],
              background=pygame.Color(pygame.color.THECOLORS['blue']))

    s = pygame.Surface((500, 500))
    s.fill(color=pygame.Color(pygame.color.THECOLORS['black']))
    T1.draw(PlaneLineArtist(s), rainbow)
    show_canvas.show_canvas(s)
    return s


def multiple_ribbons_tile():
    N = 6
    vertices = []
    for i in range(N):
        theta = 2 * i * math.pi / N
        vertices.append(numpy.array((math.cos(theta), math.sin(theta))))

    T1 = Tile(vertices=vertices,
              branch_points=[(1 / 4, 1 / 4), (3 / 4, 1 / 4)],
              ribbons=list((i, 0, (i + 1) % N, 1) for i in range(N)),
              background=None)

    s = pygame.Surface((500, 500))
    s.fill(color=pygame.Color(pygame.color.THECOLORS['black']))
    T1.draw(PlaneLineArtist(s), rainbow_length)
    show_canvas.show_canvas(s)
    return s


def hexagons_and_rhombii():
    tiles = []
    cols, rows = 12, 9
    tile_width = 2 / cols  # model space is [-1,+1]
    tile_radius = tile_width / 2
    tile_height = tile_width * math.sqrt(3) / 2
    xcentres = numpy.linspace(- 1 + tile_radius, 1 - tile_radius, cols)
    ycentres = numpy.linspace(- tile_height * (rows - 1) / 2,
                              tile_height * (rows - 1) / 2, rows)

    branch_points = [(1 / 4, 1 / 8), (3 / 4, 1 / 8)]

    def diamond(x, y, rot_, reflect_):
        return diamond_tile_maker(
            numpy.array((x, y)),
            tile_radius, rot_, reflect_, branch_points=branch_points)

    for x in xcentres:
        for y in ycentres:
            rot = random.randint(0, 5)
            reflect = random.choice((True, False))
            tiles.append(regular_tile_maker(
                6, numpy.array([x, y]), tile_radius, rot, reflect,
                branch_points=branch_points))
            tiles.append(diamond(
                x - tile_radius, y - tile_height / 2, rot, reflect))
            if x == xcentres[0]:
                tiles.append(
                    diamond(xcentres[-1] + tile_radius, y - tile_height / 2,
                            rot, reflect))
            if y == ycentres[0]:
                tiles.append(
                    diamond(x - tile_radius, ycentres[-1] + tile_height / 2,
                            rot, reflect))
            if x == xcentres[0] and y == ycentres[0]:
                tiles.append(diamond(xcentres[-1] + tile_radius,
                                     ycentres[-1] + tile_height / 2, rot,
                                     reflect))

    imsize = 1920
    s = pygame.Surface(
        (imsize, round(imsize * tile_height * rows / (cols * tile_width))))
    s.fill(color=pygame.Color(pygame.color.THECOLORS['black']))
    for tile in tiles:
        # tile.draw(PlaneLineArtist(s), rainbow_length)
        tile.draw(PlaneLineArtist(s), rainbow)
    show_canvas.show_canvas(s)
    pygame.image.save(s, 'hexagons_and_rhombii.jpg')
    return s


##############################################################################
# Examples

# rainbow_hex_tile()

# multiple_ribbons_tile()
hexagons_and_rhombii()
