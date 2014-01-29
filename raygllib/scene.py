from .model import Light

class Scene:
    def __init__(self):
        self.lights = []
        self.models = []
        self.viewers = []

    def add_light(self, light=None):
        if not light:
            light = Light((10., 10., 10.), (1., 1., 1.), 500)
        self.lights.append(light)
        for viewer in self.viewers:
            viewer.on_add_light(light)

    def add_camera_auto(self):
        pass
