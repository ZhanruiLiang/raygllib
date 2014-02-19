import os
import PIL.Image as Image
import numpy as np
import json

import pyximport
pyximport.install()

from . import _render

import raygllib.gllib as gl


def get_resouce_path(*subPaths):
    return os.path.join(os.path.dirname(__file__), *subPaths)


class Render(gl.Program):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matrix = np.eye(4, dtype=gl.GLfloat)

    def set_screen_size(self, w, h):
        m = self.matrix = np.eye(4, dtype=gl.GLfloat)
        m[0, 0] = 2 / w
        m[1, 1] = - 2 / h
        m[0, 3] = -1
        m[1, 3] = 1

    def prepare_draw(self):
        gl.glDisable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

    def set_matrix_uniform(self):
        gl.glUniformMatrix4fv(self.get_uniform_loc('matrix'), 1, gl.GL_TRUE, self.matrix)


class RectRender(Render):
    def __init__(self):
        super().__init__([
            (get_resouce_path('shaders', 'rect.v.glsl'), gl.GL_VERTEX_SHADER),
            (get_resouce_path('shaders', 'rect.g.glsl'), gl.GL_GEOMETRY_SHADER),
            (get_resouce_path('shaders', 'rect.f.glsl'), gl.GL_FRAGMENT_SHADER),
        ], [
            ('pos_size', 4, gl.GL_FLOAT),
            ('color', 4, gl.GL_FLOAT),
        ])

        self.psBuffer = gl.DynamicVertexBuffer()
        self.colorBuffer = gl.DynamicVertexBuffer()

    # @profile
    def draw_rects(self, rects):
        nRects = len(rects)
        psBuffer = np.zeros((nRects, 4), dtype=gl.GLfloat)
        colorBuffer = np.zeros((nRects, 4), dtype=gl.GLfloat)

        _render.make_rects_buffer(rects, psBuffer, colorBuffer)

        # Set buffers
        self.psBuffer.set_data(psBuffer)
        self.colorBuffer.set_data(colorBuffer)
        self.set_buffer('pos_size', self.psBuffer)
        self.set_buffer('color', self.colorBuffer)
        # Set uniforms
        self.set_matrix_uniform()
        self.draw(gl.GL_POINTS, nRects)


class FontTexture(gl.Texture2D):
    MIN_FILTER = gl.GL_LINEAR_MIPMAP_LINEAR

    def __init__(self, name):
        image = Image.open(get_resouce_path('textures', name))
        super().__init__(image)
        self.config = json.load(open(get_resouce_path('textures', name + '.json')))
        self.charMap = {c: i for i, c in enumerate(self.config['string'])}


class FontRender(Render):
    FONT = 'texmono.png'

    def __init__(self):
        super().__init__([
            (get_resouce_path('shaders', 'font.v.glsl'), gl.GL_VERTEX_SHADER),
            (get_resouce_path('shaders', 'font.g.glsl'), gl.GL_GEOMETRY_SHADER),
            (get_resouce_path('shaders', 'font.f.glsl'), gl.GL_FRAGMENT_SHADER),
        ], [
            ('pos_char_scale', 4, gl.GL_FLOAT),
            ('color', 4, gl.GL_FLOAT),
        ])
        self.fontTexture = FontTexture(self.FONT)
        self.pcsBuffer = gl.DynamicVertexBuffer()
        self.colorBuffer = gl.DynamicVertexBuffer()
        self.textureUnit = gl.TextureUnit(0)

    @staticmethod
    def get_char_size(fontSize):
        return (fontSize // 2 + 2, fontSize)

    def set_texture(self, texture):
        gl.glActiveTexture(self.textureUnit.glenum)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture.glId)
        gl.glUniform1i(self.get_uniform_loc('fontSampler'), self.textureUnit.id)

    def draw_textboxs(self, textboxes):
        fontTexture = self.fontTexture
        nChars = sum(len(t.text) for t in textboxes)
        buffer = np.zeros((nChars, 8), dtype=gl.GLfloat)
        id = 0
        for textbox in textboxes:
            x0 = textbox.x
            y0 = textbox.y
            tw, th = self.get_char_size(textbox.fontSize)
            w = textbox.width
            x = x0 + tw / 2
            y = y0 + th / 2
            buffer[id:id + len(textbox.text), 3] = textbox.fontSize
            buffer[id:id + len(textbox.text), 4:8] = textbox.color
            for i, c in enumerate(textbox.text):
                if c == '\n':
                    buffer[id, 0] = x
                    buffer[id, 1] = y
                    buffer[id, 2] = fontTexture.charMap[' ']
                    id += 1
                    y += th
                    x = x0 + tw / 2
                else:
                    if textbox.wrap and x + tw / 2 > x0 + w:
                        y += th
                        x = x0 + tw / 2
                    try:
                        charId = fontTexture.charMap[c]
                    except KeyError:
                        charId = fontTexture.charMap[' ']
                    buffer[id, 0] = x
                    buffer[id, 1] = y
                    buffer[id, 2] = charId
                    id += 1
                    x += tw
        # Set buffers
        self.pcsBuffer.set_data(buffer[:, 0:4])
        self.colorBuffer.set_data(buffer[:, 4:8])
        self.set_buffer('pos_char_scale', self.pcsBuffer)
        self.set_buffer('color', self.colorBuffer)
        # Set uniforms
        self.set_texture(self.fontTexture)
        config = fontTexture.config
        for name in ('rowsize', 'gridwidth', 'gridheight', 'fontsize'):
            gl.glUniform1i(self.get_uniform_loc(name), config[name])
        self.set_matrix_uniform()
        # Start draw
        self.draw(gl.GL_POINTS, len(buffer))
