from OpenGL.GL import *
from . import utils
from .gllib import VertexBuffer
import numpy as np


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
    def __init__(self, vertices, normals, texcoords, material, matrix):
        self.bbox = get_bound_box(np.array(vertices, dtype=GLfloat))
        self.vertices = VertexBuffer(np.array(vertices, dtype=GLfloat), GL_STATIC_DRAW)
        self.normals = VertexBuffer(np.array(normals, dtype=GLfloat), GL_STATIC_DRAW)
        if texcoords is not None:
            self.texcoords = VertexBuffer(np.array(texcoords, dtype=GLfloat), GL_STATIC_DRAW)
        else:
            self.texcoords = None
        self.material = material
        self.matrix = matrix

    def get_bbox(self):
        return self.bbox


class Material:
    """
    Attributes: Ns, Ka, Ks, Ni, d, illum
    """
    DIFFUSE_COLOR = 0
    DIFFUSE_TEXTURE = 1

    def __init__(self, name, diffuse_type, diffuse, **attrs):
        self.name = name
        for k, v in attrs.items():
            setattr(self, k, v)
        self.diffuseType = diffuse_type
        self.diffuse = diffuse
        self._textureId = None

    @property
    def textureId(self):
        if self._textureId is None:
            self._textureId = utils.make_texture(self.diffuse, GL_TEXTURE_2D)
            del self.diffuse
        return self._textureId

    def __repr__(self):
        return 'Material(name={}, diffuseType={})'.format(self.name, self.diffuseType)


class Light:
    def __init__(self, pos, color, power):
        self.pos = pos
        self.color = color
        self.power = power
