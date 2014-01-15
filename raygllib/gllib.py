import OpenGL.GL as gl
from OpenGL.arrays import vbo
import numpy as np

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


class Program:
    def __init__(self, shader_datas):
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

        self._buffers = {}

    def init_buffers(self, bufs):
        """
        bufs: [(name, size, type)]
        """
        for name, size, type in bufs:
            loc = self.get_attrib_loc(name)
            self._buffers[name] = loc, size, type, vbo.VBO(np.zeros(0))

    def set_buffer(self, name, data):
        loc, size, type, buf = self._buffers[name]
        buf.set_array(data)
        buf.bind()
        gl.glEnableVertexAttribArray(loc)
        gl.glVertexAttribPointer(loc, size, type, gl.GL_FALSE, 0, None)

    def draw(self, primitive_type, count):
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
    ENUMS = [gl.GL_TEXTURE0, gl.GL_TEXTURE1, gl.GL_TEXTURE2, gl.GL_TEXTURE3]  # FIXME

    def __init__(self, id):
        self.id = id
        self.glenum = self.ENUMS[id]
