from gi.repository import Gtk, Gdk
Gdk.threads_init()
from gi.repository import GLib
from threading import Thread, RLock, Condition
# from .utils import debug
from ._threadutils import Require
import math
import pickle

VERTICAL = Gtk.Orientation.VERTICAL
HORIZONTAL = Gtk.Orientation.HORIZONTAL

class VectorSpin(Gtk.Box):
    def __init__(self, var, valRange, normalize=False, orientation=VERTICAL):
        super().__init__(orientation=orientation)
        self.var = var
        self.normalize = normalize
        for i in range(min(3, len(var))):
            spin = Gtk.SpinButton(
                adjustment=Gtk.Adjustment(var[i], -valRange, valRange, 0.05),
                numeric=True, digits=3)
            self.pack_start(spin, True, True, 0)
            spin.connect('value-changed', self.update_var, i)

    def update_var(self, spin, i):
        with ControlPanel.lock:
            self.var[i] = spin.get_value()
            if self.normalize:
                self.var /= self.var.dot(self.var) ** .5


class GridControl(Gtk.Frame):
    def __init__(self, label):
        super().__init__(label=label, border_width=2)
        self.grid = Gtk.Grid(column_spacing=5, border_width=5)
        self.add(self.grid)


class BoxControl(Gtk.Frame):
    def __init__(self, label, orientation=VERTICAL):
        super().__init__(label=label, border_width=2)
        self.box = Gtk.Box(orientation=orientation)
        self.add(self.box)


class PropsControl(GridControl):
    def __init__(self, label, props):
        super().__init__(label)
        self.widgets = {}
        for i, prop in enumerate(props):
            name, cls, attrs = prop
            label = Gtk.Label(name, halign=Gtk.Align.END)
            self.grid.attach(label, 0, i, 1, 1)
            edit = cls(**attrs)
            self.grid.attach(edit, 1, i, 1, 1)
            self.widgets[name] = edit


class LightControl(PropsControl):
    def __init__(self, light):
        self.light = light
        props = [
            ('enable', Gtk.Switch, dict(active=light.enabled)),
            ('power', Gtk.SpinButton, dict(
                adjustment=Gtk.Adjustment(light.power, 0, light.MAX_POWER, 0.2),
                numeric=True, digits=1)),
            ('pos', VectorSpin,
                dict(var=light.pos, valRange=light.MAX_RANGE, normalize=False)),
        ]
        super().__init__('', props)
        widgets = self.widgets
        widgets['enable'].connect('notify::active', self.update_enable)
        widgets['power'].connect('value-changed', self.update_power)

    def update_enable(self, button, *args):
        with ControlPanel.lock:
            self.light.enabled = button.get_active()

    def update_power(self, spin):
        with ControlPanel.lock:
            self.light.power = float(spin.get_value())


class ColorAdjust(Gtk.ColorButton):
    def __init__(self, target, prop):
        super().__init__(color=Gdk.Color.from_floats(*getattr(target, prop)))

        def update_color(colorButton):
            setattr(target, prop, colorButton.get_color().to_floats())

        self.connect('color-set', update_color)


class MaterialControl(PropsControl):
    def __init__(self, material):
        self.material = material
        props = [
            ('name', Gtk.Entry, dict(text=material.name, editable=False)),
            ('ambient', ColorAdjust, dict(target=material, prop='Ka')),
            ('specular', ColorAdjust, dict(target=material, prop='Ks')),
            ('shininess', Gtk.SpinButton, dict(
                adjustment=Gtk.Adjustment(
                    material.shininess, 0, material.MAX_SHININESS, 1),
                numeric=True, digits=0)),
        ]
        if material.diffuseType == material.DIFFUSE_COLOR:
            props.append(
                ('diffuse', ColorAdjust, dict(target=material, prop='diffuse')))
        super().__init__('', props)
        widgets = self.widgets
        widgets['shininess'].connect('value-changed', self.update_shininess)

    def update_shininess(self, spin):
        self.material.shininess = float(spin.get_value())


class EdgesControl(GridControl):
    def __init__(self, viewer):
        super().__init__('Edges Control')
        self.viewer = viewer

        self.grid.attach(Gtk.Label('Enable'), 0, 0, 1, 1)
        enable = Gtk.Switch(active=viewer.renderer.toonRenderEnable)
        enable.connect('notify::active', self.update_enable)
        insertButton = Gtk.Button('Insert')
        removeButton = Gtk.Button('Remove')
        for i, widget in enumerate((enable, insertButton, removeButton)):
            self.grid.attach(widget, 1 + i, 0, 1, 1)

        self.edgeList = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        edges = viewer.renderer.toonRenderEdges
        viewer.renderer.toonRenderEdges = []
        for e in edges:
            self.insert_edge(e)
        self.grid.attach(self.edgeList, 0, 1, 4, 1)

        insertButton.connect('clicked', lambda _: self.insert_edge(None))
        removeButton.connect('clicked', lambda _: self.remove_edge())

        save = self.save = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD)
        save.get_buffer().set_text(str(list(sorted(edges)))) 
        self.grid.attach(save, 0, 2, 4, 2)

        self.update_enable(enable)

    def get_selected_row(self):
        return self.edgeList.get_selected_row()

    def get_selected_index(self):
        row = self.get_selected_row()
        return row.get_index() if row else len(self.edgeList)

    def insert_edge(self, value):
        edges = self.viewer.renderer.toonRenderEdges
        index = self.get_selected_index()
        if value is None:
            try:
                value = edges[index]
            except IndexError:
                value = 0.
        row = Gtk.Scale(adjustment=Gtk.Adjustment(value, 0, 1, 0), digits=5,
            orientation=HORIZONTAL)
        row.connect('format-value', lambda s, value: self.update_value(index, value))
        self.edgeList.insert(row, index)
        self.edgeList.show_all()
        edges.insert(index, value)
        edges.sort()

    def update_enable(self, switch, *args):
        enabled = switch.get_active()
        self.viewer.renderer.toonRenderEnable = enabled
        for widget in self.grid.get_children():
            if widget is switch:
                continue
            widget.set_sensitive(enabled)

    def update_value(self, index, value):
        edges = self.viewer.renderer.toonRenderEdges = [r.get_children()[0].get_value()
            for r in self.edgeList.get_children()]
        self.save.get_buffer().set_text(str(list(sorted(edges))))

    def remove_edge(self):
        row = self.get_selected_row()
        self.edgeList.remove(row)
        self.viewer.renderer.toonRenderEdges.pop(row.get_index())


class JointControl(BoxControl):
    def __init__(self, joints):
        super().__init__('Joints Control')
        for joint in sorted(joints, key=lambda joint: joint.name):
            scale = Gtk.Scale(adjustment=Gtk.Adjustment(0, -180, 180, 0),
                digits=0, orientation=HORIZONTAL)
            scale.connect('format-value', self.update_angle, joint)
            row = Gtk.Box(orientation=HORIZONTAL)
            row.pack_start(Gtk.Label(joint.name), False, False, 2)
            row.pack_end(scale, True, True, 0)
            self.box.pack_start(row, False, False, 0)

    def update_angle(self, scale, value, joint):
        with ControlPanel.lock:
            joint.angle = scale.get_value() / 180 * math.pi


class State:
    PATH = '/tmp/raygllib_state'
    vars = {}

    @staticmethod
    def save():
        pickle.dump(State.vars, open(State.PATH, 'wb'), -1)

    @staticmethod
    def load():
        State.vars = pickle.load(open(State.PATH, 'rb'))


class CameraControl(BoxControl):
    def __init__(self, viewer):
        super().__init__('Camera Control', HORIZONTAL)
        saveButton = Gtk.Button('Save')
        loadButton = Gtk.Button('Load')
        self.viewer = viewer
        self.box.pack_start(saveButton, False, False, 0)
        self.box.pack_start(loadButton, False, False, 0)

        saveButton.connect('clicked', self.save)
        loadButton.connect('clicked', self.load)

    def load(self, *args):
        State.load()
        cam = self.viewer.camera
        with ControlPanel.lock:
            cam.up[:] = State.vars['up']
            cam.pos[:] = State.vars['pos']
            cam.center[:] = State.vars['center']
            cam._scale = State.vars['scale']
            cam._gen_view_mat()
            cam._gen_proj_mat()

    def save(self, *args):
        cam = self.viewer.camera
        with ControlPanel.lock:
            State.vars['up'] = cam.up
            State.vars['pos'] = cam.pos
            State.vars['center'] = cam.center
            State.vars['scale'] = cam._scale
        State.save()

class SilhouetteControl(GridControl):
    def __init__(self, viewer):
        super().__init__('Silhoette Control')
        self.viewer = viewer
        self.grid.attach(Gtk.Label('Enable'), 0, 0, 1, 1)
        enable = Gtk.Switch(active=viewer.silhouetteEnable)
        enable.connect('notify::active', self.update_enable)
        self.grid.attach(enable, 1, 0, 1, 1) 

        edgeWidth = Gtk.Scale(
            adjustment=Gtk.Adjustment(viewer.silhouetteWidth, 0.001, 0.1),
            digits=3, orientation=HORIZONTAL)
        edgeWidth.connect('format-value', self.update_edge_width)
        self.grid.attach(edgeWidth, 0, 1, 4, 1)

    def update_enable(self, switch, *args):
        enabled = switch.get_active()
        with ControlPanel.lock:
            self.viewer.silhouetteEnable = enabled

    def update_edge_width(self, widget, value):
        with ControlPanel.lock:
            self.viewer.silhouetteWidth = widget.get_value()


class FileLoader(BoxControl):
    RECENT_LIMIT = 5
    MAX_HEIGHT = 5

    def __init__(self, viewer):
        super().__init__('File')
        self.viewer = viewer
        # Add recent chooser
        recentFilter = Gtk.RecentFilter()
        recentFilter.add_pattern('*.dae')
        self.recentList = recentList = Gtk.RecentChooserWidget(
            select_multiple=False,
            limit=self.RECENT_LIMIT,
            sort_type=Gtk.RecentSortType.MRU,
            filter=recentFilter,
        )
        # height = min(self.MAX_HEIGHT, self.RECENT_LIMIT)
        self.box.pack_start(recentList, True, True, 2)

        # Put file chooser and load button in the same row
        hbox = Gtk.Box()
        self.box.pack_end(hbox, False, False, 2)
        # Add file chooser button
        self.fileChooser = Gtk.FileChooserButton(
            'Select model...', action=Gtk.FileChooserAction.OPEN)
        hbox.pack_start(self.fileChooser, True, True, 0)
        # Add load button
        loadButton = Gtk.Button('Load')
        hbox.pack_end(loadButton, False, False, 0)
        loadButton.connect('clicked', self.load)

    def load(self, *args):
        filename = self.fileChooser.get_filename()
        if not filename:
            item = self.recentList.get_current_item()
            if item:
                filename = item.get_uri_display()
        if filename:
            self.viewer.require.load_scene(filename)


def glib_idle_add(func):
    def new_func():
        func()
    GLib.idle_add(new_func)


class ControlPanel(Thread):
    lock = RLock()

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.require = Require(self)

    def add_light(self, light):
        self._add_control('lights', LightControl, light)

    def add_material(self, material):
        self._add_control('materials', MaterialControl, material)

    def add_misc(self, viewer):
        self._add_control('misc', CameraControl, viewer)
        self._add_control('misc', FileLoader, viewer)
        self._add_control('misc', SilhouetteControl, viewer)
        self._add_control('misc', EdgesControl, viewer)

    def add_joints(self, joints):
        self._add_control('joints', JointControl, joints)

    def _add_control(self, columnName, controlClass, *args):
        @glib_idle_add
        def add_control():
            control = controlClass(*args)
            control.show_all()
            column = self.columns[columnName]
            column.pack_start(control, True, True, 2)

    def run(self):
        Gdk.threads_init()
        self.window = window = Gtk.Window(title='Control Panel')
        window.connect("delete-event", Gtk.main_quit)
        self.box = Gtk.Box(orientation=HORIZONTAL)
        self.columns = {
            'misc': Gtk.Box(orientation=VERTICAL),
            'joints': Gtk.Box(orientation=VERTICAL),
            'lights': Gtk.Box(orientation=VERTICAL),
            'materials': Gtk.Box(orientation=VERTICAL),
        }
        for name in ('misc', 'joints', 'lights', 'materials'):
            frame = Gtk.Frame(label=name.capitalize())
            frame.add(self.columns[name])
            column = Gtk.ScrolledWindow()
            column.add(frame)
            self.box.pack_start(column, True, True, 5)
        window.add(self.box)
        window.show_all()
        Gtk.main()
        Gdk.threads_quit()

    clearCondition = Condition(RLock())

    def clear(self):
        self._cleared = False

        @glib_idle_add
        def clear():
            self.clearCondition.acquire()
            # clear lights column
            for child in self.columns['lights'].get_children():
                child.destroy()
            # clear materials column
            for child in self.columns['materials'].get_children():
                child.destroy()
            self.clearCondition.notify_all()
            self.clearCondition.release()
            self._cleared = True
