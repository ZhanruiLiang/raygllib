import time
from OpenGL.GL import *
import sys
import functools
from contextlib import contextmanager

def timeit(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        elapsedTime = time.time() - startTime
        print('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsedTime * 1000)), file=sys.stderr)
    return newfunc

@contextmanager
def timeit_context(name):
    startTime = time.time()
    yield
    elapsedTime = time.time() - startTime
    print('[{}] finished in {} ms'.format(name, int(elapsedTime * 1000)), file=sys.stderr)

def make_texture(image, target, mag_filter=GL_LINEAR, min_filter=GL_LINEAR):
    data = image.convert('RGBA').tobytes()
    width, height = image.size
    glEnable(target)
    textureId = glGenTextures(1)
    glBindTexture(target, textureId)
    assert textureId > 0, 'Fail to get new texture id.'
    glTexImage2D(
        target, 0,
        GL_RGBA,  # internal format
        width, height,
        0,  # border, must be 0
        GL_RGBA,  # input data format
        GL_UNSIGNED_BYTE,
        data,
    )
    glTexParameteri(target, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(target, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(target, GL_TEXTURE_MAG_FILTER, mag_filter)
    glTexParameteri(target, GL_TEXTURE_MIN_FILTER, min_filter)
    return textureId
