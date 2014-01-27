import time
from OpenGL.GL import *
import sys
import functools
import inspect
from contextlib import contextmanager
from . import config

def timeit(func):
    @functools.wraps(func)
    def newfunc(*args, **kwargs):
        startTime = time.time()
        func(*args, **kwargs)
        elapsedTime = time.time() - startTime
        debug('function [{}] finished in {} ms'.format(
            func.__name__, int(elapsedTime * 1000)), file=sys.stderr)
    return newfunc

@contextmanager
def timeit_context(name):
    startTime = time.time()
    yield
    elapsedTime = time.time() - startTime
    debug('[{}] finished in {} ms'.format(name, int(elapsedTime * 1000)), file=sys.stderr)

def make_texture(image, target, mag_filter=GL_LINEAR, min_filter=GL_LINEAR_MIPMAP_LINEAR):
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
    glTexParameteri(target, GL_TEXTURE_WRAP_S, GL_REPEAT)
    glTexParameteri(target, GL_TEXTURE_WRAP_T, GL_REPEAT)
    glTexParameteri(target, GL_TEXTURE_MAG_FILTER, mag_filter)
    glTexParameteri(target, GL_TEXTURE_MIN_FILTER, min_filter)
    glGenerateMipmap(target)
    return textureId

_count = 0

def debug(*args, **kwargs):
    if not config.debug: 
        return 
    global _count
    # frame = inspect.stack()[1]
    # modules = []
    # stacks = inspect.stack()[1:]
    # for frame in stacks:
    #     name = inspect.getmodule(frame[0]).__name__
    #     if name != '__main__':
    #         modules.append(name)
    # if not modules:
    #     modules.append('__main__')
    # modules = '->'.join(x for x in reversed(modules))

    def p():
        print('{}: [{}]:'.format(_count, modules), *args, **kwargs)
    module = inspect.getmodule(inspect.stack()[1][0])
    if module:
        modules = module.__name__
    else:
        modules = ''
    p()
    # kwargs['file'] = _debugLogFile
    # p()
    _count += 1
