# version 330 core

const int MaxLightCount = 10;
/*const vec3 lightPosModelSpace = vec3(5, 5, 10);*/
uniform vec3 lightPosCamSpace[MaxLightCount];
uniform vec3 lightColor[MaxLightCount];
uniform float lightPower[MaxLightCount];
uniform int nLights;
uniform vec3 diffuse;
uniform vec3 Ka;
uniform vec3 Ks;
uniform float shininess;

uniform sampler2D textureSampler;
uniform bool hasSampler;
uniform mat4 viewMat, modelMat;
in vec2 uv;
in vec3 normalCamSpace;
in vec3 posCamSpace;

out vec3 fragColor;

vec3 homo_pos_to_vec3(const in vec4 p) {
    return p.xyz / p.w;
}

vec3 homo_dir_to_vec3(const in vec4 p) {
    return p.xyz;
}

void main() {
    vec3 normalCamSpace1 = normalize(normalCamSpace);
    vec3 mtlDiffuseColor;
    if(hasSampler) {
        mtlDiffuseColor = texture(textureSampler, vec2(uv.s, 1 - uv.t)).rgb;
    } else {
        mtlDiffuseColor = diffuse;
    }
    vec3 eyeVectorCamSpace = normalize(-posCamSpace);

    fragColor = vec3(0, 0, 0);
    for(int i = 0; i < nLights; i++) {
        vec3 lightVectorCamSpace = lightPosCamSpace[i] - posCamSpace;

        float dist = length(lightVectorCamSpace);
        lightVectorCamSpace = normalize(lightVectorCamSpace);

        vec3 reflectLightVectorCamSpace = reflect(lightVectorCamSpace, normalCamSpace1);

        vec3 intensity = lightColor[i] / (dist * dist) * lightPower[i];
        float d = clamp(dot(lightVectorCamSpace, normalCamSpace1), 0, 1);
        float s = clamp(dot(reflectLightVectorCamSpace, eyeVectorCamSpace), 0, 1);

        fragColor += lightColor[i] * Ka 
            + mtlDiffuseColor * intensity * d 
            + intensity * Ks * pow(s, shininess);
    }
}
