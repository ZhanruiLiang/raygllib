import numpy as np
from OpenGL.GL import GLfloat, GLuint
from . import utils

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


def make_single_index_1(list bufs, index_):
    cdef:
        int n, m, i, j, k, newBufSize
        dict h = {}
        ID[:, :] index = index_.astype(GLuint)
        ID[:] newIndex
        #float[:, :] bufItem, bufItem1
        list newBufs
        int width[3]
    n, m = index_.shape
    newBufs = [np.zeros((n, buf.shape[1]), dtype=GLfloat) for buf in bufs]
    newIndex = newIndex_ = np.zeros(n, dtype=GLuint)
    newBufSize = 0
    #for j in range(m):
    #    width[j] = bufs[j].shape[1]
    for i in range(n):
        #key = tuple(index[i])
        key = ()
        for j in range(m):
            key += tuple(bufs[j][index[i, j]])
        if key in h:
            newIndex[i] = h[key]
        else:
            for j in range(m):
                #bufItem = newBufs[j]
                #bufItem1 = bufs[j]
                #for k in range(width[j]):
                #    bufItem[newBufSize, k] = bufItem1[index[i, j], k]
                newBufs[j][newBufSize] = bufs[j][index[i, j]]
            newIndex[i] = h[key] = newBufSize
            newBufSize += 1
    newBufs = [buf[:newBufSize] for buf in newBufs]
    utils.debug('compress: nBefore={}, nAfter={}, rate={}'.format(
        n, newBufSize, newBufSize / float(n)))
    return newBufs, newIndex_


def make_single_index_2(bufs, index_):
    cdef:
        int n, m, i, j, newBufSize
        dict h = {}
        tuple key
        ID[:, :] index = index_.astype(GLuint)
        ID[:] newIndex
    n, m = index_.shape
    newBufs = [np.zeros((n, buf.shape[1]), dtype=GLfloat) for buf in bufs]
    newIndex = newIndex_ = np.zeros(n, dtype=GLuint)
    newBufSize = 0
    for j in range(m):
        h = {}
        for i in range(n):
            v = tuple(buf[index[i, j]])
            try:
                index[i, j] = h[v]
            except:
                h[v] = index[i, j]
    for i in range(n):
        key = tuple(index[i])
        if key in h:
            newIndex[i] = h[key]
        else:
            for j in range(m):
                newBufs[j][newBufSize] = bufs[j][index[i, j]]
            newIndex[i] = h[key] = newBufSize
            newBufSize += 1
    newBufs = [buf[:newBufSize] for buf in newBufs]
    utils.debug('compress: nBefore={}, nAfter={}, rate={}'.format(
        n, newBufSize, newBufSize / float(n)))
    return newBufs, newIndex_
