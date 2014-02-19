# version 330 core

uniform sampler2D fontSampler;
uniform mat4 matrix;

in vec4 color2;
in vec2 uv;

out vec4 fragColor;

void main() {
    fragColor = color2 * texture(fontSampler, uv);
}
