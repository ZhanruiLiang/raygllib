# version 330 core
uniform mat4 modelMat, viewMat, projMat;
in vec3 vertexPos;
in vec3 vertexNormal;
in vec2 vertexUV;

out vec2 uv;
out vec3 normalCamSpace;
out vec3 posCamSpace;

vec3 homo_pos_to_vec3(const in vec4 p) {
    return p.xyz / p.w;
}

vec3 homo_dir_to_vec3(const in vec4 p) {
    return p.xyz;
}

void main() {
    uv = vertexUV;
    normalCamSpace = homo_dir_to_vec3(viewMat * modelMat * vec4(vertexNormal, 0));
    posCamSpace = homo_pos_to_vec3(viewMat * modelMat * vec4(vertexPos, 1));
    gl_Position = projMat * vec4(posCamSpace, 1);
}
