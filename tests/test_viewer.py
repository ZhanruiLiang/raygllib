import crash_on_ipy
from raygllib.viewer import Viewer
from raygllib.camera import Camera
import raygllib.config as config

config.debug = True

path = '/home/ray/graduate/src/models/men.dae'
# path = '/home/ray/graduate/src/models/men-ani.dae'
# path = '/home/ray/graduate/src/guitar_builder/xx.dae'
# path = '/home/ray/graduate/guitar/guitar.dae'
# path = '/home/ray/graduate/guitar-1/Guitar-1.dae'
# path = '/tmp/xx.dae'
viewer = Viewer(path)
models = viewer.scene.models
# for model in models:
#     print(model.get_bbox())
#     print(model.matrix)
# viewer.camera = Camera((1, 2, 2), (0, 0, 0), (1, 0, 0))
if not viewer.scene.lights:
    viewer.add_light_auto()
    viewer.add_light_auto()
if models:
    viewer.camera.set_target(models[0])
viewer.show()
