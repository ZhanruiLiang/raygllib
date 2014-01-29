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

    def set_step_edges(self, edges):
        glUniform1i(self.get_uniform_loc('nEdges'), len(edges))
        glUniform1fv(self.get_uniform_loc('edges'), len(edges), edges)

    def set_material(self, material):
        if material.diffuseType == material.DIFFUSE_TEXTURE:
            glActiveTexture(self.textureUnit.glenum)
            glBindTexture(GL_TEXTURE_2D, material.diffuse.textureId)
            glUniform1i(self.get_uniform_loc('hasSampler'), 1)
            glUniform1i(self.get_uniform_loc('textureSampler'), self.textureUnit.id)
        else:
            glBindTexture(GL_TEXTURE_2D, 0)
            glUniform1i(self.get_uniform_loc('hasSampler'), 0)
            glUniform3f(self.get_uniform_loc('diffuse'), *material.diffuse)

        glUniform1f(self.get_uniform_loc('shininess'), material.shininess)
        glUniform3f(self.get_uniform_loc('Ka'), *material.Ka)
        glUniform3f(self.get_uniform_loc('Ks'), *material.Ks)

    def set_lights(self, lights):
        lights = [light for light in lights if light.enabled]
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
        if model.texcoords:
            glEnableVertexAttribArray(self._buffers['vertexUV'].location)
            self.set_buffer('vertexUV', model.texcoords)
        else:
            glDisableVertexAttribArray(self._buffers['vertexUV'].location)
        self.set_material(model.material)
        self.set_matrix('modelMat', model.matrix)
        self.draw(GL_TRIANGLES, len(model.vertices))


class ShadowRenderer(Renderer):
    """
    Usage:
    >>>r1 = Renderer()
    >>>r2 = ShadowRenderer()
    >>>glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
    >>>with r1.batch_draw():
    >>>    r1.set_matrix('viewMat', viewMat)
    >>>    r1.set_lights(lights)
    >>>    for model in models:
    >>>        r1.draw_model(model)
    >>>for light in lights:
    >>>    with r2.batch_draw():
    >>>        r2.set_matrix('viewMat', viewMat)
    >>>        r2.set_light(light)
    >>>        for model in models:
    >>>            r2.draw_model(model)
    >>>    with r1.batch_draw():
    >>>        r1.set_matrix('viewMat', viewMat)
    >>>        r1.set_lights(lights)
    >>>        for model in models:
    >>>            r1.draw_model(model)
    """
    def __init__(self):
        Program.__init__(self, [
            (get_shader_path('shadow.v.glsl'), GL_VERTEX_SHADER),
            (get_shader_path('shadow.g.glsl'), GL_GEOMETRY_SHADER),
            (get_shader_path('shadow.f.glsl'), GL_FRAGMENT_SHADER),
        ], [
            ('vertexPos', 3, GL_FLOAT),
        ])

    def prepare_draw(self):
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthMask(GL_FALSE)
        glStencilFunc(GL_ALWAYS, 0, 0x1)
        glStencilOp(GL_KEEP, GL_INVERT, GL_KEEP)
        glClear(GL_STENCIL_BUFFER_BIT)

    def post_draw(self):
        glStencilFunc(GL_EQUAL, 0, 0x1)
        glStencilOp(GL_REPLACE, GL_REPLACE, GL_REPLACE)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        glDepthMask(GL_TRUE)

    def set_light(self, light):
        glUniform3f(self.get_uniform_loc('lightPosModelSpace'), *light.pos)

    def draw_model(self, model):
        self.set_buffer('vertexPos', model.vertices)
        self.set_matrix('modelMat', model.matrix)
        self.draw(GL_TRIANGLES, len(model.vertices))
