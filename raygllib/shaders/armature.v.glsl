# version 330 core
uniform mat4 modelMat, viewMat, projMat;

const int MaxJointCount = 30;
uniform mat4 jointMats[MaxJointCount];

in vec3 vertexPos;
in vec3 vertexNormal;
in vec2 vertexUV;

in vec4 vertexWeights;
in vec4 vertexJointIds;

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
    mat4 jointMat = 
          vertexWeights.x * jointMats[int(.5 + vertexJointIds.x)]
        + vertexWeights.y * jointMats[int(.5 + vertexJointIds.y)]
        + vertexWeights.z * jointMats[int(.5 + vertexJointIds.z)]
        + vertexWeights.w * jointMats[int(.5 + vertexJointIds.w)];
    mat4 mat = viewMat * jointMat * modelMat;
    normalCamSpace = homo_dir_to_vec3(mat * vec4(vertexNormal, 0));
    posCamSpace = homo_pos_to_vec3(mat * vec4(vertexPos, 1));
    gl_Position = projMat * vec4(posCamSpace, 1);
}
