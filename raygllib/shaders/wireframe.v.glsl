# version 330 core

uniform mat4 viewMat, modelMat, projMat;

in vec3 vertexPos;
in vec3 vertexNormal;

const float Offset = 0.001;

void main() {
    gl_Position = projMat * viewMat * modelMat * vec4(vertexPos + vertexNormal * Offset, 1);
}
