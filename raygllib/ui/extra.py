from .base import (
    Widget, join_props, REQUIRED, TextBox, RectShape, Color, TextAlign, LayoutDirection,
)

colorDark = Color(.5, .5, .5, 1.)
colorLight = Color(.8, .8, .8, 1.)
colorActive = Color(.5, .8, .5, 1.)
colorFontLight = Color(.9, .9, .9, 1.)
colorFontDark = Color(.1, .1, .1, 1.)
defaultFontSize = 14


class Panel(Widget):
    properties = join_props(Widget.properties, [
        ('color', colorDark),
        ('solid', True),
    ])

    def __init__(self, *args, **kwargs):
        self.rect = rect = RectShape()
        super().__init__(*args, **kwargs)
        self.rects.append(rect)

    def on_relayout(self):
        super().on_relayout()
        self.teach_geometry(self.rect)

    @property
    def color(self):
        return self.rect.color

    @color.setter
    def color(self, color):
        self.rect.color = color


class Label(Widget):
    properties = join_props(Widget.properties, [
        ('textbox', REQUIRED),
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textboxes.append(self.textbox)

    def on_relayout(self):
        super().on_relayout()
        self.teach_geometry(self.textbox)


class Button(Widget):
    properties = join_props(Widget.properties, [
        ('solid', True),
        ('fontColor', colorFontDark),
        ('color', colorLight),
        ('text', REQUIRED),
        ('height', 16),
        ('fontSize', defaultFontSize),
    ])

    signals = ['click']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.textbox = TextBox(
            text=self.text, color=self.fontColor, align=TextAlign.CENTER,
            fontSize=self.fontSize)
        self.textboxes.append(self.textbox)

        self.rect = RectShape(color=self.color)
        self.rects.append(self.rect)

    def on_relayout(self):
        super().on_relayout()
        px, py = self.paddingX, self.paddingY
        self.teach_geometry(self.textbox)
        self.teach_geometry(self.rect)

    def on_mouse_release(self, x, y, button, modifiers):
        self.emit_signal('click')


class Switch(Panel):
    properties = join_props(Panel.properties, [
        ('text', REQUIRED),
        ('active', True),
        ('activeColor', colorActive),
        ('inactiveColor', colorDark),
        ('color', colorLight),
        ('fontColor', colorFontDark),
        ('layoutDirection', LayoutDirection.HORIZONTAL),
    ])

    signals = ['toggled']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indicate = Panel(
            solid=False, color=self.activeColor if self.active else self.inactiveColor,
            paddingX=5, paddingY=5, fixedSize=True, width=16)
        self.label = Label(
            textbox=TextBox(
                text=self.text, fontSize=defaultFontSize, color=self.fontColor,
                align=TextAlign.LEFT))
        self.children = [self.indicate, self.label]

    def on_mouse_release(self, x, y, button, modifiers):
        self.active = not self.active
        self.indicate.color = self.activeColor if self.active else self.inactiveColor
        self.emit_signal('toggled')


class Spin(Widget):
    properties = join_props(Widget.properties, [
        ('backColor', colorDark),
        ('color', colorActive),
        ('fontColor', colorFontDark),
        ('value', 0.),
        ('minValue', 0.),
        ('maxValue', 1.),
        ('digits', 3),
        ('fontSize', defaultFontSize),
        ('layoutDirection', LayoutDirection.HORIZONTAL),
        ('solid', True),
        ('text', ''),
    ])
    signals = ['value-changed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        assert self.minValue <= self.value <= self.maxValue
        self._bar = RectShape(color=self.color)
        self._back = RectShape(color=self.backColor)
        self._text = TextBox(
            text='', color=self.fontColor, align=TextAlign.CENTER,
            fontSize=self.fontSize)

        self.rects.extend([self._back, self._bar])
        self.textboxes.append(self._text)

        self.update_value(self.value, sendEvent=False)

    def update_value(self, value, sendEvent=True):
        self._text.text = '{{}}: {{:.{}f}}'\
            .format(self.digits).format(self.text, self.value)
        value = min(max(self.minValue, value), self.maxValue)
        self._bar.width = (value - self.minValue) / (self.maxValue - self.minValue)\
            * self._back.width
        if value != self.value:
            self.value = value
            if sendEvent:
                self.emit_signal('value-changed')

    def on_relayout(self):
        super().on_relayout()
        self.teach_geometry(self._back)
        self._back.teach_properties(self._bar, ('x', 'y', 'height'))
        self.teach_geometry(self._text)
        self._bar.width = (self.value - self.minValue) / (self.maxValue - self.minValue)\
            * self._back.width

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        if self.layoutDirection is LayoutDirection.HORIZONTAL:
            value = (x - self._back.x) / self._back.width \
                * (self.maxValue - self.minValue) + self.minValue
            self.update_value(value)
        else:
            raise NotImplementedError()


def command(func):
    func.isCommand = True
    return func

class CommandBar(Widget):

    @command
    def focus(self, name):
        pass
