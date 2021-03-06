from raygllib import Program, VertexBuffer
import pyglet
from OpenGL.GL import *
import numpy as np

window = pyglet.window.Window(resizable=True, width=800, height=600)

# init gl stuff
glClearColor(.1, .1, .1, 1)

program = Program([
    ('tests/simple.f.glsl', GL_FRAGMENT_SHADER),
    ('tests/simple.v.glsl', GL_VERTEX_SHADER),
], [
    ('vertex_pos', 2, GL_FLOAT),
])

points = VertexBuffer(np.array([
    (0, 0), (1, 0), (0, 1),
], dtype=GLfloat), GL_STATIC_DRAW)

label = pyglet.text.Label('Hello World', font_name='Times New Roman',
    font_size=20, x=100, y=200)

@window.event
def on_draw():
    window.clear()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    with program.batch_draw():
        program.set_buffer('vertex_pos', points)
        program.draw(GL_TRIANGLES, len(points))
    label.draw()
    print('TEXTURE: ', glIsEnabled(GL_TEXTURE_2D))
    print('draw')

pyglet.app.run()
