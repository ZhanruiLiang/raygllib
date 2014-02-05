# version 330 core

const int MaxLightCount = 10;
uniform vec3 lightPosModelSpace[MaxLightCount];
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
uniform int nEdges;
uniform float edges[10];

const vec3 roomCenterModelSpace = vec3(0.0, 0.0, 0);
const float roomSize = 10;

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
    float edge;
    for(int i = 0; i < nEdges - 1; i++) {
        edge = edges[i];
        y += (edges[i + 1] - edge) * smoothstep(edge - 0.01, edge, x);
    }
    return y;
}

float noise1(vec2 co){
    return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453);
}

float salt_and_pepper(vec3 pos) {
    float k = noise1(pos.xy);
    const float Pa = 0.01, Pb = 0.01;
    if(k < Pa) {
        return 0.5;
    }
    if(k < Pa + Pb) {
        return 2;
    }
    return 1;
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
        vec3 lightPosCamSpace = (viewMat * vec4(lightPosModelSpace[i], 1)).xyz;
        vec3 lightVectorCamSpace = lightPosCamSpace - posCamSpace;
        float dist = length(lightVectorCamSpace);
        /*vec3 lightVectorCamSpace = posCamSpace - (viewMat * vec4(roomCenterModelSpace, 1)).xyz;*/

        lightVectorCamSpace = normalize(lightVectorCamSpace);

        vec3 reflectLightVectorCamSpace = reflect(lightVectorCamSpace, normalCamSpace1);

        /*vec3 intensity = lightColor[i] / (dist * dist) * lightPower[i] * 200;*/
        vec3 intensity = lightColor[i] * lightPower[i];
        float d = multi_step(clamp(dot(lightVectorCamSpace, normalCamSpace1), 0, 1));
        float s = multi_step(clamp(dot(-reflectLightVectorCamSpace, eyeVectorCamSpace), 0, 1));

        fragColor += mtlDiffuseColor * intensity * d + intensity * Ks * pow(s, shininess);
    }
}
