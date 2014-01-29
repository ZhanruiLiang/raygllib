from OpenGL.GL import *
# import numpy as np
from contextlib import contextmanager
from threading import RLock
from . import utils


def compile_shader(source, shaderType):
    """
    source: str source code
    shaderType: GL_VERTEX_SHADER, GL_FRAGMENT_SHADER or GL_GEOMETRY_SHADER
    """
    shader = glCreateShader(shaderType)
    glShaderSource(shader, source)
    glCompileShader(shader)
    result = glGetShaderiv(shader, GL_COMPILE_STATUS)
    info = glGetShaderInfoLog(shader).decode('utf-8')
    if info:
        print('Shader compilation info:\n{}'.format(info))
    if result == GL_FALSE:
        raise Exception('GLSL compile error: {}'.format(shaderType))
    return shader

class GLResource:
    def __init__(self, method, args):
        self.method = method
        self.args = args

    def free(self):
        if self.method is None:
            return
        utils.debug('delete resource', self, trace=True)
        self.method(*self.args)
        self.method = None

    def __del__(self):
        assert self.method is None

class Texture2D(GLResource):
    MAG_FILTER = GL_LINEAR
    MIN_FILTER = GL_LINEAR_MIPMAP_LINEAR

    def __init__(self, image):
        self.textureId = self.make_texture(image)
        GLResource.__init__(self, glDeleteTextures, ([self.textureId],))

        glBindTexture(GL_TEXTURE_2D, self.textureId)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, self.MAG_FILTER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, self.MIN_FILTER)
        glGenerateMipmap(GL_TEXTURE_2D)

    def make_texture(self, image):
        data = image.convert('RGBA').tobytes()
        width, height = image.size
        glEnable(GL_TEXTURE_2D)
        textureId = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, textureId)
        assert textureId > 0, 'Fail to get new texture id.'
        glTexImage2D(
            GL_TEXTURE_2D, 0,
            GL_RGBA,  # internal format
            width, height,
            0,  # border, must be 0
            GL_RGBA,  # input data format
            GL_UNSIGNED_BYTE,
            data,
        )
        return textureId


class VertexBuffer(GLResource):
    def __init__(self, data, usage_hint=GL_STATIC_DRAW):
        """
        :param numpy.ndarray data: Data that to be put into buffer
        :param GLenum usage_hint: The last parameter of glBufferData
        """
        self.usageHint = usage_hint
        self._set_data(data)
        GLResource.__init__(self, glDeleteBuffers, (1, [self.bufferId]))

    def _set_data(self, data):
        self.data = data
        self.bufferId = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, self.bufferId)
        glBufferData(GL_ARRAY_BUFFER, data, self.usageHint)

    def __getstate__(self):
        state = self.__dict__.copy()
        state['usageHint'] = repr(self.usageHint)
        return state

    def __setstate__(self, state_dict):
        self.__dict__ = state_dict
        self.usageHint = globals()[self.usageHint]
        self._set_data(self.data)

    def __len__(self):
        return len(self.data)


class VertexBufferSlot:
    def __init__(self, location, item_size, data_type):
        self.location = location
        self.itemSize = item_size
        self.dataType = data_type

    def set_buffer(self, buffer):
        glBindBuffer(GL_ARRAY_BUFFER, buffer.bufferId)
        glVertexAttribPointer(
            self.location, self.itemSize, self.dataType, GL_FALSE, 0, None)


class Program:
    def __init__(self, shader_datas, bufs):
        """
        shader_datas: A list of (filename, shaderType) tuples.
        """
        self.id = glCreateProgram()
        shaders = []
        try:
            for name, type in shader_datas:
                source = open(name, 'r').read()
                shader = compile_shader(source, type)
                glAttachShader(self.id, shader)
                shaders.append(shader)
            glLinkProgram(self.id)
        finally:
            for shader in shaders:
                glDeleteShader(shader)
        assert self.check_linked()
        assert self.check_valid()
        self._init_buffers(bufs)

    def __del__(self):
        try:
            glDeleteVertexArrays(1, [self.vao])
        except TypeError:
            # OpenGL is destroyed.
            pass

    def _init_buffers(self, bufs):
        """
        bufs: [(name, size, type)]
        """
        self._buffers = {}
        self.vao = glGenVertexArrays(1)
        glBindVertexArray(self.vao)

        for name, size, type in bufs:
            loc = self.get_attrib_loc(name)
            self._buffers[name] = VertexBufferSlot(loc, size, type)

    def set_buffer(self, name, data):
        self._buffers[name].set_buffer(data)

    @contextmanager
    def batch_draw(self):
        self.use()
        self.enable_attribs()
        self.prepare_draw()
        yield
        self.post_draw()
        self.disable_attribs()
        self.unuse()

    def prepare_draw(self):
        pass

    def post_draw(self):
        pass

    def enable_attribs(self):
        for buf in self._buffers.values():
            glEnableVertexAttribArray(buf.location)

    def disable_attribs(self):
        for buf in self._buffers.values():
            glDisableVertexAttribArray(buf.location)

    def draw(self, primitive_type, count):
        glDrawArrays(primitive_type, 0, count)

    def get_uniform_loc(self, name):
        if isinstance(name, str):
            name = name.encode('utf-8')
        loc = glGetUniformLocation(self.id, name)
        assert loc >= 0, 'Get uniform {} failed'.format(name)
        return loc

    def get_attrib_loc(self, name):
        if isinstance(name, str):
            name = name.encode('utf-8')
        loc = glGetAttribLocation(self.id, name)
        assert loc >= 0, 'Get attribute {} failed'.format(name)
        return loc

    def print_info(self):
        info = glGetProgramInfoLog(self.id).decode('ascii')
        if info:
            print('Program info log:', info)

    def check_valid(self):
        glValidateProgram(self.id)
        result = glGetProgramiv(self.id, GL_VALIDATE_STATUS)
        if result == GL_FALSE:
            self.print_info()
            return False
        return True

    def check_linked(self):
        result = glGetProgramiv(self.id, GL_LINK_STATUS)
        if result == GL_FALSE:
            self.print_info()
            return False
        return True

    def use(self):
        glUseProgram(self.id)

    def unuse(self):
        glUseProgram(0)

    def delete(self):
        if self.id is not None:
            glDeleteProgram(self.id)
            self.id = None

class TextureUnit:
    def __init__(self, id):
        self.id = id
        self.glenum = globals()['GL_TEXTURE' + str(id)]
