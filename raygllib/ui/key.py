from pyglet.window.key import *

SHIFT = object()
ALT = object()
CTRL = object()

MODIFIERS = [SHIFT, ALT, CTRL]

class KeyCombination:
    mask = 0
    key = None

    def __hash__(self):
        return hash((self.key, self.mask))

    def __repr__(self):
        return 'KeyCombination({}, {})'.format(self.key, self.mask)


def chain(*keys):
    kc = KeyCombination()
    for key in keys:
        if key is SHIFT:
            kc.mask |= MOD_SHIFT
        elif key is ALT:
            kc.mask |= MOD_ALT
        elif key is CTRL:
            kc.mask |= MOD_CTRL
        elif kc.key is None:
            kc.key = key
        else:
            raise Exception('Invalid key combination')

    return kc
