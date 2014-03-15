# version 330 core
uniform mat4 modelMat, viewMat, projMat;

uniform bool hasArmature;
uniform int targetJoint;
const int MaxJointCount = 40;
uniform mat4 jointMats[MaxJointCount];

in vec3 vertexPos;
in vec3 vertexNormal;
in vec2 vertexUV;
in vec4 vertexWeights;
in vec4 vertexJointIds;

out vec2 uv;
out vec3 normalCamSpace;
out vec3 posCamSpace;
out float weight;

vec3 homo_pos_to_vec3(const in vec4 p) {
    return p.xyz / p.w;
}

vec3 homo_dir_to_vec3(const in vec4 p) {
    return p.xyz;
}

void show_weight() {
    for(int i = 0; i < 4; i++) {
        if(vertexJointIds[i] == targetJoint) {
            weight = vertexWeights[i];
            break;
        }
    }
}

void main() {
    uv = vertexUV;
    mat4 mat;
    weight = 0;
    if(hasArmature) {
        mat4 jointMat = 
              vertexWeights.x * jointMats[int(.5 + vertexJointIds.x)]
            + vertexWeights.y * jointMats[int(.5 + vertexJointIds.y)]
            + vertexWeights.z * jointMats[int(.5 + vertexJointIds.z)]
            + vertexWeights.w * jointMats[int(.5 + vertexJointIds.w)];
        mat = viewMat * jointMat * modelMat;
        /*show_weight();*/
    } else {
        mat = viewMat * modelMat;
    }
    normalCamSpace = homo_dir_to_vec3(mat * vec4(vertexNormal, 0));
    posCamSpace = homo_pos_to_vec3(mat * vec4(vertexPos, 1));
    gl_Position = projMat * vec4(posCamSpace, 1);
}
