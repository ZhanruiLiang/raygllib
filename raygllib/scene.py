import collada

from . import utils
from .model import Model, Material, Light

def load_scene(path):
    mesh = collada.Collada(path)
    scene = Scene()

    for node in mesh.scene.nodes:
        matrix = node.matrix
        node = node.children[0]
        # debug(type(node))
        if isinstance(node, collada.scene.CameraNode):
            # camera = Camera(pos, (0, 0, 0), up)
            # scene.camera.append(camera)
            pass
        elif isinstance(node, collada.scene.GeometryNode):
            geom = node.geometry
            # debug('load geometry:', geom.name)
            poly = geom.primitives[0]
            daeMat = mesh.materials[poly.material]
            if hasattr(daeMat.effect.diffuse, 'sampler'):
                diffuse = daeMat.effect.diffuse.sampler.surface.image.getImage()
                indexTupleSize = 3
                diffuseType = Material.DIFFUSE_TEXTURE
            else:
                indexTupleSize = 2
                diffuse = daeMat.effect.diffuse[:3]
                diffuseType = Material.DIFFUSE_COLOR
            material = Material(
                daeMat.name, diffuseType, diffuse,
                Ka=(daeMat.effect.ambient[:3]
                    if not isinstance(daeMat.effect.ambient, collada.material.Map)
                    else (0., 0., 0.)),
                Ks=daeMat.effect.specular[:3],
                shininess=daeMat.effect.shininess,
            )
            index = poly.index.flatten()
            index = index.reshape((len(index) // indexTupleSize, indexTupleSize))
            model = Model(
                poly.vertex,
                poly.normal,
                (poly.texcoordset[0] if indexTupleSize == 3 else None),
                index, material, matrix,
            )
            scene.models.append(model)
        elif isinstance(node, collada.scene.LightNode):
            daeLight = node.light
            light = Light(matrix[0:3, 3], daeLight.color, 500)
            scene.lights.append(light)
    return scene


class Scene:
    @classmethod
    def load(self, path):
        with utils.timeit_context('load model'):
            scene = load_scene(path)
        return scene

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

    def free(self):
        for model in self.models:
            model.free()
        self.models = []
        self.viewers = []
        self.lights = []

    def __del__(self):
        self.free()
