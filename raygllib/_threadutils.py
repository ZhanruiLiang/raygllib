from threading import RLock

class Require(list):
    def __init__(self, owner):
        self._owner = owner
        self.lock = RLock()
        super().__init__()

    def __getattr__(self, name):
        func = getattr(self._owner, name)

        def defered_func(*args, **kwargs):
            with self.lock:
                self.append((func, args, kwargs))

        return defered_func

    def resolve(self):
        for name, args, kwargs in self:
            with self.lock:
                name(*args, **kwargs)
        self.clear()
