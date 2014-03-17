from .base import (
    Widget, join_props, REQUIRED, TextBox, RectShape, TextAlign, LayoutDirection,
)
from . import key as K
from . import theme
from .event import EVENT_HANDLED
from .render import BackgroundRender


class Panel(Widget):
    properties = join_props(Widget.properties, [
        ('color', theme.colorLight.copy()),
        ('solid', True),
        ('focusable', False),
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

class Label(Widget, TextBox):
    properties = join_props(Widget.properties, TextBox.properties, [
        ('focusable', False),
    ])

    def __init__(self, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        TextBox.__init__(self, *args, **kwargs)
        self.textboxes.append(self)

# class Label(Widget):
#     properties = join_props(Widget.properties, [
#         ('focusable', False),
#         ('text', REQUIRED),
#     ])

    # def __init__(self, *args, **kwargs):
    #     names = [name for name, _ in TextBox.properties]
    #     kwargs1 = {name: kwargs[name] for name in names if name in kwargs}
    #     self._textbox = TextBox(**kwargs1)
    #     names = [name for name, _ in Label.properties]
    #     kwargs = {name: kwargs[name] for name in names if name in kwargs}
    #     super().__init__(*args, **kwargs)
    #     self.textboxes.append(self._textbox)

    # @property
    # def text(self):
    #     return self._textbox.text

    # @text.setter
    # def text(self, text):
    #     self._textbox.text = text

    # def on_relayout(self):
    #     super().on_relayout()
    #     self.teach_geometry(self._textbox)


class Button(Widget):
    properties = join_props(Widget.properties, [
        ('solid', True),
        ('fontColor', theme.colorFontDark.copy()),
        ('color', theme.colorButton.copy()),
        ('text', REQUIRED),
        ('height', 16),
        ('fontSize', theme.fontSizeDefault),
        ('focusable', True),
    ])

    signals = ['clicked']

    def __init__(self, *args, **kwargs):
        self.rect = RectShape()
        super().__init__(*args, **kwargs)

        self.textbox = TextBox(
            text=self.text, color=self.fontColor, align=TextAlign.CENTER,
            fontSize=self.fontSize)
        self.textboxes.append(self.textbox)

        self.rects.append(self.rect)

    @property
    def color(self):
        return self.rect.color

    @color.setter
    def color(self, color):
        self.rect.color = color

    def on_relayout(self):
        super().on_relayout()
        px, py = self.paddingX, self.paddingY
        self.teach_geometry(self.textbox)
        self.teach_geometry(self.rect)

    def on_mouse_release(self, x, y, button, modifiers):
        self.emit_signal('clicked')
        return EVENT_HANDLED

    def on_key_press(self, symbol, modifiers):
        if super().on_key_press(symbol, modifiers):
            return EVENT_HANDLED
        if symbol in (K.ENTER, K.SPACE):
            self.emit_signal('clicked')
            return EVENT_HANDLED


class Switch(Panel):
    properties = join_props(Panel.properties, [
        ('text', REQUIRED),
        ('active', True),
        ('activeColor', theme.colorActive.copy()),
        ('inactiveColor', theme.colorDark.copy()),
        ('color', theme.colorLight.copy()),
        ('layoutDirection', LayoutDirection.HORIZONTAL),
        ('focusable', True),
        ('fixedSize', True),
        ('height', 18),
    ])

    signals = ['toggled']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indicate = Panel(
            solid=False, color=self.activeColor if self.active else self.inactiveColor,
            paddingX=5, paddingY=5, fixedSize=True, width=16)
        self.label = Label(
            text=self.text, fontSize=theme.fontSizeDefault,
            color=self.activeColor if self.active else self.inactiveColor,
            align=TextAlign.LEFT)
        self.children = [self.indicate, self.label]

    def on_mouse_release(self, x, y, button, modifiers):
        self.toggle()
        return EVENT_HANDLED

    def toggle(self):
        self.active = not self.active
        self.indicate.color = self.label.color = \
            self.activeColor if self.active else self.inactiveColor
        self.emit_signal('toggled')

    def on_key_press(self, symbol, modifiers):
        if super().on_key_press(symbol, modifiers):
            return EVENT_HANDLED
        if symbol in (K.ENTER, K.SPACE):
            self.toggle()
            return EVENT_HANDLED

class Spin(Widget):
    properties = join_props(Widget.properties, [
        ('backColor', theme.colorDark.copy()),
        ('color', theme.colorActive.copy()),
        ('fontColor', theme.colorFontLight.copy()),
        ('value', 0.),
        ('minValue', 0.),
        ('maxValue', 1.),
        ('digits', 3),
        ('fontSize', theme.fontSizeDefault),
        ('layoutDirection', LayoutDirection.HORIZONTAL),
        ('solid', True),
        ('text', ''),
        ('focusable', True),
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

    def format_value(self, value):
        return '{{:.{}f}}'.format(self.digits).format(value)

    def update_value(self, value, sendEvent=True):
        value = min(max(self.minValue, value), self.maxValue)
        self._text.text = self.text + ': ' + self.format_value(value)
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

    def on_key_press(self, symbol, modifiers):
        if super().on_key_press(symbol, modifiers):
            return EVENT_HANDLED


class ColorPicker(Widget):
    properties = join_props(Widget.properties, [
        ('color', theme.Color(0., 0., 0., 0.)),
        ('layoutDirection', LayoutDirection.VERTICAL),
    ])

    signals = ['value-changed']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        name = 'RGB'
        self.spins = []
        for i in range(3):
            color = theme.Color(.4, .4, .4, 1.)
            color[i] = .8
            spin = Spin(
                text=name[i], color=color, digits=0, fontSize=theme.fontSizeSmall,
                value=self.color[i] * 255, minValue=0, maxValue=255,
                paddingX=0, paddingY=0,
            )
            self.spins.append(spin)
            spin.connect_signal('value-changed', self.update_color)
        self.hexIndicator = Label(text='')
        self.colorIndicator = Panel(
            color=self.color, paddingX=0, paddingY=0, height=20, fixedSize=1,
            layoutDirection=LayoutDirection.VERTICAL,
            children=[self.hexIndicator])
        self.children = [self.colorIndicator] + self.spins

    def update_color(self):
        name = 0
        for i, spin in enumerate(self.spins):
            self.color[i] = spin.value / 255.
            name = (name << 8) | int(spin.value + .5)
        self.colorIndicator.color = self.color
        self.hexIndicator.text = hex(name)
        self.emit_signal('value-changed')


class Title(Label):
    properties = join_props(Label.properties, [
        ('fixedSize', True),
        ('fontSize', 15),
        ('height', theme.heightTitle),
        ('color', theme.colorFontLight.copy()),
        ('backColor', theme.colorTitle.copy()),
        ('align', TextAlign.CENTER),
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rect = RectShape(color=self.backColor)
        self.rects.append(self._rect)

    def on_relayout(self):
        super().on_relayout()
        self.teach_geometry(self._rect)


class SubTitle(Title):
    properties = join_props(Title.properties, [
        ('backColor', theme.colorSubTitle.copy()),
        ('fontSize', theme.fontSizeSubTitle),
        ('height', theme.heightSubTitle),
        ('align', TextAlign.LEFT),
    ])


class Canvas(Widget):
    properties = join_props(Widget.properties, [
        ('solid', True),
        ('focusable', True),
        ('color', theme.Color(0x111111)),
    ])

    backgroundRender = BackgroundRender() 

    def draw(self):
        self.fill_background()

    def fill_background(self):
        r = self.backgroundRender
        with r.batch_draw():
            r.set_color(self.color)
            r.draw_background()

# def command(func):
#     func.isCommand = True
#     return func
# 
# class CommandBar(Widget):
# 
#     @command
#     def focus(self, name):
#         pass
