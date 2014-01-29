# version 330 core
uniform mat4 modelMat, viewMat, projMat;
in vec3 vertexPos;
out vec3 vertexPosModelSpace;

void main() {
    vec4 t = modelMat * vec4(vertexPos, 1);
    vertexPosModelSpace = t.xyz / t.w;
}
