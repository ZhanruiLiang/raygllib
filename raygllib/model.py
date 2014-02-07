import pyximport
pyximport.install()

from OpenGL.GL import *
from .gllib import VertexBuffer, Texture2D, IndexBuffer
import numpy as np

from . import _model
from . import utils
from . import matlib as M
from .utils import debug

def vector(v):
    return np.array(v, dtype=np.float32)


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
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indices.glId)

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
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indices.glId)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)


class Model:
    def __init__(self, name, geometry, matrix):
        self.name = name
        self.geometry = geometry
        self.matrix = matrix

    def update(self):
        pass

    def free(self):
        pass


class Joint:
    def __init__(self, name, parent, invBindMatrix, matrix):
        self.name = name
        self.parent = parent
        self.invBindMatrix = invBindMatrix
        self._matrixOrigin = matrix.copy()
        self.matrix = matrix
        self._angle = 0.

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, angle):
        if np.abs(self._angle - angle) < 1e-4:
            return
        # m0 = self._matrixOrigin
        # self._angle = angle
        # R = M.rotate(angle, m0[:3, 3] / m0[3, 3], m0[:3, 0])
        # self.matrix = R.dot(m0)
        c = np.cos(angle)
        s = np.sin(angle)
        xy = (0, 1)
        self.matrix = self._matrixOrigin.copy()
        self.matrix[0:3, xy] =\
            self._matrixOrigin[0:3, xy].dot(np.array([[c, -s], [s, c]]))

    def update(self):
        if self.parent:
            self.globalMatrix = np.dot(self.parent.globalMatrix, self.matrix)
        else:
            self.globalMatrix = self.matrix

class ArmaturedModel:
    def __init__(self, name, geometry, matrix, vertexWeights, vertexJointIds, joints):
        """
        joints must be sorted in topology order.
        """
        self.name = name
        self.geometry = geometry
        self.matrix = matrix
        self.vertexWeights = VertexBuffer(vertexWeights)
        self.vertexJointIds = VertexBuffer(vertexJointIds)
        self.joints = joints

    def free(self):
        self.vertexWeights.free()
        self.vertexJointIds.free()

    def get_joint_matrices(self):
        joints = self.joints
        matrices = np.zeros((4 * len(joints), 4), dtype=GLfloat)
        for i, joint in enumerate(joints):
            joint.update()
            matrices[i * 4:i * 4 + 4, :] = \
                np.dot(joint.globalMatrix, joint.invBindMatrix).T
        # debug(utils.format_matrix(matrices))
        return matrices.flatten()

    # def validate(self):
    #     joints = self.joints
    #     for joint in joints:
    #         joint.update()
    #         debug(utils.format_matrix(joint.matrix.dot(joint.invBindMatrix)))

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
        self.pos = vector(pos)
        self.color = color
        self.power = power
        self.enabled = True
