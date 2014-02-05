cdef merge_bufs(list bufs, int* start):
    n = max([buf.shape[0] for buf in bufs])
    width = sum([buf.shape[1] for buf in bufs])
    mergedBuf = np.zeros((n, width), dtype=GLfloat)
    start[0] = 0
    for j, buf in enumerate(bufs):
        start[j + 1] = start[j] + buf.shape[1]
        mergedBuf[:len(buf), start[j]:start[j + 1]] = buf

    return mergedBuf

cdef split_buf(buf, int* start, int m):
    return [buf[:, start[i]:start[i+1]] for i in range(m)]

def make_single_index(list bufs, index_):
    cdef:
        dict h = {}
        int i, j, width
        int n = index_.shape[0]
        int m = index_.shape[1]
        int start[4]

        ID[:, :] index = index_.astype(GLuint)
        ID[:] newIndexView

        float[:, :] buf
        float[:, :] newBufView
        int newBufSize = 0
        float[:] key

    buf = merge_bufs(bufs, start)
    print [start[i] for i in range(4)]
    width = start[m]
    key = np.zeros(width, dtype=GLfloat)
    newBuf = np.zeros((n, width), dtype=GLfloat)
    newBufView = newBuf
    newIndex = np.zeros(n, dtype=GLuint)
    newIndexView = newIndex

    for i in range(n):
        # key = tuple(index[i])
        for j in range(m):
            key[start[j]:start[j+1]] = buf[index[i, j], start[j]:start[j+1]]
        keyt = tuple(key)
        if keyt in h:
            newIndexView[i] = h[keyt]
        else:
            newBufView[newBufSize] = key
            newIndexView[i] = h[keyt] = newBufSize
            newBufSize += 1
    utils.debug('compress: nBefore={}, nAfter={}, rate={}'.format(
        n, newBufSize, newBufSize / float(n)))
    return split_buf(newBuf[:newBufSize], start, m), newIndex


