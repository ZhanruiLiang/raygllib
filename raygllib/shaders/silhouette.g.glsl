# version 330 core

uniform mat4 projMat;
layout (triangles_adjacency) in;
layout (triangle_strip, max_vertices=12) out;

in vec3 vertexPosCamSpace[6];

const vec3 eyeVec = vec3(0, 0, -1);
const float Pi = 3.1415926;
uniform float edgeWidth = 0.008;
const float creaseThreshodAngle = Pi * 3 / 4;
const float creaseThreshod = cos(Pi - creaseThreshodAngle);

void make_edge(vec3 v1, vec3 v2) {
    vec3 p = v2 - v1;
    float halfWidth = edgeWidth / 2;
    vec3 n = halfWidth * normalize(vec3(-p.y, p.x, 0));

    vec3 d = 0.5 * halfWidth * normalize(p);
    gl_Position = projMat * vec4(v1 - d - n, 1); EmitVertex();
    gl_Position = projMat * vec4(v1 - d + n, 1); EmitVertex();
    gl_Position = projMat * vec4(v2 + d - n, 1); EmitVertex();
    gl_Position = projMat * vec4(v2 + d + n, 1); EmitVertex();
    EndPrimitive();
}

void main() {
    vec3 n2 = normalize(cross(vertexPosCamSpace[2] - vertexPosCamSpace[0],
            vertexPosCamSpace[4] - vertexPosCamSpace[0]));
    for(int i = 0; i < 6; i += 2) {
        vec3 v1 = vertexPosCamSpace[i];
        vec3 v2 = vertexPosCamSpace[(i + 2) % 6];
        /*if(length(v2 - v1) < 1e-5) continue;*/
        vec3 v3, v4;
        v3 = vertexPosCamSpace[i + 1];
        v4 = vertexPosCamSpace[(i + 4) % 6];
        vec3 n1 = normalize(cross(v3 - v1, v2 - v1));
        float s1, s2;
        s1 = dot(eyeVec, n1);
        s2 = dot(eyeVec, n2);
        if(s1 * s2 <= 0) {
            // v1 -> v2 is a contour edge
            make_edge(v1, v2);
        }else if(s1 > 0) {
        }else if(dot(n1, n2) < creaseThreshod) {
            // v1 -> v2 is a crease edge
            make_edge(v1, v2);
        }
    }
}
