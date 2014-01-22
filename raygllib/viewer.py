from OpenGL.GL import *
from .model import Model, Material, Light
from .scene import Scene
from .render import Renderer
from .camera import Camera
from . import matlib
from . import utils
import collada
import pyglet


def load_scene(path):
    mesh = collada.Collada(path)
    scene = Scene()

    for node in mesh.scene.nodes:
        matrix = node.matrix
        node = node.children[0]
        if isinstance(node, collada.scene.CameraNode):
            # camera = Camera(pos, (0, 0, 0), up)
            # scene.camera.append(camera)
            pass
        elif isinstance(node, collada.scene.GeometryNode):
            geom = node.geometry
            poly = geom.primitives[0]
            daeMat = mesh.materials[poly.material]
            image = daeMat.effect.diffuse.sampler.surface.image.getImage()
            material = Material(
                daeMat.name, image,
                Ka=daeMat.effect.ambient[:3],
                Ks=daeMat.effect.specular[:3],

                shininess=daeMat.effect.shininess,
            )
            model = Model(
                poly.vertex[poly.index[:, 0]],
                poly.normal[poly.index[:, 1]],
                poly.texcoordset[0][poly.index[:, 2]],
                material,
                matrix,
            )
            scene.models.append(model)
        elif isinstance(node, collada.scene.LightNode):
            daeLight = node.light
            light = Light(matrix[0:3, 3], daeLight.color, 500)
            scene.lights.append(light)
    return scene


class Viewer:
    def __init__(self, path):
        window = pyglet.window.Window(width=800, height=600, resizable=True,
            config=pyglet.gl.Config(sample_buffers=1, samples=4))
        glEnable(GL_DEPTH_TEST)
        glClearColor(.9, .9, .9, 1.)

        self.window = window
        self.renderer = Renderer()
        self.projMat = matlib.identity()
        self.camera = Camera((0, -10, 0), (0, 0, 0), (0, 0, 1))

        with utils.timeit_context('load model'):
            self.scene = load_scene(path)

        @window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            if self.camera:
                self.camera.drag(dx, dy)

        @window.event
        def on_mouse_scroll(x, y, xs, ys):
            if self.camera:
                self.camera.scale(0.05 * ys)

        @window.event
        def on_resize(w, h):
            self.projMat = matlib.ortho_view(-w / h, w / h, -1, 1, 0, 100)

        fpsDisplay = pyglet.clock.ClockDisplay()

        @window.event
        def on_draw():
            window.clear()
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            R = self.renderer
            with R.batch_draw():
                R.set_matrix('viewMat', self.camera.viewMat)
                R.set_matrix('projMat', self.projMat)
                self.scene.draw(self.renderer)

            fpsDisplay.draw()

    def show(self):
        pyglet.app.run()

    def add_light_auto(self):
        pass

    def add_camera_auto(self):
        pass
