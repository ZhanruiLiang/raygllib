import pyglet

import raygllib.gllib as gl
from .base import Widget, Canvas, RectShape, join_props
from .event import EVENT_HANDLED, EVENT_UNHANDLED
from .render import RectRender, FontRender
from .theme import Color
from .layout import LayoutManager
from . import theme

__all__ = ['Window', 'EVENT_HANDLED', 'EVENT_UNHANDLED']

def collect_rects(widget):
    for rect in widget.rects:
        yield rect
    for child in widget.children:
        yield from collect_rects(child)

def collect_textboxes(widget):
    for textbox in widget.textboxes:
        yield textbox
    for child in widget.children:
        yield from collect_textboxes(child)

def collect_canvases(widget):
    if isinstance(widget, Canvas):
        yield widget
    for child in widget.children:
        yield from collect_canvases(child)


class FocusRect(RectShape):
    properties = join_props(RectShape.properties, [
        ('color', theme.colorFocus.copy()),
    ])
    BLINK_INTERVAL = 1.2
    MIN_ALPHA = 0.2
    MAX_ALPHA = 0.4
    HEIGHT_ON_CANVAS = 10
    _time = 0
    _target = None

    def update(self, dt):
        if self.target:
            T = self.BLINK_INTERVAL
            t = self._time
            if t < T / 2:
                k = t * 2 / T
            else:
                k = 2 - t * 2 / T
            self.color[3] = self.MIN_ALPHA * (1 - k) + self.MAX_ALPHA * k
            self._time = (t + dt) % T
        else:
            self.color[3] = 0.

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, target):
        self._target = target
        if target:
            target.teach_properties(self, ('x', 'y', 'width', 'height'))
            if isinstance(self.target, Canvas):
                self.height = self.HEIGHT_ON_CANVAS
        self._time = 0

    def on_relayout(self):
        if self.target:
            self.target.teach_properties(self, ('x', 'y', 'width', 'height'))
            if isinstance(self.target, Canvas):
                self.height = self.HEIGHT_ON_CANVAS


class Window(pyglet.window.Window):
    KEY_REPEAT_INTERVAL = 0.04
    KEY_REPEAT_DELAY = 0.4

    def __init__(self,
            vsync=True, config=pyglet.gl.Config(sample_buffers=1, samples=4),
            color=Color(1., 1., 1., 1.),
            **kwargs):
        self._root = Widget(x=0, y=0, fixedSize=True)
        self._layoutManager = LayoutManager(self._root)
        self._needRelayout = True
        self.color = color
        # Widgets is sorted by pre-order traversal
        self._widgets = []
        self._textboxes = []
        self._canvases = []
        self._rects = []

        self._rectRender = RectRender()
        self._fontRender = FontRender()

        self._shortcuts = {}
        self._shortcutId = 0

        self.focus = None
        self._focusRect = FocusRect()

        # Indicate if a key is pressing. Used in the key repeat system.
        self._pressing = False

        super().__init__(vsync=vsync, config=config, **kwargs)

    @property
    def root(self):
        return self._root

    def _locate_widget_at(self, x, y):
        for widget in reversed(self._widgets):
            if not widget.solid:
                continue
            x1 = widget.x
            y1 = widget.y
            w = widget.width
            h = widget.height
            if x1 <= x < x1 + w and y1 <= y < y1 + h:
                yield widget

    def _handle_mouse_event(self, eventName, x, y, *args):
        y = self.height - y
        for widget in self._locate_widget_at(x, y):
            result = getattr(widget, eventName)(x, y, *args)
            if result is EVENT_HANDLED:
                break

    def add_shortcut(self, keyComb, callback, *args):
        func = lambda: callback(*args)
        func.shortcutId = self._shortcutId
        self._shortcutId += 1
        if keyComb not in self._shortcuts:
            self._shortcuts[keyComb] = [func]
        else:
            self._shortcuts[keyComb].append(func)
        return func.shortcutId

    def remove_shortcut(self, keyComb, shortcutId):
        for i, func in enumerate(self._shortcuts[keyComb]):
            if func.shortcutId == shortcutId:
                self._shortcuts[keyComb].pop(i)
                break
        else:
            raise KeyError((keyComb, shortcutId))

    # Event handlers ##########################################################

    def on_resize(self, w, h):
        self.root.width = w
        self.root.height = h
        self.request_relayout()
        self._fontRender.set_screen_size(w, h)
        self._rectRender.set_screen_size(w, h)

    def on_key_press(self, symbol, modifiers, _is_repeat=False):
        # print(symbol, modifiers)
        if not _is_repeat:
            self._pressing = (symbol, modifiers)
            self._keyRepeatColdDown = self.KEY_REPEAT_DELAY
        for kc in self._shortcuts:
            if kc.key == symbol and (kc.mask & modifiers) == kc.mask:
                for func in reversed(self._shortcuts[kc]):
                    result = func()
                    if result is EVENT_HANDLED:
                        return
        if self.focus is not None:
            self.focus.on_key_press(symbol, modifiers)

    def on_key_release(self, symbol, modifiers):
        self._pressing = None

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self._handle_mouse_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    def on_mouse_motion(self, x, y, dx, dy):
        for widget in self._locate_widget_at(x, self.height - y):
            if widget.focusable:
                self.set_focus(widget)
                break
        self._handle_mouse_event('on_mouse_motion', x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifiers):
        self._handle_mouse_event('on_mouse_press', x, y, button, modifiers)

    def on_mouse_scroll(self, x, y, button, modifiers):
        self._handle_mouse_event('on_mouse_scroll', x, y, button, modifiers)

    def on_mouse_release(self, x, y, button, modifiers):
        self._handle_mouse_event('on_mouse_release', x, y, button, modifiers)

    def request_relayout(self):
        self._needRelayout = True

    def relayout(self):
        self._needRelayout = False
        self._layoutManager.relayout()
        self._focusRect.on_relayout()
        self._collect(self._layoutManager.widgets)

    def update(self, dt):
        if self._needRelayout:
            self.relayout()
        self._focusRect.update(dt)
        if self._pressing:
            self._keyRepeatColdDown -= dt
            if self._keyRepeatColdDown <= 0:
                symbol, modifiers = self._pressing
                self.on_key_press(symbol, modifiers, _is_repeat=True)
                self._keyRepeatColdDown += self.KEY_REPEAT_INTERVAL

    def _collect(self, widgets):
        self._widgets = widgets
        self._textboxes = list(collect_textboxes(self.root))
        self._rects = list(collect_rects(self.root))
        self._canvases = list(collect_canvases(self.root))
        self._rects.append(self._focusRect)
        self._make_focus_chain()
        for widget in widgets:
            widget.request_relayout = self.request_relayout

    def _make_focus_chain(self):
        widgets = [widget for widget in self._widgets if widget.focusable]
        for i in range(len(widgets)):
            widgets[i]._prevFocus = widgets[i - 1]
            widgets[i - 1]._nextFocus = widgets[i]
            widgets[i].set_focus = self.set_focus
        if widgets and self.focus is None:
            self.set_focus(widgets[0])

    def set_focus(self, widget):
        if widget != self.focus:
            self.focus = widget
            self._focusRect.target = widget

    def on_draw(self):
        gl.glClearColor(*self.color)
        self.clear()
        root = self.root
        gl.glViewport(0, 0, int(self.root.width), int(self.root.height))

        with self._rectRender.batch_draw():
            self._rectRender.draw_rects(self._rects)

        with self._fontRender.batch_draw():
            self._fontRender.draw_textboxs(self._textboxes)

        for canvas in self._canvases:
            gl.glViewport(
                int(canvas.x),
                int(root.height - (canvas.y + canvas.height)),
                int(canvas.width), 
                int(canvas.height),
            )
            canvas.draw()
