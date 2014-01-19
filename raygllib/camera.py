import numpy as np
from . import matlib as M

class Camera:
    DRAG_SPEED = 0.005

    def __init__(self, pos, center, up):
        self.pos = pos + (1,)
        self.center = center
        self.iy = np.hstack([M.normalized(up), 0])
        self.ix = np.hstack([M.normalized(np.cross(np.array(center) - pos, up)), 0])
        self.up = up + (0,)
        self._scale = 1.
        self._gen_view_mat()

    def _gen_view_mat(self):
        self.viewMat = M.look_at(self.pos[:3], self.center, self.up[:3]).dot(
            M.scale(self._scale))

    def drag(self, dx, dy):
        dy = 0
        axis = -dy * self.ix + dx * self.iy
        r = (dx * dx + dy * dy) ** .5
        if r < 2:
            return
        R = M.rotate(-self.DRAG_SPEED * r, self.center, axis[:3])
        self.pos = R.dot(self.pos)
        self.ix = R.dot(self.ix)
        self.iy = R.dot(self.iy)
        self.up = R.dot(self.up)
        self._gen_view_mat()

    def scale(self, ds):
        self._scale *= (1 + ds)
        self._gen_view_mat()
