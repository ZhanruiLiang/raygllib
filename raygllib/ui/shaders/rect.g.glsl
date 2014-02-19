# version 330 core

layout(points) in;
layout(triangle_strip, max_vertices=4) out;

uniform mat4 matrix;

in vec4 color1[];
in vec2 pos[];
in vec2 size[];

out vec4 color2;

void main() {
    float width = size[0].x;
    float height = size[0].y;
    vec4 dx = vec4(0, width, 0, width); 
    vec4 dy = vec4(0, 0, height, height);
    for(int i = 0; i < 4; i++) {
        gl_Position = matrix * vec4(pos[0].x + dx[i], pos[0].y + dy[i], 0, 1);
        color2 = color1[0];
        EmitVertex();
    }
    EndPrimitive();
}
