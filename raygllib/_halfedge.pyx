from OpenGL.GL import GLfloat, GLuint
import numpy as np

cdef class HalfEdge:
    cdef public:
        HalfEdge next
        HalfEdge twin
        unsigned int vertexId

def make_adj_indices(float[:, :] vertices, unsigned int[:] indices):
    cdef:
        int i, k, v1, v2
        int nTriangles = len(indices) // 3
        unsigned int[:] adjIndices = np.zeros(nTriangles * 6, dtype=GLuint)
        dict edges = {}
        HalfEdge edge

    triangle = [None] * 3
    for i in range(0, nTriangles * 3, 3):
        for k in range(3):
            v1 = indices[i + k]
            v2 = indices[i + (k + 1) % 3]
            edge = edges[v1, v2] = HalfEdge()
            edge.vertexId = v1
            edge.twin = edges.get((v2, v1), edge)
            edge.twin.twin = edge
            triangle[k] = edge
        for k in range(3):
            triangle[k].next = triangle[(k + 1) % 3]
    for i in range(0, nTriangles * 3, 3):
        for k in range(3):
            v1 = indices[i + k]
            v2 = indices[i + (k + 1) % 3]
            edge = edges[v1, v2]
            adjIndices[(i + k) * 2] = v1
            adjIndices[(i + k) * 2 + 1] = edge.twin.next.next.vertexId
    return adjIndices
