import pickle
import os
from .base import (
    Widget, join_props, REQUIRED, TextBox, RectShape, TextAlign, LayoutDirection,
)
from . import key as K
from . import theme
from .event import EVENT_HANDLED

from raygllib import utils


def shortcut(keyComb, doc=''):
    def deco(func):
        func._shortcut = keyComb
        func._shortCutDoc = doc
        return func
    return deco


class Editor:
    def __init__(self):
        self.text = ''
        self._shortcuts = {}
        for name in dir(self):
            method = getattr(self, name)
            if hasattr(method, '_shortcut'):
                self._shortcuts[method._shortcut] = method

    def clear(self):
        self.text = ''

    def input(self, chars):
        if self.validate(self.text, chars):
            self.text += chars
            self.on_text_update()
            return True
        self.on_alert()
        return False

    def delete(self, nChars):
        if len(self.text) >= nChars:
            self.text = self.text[:-nChars]
            self.on_text_update()
            return True
        self.on_alert()
        return False

    def validate(self, current, chars):
        return True

    def on_alert(self):
        pass

    def on_text_update(self):
        pass

    def on_press_return(self, modifiers):
        self.input('\n')

    @staticmethod
    def symbol_to_char(symbol, modifiers):
        try:
            if symbol < 128:
                c = chr(symbol)
                if K.MOD_SHIFT & modifiers:
                    c = c.upper()
                return c
        except:
            return None
        return None

    def on_key_press(self, symbol, modifiers):
        if symbol == K.BACKSPACE:
            if self.delete(1):
                return EVENT_HANDLED
        elif symbol == K.RETURN:
            if self.on_press_return(modifiers):
                return EVENT_HANDLED
        else:
            for kc in self._shortcuts:
                if kc.key == symbol and kc.mask & modifiers == kc.mask:
                    method = self._shortcuts[kc]
                    result = method()
                    if result == EVENT_HANDLED:
                        return EVENT_HANDLED
            c = self.symbol_to_char(symbol, modifiers)
            if c is not None and self.input(c):
                return EVENT_HANDLED
            else:
                self.on_alert()


class TextInput(Widget, Editor):
    properties = join_props(Widget.properties, [
        ('backColor', theme.colorTextInput),
        ('fontColor', theme.colorFontDark),
        ('fontSize', theme.defaultFontSize),
        ('solid', True),
        ('focusable', True),
        ('text', ''),
    ])

    def __init__(self, *args, **kwargs):
        Editor.__init__(self)
        Widget.__init__(self, *args, **kwargs)
        self._textbox = TextBox(
            text=self.text, fontSize=self.fontSize, color=self.fontColor,
            align=TextAlign.LEFT,
        )
        self._back = RectShape(color=self.backColor)
        self.textboxes.append(self._textbox)

    def on_text_update(self):
        self._textbox.text = self.text

    def on_relayout(self):
        super().on_relayout()
        self.teach_geometry(self._textbox)
        self.teach_geometry(self._back)

    def on_key_press(self, symbol, modifiers):
        if Widget.on_key_press(self, symbol, modifiers):
            return EVENT_HANDLED
        return Editor.on_key_press(self, symbol, modifiers)

    @shortcut(K.chain(K.CTRL, K.K), 'Clear')
    def delete_all(self):
        self.delete(len(self.text))
        return EVENT_HANDLED


class NumericInput(TextInput, Editor):
    ALLOW_CHARS = '0123456789.'

    def get_value(self):
        try:
            return float(self.text)
        except ValueError:
            return None

    def validate(self, current, chars):
        for c in chars:
            if c not in self.ALLOW_CHARS:
                return False
        return True


class History:
    PATH = os.path.expanduser('~/.raygllib.history')
    MAX_LINES = 1000

    def load(self):
        try:
            with open(self.PATH, 'rb') as histfile:
                lines = pickle.load(histfile)
            self.lines = lines
        except Exception as e:
            self.lines = []
            utils.debug(e)

    def save(self):
        lines = self.lines[:self.MAX_LINES]
        with open(self.PATH, 'wb') as histfile:
            pickle.dump(lines, histfile)

    def add(self, line):
        self.lines.append(line)

    def search(self, key, start=None, direction=-1):
        """
        key: A function acceptting a line as argument.
        """
        lines = self.lines
        if start is None:
            start = len(self.lines) - 1
        if direction > 0:
            r = range(start, len(lines), direction)
        else:
            r = range(start, -1, direction)
        for i in r:
            if key(lines[i]):
                return i, lines[i]
        return None, None

    def __len__(self):
        return len(self.lines)


class PathHistory(History):
    PATH = os.path.expanduser('~/.raygllib.history.path')


class PathInput(TextInput):
    signals = ['open']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._history = PathHistory()
        self._history.load()
        self._histIndex = None
        self._histKey = None

    def on_press_return(self, modifiers):
        if self.text:
            self._history.add(self.text)
            self._history.save()
            self.emit_signal('open')

    def _match_history(self, direction):
        prefix = self.text if self._histKey is None else self._histKey
        i, line = self._history.search(
            lambda line: line.startswith(prefix),
            start=self._histIndex,
            direction=direction
        )
        # print(self._histIndex, self._histKey)
        if line is not None:
            self.text = ''
            self.input(line)
            self._histIndex = i + direction
            self._histKey = prefix
        else:
            self._histIndex = None
            if self._histKey is not None:
                self.text = ''
                self.input(self._histKey)
        return EVENT_HANDLED

    def _search_history(self, direction):
        key = self.text if self._histKey is None else self._histKey
        i, line = self._history.search(
            lambda line: line.find(key) >= 0,
            start=self._histIndex,
            direction=direction
        )
        # print(self._histIndex, self._histKey)
        if line is not None:
            self.text = ''
            self.input(line)
            self._histIndex = i + direction
            self._histKey = key 
        else:
            self._histIndex = None
            if self._histKey is not None:
                self.text = ''
                self.input(self._histKey)
        return EVENT_HANDLED

    def on_text_update(self):
        super().on_text_update()
        self._histKey = None

    @shortcut(K.chain(K.UP), 'Match history up')
    def match_history_up(self):
        return self._match_history(-1)

    @shortcut(K.chain(K.DOWN), 'Match history down')
    def match_history_down(self):
        return self._match_history(1)

    @shortcut(K.chain(K.CTRL, K.R), 'Search history up')
    def search_history_up(self):
        return self._search_history(-1)

    @shortcut(K.chain(K.CTRL, K.SHIFT, K.R), 'Search history down')
    def search_history_down(self):
        return self._search_history(1)

    @shortcut(K.chain(K.CTRL, K.SPACE), 'Complete path by prefix')
    def path_complete(self):
        currentPath = self.text
        if currentPath:
            dir, prefix = os.path.split(currentPath)
            names = os.listdir(os.path.expanduser(dir))
            for name in names:
                if name.startswith(prefix):
                    suffix = name[len(prefix):]
                    if self.input(suffix):
                        return EVENT_HANDLED
