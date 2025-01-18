from typing import Union, List, Tuple, Optional

import numpy
import pygame

Point2 = numpy.ndarray  # must be 2x1 element column vector.
Vertices = list[Point2]


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
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.centre = numpy.array((surface.get_width() / 2,
                                   surface.get_height() / 2))

    def stroke(self, a: Point2, b: Point2, colour: pygame.Color, width: int):
        pygame.draw.line(self.surface, colour, a, b, width)

    def model_to_camera_space(self, points2d: numpy.ndarray) -> numpy.ndarray:
        return numpy.hstack((points2d, numpy.ones((points2d.shape[0], 1))))

    def camera_to_image_space(self, points3d: numpy.ndarray) -> numpy.ndarray:
        return points3d[:, :-1] * self.centre[0] + self.centre


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
    print(T)
    print(P)
    B = T @ BMatrix @ P
    print(B)
    return B


class Tile(object):
    def __init__(self,
                 vertices: Vertices,
                 branch_points: List[Tuple[float, float]],
                 connections: List[Tuple[int, int, int]],
                 background: pygame.Color = pygame.Color(0, 0, 0, 255)
                 ):
        """ Builds a polygonal tile that can draw itself.
        vertices: the vertices in anti-clockwise order.  These are in some
                  model space with a right-handed coordinate system.
        branch_points: each edge of the tile has a number of sites where
                  branches begin.  These are centred at the given fractions of
                  distance along the edges, and width a given fraction of the
                  distance along the edge.  If there are n branches they are
                  indexed as 0...n-1
        connections: a list of triples [from_edge, branch_index, to_edge]
        """
        self.background = background
        self.vertices = vertices
        self.connections = connections
        self.branch_points = branch_points
        self.N = len(vertices)

    @staticmethod
    def do_transform(point, transform):
        return point if transform is None else ([*point, 1.0] @ transform)[:-1]

    def draw(self,
             line_artist: LineArtist,
             colour: pygame.Color = pygame.color.THECOLORS['white'],
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
        normal_scale = 0.25
        for connection in self.connections:
            from_edge, branch_index, to_edge = connection
            a1, b1 = self.endpoints(from_edge, transform)
            a2, b2 = self.endpoints(to_edge, transform)
            n1 = self.edge_normal(a1, b1)
            n2 = self.edge_normal(a2, b2)
            centre = self.branch_points[branch_index][0]
            halfwidth = self.branch_points[branch_index][1] * 0.5

            def fraction_to_control_points_model(fraction: float):
                P1 = a1 + (b1 - a1) * branch_fraction
                P2 = a2 + (b2 - a2) * (1.0 - branch_fraction)
                N1 = P1 + n1 * numpy.linalg.norm(b1 - a1) * normal_scale
                N2 = P2 + n2 * numpy.linalg.norm(b2 - a2) * normal_scale
                return P1, N1, N2, P2

            # find the length of the base lines in pixels, and choose the max,
            # to estimate the number of samples required
            px_s = fraction_to_control_points_model(centre - halfwidth)
            px_f = fraction_to_control_points_model(centre + halfwidth)
            samples = 2 + 2 * max(numpy.linalg.norm(px_s[0] - px_s[3]),
                                  numpy.linalg.norm(px_f[0] - px_f[3]))
            for branch_fraction in numpy.linspace(centre - halfwidth,
                                                  centre + halfwidth, samples):
                control_points = fraction_to_control_points_model(
                    branch_fraction)
                ts = numpy.linspace(0.0, 1.0, 50)
                bs = bezier(P1, N1, N2, P2, ts)
                b0 = bs[0]
                for b in bs[1:]:
                    line_artist.stroke(b0, b, colour, 2)
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
        normal = numpy.array([[(a - b)[1], (b - a)[0]]])
        return normal / numpy.linalg.norm(normal)


import show_canvas

vertices = [
    numpy.array((100, 50), dtype=float),
    numpy.array((300, 50), dtype=float),
    numpy.array((250, 250), dtype=float),
    numpy.array((450, 450), dtype=float),
    numpy.array((100, 450), dtype=float),
    numpy.array((50, 250), dtype=float)
]

T1 = Tile(vertices=vertices,
          branch_points=[(0.5, 0.2)],
          connections=[(0, 0, 1), (2, 0, 4), (3, 0, 5)],
          background=pygame.Color(pygame.color.THECOLORS['blue']))

s = pygame.Surface((500, 500))
s.fill(color=pygame.Color(pygame.color.THECOLORS['black']))
T1.draw(PlaneLineArtist(s), pygame.Color(pygame.color.THECOLORS['pink']),
        numpy.array([[0.5, 0, 0], [0, 0.5, 0], [0, 0, 1]], numpy.float32))

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
show_canvas.show_canvas(s)
