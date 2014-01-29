from gi.repository import Gtk, Gdk
from gi.repository import GLib
from threading import Thread, RLock
from .model import Light

class LightPosSpinButton(Gtk.SpinButton):
    def __init__(self, value):
        R = Light.MAX_RANGE
        super().__init__(
            adjustment=Gtk.Adjustment(value, -R, R, .05), numeric=True, digits=3)

class Control(Gtk.Frame):
    def __init__(self, label):
        super().__init__(border_width=2)
        self.grid = Gtk.Grid(column_spacing=5, border_width=5)
        self.add(self.grid)

class PropsControl(Control):
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
                adjustment=Gtk.Adjustment(light.power, 0, light.MAX_POWER, 50),
                numeric=True, digits=0)),
            ('x', LightPosSpinButton, dict(value=light.pos[0])),
            ('y', LightPosSpinButton, dict(value=light.pos[1])),
            ('z', LightPosSpinButton, dict(value=light.pos[2])),
        ]
        super().__init__('Light Control', props)
        widgets = self.widgets
        widgets['x'].connect('value-changed', self.update_pos, 0)
        widgets['y'].connect('value-changed', self.update_pos, 1)
        widgets['z'].connect('value-changed', self.update_pos, 2)
        widgets['enable'].connect('notify::active', self.update_enable)
        widgets['power'].connect('value-changed', self.update_power)

    def update_pos(self, spin, axis):
        pos = list(self.light.pos)
        pos[axis] = float(spin.get_value())
        with ControlPanel.lock:
            self.light.pos = tuple(pos)

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
        super().__init__('Material Control', props)
        widgets = self.widgets
        widgets['shininess'].connect('value-changed', self.update_shininess)

    def update_shininess(self, spin):
        self.material.shininess = float(spin.get_value())


class EdgesControl(Control):
    def __init__(self, viewer):
        super().__init__('Edges Control')
        self.viewer = viewer

        self.grid.attach(Gtk.Label('Enable'), 0, 0, 1, 1)
        enable = Gtk.Switch(active=viewer.enableToonRender)
        enable.connect('notify::active', self.update_enable)
        insertButton = Gtk.Button('Insert')
        removeButton = Gtk.Button('Remove')
        for i, widget in enumerate((enable, insertButton, removeButton)):
            self.grid.attach(widget, 1 + i, 0, 1, 1)

        self.edgeList = Gtk.ListBox(selection_mode=Gtk.SelectionMode.SINGLE)
        edges = viewer.toonRenderEdges
        viewer.toonRenderEdges = []
        for e in edges:
            self.insert_edge(e)
        self.grid.attach(self.edgeList, 0, 1, 4, 1)

        insertButton.connect('clicked', lambda _: self.insert_edge(None))
        removeButton.connect('clicked', lambda _: self.remove_edge())

        save = self.save = Gtk.TextView(editable=False, wrap_mode=Gtk.WrapMode.WORD)
        save.get_buffer().set_text(str(list(sorted(edges)))) 
        self.grid.attach(save, 0, 2, 4, 2)

    def get_selected_row(self):
        return self.edgeList.get_selected_row()

    def get_selected_index(self):
        row = self.get_selected_row()
        return row.get_index() if row else len(self.edgeList)

    def insert_edge(self, value):
        edges = self.viewer.toonRenderEdges
        index = self.get_selected_index()
        if value is None:
            try:
                value = edges[index]
            except IndexError:
                value = 0.
        row = Gtk.Scale(adjustment=Gtk.Adjustment(value, 0, 1, 0), digits=5,
            orientation=Gtk.Orientation.HORIZONTAL)
        row.connect('format-value', lambda s, value: self.update_value(index, value))
        self.edgeList.insert(row, index)
        self.edgeList.show_all()
        edges.insert(index, value)

    def update_enable(self, switch, *args):
        enabled = switch.get_active()
        self.viewer.enableToonRender = enabled
        for widget in self.grid.get_children():
            if widget is switch:
                continue
            widget.set_sensitive(enabled)

    def update_value(self, index, value):
        self.viewer.toonRenderEdges = [r.get_children()[0].get_value()
            for r in self.edgeList.get_children()]
        self.save.get_buffer().set_text(str(list(sorted(self.viewer.toonRenderEdges))))

    def remove_edge(self):
        row = self.get_selected_row()
        self.edgeList.remove(row)
        self.viewer.toonRenderEdges.pop(row.get_index())


class ControlPanel(Thread):
    lock = RLock()

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True

    def add_light(self, light):
        self._add_control('lights', LightControl, light)

    def add_material(self, material):
        self._add_control('materials', MaterialControl, material)

    def add_edges(self, viewer):
        self._add_control('edges', EdgesControl, viewer)

    def _add_control(self, columnName, controlClass, *args):
        def func():
            control = controlClass(*args)
            control.show_all()
            column = self.columns[columnName]
            column.pack_start(control, False, False, 5)
        GLib.idle_add(func)

    def run(self):
        self.window = window = Gtk.Window(title='Control Panel')
        window.connect("delete-event", Gtk.main_quit)
        self.box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.columns = {
            'edges': Gtk.Box(orientation=Gtk.Orientation.VERTICAL),
            'lights': Gtk.Box(orientation=Gtk.Orientation.VERTICAL),
            'materials': Gtk.Box(orientation=Gtk.Orientation.VERTICAL),
        }
        for name in ('edges', 'lights', 'materials'):
            frame = Gtk.Frame(label=name.capitalize())
            frame.add(self.columns[name])
            self.box.pack_start(frame, False, True, 5)
        window.add(self.box)
        window.show_all()
        Gtk.main()
