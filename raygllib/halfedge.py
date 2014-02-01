import pyximport
pyximport.install()

from .gllib import VertexBuffer, IndexBuffer
from OpenGL.GL import GLfloat, GLuint, GL_STATIC_DRAW
import numpy as np
from . import _halfedge
from .utils import debug
# from . import _halfedgeptr as _halfedge

class AdjacencyVertexBuffer:
    # @profile
    def __init__(self, vertices, indices):
        indices = indices.astype(GLuint)
        adjIndices = _halfedge.make_adj_indices(indices)
        self.vertices = VertexBuffer(np.array(vertices, dtype=GLfloat), GL_STATIC_DRAW)
        self.indices = IndexBuffer(np.array(adjIndices, dtype=GLuint), GL_STATIC_DRAW)
        debug('nVertices', len(vertices), 'nAdjIndices', len(self.indices))
