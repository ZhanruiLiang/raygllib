import os
import numpy as np
from OpenGL.GL import *
from .gllib import Program, TextureUnit 

curDir = os.path.split(__file__)[0]

def get_shader_path(name):
    return os.path.join(curDir, 'shaders', name)


class Renderer(Program):
    def __init__(self):
        super().__init__([
            (get_shader_path('model.v.glsl'), GL_VERTEX_SHADER),
            (get_shader_path('model.f.glsl'), GL_FRAGMENT_SHADER),
        ], [
            ('vertexPos', 3, GL_FLOAT),
            ('vertexNormal', 3, GL_FLOAT),
            ('vertexUV', 2, GL_FLOAT),
        ])
        self.textureUnit = TextureUnit(0)

    def set_MVP(self, modelMat, viewMat, projMat):
        glUniformMatrix4fv(self.get_uniform_loc('modelMat'), 1, GL_TRUE, modelMat)
        glUniformMatrix4fv(self.get_uniform_loc('viewMat'), 1, GL_TRUE, viewMat)
        glUniformMatrix4fv(self.get_uniform_loc('projMat'), 1, GL_TRUE, projMat)

    def set_matrix(self, name, mat):
        glUniformMatrix4fv(self.get_uniform_loc(name), 1, GL_TRUE, mat)

    def set_material(self, material):
        glActiveTexture(self.textureUnit.glenum)
        glBindTexture(GL_TEXTURE_2D, material.textureId)
        glUniform1i(self.get_uniform_loc('textureSampler'), self.textureUnit.id)
        glUniform1f(self.get_uniform_loc('shininess'), material.shininess)
        glUniform3f(self.get_uniform_loc('Ka'), *material.Ka)
        glUniform3f(self.get_uniform_loc('Ks'), *material.Ks)

    def set_lights(self, lights):
        n = len(lights)
        glUniform1fv(self.get_uniform_loc('lightPower'), n,
            np.array([light.power for light in lights], 'f'))
        glUniform3fv(self.get_uniform_loc('lightColor'), n,
            np.array([light.color for light in lights], 'f'))
        glUniform3fv(self.get_uniform_loc('lightPosCamSpace'), n,
            np.array([light.pos for light in lights], 'f'))
        glUniform1i(self.get_uniform_loc('nLights'), n)

    def draw_model(self, model):
        self.set_buffer('vertexPos', model.vertices)
        self.set_buffer('vertexNormal', model.normals)
        self.set_buffer('vertexUV', model.texcoords)
        self.set_material(model.material)
        self.set_matrix('modelMat', model.matrix)
        self.draw(GL_TRIANGLES, len(model.vertices))
