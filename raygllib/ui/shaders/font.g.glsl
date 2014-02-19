# version 330 core

layout(points) in;
layout(triangle_strip, max_vertices=4) out;

uniform int rowsize, gridwidth, gridheight, fontsize;
uniform mat4 matrix;
uniform sampler2D fontSampler;

in vec2 pos[];
in int charId[];
in float scale[];
in vec4 color1[];

out vec4 color2;
out vec2 uv;

void main() {
    vec2 fontTextureSize = textureSize(fontSampler, 0).xy;
    int w2 = gridwidth / 2;
    int h2 = gridheight / 2;
    vec4 dx = vec4(-w2, w2, -w2, w2);
    vec4 dy = vec4(-h2, -h2, h2, h2);
    for(int i = 0; i < 4; i++) {
        vec2 dp = vec2(dx[i], dy[i]);
        uv = (vec2(
            (.5 + charId[0] % rowsize) * gridwidth,
            (.5 + charId[0] / rowsize) * gridheight) + dp) / fontTextureSize;
        gl_Position = matrix * vec4(pos[0] + dp * scale[0] / fontsize, 0, 1);
        color2 = color1[0];
        EmitVertex();
    }
    EndPrimitive();
}
