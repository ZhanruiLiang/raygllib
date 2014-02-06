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

class ShadowedViewer(Viewer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.shadowRenderer = ShadowRenderer()

    def draw(self):
        self.window.clear()
        glClearColor(.0, .0, .0, 1.)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_STENCIL_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_ONE, GL_ONE)
        glDepthFunc(GL_LEQUAL)

        r1 = self.renderer
        r2 = self.shadowRenderer

        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        glDepthMask(GL_TRUE)
        with r1.batch_draw():
            r1.set_matrix('viewMat', self.camera.viewMat)
            r1.set_matrix('projMat', self.projMat)
            r1.set_lights(self.scene.lights)
            for model in self.scene.models:
                r1.draw_model(model)
        for light in self.scene.lights:
            with r2.batch_draw():
                r2.set_light(light)
                r2.set_matrix('viewMat', self.camera.viewMat)
                r2.set_matrix('projMat', self.projMat)
                for model in self.scene.models:
                    r2.draw_model(model)
            # glDisable(GL_STENCIL_TEST)
            glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
            glDepthMask(GL_TRUE)
            with r1.batch_draw():
                r1.set_matrix('viewMat', self.camera.viewMat)
                r1.set_matrix('projMat', self.projMat)
                r1.set_lights([light])
                for model in self.scene.models:
                    r1.draw_model(model)

        glDisable(GL_DEPTH_TEST)
        self.fpsDisplay.draw()
