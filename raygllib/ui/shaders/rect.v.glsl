# version 330 core

in vec4 pos_size;
in vec4 color;

out vec2 pos;
out vec2 size;
out vec4 color1;

void main() {
    pos = pos_size.xy;
    size = pos_size.zw;
    color1 = color;
}
