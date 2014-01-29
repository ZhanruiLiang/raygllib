from OpenGL.GL import *
from .model import Model, Material, Light
from .scene import Scene
from .render import Renderer, ShadowRenderer
from .camera import Camera
from . import matlib
from . import utils
from .utils import debug
from .panel import ControlPanel, LightControl
import collada
import pyglet


def load_scene(path):
    mesh = collada.Collada(path)
    scene = Scene()

    for node in mesh.scene.nodes:
        matrix = node.matrix
        node = node.children[0]
        debug(type(node))
        if isinstance(node, collada.scene.CameraNode):
            # camera = Camera(pos, (0, 0, 0), up)
            # scene.camera.append(camera)
            pass
        elif isinstance(node, collada.scene.GeometryNode):
            geom = node.geometry
            debug('load geometry:', geom.name)
            poly = geom.primitives[0]
            daeMat = mesh.materials[poly.material]
            if hasattr(daeMat.effect.diffuse, 'sampler'):
                diffuse = daeMat.effect.diffuse.sampler.surface.image.getImage()
                indexTupleSize = 3
                diffuseType = Material.DIFFUSE_TEXTURE
            else:
                indexTupleSize = 2
                diffuse = daeMat.effect.diffuse[:3]
                diffuseType = Material.DIFFUSE_COLOR
            material = Material(
                daeMat.name, diffuseType, diffuse,
                Ka=(daeMat.effect.ambient[:3]\
                    if not isinstance(daeMat.effect.ambient, collada.material.Map) else (0., 0., 0.)),
                Ks=daeMat.effect.specular[:3],
                shininess=daeMat.effect.shininess,
            )
            index = poly.index.flatten()
            index = index.reshape((len(index) // indexTupleSize, indexTupleSize))
            model = Model(
                poly.vertex[index[:, 0]],
                poly.normal[index[:, 1]],
                (poly.texcoordset[0][index[:, 2]] if indexTupleSize == 3 else None),
                material,
                matrix,
            )
            debug('load model:', model)
            # assert False
            scene.models.append(model)
        elif isinstance(node, collada.scene.LightNode):
            daeLight = node.light
            light = Light(matrix[0:3, 3], daeLight.color, 500)
            scene.lights.append(light)
    return scene

class Viewer:
    FPS = 60

    def __init__(self, path):
        self.panel = ControlPanel()
        self.panel.start()

        self.window = window = pyglet.window.Window(
            width=800, height=600, resizable=True, vsync=True,
            config=pyglet.gl.Config(sample_buffers=1, samples=4, stencil_size=8))
        glEnable(GL_DEPTH_TEST)
        glClearColor(.9, .9, .9, 1.)

        self.window = window
        self.renderer = Renderer()
        self.projMat = matlib.identity()
        self.camera = Camera((0, -10, 0), (0, 0, 0), (0, 0, 1))
        self.enableToonRender = True
        self.toonRenderEdges = [0.24845, 0.36646, 0.62733, 0.96894]

        self.panel.add_edges(self)

        with utils.timeit_context('load model'):
            self.scene = load_scene(path)

        for light in self.scene.lights:
            self.on_add_light(light)

        materials = []
        for model in self.scene.models:
            material = model.material
            if material in materials:
                continue
            self.panel.add_material(material)
            materials.append(material)

        self.scene.viewers.append(self)

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

        self.fpsDisplay = pyglet.clock.ClockDisplay()

        @window.event
        def on_draw():
            self.draw()

        @window.event
        def on_key_press(key, modifiers):
            self.on_key_press(key, modifiers)

        pyglet.clock.schedule_interval(self.update, 1 / self.FPS)

    def on_add_light(self, light):
        debug('on add light', light)
        self.panel.add_light(light)

    def on_key_press(self, key, modifiers):
        K = pyglet.window.key
        C = self.camera
        func = {
            K._1: C.front_view, K._2: C.back_view,
            K._3: C.left_view, K._4: C.right_view,
            K._5: C.top_view, K._6: C.bottom_view,
        }.get(key, None)
        if func:
            func()

    def update(self, dt):
        self.camera.update(dt)

    def draw(self):
        self.window.clear()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        R = self.renderer
        with ControlPanel.lock:
            with R.batch_draw():
                R.set_matrix('viewMat', self.camera.viewMat)
                R.set_matrix('projMat', self.projMat)
                if not self.enableToonRender:
                    R.set_step_edges([])
                else:
                    R.set_step_edges(self.toonRenderEdges)
                R.set_lights(self.scene.lights)
                for model in self.scene.models:
                    R.draw_model(model)

            glDisable(GL_DEPTH_TEST)
            self.fpsDisplay.draw()

    def show(self):
        pyglet.app.run()

class ShadowedViewer(Viewer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shadowRenderer = ShadowRenderer()

    def draw(self):
        self.window.clear()
        glClearColor(.0, .0, .0, 1.)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_STENCIL_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_ONE)
        glDepthFunc(GL_LEQUAL)

        r1 = self.renderer
        r2 = self.shadowRenderer

        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthMask(GL_TRUE)
        with r1.batch_draw():
            r1.set_matrix('viewMat', self.camera.viewMat)
            r1.set_matrix('projMat', self.projMat)
            r1.set_lights(self.scene.lights)
            for model in self.scene.models:
                r1.draw_model(model)
        for light in self.scene.lights:
            with r2.batch_draw():
                r2.set_light(light)
                r2.set_matrix('viewMat', self.camera.viewMat)
                r2.set_matrix('projMat', self.projMat)
                for model in self.scene.models:
                    r2.draw_model(model)
            # glDisable(GL_STENCIL_TEST)
            glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
            glDepthMask(GL_TRUE)
            with r1.batch_draw():
                r1.set_matrix('viewMat', self.camera.viewMat)
                r1.set_matrix('projMat', self.projMat)
                r1.set_lights([light])
                for model in self.scene.models:
                    r1.draw_model(model)

        glDisable(GL_DEPTH_TEST)
        self.fpsDisplay.draw()
