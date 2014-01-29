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
uniform int nEdges = 2;
uniform float edges[5];

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

float multi_step(float x) {
    if(nEdges == 0) 
        return x;
    float y = 0;
    for(int i = 0; i < nEdges; i++) {
        y += smoothstep(edges[i] - 0.02, edges[i], x);
    }
    y /= nEdges;
    return y;
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

    fragColor = Ka * mtlDiffuseColor;
    for(int i = 0; i < nLights; i++) {
        vec3 lightVectorCamSpace = lightPosCamSpace[i] - posCamSpace;

        float dist = length(lightVectorCamSpace);
        lightVectorCamSpace = normalize(lightVectorCamSpace);

        vec3 reflectLightVectorCamSpace = reflect(lightVectorCamSpace, normalCamSpace1);

        vec3 intensity = lightColor[i] / (dist * dist) * lightPower[i];
        /*float d = clamp(dot(lightVectorCamSpace, normalCamSpace1), 0, 1);*/
        /*float s = clamp(dot(reflectLightVectorCamSpace, eyeVectorCamSpace), 0, 1);*/
        float d = multi_step(clamp(dot(lightVectorCamSpace, normalCamSpace1), 0, 1));
        float s = multi_step(clamp(dot(reflectLightVectorCamSpace, eyeVectorCamSpace), 0, 1));

        fragColor += mtlDiffuseColor * intensity * d + intensity * Ks * pow(s, shininess);
    }
}
