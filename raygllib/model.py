import pyximport
pyximport.install()

from OpenGL.GL import *
from .gllib import VertexBuffer, Texture2D, IndexBuffer
import numpy as np

from . import _model
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


class AdjacencyVertexBuffer:
    # @profile
    def __init__(self, vertices, indices):
        indices = indices.astype(GLuint)
        adjIndices = _model.make_adj_indices(indices)
        self.vertices = VertexBuffer(np.array(vertices, dtype=GLfloat), GL_STATIC_DRAW)
        self.indices = IndexBuffer(np.array(adjIndices, dtype=GLuint), GL_STATIC_DRAW)
        utils.debug('nVertices', len(vertices), 'nAdjIndices', len(self.indices))

    def bind(self):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indices.bufferId)

    def draw(self):
        glDrawElements(GL_TRIANGLES_ADJACENCY, len(self.indices), GL_UNSIGNED_INT, None) 


class Geometry:
    def __init__(self, name, vertices, normals, texcoords, indices, material):
        self.name = name
        self.vertices = VertexBuffer(
            np.array(vertices[indices[:, 0]], dtype=GLfloat), GL_STATIC_DRAW)
        self.normals = VertexBuffer(
            np.array(normals[indices[:, 1]], dtype=GLfloat), GL_STATIC_DRAW)
        if texcoords is not None:
            self.texcoords = VertexBuffer(
                np.array(texcoords[indices[:, 2]], dtype=GLfloat), GL_STATIC_DRAW)
        else:
            self.texcoords = None
        # with utils.timeit_context('Build AdjacencyVertexBuffer'):
        self.adjVertices = AdjacencyVertexBuffer(vertices, indices[:, 0])
        self.material = material

    def __repr__(self):
        return '{}(nVertices={})'.format(self.__class__.__name__, len(self.vertices))

    def free(self):
        self.vertices.free()
        self.normals.free()
        self.adjVertices.vertices.free()
        self.adjVertices.indices.free()
        if self.texcoords is not None:
            self.texcoords.free()
        if self.material.diffuseType == Material.DIFFUSE_TEXTURE:
            self.material.diffuse.free()

    def draw(self):
        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices))


class CompressedGeometry(Geometry):
    @staticmethod
    def make_single_index(bufs, index):
        h = {}
        n, m = index.shape
        newBufs = [np.zeros((n, buf.shape[1]), dtype=GLfloat) for buf in bufs]
        newIndex = np.zeros(n, dtype=GLuint)
        newBufSize = 0
        for i in range(n):
            # key = tuple(index[i])
            key = ()
            for j in range(m):
                key += tuple(bufs[j][index[i, j]])
            if key in h:
                newIndex[i] = h[key]
            else:
                for j in range(m):
                    newBufs[j][newBufSize] = bufs[j][index[i, j]]
                newIndex[i] = h[key] = newBufSize
                newBufSize += 1
        newBufs = [buf[:newBufSize] for buf in newBufs]
        utils.debug('compress: nBefore={}, nAfter={}, rate={}'.format(
            n, newBufSize, newBufSize / n))
        return newBufs, newIndex

    def __init__(self, name, vertices, normals, texcoords, indices, material):
        self.name = name
        self.material = material

        self.adjVertices = AdjacencyVertexBuffer(vertices, indices[:, 0])

        bufs = [vertices, normals, texcoords]\
            if texcoords is not None else [vertices, normals]
        with utils.timeit_context('Compress'):
            # newBufs, newIndex = self.make_single_index(bufs, indices)
            newBufs, newIndex = _model.make_single_index_1(bufs, indices)
        self.vertices = VertexBuffer(newBufs[0])
        self.normals = VertexBuffer(newBufs[1])
        if texcoords is not None:
            self.texcoords = VertexBuffer(newBufs[2])
        else:
            self.texcoords = None
        self.indices = IndexBuffer(newIndex)

    def free(self):
        super().free()
        self.indices.free()

    def draw(self):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indices.bufferId)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)


class Model:
    def __init__(self, name, geometry, matrix):
        self.name = name
        self.geometry = geometry
        self.matrix = matrix

    def update(self):
        pass


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
    MAX_POWER = 10
    MAX_RANGE = 100

    def __init__(self, pos, color, power):
        self.pos = pos
        self.color = color
        self.power = power
        self.enabled = True
