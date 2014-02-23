import math
import os
from OpenGL.GL import *
import pyglet

from .render import (
    Renderer, SilhouetteRenderer, WireframeRenderer
)
from .camera import Camera
from .model import Scene
# from .utils import debug
from . import config
import raygllib.ui as ui
import pyglet.window.key as K

VERTICAL = ui.LayoutDirection.VERTICAL
HORIZONTAL = ui.LayoutDirection.HORIZONTAL

class PropsControl(ui.Widget):
    def __init__(self, title, props, **kwargs):
        super().__init__(layoutDirection=VERTICAL, **kwargs)
        self.children.append(ui.SubTitle(text=title, fontSize=12))

        self.propWidgets = {}
        for i, prop in enumerate(props):
            name, cls, attrs = prop
            label = ui.Label(
                text=name, align=ui.TextAlign.RIGHT, wrap=True, fixedSize=True, width=80)
            self.propWidgets[name] = edit = cls(**attrs)
            self.children.append(ui.Widget(
                layoutDirection=HORIZONTAL,
                children=[label, edit]))

class PositionControl(ui.Widget):
    def __init__(self, var, valRange):
        super().__init__(layoutDirection=VERTICAL)
        self.var = var
        for i, name in enumerate('xyz'):
            spin = ui.Spin(
                text=name, value=var[i], minValue=-valRange, maxValue=valRange)
            self.children.append(spin)
            spin.connect_signal('value-changed', self.update_value, spin, i)

    def update_value(self, spin, i):
        self.var[i] = spin.value


class LightControl(ui.Widget):
    def __init__(self, light):
        self.light = light
        super().__init__(fixedSize=True, height=100)
        enable = ui.Switch(text='Enable', active=light.enabled)
        power = ui.Spin(text='Power',
            value=light.power, minValue=0, maxValue=light.MAX_POWER, digits=1)
        position = PositionControl(var=light.pos, valRange=light.MAX_RANGE)
        self.children.extend([enable, power, position])
        enable.connect_signal('toggled', self.update_enable, enable)
        power.connect_signal('value-changed', self.update_power, power)

    def update_enable(self, switch):
        self.light.enabled = switch.active

    def update_power(self, spin):
        self.light.power = float(spin.value)


class ColorAdjust(ui.ColorPicker):
    def __init__(self, target, prop):
        super().__init__(color=ui.Color(*getattr(target, prop)))
        self.connect_signal('value-changed',
            lambda: setattr(target, prop, tuple(self.color)[:3]))


class MaterialControl(PropsControl):
    def __init__(self, material):
        self.material = material
        props = [
            ('ambient', ColorAdjust, dict(target=material, prop='Ka')),
            ('specular', ColorAdjust, dict(target=material, prop='Ks')),
            ('shininess', ui.Spin, dict(
                value=material.shininess, minValue=0,
                maxValue=material.MAX_SHININESS, digits=0)),
        ]
        if material.diffuseType == material.DIFFUSE_COLOR:
            props.append(
                ('diffuse', ColorAdjust, dict(target=material, prop='diffuse')))
        super().__init__(material.name, props, fixedSize=0, height=280)
        widgets = self.propWidgets
        widgets['shininess'].connect_signal(
            'value-changed', self.update_shininess, widgets['shininess'])

    def update_shininess(self, spin):
        self.material.shininess = float(spin.value)


class EdgesControl(ui.Widget):
    def __init__(self, viewer):
        BUTTON_WIDTH = 72

        super().__init__(layoutDirection=VERTICAL)
        self.viewer = viewer
        # Title
        self.children.append(ui.SubTitle(text='##Toon Edges'))
        # The first row
        enable = ui.Switch(text='Enable', fixedSize=True, width=80,
            active=viewer.canvas.renderer.toonRenderEnable)
        enable.connect_signal('toggled', self.update_enable, enable)

        insertButton = ui.Button(text='Insert', fixedSize=True, width=BUTTON_WIDTH)
        removeButton = ui.Button(text='Remove', fixedSize=True, width=BUTTON_WIDTH)
        copyButton = ui.Button(text='Copy', fixedSize=True, width=BUTTON_WIDTH)
        self.children.append(ui.Widget(
            layoutDirection=HORIZONTAL, fixedSize=True, height=18,
            children=[enable, insertButton, removeButton, copyButton]))
        insertButton.connect_signal('clicked', self.insert_edge, .5)
        removeButton.connect_signal('clicked', self.remove_edge)
        copyButton.connect_signal('clicked', self.copy)
        # Edges controllers
        self.edgeList = ui.Widget(layoutDirection=VERTICAL)
        edges = viewer.canvas.renderer.toonRenderEdges
        viewer.canvas.renderer.toonRenderEdges = []
        for e in edges:
            self.insert_edge(e)
        self.children.append(self.edgeList)

    def copy(self):
        print([x.value for x in self.edgeList.children])

    def update_enable(self, switch):
        self.viewer.canvas.renderer.toonRenderEnable = switch.active

    def update_value(self, index, value):
        self.viewer.canvas.renderer.toonRenderEdges = [
            x.value for x in self.edgeList.children]

    def insert_edge(self, value):
        edge = ui.Spin(
            value=value, minValue=0., maxValue=1., digits=5, fixedSize=True, height=20)
        edges = self.viewer.canvas.renderer.toonRenderEdges
        if len(edges) < config.maxToonEdges:
            self.edgeList.children.append(edge)
            edges.append(value)
            edges.sort()
            self.edgeList.request_relayout()

    def remove_edge(self):
        edges = self.viewer.canvas.renderer.toonRenderEdges
        if len(edges > 1):
            edges.pop()
            self.edgeList.children.pop()
            self.edgeList.request_relayout()


class JointControl(ui.Widget):
    def __init__(self, viewer, joints):
        super().__init__(layoutDirection=VERTICAL)
        self.children.append(ui.SubTitle(text='##Joints Control'))
        self.viewer = viewer
        self.joints = joints
        for joint in sorted(joints, key=lambda joint: joint.name):
            scale = ui.Spin(
                text=joint.name, value=0, minValue=-180, maxValue=180, digits=1,
                fixedSize=False, height=18, fontSize=14)
            scale.connect_signal('value-changed', self.update_angle, scale, joint)
            self.children.append(scale)

    def update_angle(self, scale, joint):
        self.viewer.selectedJoint = joint
        # debug('seleted', joint)
        joint.angle = scale.value / 180 * math.pi


class SilhouetteControl(ui.Widget):
    def __init__(self, viewer):
        super().__init__(layoutDirection=VERTICAL)
        self.children.append(ui.SubTitle(text='##Silhoette Control'))
        self.viewer = viewer

        enable = ui.Switch(text='Enable', active=viewer.canvas.silhouetteEnable)
        enable.connect_signal('toggled', self.update_enable, enable)
        self.children.append(enable)

        edgeWidth = ui.Spin(
            text='Width', digits=3, fixedSize=True, height=18,
            value=viewer.canvas.silhouetteWidth, minValue=0.001, maxValue=0.1,
        )
        edgeWidth.connect_signal('value-changed', self.update_edge_width, edgeWidth)
        self.children.append(edgeWidth)

    def update_enable(self, switch):
        self.viewer.canvas.silhouetteEnable = switch.active

    def update_edge_width(self, widget):
        self.viewer.canvas.silhouetteWidth = widget.value


class FileLoader(ui.Widget):
    def __init__(self, viewer):
        super().__init__(layoutDirection=VERTICAL)
        self.viewer = viewer
        pathInput = ui.PathInput(
            hint='Input path to load scene', fixedSize=True, height=40)
        self.children.append(pathInput)
        pathInput.connect_signal('open', self.load, pathInput)

    def load(self, pathInput):
        filename = os.path.expanduser(pathInput.text)
        self.viewer.load_scene(filename)

class Group(ui.Panel):
    def __init__(self, title):
        super().__init__(layoutDirection=VERTICAL)
        self.children.append(ui.Title(text=title))


class ControlPanel(ui.Widget):
    def __init__(self, fixedSize=False, width=400, **kwargs):
        super().__init__(layoutDirection=HORIZONTAL, **kwargs)
        self._col1 = ui.Widget(fixedSize=True, width=300)
        # self._col2 = ui.Widget(fixedSize=True, width=200)
        self.children.append(self._col1)
        # self.children.append(self._col2)
        self.clear()

    def add_control(self, group, control):
        self.groups[group].children.append(control)

    def clear(self):
        self._col1.children = []
        # self._col2.children = []
        self.groups = groups = {
            'misc': Group(title='#Misc'),
            'joints': Group(title='#Joints'),
            'lights': Group(title='#Lights'),
            'materials': Group(title='#Materials'),
        }
        for name in ('misc', 'lights', 'materials', 'joints'):
            self._col1.children.append(groups[name])
        # for name in ('joints',):
        #     self._col2.children.append(groups[name])


class ViewerCanvas(ui.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scene = None

        self.renderer = Renderer()

        self.silhouetteRenderer = SilhouetteRenderer()
        self.silhouetteEnable = config.silhouetteEnable
        self.silhouetteWidth = 0.01

        self.wireframeRenderer = WireframeRenderer()
        self.wireframeEnable = config.wireframeEnable

        self._scale = 1.
        self.camera = Camera((0, -10, 0), (0, 0, 0), (0, 0, 1))

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.camera.on_mouse_drag(x, y, dx, dy, buttons, modifiers)

    def on_mouse_scroll(self, x, y, xs, ys):
        self.camera.scale(1 + 0.05 * ys)

    def on_relayout(self):
        super().on_relayout()
        self.camera.on_resize(self.width, self.height)

    def on_key_press(self, key, modifiers):
        super().on_key_press(key, modifiers)
        C = self.camera
        func = {
            K._1: C.front_view, K._2: C.back_view,
            K._3: C.left_view, K._4: C.right_view,
            K._5: C.top_view, K._6: C.bottom_view,
        }.get(key, None)
        if func:
            func()

    def draw(self):
        scene = self.scene
        camera = self.camera
        models = scene.models

        R = self.renderer
        Rs = self.silhouetteRenderer
        # Rw = self.wireframeRenderer
        glEnable(GL_DEPTH_TEST)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        # glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glCullFace(GL_BACK)
        glDisable(GL_BLEND)

        with R.batch_draw():
            # if self.selectedJoint is None:
            #     glUniform1i(R.get_uniform_loc('targetJoint'), -1)
            # else:
            #     glUniform1i(R.get_uniform_loc('targetJoint'), self.selectedJoint.id)
            R.set_matrix('viewMat', camera.viewMat)
            R.set_matrix('projMat', camera.projMat)
            # print(camera.projMat.dot(camera.viewMat).dot([0, 0, 0, 1]))
            R.set_lights(scene.lights)
            for model in models:
                R.draw_model(model)

        if self.silhouetteEnable:
            with Rs.batch_draw():
                Rs.set_matrix('viewMat', camera.viewMat)
                Rs.set_matrix('projMat', camera.projMat)
                glUniform1f(Rs.get_uniform_loc('edgeWidth'), self.silhouetteWidth)
                for model in models:
                    Rs.draw_model(model)

        # if self.wireframeEnable:
        #     with Rw.batch_draw():
        #         Rw.set_matrix('viewMat', camera.viewMat)
        #         Rw.set_matrix('projMat', camera.projMat)
        #         for model in models:
        #             Rw.draw_model(model)

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
        glDisable(GL_DEPTH_TEST)

class Viewer(ui.Window):
    FPS = 30

    def __init__(self, resizable=True, **kwargs):
        super().__init__(resizable=resizable, color=ui.Color(0x111111), **kwargs)
        self.scene = None
        self.selectedJoint = None

        self.panel = ControlPanel()
        self.canvas = ViewerCanvas()

        self.root.layoutDirection = HORIZONTAL
        self.root.color = self.color.copy()
        self.root.children.append(self.panel)
        self.root.children.append(self.canvas)

        pyglet.clock.schedule_interval(self.update, 1 / self.FPS)

    def load_scene(self, path):
        scene = Scene.load(path)
        if not scene.lights:
            scene.add_light()
        if scene.models:
            self.camera.set_target(scene.models[0])
        self.set_scene(scene)

    @property
    def camera(self):
        return self.canvas.camera

    def set_scene(self, scene):
        panel = self.panel
        panel.clear()
        # self.panel.add_control('misc', CameraControl(self))
        panel.add_control('misc', FileLoader(self))
        panel.add_control('misc', SilhouetteControl(self))
        panel.add_control('misc', EdgesControl(self))

        self.canvas.camera.set_target(None)
        if self.scene is not None:
            self.scene.free()
        self.canvas.scene = self.scene = scene

        for light in scene.lights:
            panel.add_control('lights', LightControl(light))

        materials = []
        for model in scene.models:
            material = model.geometry.material
            if material in materials:
                continue
            # panel.add_control('materials', MaterialControl(material))
            materials.append(material)

        joints = []
        for model in scene.models:
            if hasattr(model, 'joints'):
                joints.extend(model.joints)
        panel.add_control('joints', JointControl(self, joints))
        self.request_relayout()

    def update(self, dt):
        super().update(dt)
        self.camera.update(dt)
        self.scene.update(dt)
