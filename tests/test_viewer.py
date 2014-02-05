import crash_on_ipy
from raygllib.viewer import Viewer, ShadowedViewer
from raygllib.camera import Camera
from raygllib.scene import Scene
import raygllib.config as config

config.debug = True

# path = '/home/ray/graduate/src/models/men-ani.dae'
# path = '/home/ray/graduate/src/guitar_builder/xx.dae'
# path = '/home/ray/graduate/guitar/guitar.dae'
path = '/home/ray/graduate/src/models/men.dae'
# path = '/home/ray/graduate/src/models/men20/men20-export.dae'
# path = '/home/ray/graduate/guitar-1/Guitar-1.dae'
# path = '/home/ray/graduate/src/models/stick2.dae'
# path = '/home/ray/graduate/src/models/bunny.dae'
viewer = Viewer()
viewer.load_scene(path)
# viewer.camera = Camera((1, 2, 2), (0, 0, 0), (1, 0, 0))
viewer.show()
