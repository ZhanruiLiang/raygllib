# version 330 core

in vec4 pos_char_scale;
in vec4 color;

out vec2 pos;
out int charId;
out float scale;
out vec4 color1;

void main() {
    pos = pos_char_scale.xy;
    charId = int(pos_char_scale.z + .5);
    scale = pos_char_scale.w;
    color1 = color;
}
