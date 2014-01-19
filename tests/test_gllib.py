import unittest
import numpy as np
from raygllib import VertexBuffer
from OpenGL.GL import GL_STATIC_DRAW
import pyglet

class TestGllib(unittest.TestCase):
    def setUp(self):
        self.window = pyglet.window.Window()

    def test_vertex_buffer(self):
        import pickle
        vbo = VertexBuffer(np.array([1, 2, 3]))
        assert hasattr(vbo, 'data')
        assert hasattr(vbo, 'bufferId')
        s = pickle.dumps(vbo)
        vbo1 = pickle.loads(s)
        assert hasattr(vbo1, 'data')
        assert hasattr(vbo1, 'bufferId')

if __name__ == '__main__':
    unittest.main()
