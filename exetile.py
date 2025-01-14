from typing import Union, List, Tuple

import numpy
import pygame

Point2 = numpy.ndarray  # must be 2x1 element column vector.
Vertices = list[Point2]


class LineArtist(object):
    def stroke(self, a: Point2, b: Point2, colour: pygame.Color, width: int):
        pass


BMatrix = numpy.array([[ 1, 0, 0, 0],
                       [-3, 3, 0, 0],
                       [ 3,-6, 3, 0],
                       [-1, 3,-3, 1]])

def bezier(P1, N1, N2, P2, ts):
    []

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

    def draw(self,
             transform: numpy.ndarray,
             line_artist: LineArtist,
             colour: pygame.Color):
        """ draw the tile given a projection matrix to image space. """
        for connection in self.connections:
            from_edge, branch_index, to_edge = connection
            a1, b1 = self.endpoints(from_edge)
            a2, b2 = self.endpoints(to_edge)
            n1 = self.edge_normal(a1, b1)
            n2 = self.edge_normal(a2, b2)
            # for now, just getting the centre
            branch_fraction = self.branch_points[branch_index][0]
            P1 = a1 + (b1 - a1) * branch_fraction
            P2 = a2 + (b2 - a2) * branch_fraction
            N1 = P1 + n1 * numpy.linalg.norm(b1 - a1)
            N2 = P2 + n2 * numpy.linalg.norm(b2 - a2)
            ts = numpy.linspace(0.0, 1.0, 10)
            tts = ts * ts
            ttts = ts * tts

                bezier(P1, N1, N2, P2, t)

    def endpoints(self, edge_index) -> Tuple[Point2, Point2]:
        """ the points defining the edge of given index [0..N-1] """
        return self.vertices[edge_index], self.vertices[
            (edge_index + 1) % self.N]

    def edge_normal(self, a: Point2, b: Point2):
        """ get the unit normal of an edge """
        normal = numpy.array([[(b - a)[1], (a - b)[0]]])
        return normal / numpy.linalg.norm(normal)

