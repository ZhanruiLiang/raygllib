import numpy as np
from OpenGL.GL import GLfloat

def vec3_to_vec4(v):
    return np.hstack([v, 1.])

def vec3_to_vec4_n(v):
    return np.hstack([v, 0.])

def vec4_to_vec3(v):
    if v[3] == 0:
        return v[:3]
    return v[:3] / v[3]

def scale(x, y=None, z=None):
    if y is None:
        y = z = x
    mat = identity()
    mat[0, 0] = x
    mat[1, 1] = y
    mat[2, 2] = z
    return mat

def translate(x, y, z):
    mat = identity()
    mat[0:3, 3] = (x, y, z)
    return mat

def length(v):
    return np.sqrt(np.dot(v, v))

def rotate(angle, center, axis):
    """
    angle: In radians
    """
    n = normalized(np.array(axis, dtype=GLfloat))
    I3 = identity(3)
    T = np.array([
        (0, -n[2], n[1]),
        (n[2], 0, -n[0]),
        (-n[1], n[0], 0),
    ], dtype=GLfloat)
    c = np.cos(angle)
    R = (c * I3 + (1 - c) * np.outer(n, n)) + np.sin(angle) * T
    mat = identity()
    mat[0:3, 0:3] = R
    mat[0:3, 3] = (I3 - R).dot(center)
    return mat

def normalized(a):
    d = np.dot(a, a) ** .5
    return a / (d if d != 0 else 1)

def look_at(eye, center, up):
    z = normalized(eye - np.array(center))
    x = normalized(np.cross(up, z))
    y = normalized(np.cross(z, x))
    mat = identity()
    mat[0, 0:3] = x
    mat[1, 0:3] = y
    mat[2, 0:3] = z
    mat[0:3, 3] = - np.dot(mat[0:3, 0:3], eye)
    return mat

def perspective_vew(fovy, aspect, z_near, z_far):
    pass

def ortho_view(left, right, bottom, top, near, far):
    return np.array([
        [2. / (right - left), 0, 0, - (right + left) / (right - left)],
        [0, 2. / (top - bottom), 0, - (top + bottom) / (top - bottom)],
        [0, 0, 2. / (near - far), (near + far) / (near - far)],
        [0, 0, 0, 1],
    ], dtype=GLfloat)

def identity(n=4):
    return np.eye(n, dtype=GLfloat)
