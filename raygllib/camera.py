import numpy as np
from . import matlib as M
from .utils import debug

class Variable:
    def __init__(self, value, finish_time=0.8):
        self._finishTime = finish_time
        value = np.array(value, dtype=np.float)
        self.value = value
        self.set(value)
        self.finished = True

    def set(self, value):
        self._startValue = self.value
        self._endValue = np.array(value, dtype=np.float)
        self._time = 0.
        self.finished = False

    def update(self, dt):
        if self.finished:
            return
        self._time += dt
        if self._time > self._finishTime:
            self.value = self._endValue
            self.finished = True
        else:
            t = self._time / self._finishTime
            self.value = (1 - t) * self._startValue + t * self._endValue

    def get(self):
        return self.value

    def __repr__(self):
        return 'Variable(v0={}, v1={}, v={}, t={}, tt={}, progress={})'.format(
            tuple(self._startValue), tuple(self._endValue), tuple(self.value),
            self._time, self._finishTime, self._time / self._finishTime)


class BallVariable(Variable):
    def set(self, value):
        x = M.normalized(self.value)
        y = M.normalized(np.array(value, dtype=np.float))
        z = M.normalized(np.cross(x, y))
        if np.allclose(z, 0):
            z = M.normalized(np.cross(x, np.random.random(3)))

        angle = np.arccos(np.dot(x, y))
        y = np.cross(z, x)
        self._ix = x
        self._iy = y
        self._time = 0.
        self._angle = angle
        if abs(angle) >= 1e-5:
            self.finished = False

    def update(self, dt):
        if self.finished:
            return
        self._time += dt
        if self._time > self._finishTime:
            self.finished = True
            a = self._angle
        else:
            a = self._time / self._finishTime * self._angle
        self.value = np.cos(a) * self._ix + np.sin(a) * self._iy

    def __repr__(self):
        return 'BallVariable(x={}, y={}, t={}, tt={}, progress={})'.format(
            tuple(self._ix), tuple(self._iy), self._time, self._finishTime,
            self._time / self._finishTime)


class Camera:
    DRAG_SPEED = 0.005

    def __init__(self, pos, center, up):
        self.pos = M.vec3_to_vec4(pos)
        self.center = M.vec3_to_vec4(center)
        self.iy = np.hstack([M.normalized(up), 0])
        self.ix = np.hstack([M.normalized(np.cross(np.array(center) - pos, up)), 0])
        self.up = M.vec3_to_vec4_n(up)
        self._scale = 1.
        self._gen_view_mat()
        self.posVar = BallVariable(M.vec4_to_vec3(self.pos - self.center))
        self.centerVar = Variable(self.center)
        self.upVar = BallVariable(M.vec4_to_vec3(self.up))
        self.target = None
        self.tracking = False

    def _gen_view_mat(self):
        self.viewMat = M.look_at(self.pos[:3], self.center[:3], self.up[:3]).dot(
            M.scale(self._scale))

    def drag(self, dx, dy):
        axis = -dy * self.ix + dx * self.iy
        r = (dx * dx + dy * dy) ** .5
        if r < 2:
            return
        R = M.rotate(-self.DRAG_SPEED * r, self.center[:3], axis[:3])
        self.pos = R.dot(self.pos)
        self.ix = R.dot(self.ix)
        self.iy = R.dot(self.iy)
        self.up = R.dot(self.up)
        self._gen_view_mat()
        self.tracking = False

    def scale(self, ds):
        self._scale *= (1 + ds)
        self._gen_view_mat()

    def update(self, dt):
        if self.tracking:
            self.posVar.update(dt)
            self.pos = M.vec3_to_vec4(
                self.target.matrix[0:3, 3] + self.dist * self.posVar.get())
            self.upVar.update(dt)
            self.up = M.vec3_to_vec4_n(self.upVar.get())
            self.centerVar.update(dt)
            self.center = self.centerVar.get()
            self._gen_view_mat()
            if self.posVar.finished and self.upVar.finished and self.centerVar.finished:
                self.tracking = False

    def set_target(self, target):
        self.target = target

    def _switch_view(self, x, y, z):
        """
        y: up
        z: out
        """
        if self.target is None:
            debug('no target')
            return
        m = self.target.matrix
        self.dist = np.linalg.norm(self.pos - self.center)
        self.posVar.set(M.normalized(np.sign(z) * m[0:3, np.abs(z) - 1]))
        self.upVar.set(np.sign(y) * m[0:3, np.abs(y) - 1])
        self.centerVar.set(M.vec3_to_vec4(m[0:3, 3]))
        self.tracking = True

    def top_view(self):
        self._switch_view(0, 2, 3)

    def bottom_view(self):
        self._switch_view(0, -2, -3)

    def left_view(self):
        self._switch_view(0, 3, -1)

    def right_view(self):
        self._switch_view(0, 3, 1)

    def front_view(self):
        self._switch_view(0, 3, -2)

    def back_view(self):
        self._switch_view(0, 3, 2)
