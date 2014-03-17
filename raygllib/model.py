import pyximport
pyximport.install()

import collada
from OpenGL.GL import *
from .gllib import VertexBuffer, Texture2D, IndexBuffer
import numpy as np

from . import _model
from . import utils
from . import matlib as M
from . import config
from .utils import debug

def vector(v):
    return np.array(v, dtype=np.float32)


def get_bound_box(vs):
    """
    :param np.ndarray vs: A list of vertices
    """
    m = vs.shape[1]
    result = ()
    for i in range(m):
        result += (vs[:, i].min(), vs[:, i].max())
    return result


class AdjacencyVertexBuffer:
    # @profile
    def __init__(self, vertices, indices):
        indices = indices.astype(GLuint)
        adjIndices = _model.make_adj_indices(indices)
        self.vertices = VertexBuffer(np.array(vertices, dtype=GLfloat), GL_STATIC_DRAW)
        self.indices = IndexBuffer(np.array(adjIndices, dtype=GLuint), GL_STATIC_DRAW)
        utils.debug('nVertices', len(vertices), 'nAdjIndices', len(self.indices))

    def bind(self):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indices.glId)

    def draw(self):
        glDrawElements(GL_TRIANGLES_ADJACENCY, len(self.indices), GL_UNSIGNED_INT, None) 


class Geometry:
    def __init__(self, name, vertices, normals, texcoords, indices, material):
        self.name = name
        self.vertices = VertexBuffer(
            np.array(vertices[indices[:, 0]], dtype=GLfloat), GL_STATIC_DRAW)
        self.normals = VertexBuffer(
            np.array(normals[indices[:, 1]], dtype=GLfloat), GL_STATIC_DRAW)
        if texcoords is not None:
            self.texcoords = VertexBuffer(
                np.array(texcoords[indices[:, 2]], dtype=GLfloat), GL_STATIC_DRAW)
        else:
            self.texcoords = None
        # with utils.timeit_context('Build AdjacencyVertexBuffer'):
        self.adjVertices = AdjacencyVertexBuffer(vertices, indices[:, 0])
        self.material = material

    def __repr__(self):
        return '{}(nVertices={})'.format(self.__class__.__name__, len(self.vertices))

    def free(self):
        self.vertices.free()
        self.normals.free()
        self.adjVertices.vertices.free()
        self.adjVertices.indices.free()
        if self.texcoords is not None:
            self.texcoords.free()
        if self.material.diffuseType == Material.DIFFUSE_TEXTURE:
            self.material.diffuse.free()

    def draw(self):
        glDrawArrays(GL_TRIANGLES, 0, len(self.vertices))


class CompressedGeometry(Geometry):
    @staticmethod
    def make_single_index(bufs, index):
        h = {}
        n, m = index.shape
        newBufs = [np.zeros((n, buf.shape[1]), dtype=GLfloat) for buf in bufs]
        newIndex = np.zeros(n, dtype=GLuint)
        newBufSize = 0
        for i in range(n):
            # key = tuple(index[i])
            key = ()
            for j in range(m):
                key += tuple(bufs[j][index[i, j]])
            if key in h:
                newIndex[i] = h[key]
            else:
                for j in range(m):
                    newBufs[j][newBufSize] = bufs[j][index[i, j]]
                newIndex[i] = h[key] = newBufSize
                newBufSize += 1
        newBufs = [buf[:newBufSize] for buf in newBufs]
        utils.debug('compress: nBefore={}, nAfter={}, rate={}'.format(
            n, newBufSize, newBufSize / n))
        return newBufs, newIndex

    def __init__(self, name, vertices, normals, texcoords, indices, material):
        self.name = name
        self.material = material

        self.adjVertices = AdjacencyVertexBuffer(vertices, indices[:, 0])

        bufs = [vertices, normals, texcoords]\
            if texcoords is not None else [vertices, normals]
        with utils.timeit_context('Compress'):
            # newBufs, newIndex = self.make_single_index(bufs, indices)
            newBufs, newIndex = _model.make_single_index_1(bufs, indices)
        self.vertices = VertexBuffer(newBufs[0])
        self.normals = VertexBuffer(newBufs[1])
        if texcoords is not None:
            self.texcoords = VertexBuffer(newBufs[2])
        else:
            self.texcoords = None
        self.indices = IndexBuffer(newIndex)

    def free(self):
        super().free()
        self.indices.free()

    def draw(self):
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.indices.glId)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)


class Model:
    def __init__(self, name, geometry, matrix):
        self.name = name
        self.geometry = geometry
        self.matrix = matrix.astype(GLfloat)

    def update(self, dt):
        pass

    def free(self):
        pass


class Joint:
    id = -1

    def __init__(self, name, parent, invBindMatrix, matrix):
        self.name = name
        self.parent = parent
        self.invBindMatrix = invBindMatrix
        self._matrixOrigin = matrix.copy()
        self.matrix = matrix
        self._angle = 0.

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, angle):
        if np.abs(self._angle - angle) < 1e-4:
            return
        self._angle = angle
        # m0 = self._matrixOrigin
        # R = M.rotate(angle, m0[:3, 3] / m0[3, 3], m0[:3, 0])
        # self.matrix = R.dot(m0)
        c = np.cos(angle)
        s = np.sin(angle)
        xy = (0, 1)
        self.matrix = self._matrixOrigin.copy()
        self.matrix[0:3, xy] =\
            self._matrixOrigin[0:3, xy].dot(np.array([[c, -s], [s, c]]))

    def update(self):
        if self.parent:
            self.globalMatrix = np.dot(self.parent.globalMatrix, self.matrix)
        else:
            self.globalMatrix = self.matrix

    def __repr__(self):
        if self.parent:
            return 'Joint({}, {}, parent={})'.format(self.id, self.name, self.parent.name)
        else:
            return 'Joint({}, {})'.format(self.id, self.name)


class ArmaturedModel(Model):
    def __init__(self, name, geometry, matrix, vertexWeights, vertexJointIds, joints):
        """
        joints must be sorted in topology order.
        """
        super().__init__(name, geometry, matrix)
        self.vertexWeights = VertexBuffer(vertexWeights)
        self.vertexJointIds = VertexBuffer(vertexJointIds)
        self.joints = joints
        if config.drawJointAxis:
            self.axies = [Axis(0.1, joint.matrix) for joint in joints]
        self.update(0)

    def free(self):
        self.vertexWeights.free()
        self.vertexJointIds.free()

    def get_joint_matrices(self):
        return self._matrices.flatten()

    # def validate(self):
    #     joints = self.joints
    #     for joint in joints:
    #         joint.update()
    #         debug(utils.format_matrix(joint.matrix.dot(joint.invBindMatrix)))

    def update(self, dt):
        joints = self.joints
        matrices = np.zeros((4 * len(joints), 4), dtype=GLfloat)
        for i, joint in enumerate(joints):
            joint.update()
            if config.drawJointAxis:
                axis = self.axies[i]
                axis.matrix = joint.globalMatrix.dot(M.scale(axis.scale))
            id = joint.id
            matrices[id * 4:id * 4 + 4, :] = \
                np.dot(joint.globalMatrix, joint.invBindMatrix).T
        self._matrices = matrices


class Material:
    """
    Attributes: Ns, Ka, Ks, Ni, d, illum
    """
    DIFFUSE_COLOR = 0
    DIFFUSE_TEXTURE = 1

    MAX_SHININESS = 500

    def __init__(self, name, diffuse_type, diffuse, **attrs):
        self.name = name
        for k, v in attrs.items():
            setattr(self, k, v)
        self.diffuseType = diffuse_type
        self.diffuse = diffuse
        if self.diffuseType == self.DIFFUSE_TEXTURE:
            self.diffuse = Texture2D(diffuse)

    def __repr__(self):
        return 'Material(name={}, diffuseType={})'.format(self.name, self.diffuseType)


class Light:
    MAX_POWER = 10
    MAX_RANGE = 100

    def __init__(self, pos, color, power):
        self.pos = vector(pos)
        self.color = color
        self.power = power
        self.enabled = True


class Axis(Model):
    _geometry = None

    @classmethod
    def get_geometry(cls):
        if cls._geometry is None:
            scene = Scene.load(utils.file_relative_path(__file__, 'models', 'axis.dae'))
            cls._geometry = scene.geometries[0]
        return cls._geometry

    def __init__(self, scale, matrix):
        self.scale = scale
        super().__init__('axis', self.get_geometry(), matrix)


def load_scene(path):
    mesh = collada.Collada(path)
    scene = Scene()
    jointRoots = {}
    for node in mesh.scene.nodes:
        matrix = node.matrix
        nodeName = node.xmlnode.attrib.get('name', None)
        node = node.children[0]
        # debug(type(node))
        if isinstance(node, collada.scene.CameraNode):
            # camera = Camera(pos, (0, 0, 0), up)
            # scene.camera.append(camera)
            pass
        elif isinstance(node, collada.scene.GeometryNode):
            geometry = build_geometry(scene, mesh, node.geometry)
            scene.geometries.append(geometry)
            model = Model(nodeName, geometry, matrix)
            scene.add_model(model)
        elif isinstance(node, collada.scene.ControllerNode):
            controller = node.controller
            geom = node.controller.geometry
            geometry = build_geometry(scene, mesh, geom)
            scene.geometries.append(geometry)

            maxJointsPerVertex = 4
            nVertices = len(controller.weight_index)
            poly = geom.primitives[0]
            vertexIds = poly.index[:, 0]
            weightData = controller.weights.data.flatten()
            weightIndex = controller.weight_index
            weights = np.zeros((nVertices, maxJointsPerVertex), dtype=GLfloat)
            jointIds = np.zeros((nVertices, maxJointsPerVertex), dtype=GLfloat)
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
                    weights[i] /= weights[i].sum()
                    jointIds[i, :] = [j for _, j in data]
                    # weights[i, :] = 0
                else:
                    weights[i, :nJoints] = weightData[wIndex]
                    jointIds[i, :nJoints] = jIndex
            debug('WARNNING: nExceedVertex', nExceedVertex)
            weights = weights[vertexIds]
            jointIds = jointIds[vertexIds]
            # Make joints
            # import pdb; pdb.set_trace()
            joints = jointRoots[controller.xmlnode.attrib['name'].replace('.', '_')]
            for joint in joints:
                joint.invBindMatrix =\
                    controller.joint_matrices[joint.name.encode('utf-8')]
            debug('nJoinst:', len(joints))

            jointSouce = controller.sourcebyid[controller.joint_source]
            nameToJoint = {joint.name: joint for joint in joints}
            for i, name in enumerate(jointSouce):
                joint = nameToJoint[name.decode('utf-8')]
                joint.id = i
            del nameToJoint, jointSouce

            # list(map(debug, joints))

            # Make armatured model
            # debug('model matrix', matrix)
            matrix = controller.bind_shape_matrix
            # debug('bind_shape_matrix', matrix)
            model = ArmaturedModel(nodeName, geometry, matrix, weights, jointIds, joints)

            scene.add_model(model)
        elif isinstance(node, collada.scene.LightNode):
            daeLight = node.light
            light = Light(matrix[0:3, 3], daeLight.color, config.defaultLightPower)
            scene.lights.append(light)
        else:
            attrib = node.xmlnode.attrib
            type = attrib.get('type', '') or attrib.get('TYPE')
            if type.lower() == 'joint':
                joints = []
                build_joint_hierachy(node, matrix, None, joints)
                jointRoots[nodeName] = joints
    return scene


def build_joint_hierachy(node, matrix, parent, joints):
    joint = Joint(node.xmlnode.attrib['sid'], parent, None, matrix.dot(node.matrix))
    joints.append(joint)
    for subNode in node.children:
        build_joint_hierachy(subNode, np.eye(4, dtype=np.float32), joint, joints)


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
    debug('load geometry: nVertices={}, nFaces={}, nIndices={}'.format(
        len(poly.vertex), len(index) // 3, len(index)))
    # return CompressedGeometry(
    return Geometry(
        name, poly.vertex, poly.normal,
        (poly.texcoordset[0] if indexTupleSize == 3 else None),
        index, material,
    )


class Scene:
    @classmethod
    def load(self, path):
        with utils.timeit_context('load model'):
            scene = load_scene(path)
        return scene

    def __init__(self):
        self.lights = []
        self._models = {}
        self.geometries = []

    @property
    def models(self):
        return self._models.values()

    def add_model(self, model):
        assert model.name not in self._models
        self._models[model.name] = model

    def pop_model(self, name):
        self._models.pop(name)

    def get_model(self, name):
        for model in self.models:
            if model.name == name:
                return model
        raise KeyError(name)

    def add_light(self, light=None):
        if not light:
            light = Light((10., 10., 10.), (1., 1., 1.), config.defaultLightPower)
        self.lights.append(light)

    def free(self):
        for geometry in self.geometries:
            geometry.free()
        for model in self.models:
            model.free()
        self._models.clear()
        self.lights.clear()

    def update(self, dt):
        for model in self.models:
            model.update(dt)

    def __del__(self):
        self.free()
