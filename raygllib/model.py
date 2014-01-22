from OpenGL.GL import *
from . import utils
from .gllib import VertexBuffer
import numpy as np

class Model:
    def __init__(self, vertices, normals, texcoords, material, matrix):
        self.vertices = VertexBuffer(np.array(vertices, dtype=GLfloat), GL_STATIC_DRAW)
        self.normals = VertexBuffer(np.array(normals, dtype=GLfloat), GL_STATIC_DRAW)
        self.texcoords = VertexBuffer(np.array(texcoords, dtype=GLfloat), GL_STATIC_DRAW)
        self.material = material
        self.matrix = matrix


class Material:
    """
    Attributes: Ns, Ka, Ks, Ni, d, illum
    """
    def __init__(self, name, image, **attrs):
        self.name = name
        for k, v in attrs.items():
            setattr(self, k, v)
        self._textureId = None
        self.image = image

    @property
    def textureId(self):
        if self._textureId is None:
            self._textureId = utils.make_texture(self.image, GL_TEXTURE_2D)
            del self.image
        return self._textureId

    def __repr__(self):
        return 'Material(name={})'.format(self.name)


class Light:
    def __init__(self, pos, color, power):
        self.pos = pos
        self.color = color
        self.power = power
