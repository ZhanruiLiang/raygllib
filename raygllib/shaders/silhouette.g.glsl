# version 330 core

uniform mat4 projMat;
layout (triangles_adjacency) in;
/*layout (triangle_strip, max_vertices=12) out;*/
layout (line_strip, max_vertices=6) out;

in vec3 vertexPosCamSpace[6];

const vec3 eyeVec = vec3(0, 0, -1);
const float Pi = 3.1415926;
const float creaseThreshodAngle = Pi * 3 / 4;
const float creaseThreshod = cos(Pi - creaseThreshodAngle);

vec3 v1, v2, v3, v4;
vec3 n2;

void main() {
    n2 = normalize(cross(vertexPosCamSpace[2] - vertexPosCamSpace[0],
            vertexPosCamSpace[4] - vertexPosCamSpace[0]));
    for(int i = 0; i < 6; i += 2) {
        v1 = vertexPosCamSpace[i];
        v2 = vertexPosCamSpace[(i + 2) % 6];
        v3 = vertexPosCamSpace[i + 1];
        v4 = vertexPosCamSpace[(i + 4) % 6];
        vec3 n1 = normalize(cross(v3 - v1, v2 - v1));
        if(dot(eyeVec, n1) * dot(eyeVec, n2) <= 0) {
            // v1 -> v2 is a contour edge
            gl_Position = projMat * vec4(v1, 1); EmitVertex();
            gl_Position = projMat * vec4(v2, 1); EmitVertex();
            EndPrimitive();
        }else if(dot(eyeVec, n1) > 0 && dot(eyeVec, n2) > 0) {
            continue;
        }
        if(dot(n1, n2) < creaseThreshod) {
            // v1 -> v2 is a crease edge
            gl_Position = projMat * vec4(v1, 1); EmitVertex();
            gl_Position = projMat * vec4(v2, 1); EmitVertex();
            EndPrimitive();
        }
    }
}
