from OpenGL.GL import *
from .gllib import VertexBuffer, Texture2D
from .halfedge import AdjacencyVertexBuffer
import numpy as np
from . import utils


def get_bound_box(vs):
    """
    :param np.ndarray vs: A list of vertices
    """
    m = vs.shape[1]
    result = ()
    for i in range(m):
        result += (vs[:, i].min(), vs[:, i].max())
    return result


class Model:
    def __init__(self, vertices, normals, texcoords, indices, material, matrix):
        self.bbox = get_bound_box(np.array(vertices, dtype=GLfloat))
        self.vertices = VertexBuffer(
            np.array(vertices[indices[:, 0]], dtype=GLfloat), GL_STATIC_DRAW)
        self.normals = VertexBuffer(
            np.array(normals[indices[:, 1]], dtype=GLfloat), GL_STATIC_DRAW)
        if texcoords is not None:
            self.texcoords = VertexBuffer(
                np.array(texcoords[indices[:, 2]], dtype=GLfloat), GL_STATIC_DRAW)
        else:
            self.texcoords = None
        with utils.timeit_context('Build AdjacencyVertexBuffer'):
            self.adjVertices = AdjacencyVertexBuffer(vertices, indices[:, 0])
        self.material = material
        self.matrix = matrix

    def __repr__(self):
        return 'Modle(nVertices={})'.format(len(self.vertices))

    def get_bbox(self):
        return self.bbox

    def free(self):
        self.vertices.free()
        self.normals.free()
        self.adjVertices.vertices.free()
        self.adjVertices.indices.free()
        if self.texcoords is not None:
            self.texcoords.free()
        if self.material.diffuseType == Material.DIFFUSE_TEXTURE:
            self.material.diffuse.free()


class Material:
    """
    Attributes: Ns, Ka, Ks, Ni, d, illum
    """
    DIFFUSE_COLOR = 0
    DIFFUSE_TEXTURE = 1

    MAX_SHININESS = 500

    def __init__(self, name, diffuse_type, diffuse, **attrs):
        self.name = name
        for k, v in attrs.items():
            setattr(self, k, v)
        self.diffuseType = diffuse_type
        self.diffuse = diffuse
        if self.diffuseType == self.DIFFUSE_TEXTURE:
            self.diffuse = Texture2D(diffuse)

    def __repr__(self):
        return 'Material(name={}, diffuseType={})'.format(self.name, self.diffuseType)


class Light:
    MAX_POWER = 5000
    MAX_RANGE = 100

    def __init__(self, pos, color, power):
        self.pos = pos
        self.color = color
        self.power = power
        self.enabled = True
