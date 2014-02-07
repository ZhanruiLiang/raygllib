import unittest
import raygllib.config as config
from raygllib.viewer import Viewer

class TestViewer(unittest.TestCase):
    def test_viewer(self):
        # from raygllib.camera import Camera
        config.debug = True

        # path = '/home/ray/graduate/src/models/men-ani.dae'
        # path = '/home/ray/graduate/src/guitar_builder/xx.dae'
        # path = '/home/ray/graduate/guitar/guitar.dae'
        # path = '/home/ray/graduate/src/models/men.dae'
        path = '/home/ray/graduate/src/models/hand.dae'
        # path = '/home/ray/graduate/src/models/men20/men20-export.dae'
        # path = '/home/ray/graduate/guitar-1/Guitar-1.dae'
        # path = '/home/ray/graduate/src/models/stick2.dae'
        # path = '/home/ray/graduate/src/models/bunny.dae'
        viewer = Viewer()
        viewer.load_scene(path)
        # viewer.camera = Camera((1, 2, 2), (0, 0, 0), (1, 0, 0))
        viewer.show()

if __name__ == '__main__':
    import crash_on_ipy
    TestViewer().test_viewer()
