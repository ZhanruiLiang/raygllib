import unittest
import os
from raygllib import scene

def get_model_path(name):
    return os.path.join(os.path.dirname(__file__), 'models', name)


class TestScene(unittest.TestCase):
    def test_load(self):
        aScene = scene.Scene.load(get_model_path('scene.dae'))
        assert aScene.models
