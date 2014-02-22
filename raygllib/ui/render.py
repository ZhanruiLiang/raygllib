import os
import PIL.Image as Image
import numpy as np
import json

import pyximport
pyximport.install()

from . import _render
from .base import TextAlign

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
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

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
        # gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
        # rects = [rect for rect in rects if rect.visible]
        nRects = len(rects)
        psBuffer = np.zeros((nRects, 4), dtype=gl.GLfloat)
        colorBuffer = np.zeros((nRects, 4), dtype=gl.GLfloat)

        _render.make_rects_buffer(rects, psBuffer, colorBuffer)
        # print('-'* 80)
        # for i in range(nRects):
        #     print(i, 'pos', psBuffer[i, 0:2], 'size', psBuffer[i, 2:4], 'color', colorBuffer[i])

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

    def set_texture(self, texture):
        gl.glActiveTexture(self.textureUnit.glenum)
        gl.glBindTexture(gl.GL_TEXTURE_2D, texture.glId)
        gl.glUniform1i(self.get_uniform_loc('fontSampler'), self.textureUnit.id)

    def draw_textboxs(self, textboxes):
        if not textboxes:
            # Nothing to draw, exit to avoid np.vstack exception.
            return
        fontTexture = self.fontTexture
        for textbox in textboxes:
            state = self._make_state(textbox)
            if textbox._renderState != state:
                textbox._buffer = self._make_buffer(textbox)
                textbox._renderState = state
        buffer = np.vstack([textbox._buffer for textbox in textboxes])
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

    def _iter_lines(self, text, wrapNum):
        if wrapNum <= 0:
            for line in text.split('\n'):
                yield line
            return

        for line in text.split('\n'):
            for i in range(0, len(line), wrapNum):
                yield line[i:i + wrapNum]

    def _make_state(self, textbox):
        t = textbox
        return (
            id(t.text), len(t.text), t.color, t.fontSize, t.wrap,
            t.x, t.y, t.width, t.height, t.align,
        )

    def _make_buffer(self, textbox):
        charMap = self.fontTexture.charMap
        tw, th = self.get_char_size(textbox.fontSize)
        text = textbox.text
        nChars = len(text) - text.count('\n')
        x0 = textbox.x
        y0 = textbox.y
        w = textbox.width
        # Init buffer
        buffer = np.zeros((nChars, 8), dtype=gl.GLfloat)
        buffer[:, 3] = textbox.fontSize
        buffer[:, 4:8] = textbox.color

        wrapNum = int(w // tw) if textbox.wrap else 0
        y = y0 + th / 2
        id = 0
        for line in self._iter_lines(text, wrapNum):
            n = len(line)
            for i, c in enumerate(line):
                try:
                    charId = charMap[c]
                except KeyError:
                    charId = charMap[' ']
                buffer[id + i, 2] = charId
            xs = np.arange(x0 + tw / 2, x0 + tw * n, tw)
            if textbox.align is TextAlign.CENTER:
                xs += (w - tw * n) / 2
            elif textbox.align is TextAlign.RIGHT:
                xs += w - tw * n
            buffer[id:id + n, 0] = xs
            buffer[id:id + n, 1] = y
            y += th
            id += n
        return buffer


    @staticmethod
    def get_char_size(fontSize):
        return (fontSize // 2 + 2, fontSize)
