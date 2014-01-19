import raygllib.matlib as mat
import unittest
import numpy as np

class TestMatlib(unittest.TestCase):
    def test_normalized(self):
        x = (0, 1, 2)
        x0 = mat.normalized(x)
        self.assertTrue(np.equal(1, np.dot(x0, x0) ** .5))

    def test_ortho_view(self):
        left, right, bottom, top, near, far = -8, 8, -6, 6, -10, 10
        m = mat.ortho_view(left, right, bottom, top, near, far)
        self.assertTrue(np.allclose(np.dot(m, (left, 0, 0, 1)), (-1, 0, 0, 1)))
        self.assertTrue(np.allclose(np.dot(m, (right, 0, 0, 1)), (1, 0, 0, 1)))
        self.assertTrue(np.allclose(np.dot(m, (0, bottom, 0, 1)), (0, -1, 0, 1)))
        self.assertTrue(np.allclose(np.dot(m, (0, top, 0, 1)), (0, 1, 0, 1)))
        self.assertTrue(np.allclose(np.dot(m, (0, 0, far, 1)), (0, 0, -1, 1)))
        self.assertTrue(np.allclose(np.dot(m, (0, 0, near, 1)), (0, 0, 1, 1)))

    def test_look_at(self):
        for up in [(0, 1, 0), (1, 0, 0), (0, 0, 1), (.2, .4, .1)]:
            eye = (1, 2, 3)
            center = (.1, .2, .3)
            up = (0, 1, 0)
            m = mat.look_at(eye, center, up)
            eyeProj = m.dot(eye + (1,))
            self.assertTrue(sum((eyeProj - (0, 0, 0, 1)) ** 2) < 1e-8)
            centerProj = m.dot(center + (1,))
            cx, cy = centerProj[0:2] 
            self.assertTrue(abs(cx) < 1e-6)
            self.assertTrue(abs(cy) < 1e-6)

    def test_rotate(self):
        angle = np.pi / 6
        center = (1, 2, 3)
        axis = (9, 8, 7)
        R = mat.rotate(angle, center, axis)

        def decompose(p):
            n = mat.normalized(axis)
            p = p[:3] - center
            pn = p.dot(n) * n
            return pn, p - pn

        for t in range(100):
            p = np.random.rand(4)
            p[3] = 1
            p1 = R.dot(p)
            pn, pt = decompose(p)
            p1n, p1t = decompose(p1)
            self.assertTrue(np.allclose(pn, p1n))
            l1 = np.linalg.norm(pt, 2)
            l2 = np.linalg.norm(p1t, 2)
            print(l1, l2)
            self.assertTrue(self.equal(l1, l2))
            self.assertTrue(self.equal(np.dot(pt, p1t) / (l1 * l2), np.cos(angle)))

    def equal(self, a, b):
        return np.abs(a - b) < 1e-6

if __name__ == '__main__':
    unittest.main()
