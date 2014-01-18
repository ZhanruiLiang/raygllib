import OpenGL.GL as gl
from collections import namedtuple
import numpy as np
from contextlib import contextmanager

def compile_shader(source, shaderType):
    """
    source: str source code
    shaderType: GL_VERTEX_SHADER, GL_FRAGMENT_SHADER or GL_GEOMETRY_SHADER
    """
    shader = gl.glCreateShader(shaderType)
    gl.glShaderSource(shader, source)
    gl.glCompileShader(shader)
    result = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
    info = gl.glGetShaderInfoLog(shader).decode('utf-8')
    if info:
        print('Shader compilation info:\n{}'.format(info))
    if result == gl.GL_FALSE:
        raise Exception('GLSL compile error: {}'.format(shaderType))
    return shader

class VertexBuffer:
    def __init__(self, location, item_size, data_type, usage_hint):
        self.location = location
        self.itemSize = item_size
        self.dataType = data_type
        self.usage_hint = usage_hint
        self.bufferId = gl.glGenBuffers(1)

    def __del__(self):
        gl.glDeleteBuffers(1, [self.bufferId])

    def set_data(self, data):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.bufferId)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, data, self.usage_hint)

    def bind(self):
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.bufferId)
        gl.glVertexAttribPointer(
            self.location, self.itemSize, self.dataType, gl.GL_FALSE, 0, None)

BufferItem = namedtuple('BufferItem', 'loc size type buf')

class Program:
    def __init__(self, shader_datas, bufs):
        """
        shader_datas: A list of (filename, shaderType) tuples.
        """
        self.id = gl.glCreateProgram()
        shaders = []
        try:
            for name, type in shader_datas:
                source = open(name, 'r').read()
                shader = compile_shader(source, type)
                gl.glAttachShader(self.id, shader)
                shaders.append(shader)
            gl.glLinkProgram(self.id)
        finally:
            for shader in shaders:
                gl.glDeleteShader(shader)
        assert self.check_linked()
        assert self.check_valid()
        self._init_buffers(bufs)

    def __del__(self):
        gl.glBindVertexArray(0)
        gl.glDeleteVertexArrays(1, [self.vao])

    def _init_buffers(self, bufs):
        """
        bufs: [(name, size, type, usage)]
        """
        self._buffers = {}
        self.vao = gl.glGenVertexArrays(1)
        gl.glBindVertexArray(self.vao)

        for name, size, type, usage in bufs:
            loc = self.get_attrib_loc(name)
            self._buffers[name] = VertexBuffer(loc, size, type, usage)

    def set_buffer(self, name, data):
        buf = self._buffers[name]
        buf.set_data(data)

    @contextmanager
    def batch_draw(self):
        self.use()
        for buf in self._buffers.values():
            gl.glEnableVertexAttribArray(buf.location)
        yield
        for buf in self._buffers.values():
            gl.glDisableVertexAttribArray(buf.location)
        self.unuse()

    def draw(self, primitive_type, count):
        for buf in self._buffers.values():
            buf.bind()
        gl.glDrawArrays(primitive_type, 0, count)

    def get_uniform_loc(self, name):
        if isinstance(name, str):
            name = name.encode('utf-8')
        loc = gl.glGetUniformLocation(self.id, name)
        assert loc >= 0, 'Get uniform {} failed'.format(name)
        return loc

    def get_attrib_loc(self, name):
        if isinstance(name, str):
            name = name.encode('utf-8')
        loc = gl.glGetAttribLocation(self.id, name)
        assert loc >= 0, 'Get attribute {} failed'.format(name)
        return loc

    def print_info(self):
        info = gl.glGetProgramInfoLog(self.id).decode('ascii')
        if info:
            print('Program info log:', info)

    def check_valid(self):
        gl.glValidateProgram(self.id)
        result = gl.glGetProgramiv(self.id, gl.GL_VALIDATE_STATUS)
        if result == gl.GL_FALSE:
            self.print_info()
            return False
        return True

    def check_linked(self):
        result = gl.glGetProgramiv(self.id, gl.GL_LINK_STATUS)
        if result == gl.GL_FALSE:
            self.print_info()
            return False
        return True

    def use(self):
        gl.glUseProgram(self.id)

    def unuse(self):
        gl.glUseProgram(0)

    def delete(self):
        if self.id != 0:
            gl.glDeleteProgram(self.id)


class TextureUnit:
    def __init__(self, id):
        self.id = id
        self.glenum = getattr(gl, 'GL_TEXTURE' + str(id))
