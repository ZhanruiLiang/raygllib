from OpenGL.GL import *
import pyglet

from .render import (
    Renderer, SilhouetteRenderer, WireframeRenderer
)
from .camera import Camera
from .panel import ControlPanel
from .model import Scene
# from .utils import debug
from ._threadutils import Require
from . import config


class Viewer:
    FPS = 30

    def __init__(self):
        self.require = Require(self)

        self.panel = ControlPanel()
        self.panel.start()

        self.window = window = pyglet.window.Window(
            width=800, height=600, resizable=True, vsync=True,
            config=pyglet.gl.Config(sample_buffers=1, samples=4))
        glEnable(GL_DEPTH_TEST)

        self.renderer = Renderer()

        self.silhouetteRenderer = SilhouetteRenderer()
        self.silhouetteEnable = config.silhouetteEnable
        self.silhouetteWidth = 0.01

        self.wireframeRenderer = WireframeRenderer()
        self.wireframeEnable = config.wireframeEnable

        self._scale = 1.
        self.camera = Camera((0, -10, 0), (0, 0, 0), (0, 0, 1))

        self.panel.add_misc(self)
        self.scene = None
        self.selectedJoint = None

        @window.event
        def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
            self.camera.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

        @window.event
        def on_mouse_scroll(x, y, xs, ys):
            self.camera.scale(1 + 0.05 * ys)

        @window.event
        def on_resize(w, h):
            self.camera.on_resize(w, h)

        self.fpsDisplay = pyglet.clock.ClockDisplay()

        @window.event
        def on_draw():
            self.draw()

        @window.event
        def on_key_press(key, modifiers):
            self.on_key_press(key, modifiers)

        pyglet.clock.schedule_interval(self.update, 1 / self.FPS)

    def load_scene(self, path):
        scene = Scene.load(path)
        if not scene.lights:
            scene.add_light()
        if scene.models:
            self.camera.set_target(scene.models[0])
        self.set_scene(scene)

    def set_scene(self, scene):
        clearCondition = self.panel.clearCondition
        with clearCondition:
            self.panel.clear()
            if not self.panel._cleared:
                clearCondition.wait()
        if self.scene is not None:
            self.scene.free()
        self.scene = scene
        self.scene.viewers.append(self)

        for light in self.scene.lights:
            self.on_add_light(light)

        materials = []
        for model in self.scene.models:
            material = model.geometry.material
            if material in materials:
                continue
            self.panel.add_material(material)
            materials.append(material)

        joints = []
        for model in self.scene.models:
            if hasattr(model, 'joints'):
                joints.extend(model.joints)
        self.panel.add_joints(self, joints)

    def on_add_light(self, light):
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
        with ControlPanel.lock:
            self.camera.update(dt)
            self.scene.update(dt)
        self.require.resolve()

    def draw(self):
        self.window.clear()
        R = self.renderer
        # Rs = self.silhouetteRenderer
        # Rw = self.wireframeRenderer
        models = self.scene.models
        with ControlPanel.lock:
            glClearColor(.9, .9, .9, 1.)
            # glClearColor(0, 0, 0, 1)
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glEnable(GL_DEPTH_TEST)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glCullFace(GL_BACK)

            with R.batch_draw():
                # if self.selectedJoint is None:
                #     glUniform1i(R.get_uniform_loc('targetJoint'), -1)
                # else:
                #     glUniform1i(R.get_uniform_loc('targetJoint'), self.selectedJoint.id)
                R.set_matrix('viewMat', self.camera.viewMat)
                R.set_matrix('projMat', self.camera.projMat)
                R.set_lights(self.scene.lights)
                for model in models:
                    R.draw_model(model)

            # if self.silhouetteEnable:
            #     with Rs.batch_draw():
            #         Rs.set_matrix('viewMat', self.camera.viewMat)
            #         Rs.set_matrix('projMat', self.camera.projMat)
            #         glUniform1f(Rs.get_uniform_loc('edgeWidth'), self.silhouetteWidth)
            #         for model in models:
            #             Rs.draw_model(model)

            # if self.wireframeEnable:
            #     with Rw.batch_draw():
            #         Rw.set_matrix('viewMat', self.camera.viewMat)
            #         Rw.set_matrix('projMat', self.camera.projMat)
            #         for model in models:
            #             Rw.draw_model(model)

            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glDisable(GL_DEPTH_TEST)
            self.fpsDisplay.draw()

    def show(self):
        pyglet.app.run()
