import os
import numpy as np
from OpenGL.GL import *
from .gllib import Program, TextureUnit, UniformNotFoundError
from . import config
from .model import ArmaturedModel
# from .utils import debug


def get_shader_path(name):
    return os.path.join(os.path.dirname(__file__), 'shaders', name)


class Renderer(Program):
    def __init__(self):
        super().__init__([
            (get_shader_path('model.v.glsl'), GL_VERTEX_SHADER),
            (get_shader_path('model.f.glsl'), GL_FRAGMENT_SHADER),
        ], [
            ('vertexPos', 3, GL_FLOAT),
            ('vertexNormal', 3, GL_FLOAT),
            ('vertexUV', 2, GL_FLOAT),
            ('vertexWeights', 4, GL_FLOAT),
            ('vertexJointIds', 4, GL_FLOAT),
        ])
        self.textureUnit = TextureUnit(0)
        self.toonRenderEdges = config.toonRenderEdges

        self.toonRenderEnable = config.toonRenderEnable

    def prepare_draw(self):
        if self.toonRenderEnable:
            edges = self.toonRenderEdges
        else:
            edges = []
        glUniform1i(self.get_uniform_loc('nEdges'), len(edges))
        glUniform1fv(self.get_uniform_loc('edges'), len(edges), edges)

    def set_material(self, material):
        if material.diffuseType == material.DIFFUSE_TEXTURE:
            glActiveTexture(self.textureUnit.glenum)
            glBindTexture(GL_TEXTURE_2D, material.diffuse.glId)
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
        try:
            glUniform3fv(self.get_uniform_loc('lightPosModelSpace'), n,
                np.array([light.pos for light in lights], 'f'))
        except UniformNotFoundError:
            pass
        glUniform1i(self.get_uniform_loc('nLights'), n)

    def draw_model(self, model):
        self.set_buffer('vertexPos', model.geometry.vertices)
        self.set_buffer('vertexNormal', model.geometry.normals)
        if model.geometry.texcoords:
            glEnableVertexAttribArray(self._buffers['vertexUV'].location)
            self.set_buffer('vertexUV', model.geometry.texcoords)
        else:
            glDisableVertexAttribArray(self._buffers['vertexUV'].location)
        self.set_material(model.geometry.material)
        self.set_matrix('modelMat', model.matrix)
        if isinstance(model, ArmaturedModel):
            glUniform1i(self.get_uniform_loc('hasArmature'), 1)
            self.set_buffer('vertexWeights', model.vertexWeights)
            self.set_buffer('vertexJointIds', model.vertexJointIds)
            glUniformMatrix4fv(self.get_uniform_loc('jointMats'),
                len(model.joints), GL_FALSE, model.get_joint_matrices())
            model.geometry.draw()
        else:
            glUniform1i(self.get_uniform_loc('hasArmature'), 0)
            # Disable unused attributes.
            locs = list(map(self.get_attrib_loc, ('vertexWeights', 'vertexJointIds')))
            for loc in locs:
                glDisableVertexAttribArray(loc)
            model.geometry.draw()
            for loc in locs:
                glEnableVertexAttribArray(loc)


class SilhouetteRenderer(Program):
    def __init__(self):
        super().__init__([
            (get_shader_path('silhouette.v.glsl'), GL_VERTEX_SHADER),
            (get_shader_path('silhouette.f.glsl'), GL_FRAGMENT_SHADER),
            (get_shader_path('silhouette.g.glsl'), GL_GEOMETRY_SHADER),
        ], [
            ('vertexPos', 3, GL_FLOAT),
        ])

    def draw_model(self, model):
        self.set_buffer('vertexPos', model.geometry.adjVertices.vertices)
        model.geometry.adjVertices.bind()
        self.set_matrix('modelMat', model.matrix)
        model.geometry.adjVertices.draw()


class WireframeRenderer(Program):
    def __init__(self):
        super().__init__([
            (get_shader_path('wireframe.v.glsl'), GL_VERTEX_SHADER),
            (get_shader_path('wireframe.f.glsl'), GL_FRAGMENT_SHADER),
        ], [
            ('vertexPos', 3, GL_FLOAT),
            ('vertexNormal', 3, GL_FLOAT),
        ])

    def draw_model(self, model):
        self.set_buffer('vertexPos', model.geometry.vertices)
        self.set_buffer('vertexNormal', model.geometry.normals)
        self.set_matrix('modelMat', model.matrix)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        model.geometry.draw()
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
