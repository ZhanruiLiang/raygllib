from .base import Widget, make_hbox, join_props, LayoutDirection, TextAlign
from .extra import Panel, Title, Button
from .layout import LayoutManager
from . import theme

class DialogTitleBar(Widget):
    properties = join_props(Widget.properties, [
        ('layoutDirection', LayoutDirection.HORIZONTAL),
        ('fixedSize', True),
        ('height', theme.heightSubTitle),
        ('solid', True),
        ('focusable', True),
    ])

    def __init__(self, dialog, **kwargs):
        self.dialog = dialog
        super().__init__(**kwargs)
        closeButton = Button(text='CLOSE', fixedSize=True, fontSize=8, width=38)
        closeButton.connect_signal('clicked', dialog.close)
        self.children.extend([
            Title(
                text=dialog._title, fixedSize=False, fontSize=theme.fontSizeSubTitle,
                paddingX=0, paddingY=0, align=TextAlign.LEFT),
            closeButton,
        ])

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        self.dialog._layoutManager.move(dx, dy)


class Dialog(Panel):
    properties = join_props(Panel.properties, [
        ('closable', True),
        ('focusable', False),
        ('paddingY', 0),
        ('paddingX', 0),
        ('title', ''),
        ('fixedSize', True),
        ('width', 300),
        ('height', 200),
        ('autoCenter', False),
    ])
    signals = ['close']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.titleBar = DialogTitleBar(self)
        bottom = Panel(
            fixedSize=True, height=2, color=theme.colorTitle, paddingX=0, paddingY=0)
        self.body = Widget()
        self.children.extend([self.titleBar, self.body, bottom])
        self.layoutDirection = LayoutDirection.VERTICAL
        self._layoutManager = LayoutManager(self)
        self._needClose = False

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title):
        self._title = title
        if hasattr(self, 'titleBar'):
            self.titleBar.text = title

    def close(self):
        if self.closable:
            self._needClose = True
            self.emit_signal('close')

    def on_resize(self, width, height):
        if self.autoCenter:
            self.x = (width - self.width) / 2
            self.y = (height - self.height) / 2
        self.relayout()

    def relayout(self):
        self._layoutManager.relayout()


# class MessageDialog(Dialog):
#     pass
