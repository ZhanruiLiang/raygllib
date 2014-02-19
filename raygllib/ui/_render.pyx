
def make_rects_buffer(list rects, float[:, :] psBuffer, float[:, :] colorBuffer):
    cdef:
        int i, j

    for i in range(len(rects)):
        rect = rects[i]
        psBuffer[i, 0] = rect.x
        psBuffer[i, 1] = rect.y
        psBuffer[i, 2] = rect.width
        psBuffer[i, 3] = rect.height
        color = rect.color
        for j in range(4):
            colorBuffer[i, j] = color[j]
