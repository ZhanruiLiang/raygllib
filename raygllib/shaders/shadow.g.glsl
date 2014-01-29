# version 330 core
uniform mat4 viewMat, projMat;
uniform vec3 lightPosModelSpace;
const float EXTRUDE = 10;

layout (triangles) in;
layout (triangle_strip, max_vertices=15) out;

in vec3 vertexPosModelSpace[3];

void main() {
    mat4 M = projMat * viewMat;
    // front cap
    for(int i = 0; i < 3; i++) {
        gl_Position = M * vec4(vertexPosModelSpace[i], 1);
        EmitVertex();
    }
    EndPrimitive();
    // side
    vec4 v[3];
    for(int i = 0; i < 3; i++) {
        v[i] = vec4(
            lightPosModelSpace + EXTRUDE * (vertexPosModelSpace[i] - lightPosModelSpace), 1);
    }
    for(int i = 0; i < 3; i++) {
        gl_Position = M * vec4(vertexPosModelSpace[i], 1); EmitVertex();
        gl_Position = M * v[i]; EmitVertex();
        gl_Position = M * v[(i + 1) % 3]; EmitVertex();
        EndPrimitive();
        gl_Position = M * vec4(vertexPosModelSpace[(i + 1) % 3], 1); EmitVertex();
        gl_Position = M * vec4(vertexPosModelSpace[i], 1); EmitVertex();
        gl_Position = M * v[(i + 1) % 3]; EmitVertex();
        EndPrimitive();
    }
    // back cap
    for(int i = 2; i >= 0; i--) {
        gl_Position = M * v[i]; EmitVertex();
    }
    EndPrimitive();
}
