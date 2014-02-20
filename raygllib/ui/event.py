EVENT_HANDLED = True
EVENT_UNHANDLED = None

class EventHandler:
    def on_key_press(self, symbol, modifiers):
        pass

    def on_mouse_drag(self, x, y, dx, dy, buttons, modifiers):
        pass

    def on_mouse_motion(self, x, y, dx, dy):
        pass

    def on_mouse_press(self, x, y, button, modifiers):
        pass

    def on_mouse_scroll(self, x, y, button, modifiers):
        pass

    def on_mouse_release(self, x, y, button, modifiers):
        pass


class SignalDispatcher:
    signals = []

    def __init__(self):
        self._signalHandlers = {signal: [] for signal in self.signals}
        self._handlerId = 0

    def connect_signal(self, signal, handler, *args):
        assert signal in self._signalHandlers
        func = lambda: handler(*args)
        func.handerId = handlerId = self._handlerId
        self._handlerId += 1
        self._signalHandlers[signal].append(func)
        return handlerId

    def disconnect_signal(self, signal, handlerId):
        handlers = self._signalHandlers[signal]
        for i, f in enumerate(handlers):
            if f.handlerId == handlerId:
                handlers.pop(i)
                break
        else:
            raise KeyError((signal, handlerId))

    def emit_signal(self, signal):
        for handler in self._signalHandlers[signal]:
            handler()
