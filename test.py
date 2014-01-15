from raygllib import Program
import pyglet
from OpenGL.GL import *
import numpy as np

window = pyglet.window.Window(resizable=True, width=800, height=600)

# init gl stuff
glClearColor(1, 1, 1, 1)

program = Program([
    ('simple.f.glsl', GL_FRAGMENT_SHADER),
    ('simple.v.glsl', GL_VERTEX_SHADER),
])

program.init_buffers([
    ('vertex_pos', 2, GL_FLOAT),
])

points = np.array([
    (0, 0), (1, 0), (0, 1),
], dtype=GLfloat)

@window.event
def on_draw():
    program.use()
    program.set_buffer('vertex_pos', points)
    program.draw(GL_TRIANGLES, 3)

pyglet.app.run()
