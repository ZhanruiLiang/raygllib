from .base import Widget, join_props, REQUIRED, TextBox, RectShape

class Label(Widget):
    properties = join_props(Widget.properties, [
        ('textbox', REQUIRED),
    ])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textboxes.append(self.textbox)

    def on_relayout(self):
        super().on_relayout()
        t = self.textbox
        t.x = self._rect.x
        t.y = self._rect.y
        t.width = self._rect.width
        t.height = self._rect.height


def command(func):
    func.isCommand = True
    return func

class CommandBar(Widget):

    @command
    def focus(self, name):
        pass

class SpinBar(Widget):
    pass
