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
        Model space is assumed to be in [-1,1] x [-1,1]
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
                 background: pygame.Color = pygame.Color(0, 0, 0, 255)
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
        """
        self.background = background
        self.vertices = vertices
        self.ribbons = ribbons
        self.branch_points = branch_points
        self.N = len(vertices)

    @staticmethod
    def do_transform(point, transform):
        return point if transform is None else ([*point, 1.0] @ transform)[:-1]

    def draw(self,
             line_artist: LineArtist,
             colourspec=pygame.color.THECOLORS['white'],
             transform: numpy.ndarray = None):
        """ draw the tile given a projection matrix to image space. """
        for i in range(self.N):
            line_artist.stroke(a=self.do_transform(self.vertices[i], transform),
                               b=self.do_transform(
                                   self.vertices[(i + 1) % self.N], transform),
                               colour=pygame.Color(
                                   pygame.color.THECOLORS['green']),
                               width=2)
        # fraction of the normal to the separation
        normal_scale = 0.5
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
                normal_size = numpy.linalg.norm(P2 - P1) * normal_scale
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
                for b in bs[1:]:
                    line_artist.stroke(
                        b0, b, expand_colour(colourspec, frac), 2)
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
    N = 5
    vertices = []
    for i in range(N):
        theta = 2 * i * math.pi / N
        vertices.append(numpy.array((math.cos(theta), math.sin(theta))))

    T1 = Tile(vertices=vertices,
              branch_points=[(1 / 4, 1 / 3), (3 / 4, 1 / 3)],
              ribbons=
                  list([(i, 0, (i+1)%N, 1) for i in range(N)]),
              # [
              #     (0, 0, 1, 0), (0, 1, 2, 1), (1, 1, 2, 0)
              #     # (0, 0, 1, 1), (2, 0, 4, 1), (3, 0, 6, 1), (5, 0, 7, 1),
              #     # (0, 1, 0, 0), (2, 1, 4, 0), (3, 1, 6, 0), (5, 1, 7, 0)
              # ],
              background=pygame.Color(pygame.color.THECOLORS['blue']))

    s = pygame.Surface((500, 500))
    s.fill(color=pygame.Color(pygame.color.THECOLORS['black']))
    T1.draw(PlaneLineArtist(s), rainbow)
    show_canvas.show_canvas(s)
    return s


# T1.draw(PlaneLineArtist(s), pygame.Color(pygame.color.THECOLORS['magenta']))


# s = pygame.Surface((500, 500), flags=pygame.SRCALPHA)
# s.fill(pygame.Color(0, 0, 0, 255))
# ts = numpy.linspace(0.0, 1.0, 30)
# pygame.draw.circle(s, pygame.color.THECOLORS['blue'], P1, 5, 0)
# pygame.draw.circle(s, pygame.color.THECOLORS['blue'], N1, 5, 0)
# pygame.draw.circle(s, pygame.color.THECOLORS['blue'], N2, 5, 0)
# pygame.draw.circle(s, pygame.color.THECOLORS['blue'], P2, 5, 0)
# bs = bezier(P1, N1, N2, P2, ts)
# print(bs.shape)
# print(bs)
# b0 = bs[0]
# for b in bs[1:]:
#     pygame.draw.line(s, pygame.color.THECOLORS['white'], b0, b, 1)
#     b0 = b


##############################################################################
# Examples

# rainbow_hex_tile()

multiple_ribbons_tile()
