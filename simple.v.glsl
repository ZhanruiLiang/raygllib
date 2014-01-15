# version 330 core

in vec2 vertex_pos;

void main() {
    gl_Position = vec4(vertex_pos, 0, 1);
}
