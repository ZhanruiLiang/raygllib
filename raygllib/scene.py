class Scene:
    def __init__(self):
        self.lights = []
        self.models = []

    def draw(self, renderer):
        R = renderer
        R.set_lights(self.lights)
        for model in self.models:
            R.draw_model(model)
