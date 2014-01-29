from raygllib import panel
from raygllib.model import Light, Material
from raygllib._threadutils import Require
from time import sleep

mainPanel = panel.ControlPanel()

light = Light((1, 2, 3), color=(1., 1., 1.), power=200)
mainPanel.add_light(light)

light = Light((2, 3, 4), color=(1., 1., 1.), power=500)
mainPanel.add_light(light)

material = Material(
    'test material', Material.DIFFUSE_COLOR, (.1, .2, .3),
    Ka=(.2, .3, .4), Ks=(1., 1., 1.), shininess=50)
mainPanel.add_material(material)

class MockViewer:
    enableToonRender = True
    toonRenderEdges = [.5, .7, .9]

    def __init__(self):
        self.require = Require(self)

    def load_scene(self, path):
        print('load scene:', path)

viewer = MockViewer()
mainPanel.add_misc(viewer)

mainPanel.start()

while 1:
    with mainPanel.lock:
        viewer.require.resolve()
    sleep(0.02)
