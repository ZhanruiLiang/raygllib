import numpy as np

ctypedef unsigned int ID

cdef class HalfEdge:
    cdef public:
        HalfEdge next, twin
        ID vertexId

def make_adj_indices(ID[:] indices):
    cdef:
        int i, k, v1, v2
        ID[:] adjIndices = np.zeros(len(indices) * 2, dtype=np.uint)
        dict edges = {}
        HalfEdge edge

    for i in range(0, len(indices), 3):
        triangle = [HalfEdge() for k in range(3)]
        for k in range(3):
            v1 = indices[i + k]
            v2 = indices[i + (k + 1) % 3]
            edge = edges[v1, v2] = triangle[k]
            edge.vertexId = v1
            edge.twin = edges.get((v2, v1), edge)
            edge.twin.twin = edge
            edge.next = triangle[(k + 1) % 3]
    for i in range(0, len(indices), 3):
        for k in range(3):
            v1 = indices[i + k]
            v2 = indices[i + (k + 1) % 3]
            edge = edges[v1, v2]
            adjIndices[(i + k) * 2] = v1
            adjIndices[(i + k) * 2 + 1] = edge.twin.next.next.vertexId
    return adjIndices
