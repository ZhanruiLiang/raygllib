import os
import pickle
from raygllib import Program, TextureUnit, VertexBuffer
from OpenGL.GL import *
import Image
import numpy as np
import hashlib
import datetime

curDir = os.path.split(__file__)[0]

def get_path(name):
    return os.path.join(curDir, name)


class Light:
    def __init__(self, pos, color, power):
        self.pos = pos
        self.color = color
        self.power = power


class ModelRenderer(Program):
    def __init__(self):
        super().__init__([
            (get_path('model.v.glsl'), GL_VERTEX_SHADER),
            (get_path('model.f.glsl'), GL_FRAGMENT_SHADER),
        ], [
            ('vertexPos', 3, GL_FLOAT),
            ('vertexNormal', 3, GL_FLOAT),
            ('vertexUV', 2, GL_FLOAT),
        ])
        self.textureUnit = TextureUnit(0)
        self.lights = []

    def set_MVP(self, modelMat, viewMat, projMat):
        glUniformMatrix4fv(self.get_uniform_loc('modelMat'), 1, GL_TRUE, modelMat)
        glUniformMatrix4fv(self.get_uniform_loc('viewMat'), 1, GL_TRUE, viewMat)
        glUniformMatrix4fv(self.get_uniform_loc('projMat'), 1, GL_TRUE, projMat)

    def set_matrix(self, name, mat):
        glUniformMatrix4fv(self.get_uniform_loc(name), mat)

    def set_material(self, material):
        glActiveTexture(self.textureUnit.glenum)
        glBindTexture(GL_TEXTURE_2D, material.textureId)
        glUniform1i(self.get_uniform_loc('textureSampler'), self.textureUnit.id)
        glUniform1f(self.get_uniform_loc('shininess'), material.Ns)
        glUniform3f(self.get_uniform_loc('Ka'), *material.Ka)
        glUniform3f(self.get_uniform_loc('Kd'), *material.Kd)
        glUniform3f(self.get_uniform_loc('Ks'), *material.Ks)

    def add_light(self, light):
        self.lights.append(light)

    def prepare_draw(self):
        n = len(self.lights)
        glUniform1fv(self.get_uniform_loc('lightPower'), n,
            [light.power for light in self.lights])
        glUniform3fv(self.get_uniform_loc('lightColor'), n,
            [light.color for light in self.lights])
        glUniform3fv(self.get_uniform_loc('lightPosCamSpace'), n,
            [light.pos for light in self.lights])
        glUniform1i(self.get_uniform_loc('nLights'), n)

    def draw_model(self, model):
        for obj in model.objects:
            self.set_buffer('vertexPos', obj.vertices)
            self.set_buffer('vertexNormal', obj.normals)
            self.set_buffer('vertexUV', obj.texcoords)
            self.set_material(obj.material)
            self.draw(GL_TRIANGLES, len(obj.vertices))


class Material:
    """
    Attributes: Ns, Ka, Ks, Ni, d, illum
    """
    def __init__(self, name):
        self.name = name
        self.imagePath = None

    def load_image(self, image_path):
        self.imagePath = image_path
        self.textureId = make_texture(Image.open(image_path), GL_TEXTURE_2D)

    def __setstate__(self, new_dict):
        self.__dict__ = new_dict
        self.load_image(new_dict['imagePath'])


class MaterialGroup:
    def __init__(self, filename):
        dir, name = os.path.split(filename)
        self.materials = {}
        with open(filename, 'r') as infile:
            material = None
            for line in infile:
                line = line.strip()
                if not line or line[0] == '#':
                    continue
                cmd, args = line.split(' ', 1)
                if cmd == 'map_Kd':
                    imagePath = os.path.join(dir, args)
                    material.load_image(imagePath)
                elif cmd == 'Ns':
                    material.Ns = float(args)
                elif cmd == 'Ka':
                    material.Ka = parse_vec(args)
                elif cmd == 'Kd':
                    material.Kd = parse_vec(args)
                elif cmd == 'Ks':
                    material.Ks = parse_vec(args)
                elif cmd == 'Ni':
                    material.Ni = float(args)
                elif cmd == 'd':
                    material.d = float(args)
                elif cmd == 'illum':
                    material.illum = int(args)
                elif cmd == 'newmtl':
                    material = Material(args)
                    self.materials[material.name] = material

    def get(self, name):
        return self.materials[name]


class Model:
    def __init__(self):
        self.objects = []

    def finish(self):
        for obj in self.objects:
            obj.finish()


class ModelObject:
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.normals = []
        self.texcoords = []
        self.material = None

    def finish(self):
        self.vertices = VertexBuffer(
            np.array(self.vertices, dtype=GLfloat), GL_STATIC_DRAW)
        self.normals = VertexBuffer(
            np.array(self.normals, dtype=GLfloat), GL_STATIC_DRAW)
        self.texcoords = VertexBuffer(
            np.array(self.texcoords, dtype=GLfloat), GL_STATIC_DRAW)


DUMP_FOLDER = '__modeldump__'
META_FILE = 'meta'
CACHE_SIZE = 32

def load(filename, force_reload=False):
    if not os.path.exists(DUMP_FOLDER):
        os.mkdir(DUMP_FOLDER)
    metaPath = os.path.join(DUMP_FOLDER, META_FILE)
    try:
        meta = pickle.load(open(metaPath, 'rb'))
    except:
        meta = {}
    data = open(filename, 'rb').read()
    md5hash = hashlib.md5()
    md5hash.update(data)
    md5 = md5hash.digest()
    if not force_reload and md5 in meta:
        modelPath = os.path.join(DUMP_FOLDER, meta[md5][1])
        meta[md5] = datetime.datetime.now(), meta[md5][1]
        result = pickle.load(open(modelPath, 'rb'))
    else:
        result = _load(filename)
        meta[md5] = datetime.datetime.now(), md5hash.hexdigest()
        modelPath = os.path.join(DUMP_FOLDER, meta[md5][1])
        with open(modelPath, 'wb') as outfile:
            pickle.dump(result, outfile, -1)
    meta = dict(list(sorted(meta.items(), key=lambda x: x[1][0]))[:CACHE_SIZE])
    with open(metaPath, 'wb') as outfile:
        pickle.dump(meta, outfile, -1)
    return result


def _load(filename):
    name, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext == '.obj':
        return _load_obj(filename)
    elif ext == '.dae':
        return _load_collada(filename)


def _load_collada(filename):
    pass


def _load_obj(filename):
    dir, name = os.path.split(filename)
    with open(filename, 'r') as infile:
        tmpVs = tmpVs = []  # temperary vertices
        tmpVns = tmpVns = []  # temperary normals
        tmpVts = tmpVts = []  # temperary texcoords
        lineId = 0
        obj = None
        model = Model()
        for line in infile:
            line = line.strip()
            lineId += 1
            if not line:
                continue
            if line[0] == '#':
                continue
            cmd, args = line.split(' ', 1)
            if cmd == 'f':
                # face = parse_face(args)
                for triple in args.split(' '):
                    idxV, idxT, idxN = triple.split('/')
                    obj.vertices.append(tmpVs[int(idxV) - 1])
                    obj.texcoords.append(tmpVts[int(idxT) - 1])
                    obj.normals.append(tmpVns[int(idxN) - 1])
            elif cmd == 'v':
                tmpVs.append(parse_vec(args))
            elif cmd == 'vn':
                tmpVns.append(parse_vec(args))
            elif cmd == 'vt':
                tmpVts.append(parse_vec(args))
            elif cmd == 'o':
                obj = ModelObject(args)
                model.objects.append(obj)
            elif cmd == 'mtllib':
                path = os.path.join(dir, args)
                model.mtllib = MaterialGroup(path)
            elif cmd == 'usemtl':
                obj.material = model.mtllib.get(args)

            if lineId % 100 == 0:
                print('\r', lineId, end='')
    model.finish()
    return model


def parse_vec(args):
    return tuple(map(float, args.split(' ')))

def convert_index(index, default):
    return (int(index) - 1) if index else default

def parse_face(args):
    face = args.split()
    for i, indices in enumerate(face):
        face[i] = tuple(convert_index(idx, None) for idx in indices.split('/'))
    return face

def make_texture(image, target, mag_filter=GL_LINEAR, min_filter=GL_LINEAR):
    data = image.convert('RGBA').tobytes()
    width, height = image.size
    glEnable(target)
    textureId = glGenTextures(1)
    glBindTexture(target, textureId)
    assert textureId > 0, 'Fail to get new texture id.'
    glTexImage2D(
        target, 0,
        GL_RGBA,  # internal format
        width, height,
        0,  # border, must be 0
        GL_RGBA,  # input data format
        GL_UNSIGNED_BYTE,
        data,
    )
    glTexParameteri(target, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(target, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(target, GL_TEXTURE_MAG_FILTER, mag_filter)
    glTexParameteri(target, GL_TEXTURE_MIN_FILTER, min_filter)
    return textureId
