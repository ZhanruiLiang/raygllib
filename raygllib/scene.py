import collada

from . import utils
from . import config
from .model import Model, Material, Light, Geometry, CompressedGeometry

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
            name = geom.name
            poly = geom.primitives[0]
            daeMat = mesh.materials[poly.material]
            if hasattr(daeMat, '_gllibMaterail'):
                material = daeMat._gllibMaterail
            else:
                if hasattr(daeMat.effect.diffuse, 'sampler'):
                    diffuse = daeMat.effect.diffuse.sampler.surface.image.getImage()
                    diffuseType = Material.DIFFUSE_TEXTURE
                else:
                    diffuse = daeMat.effect.diffuse[:3]
                    diffuseType = Material.DIFFUSE_COLOR
                material = daeMat._gllibMaterail = Material(
                    daeMat.name, diffuseType, diffuse,
                    Ka=(daeMat.effect.ambient[:3]
                        if not isinstance(daeMat.effect.ambient, collada.material.Map)
                        else (0., 0., 0.)),
                    Ks=daeMat.effect.specular[:3],
                    shininess=daeMat.effect.shininess,
                )
            index = poly.index
            indexTupleSize = 3 if material.diffuseType == Material.DIFFUSE_TEXTURE else 2
            index = index.reshape((index.size // indexTupleSize, indexTupleSize))
            # geometry = CompressedGeometry(
            geometry = Geometry(
                name, poly.vertex, poly.normal,
                (poly.texcoordset[0] if indexTupleSize == 3 else None),
                index, material,
            )
            scene._geometries.append(geometry)
            model = Model(name, geometry, matrix)
            scene.models.append(model)
        elif isinstance(node, collada.scene.LightNode):
            daeLight = node.light
            light = Light(matrix[0:3, 3], daeLight.color, config.defaultLightPower)
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
        self._geometries = []

    def get_model(self, name):
        for model in self.models:
            if model.name == name:
                return model
        raise KeyError(name)

    def add_light(self, light=None):
        if not light:
            light = Light((10., 10., 10.), (1., 1., 1.), 800)
        self.lights.append(light)
        for viewer in self.viewers:
            viewer.on_add_light(light)

    def free(self):
        for geometry in self._geometries:
            geometry.free()
        self.models = []
        self.viewers = []
        self.lights = []

    def __del__(self):
        self.free()
