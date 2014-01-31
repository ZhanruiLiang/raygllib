# version 330 core

uniform mat4 viewMat, modelMat;

in vec3 vertexPos;
out vec3 vertexPosCamSpace;

void main() {
    vec4 v = viewMat * modelMat * vec4(vertexPos, 1);
    vertexPosCamSpace = v.xyz / v.w;
}
