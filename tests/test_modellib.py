import pyglet
from OpenGL.GL import *
import crash_on_ipy
import raygllib.matlib as M
import raygllib.utils as utils
from raygllib.camera import Camera
import raygllib.modellib as modellib
import threading

# Create OpenGL context and window
window = pyglet.window.Window(width=800, height=600, resizable=True,
    config=pyglet.gl.Config(sample_buffers=1, samples=4))

glEnable(GL_DEPTH_TEST)
glClearColor(.9, .9, .9, 1.)

program = modellib.ModelRenderer()
program.add_light(modellib.Light((2., 2., 20.), (1., 1., 1.), 600))
program.add_light(modellib.Light((-2., 2., 10.), (1., 1., 1.), 400))

modelMat = M.scale(1).dot(M.identity())
cam = Camera((3, 2, 5), (0, .0, 0), (0, 1, 0))
projMat = M.identity()

with utils.timeit_context('load model'):
    # model = modellib.load('tests/cube.obj')
    # model = modellib.load('/home/ray/graduate/src/models/men.obj')
    model = modellib.load('/home/ray/graduate/src/models/men-ani.obj')


def update(dt):
    pass
pyglet.clock.schedule_interval(update, 1 / 30)

@window.event
def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    cam.drag(dx, dy)

@window.event
def on_mouse_scroll(x, y, xs, ys):
    cam.scale(0.05 * ys)

@window.event
def on_resize(w, h):
    global projMat
    projMat = M.ortho_view(-w / h, w / h, -1, 1, 0, 100)

fpsDisplay = pyglet.clock.ClockDisplay()

@window.event
def on_draw():
    window.clear()
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    with program.batch_draw():
        program.set_MVP(modelMat, cam.viewMat, projMat)
        program.draw_model(model)
    glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

    fpsDisplay.draw()

# window.push_handlers(pyglet.window.event.WindowEventLogger())

from gi.repository import Gtk
class MyWindow(Gtk.Window):

    def __init__(self):
        Gtk.Window.__init__(self, title="Hello World")

        self.button = Gtk.Button(label="Click Here")
        self.button.connect("clicked", self.on_button_clicked)
        self.add(self.button)

    def on_button_clicked(self, widget):
        print("Hello World")

class App(threading.Thread):
    def run(self):

        win = MyWindow()
        win.connect("delete-event", Gtk.main_quit)
        win.show_all()
        Gtk.main()

# app = App()
# app.start()
# 
pyglet.app.run()
