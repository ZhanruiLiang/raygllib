import collada
import numpy as np

from . import utils
from .utils import debug
from . import config
from .model import Model, Material, Light, Geometry, ArmaturedModel, Joint


def build_geometry(scene, mesh, geometryCollada):
    geom = geometryCollada
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
    # return CompressedGeometry(
    return Geometry(
        name, poly.vertex, poly.normal,
        (poly.texcoordset[0] if indexTupleSize == 3 else None),
        index, material,
    )


def build_joints(node, parent, joints):
    joint = Joint(node.xmlnode.attrib['sid'], parent, None, node.matrix)
    joints.append(joint)
    for subNode in node.children:
        build_joints(subNode, joint, joints)


def load_scene(path):
    mesh = collada.Collada(path)
    scene = Scene()
    joints = None

    for node in mesh.scene.nodes:
        matrix = node.matrix
        node = node.children[0]
        # debug(type(node))
        if isinstance(node, collada.scene.CameraNode):
            # camera = Camera(pos, (0, 0, 0), up)
            # scene.camera.append(camera)
            pass
        elif isinstance(node, collada.scene.GeometryNode):
            geometry = build_geometry(scene, mesh, node.geometry)
            scene._geometries.append(geometry)
            model = Model(geometry.name, geometry, matrix)
            scene.models.append(model)
        elif isinstance(node, collada.scene.ControllerNode):
            controller = node.controller
            geom = node.controller.geometry
            geometry = build_geometry(scene, mesh, geom)
            scene._geometries.append(geometry)

            maxJointsPerVertex = 4
            nVertices = len(controller.weight_index)
            poly = geom.primitives[0]
            vertexIds = poly.index[:, 0]
            weightData = controller.weights.data.flatten()
            weightIndex = controller.weight_index
            weights = np.zeros((nVertices, maxJointsPerVertex), dtype=np.float32)
            jointIds = np.zeros((nVertices, maxJointsPerVertex), dtype=np.float32)
            jointIndex = controller.joint_index
            nExceedVertex = 0
            for i in range(nVertices):
                wIndex = weightIndex[i]
                jIndex = jointIndex[i]
                nJoints = len(jIndex)
                if nJoints > maxJointsPerVertex:
                    nExceedVertex += 1
                    data = list(zip(-weightData[wIndex], jIndex))
                    data.sort()
                    data = data[:maxJointsPerVertex]
                    weights[i, :] = [-w for w, _ in data]
                    jointIds[i, :] = [j for _, j in data]
                else:
                    weights[i, :nJoints] = weightData[wIndex]
                    jointIds[i, :nJoints] = jIndex
            debug('WARNNING: nExceedVertex', nExceedVertex)
            weights = weights[vertexIds]
            jointIds = jointIds[vertexIds]
            # Make joints
            # debug('bind_shape_matrix', utils.format_matrix(controller.bind_shape_matrix))
            for joint in joints:
                joint.invBindMatrix =\
                    controller.joint_matrices[joint.name.encode('utf-8')]

            # Make armatured model
            matrix = controller.bind_shape_matrix
            model = ArmaturedModel(
                geometry.name, geometry, matrix, weights, jointIds, joints)

            scene.models.append(model)
        elif isinstance(node, collada.scene.LightNode):
            daeLight = node.light
            light = Light(matrix[0:3, 3], daeLight.color, config.defaultLightPower)
            scene.lights.append(light)
        else:
            attrib = node.xmlnode.attrib
            type = attrib.get('type', '') or attrib.get('TYPE')
            if type.lower() == 'joint':
                joints = []
                build_joints(node, None, joints)

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
            light = Light((10., 10., 10.), (1., 1., 1.), config.defaultLightPower)
        self.lights.append(light)
        for viewer in self.viewers:
            viewer.on_add_light(light)

    def free(self):
        for geometry in self._geometries:
            geometry.free()
        for model in self.models:
            model.free()
        self.models = []
        self.viewers = []
        self.lights = []

    def __del__(self):
        self.free()
