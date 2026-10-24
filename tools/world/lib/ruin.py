# Buildings for the foothill picture, drawn per pixel in the cherry-tree style (no outlines, light from the upper left).
import numpy as np
from scipy import ndimage as ndi
import sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
from objects2 import STONE, MOSS3, WOOD, TILE, put, hx

def _q(P, v, g):
    v = min(max(v, 0), 0.999) * len(P); i = int(v)
    return P[min(len(P) - 1, i + (g < (v - i) * 0.9))]

class Ruin:
    """A roofless chapel: back wall with an empty pointed window, broken side walls, a collapsed front with
    half a doorway arch, fallen blocks, moss. (x0, y0)-(x1, y1) = footprint on the ground."""
    def __init__(s, x0, y0, x1, y1, seed=3):
        s.x0, s.y0, s.x1, s.y1 = x0, y0, x1, y1
        r = np.random.default_rng(seed)
        s.g = r.random((80, 120)); s.r = r
        n = ndi.gaussian_filter1d(r.normal(0, 1, 200), 2.5); s.jag = n / n.std()
        s.moss = ndi.gaussian_filter(r.normal(0, 1, (80, 120)), 1.4)

    def footprint(s, H, W):
        yy, xx = np.mgrid[0:H, 0:W]
        return (xx >= s.x0 - 6) & (xx <= s.x1 + 6) & (yy >= s.y0 - 34) & (yy <= s.y1 + 6)

    def _stone(s, i, j, v, face=False):
        g = s.g[j % 80, i % 120]
        course = (j % 4 == 3) if face else False                       # mortar courses on faces
        joint = face and ((i + 5 * ((j // 4) % 2)) % 7 == 0)
        v = v - 0.14 * (course or joint) + 0.12 * (g - .5)
        c = _q(STONE, v, g)
        if s.moss[j % 80, i % 120] > 0.7 and not course: c = MOSS3[1 if v < 0.5 else 2]
        return c

    def hwall(s, img, x0, x1, yb, hmax, thick=3, window=None, door=None, gable=False):
        """A wall running across the picture: top surface, then its face towards us, broken top edge."""
        for i in range(x0, x1):
            t = (i - x0) / max(x1 - x0 - 1, 1)
            if gable:                                                  # gable: highest in the middle, one side broken away
                prof = 1 - abs(t - 0.5) * 1.5
                if t > 0.62: prof *= np.clip(1 - (t - 0.62) * 2.4, 0.25, 1)
            else:
                prof = 0.8
            h = int(round(hmax * prof * (0.9 + 0.1 * s.jag[(i * 2) % 200]) + 1.2 * s.jag[(i * 7 + 13) % 200]))
            h = max(h, 2)
            if window and window[0] <= i < window[1]:                  # the empty pointed window keeps its frame
                pass
            top = yb - h
            for j in range(top - thick, top):                          # top surface, lit
                put(img, i, j, s._stone(i, j, 0.84 - 0.15 * t))
            for j in range(top, yb):                                   # face, a bit darker, courses
                v = 0.66 - 0.2 * t - 0.12 * (j - top) / max(h, 1)
                if window:
                    wx0, wx1, wy0, wy1 = window
                    cx = (wx0 + wx1) / 2; r_ = (wx1 - wx0) / 2
                    inside = wx0 <= i < wx1 and wy0 <= j < wy1
                    if inside and j < wy0 + r_ * 1.4:                  # pointed arch head
                        inside = (np.hypot(i - wx0, j - (wy0 + r_ * 1.4)) <= 2 * r_) and (np.hypot(i - wx1 + 1, j - (wy0 + r_ * 1.4)) <= 2 * r_)
                    if inside: continue                                # opening: the ground behind shows through
                    if (wx0 - 1 <= i <= wx1) and (wy0 - 1 <= j <= wy1) and not inside: v += 0.12   # dressed frame
                if door and door[0] <= i < door[1] and j > yb - door[2]: continue
                put(img, i, j, s._stone(i, j, v, face=True))
            for k in range(2): put(img, i, yb + k, img[min(yb + k, img.shape[0] - 1), i] * 0 + hx('#2a2526') if k == 0 else hx('#4a4446'))

    def vwall(s, img, x, y0, y1, hmax):
        """A side wall running away from us: we see its top and its lit outer face (left wall) or shade."""
        for j in range(y0, y1):
            t = (j - y0) / max(y1 - y0, 1)
            h = int(round(hmax * (1 - 0.6 * t) * np.clip(0.7 + 0.3 * s.jag[(j * 5 + x) % 200], 0.3, 1.2)))
            for k in range(h):                                          # stacked: higher wall = taller stripe upward
                put(img, x, j - k, s._stone(x, j - k, 0.6, face=True)); put(img, x + 1, j - k, s._stone(x + 1, j - k, 0.5, face=True)); put(img, x + 2, j - k, s._stone(x + 2, j - k, 0.42, face=True))
            for u in range(3): put(img, x + u, j - h, s._stone(x + u, j - h, 0.86 - 0.08 * u))

    def draw(s, img):
        x0, y0, x1, y1 = s.x0, s.y0, s.x1, s.y1
        H, W, _ = img.shape
        # interior: trodden earth and rubble, shadow along the back wall
        for j in range(y0, y1):
            for i in range(x0 + 3, x1 - 3):
                if s.g[j % 80, i % 120] < 0.25: put(img, i, j, img[j, i] * 0.8)
        for j in range(y0, y0 + 6):
            for i in range(x0, x1): put(img, i, j, img[j, i] * (0.55 + 0.07 * (j - y0)))
        # back wall: the tallest part, with the empty window
        wcx = (x0 + x1) // 2
        s.hwall(img, x0, x1, y0, 34, window=(wcx - 5, wcx + 5, y0 - 26, y0 - 6), gable=True)
        # side walls, ruined lower towards the front
        s.vwall(img, x0, y0 + 1, y1, 16)
        s.vwall(img, x1 - 3, y0 + 1, y1 - 8, 13)
        # front: collapsed, only stumps and half a doorway arch on the left of the gap
        s.hwall(img, x0, x0 + 14, y1, 9)
        s.hwall(img, x1 - 12, x1, y1, 6)
        for k in range(10):                                              # the half arch
            a = np.pi * (0.5 + 0.5 * k / 9)
            i = int(round(x0 + 20 + 7 * np.cos(a))); j = int(round(y1 - 10 - 9 * np.sin(a)))
            for u in range(2): put(img, i + u, j, s._stone(i + u, j, 0.62 - 0.05 * u, face=True))
        # fallen blocks scattered in front and inside
        for _ in range(26):
            i = int(s.r.uniform(x0 - 8, x1 + 8)); j = int(s.r.uniform(y1 - 18, y1 + 10))
            w, h = int(s.r.integers(2, 5)), int(s.r.integers(2, 3))
            for u in range(w):
                for v in range(h): put(img, i + u, j + v, s._stone(i + u, j + v, 0.8 - 0.22 * v - 0.1 * u / w))
            for u in range(w): put(img, i + u + 1, j + h, img[min(j + h, H - 1), min(i + u + 1, W - 1)] * 0.6)


class Cottage:
    """Small stone shepherd's house: wall face with a warm window and a door, slate roof seen from above,
    chimney with a thin smoke trail. (x, y) = bottom-left of the front wall."""
    def __init__(s, x, y, w=34, wall=12, roof=16, seed=5):
        s.x, s.y, s.w, s.wall, s.roof = x, y, w, wall, roof
        r = np.random.default_rng(seed); s.g = r.random((80, 80))
        n = ndi.gaussian_filter1d(r.normal(0, 1, 200), 2.5); s.wob = n / n.std()

    def footprint(s, H, W):
        yy, xx = np.mgrid[0:H, 0:W]
        return (xx >= s.x - 5) & (xx <= s.x + s.w + 5) & (yy >= s.y - s.wall - s.roof - 12) & (yy <= s.y + 4)

    def draw(s, img):
        x, y, w = s.x, s.y, s.w
        top = y - s.wall
        FL = [hx('#fde7a0'), hx('#f2b44a'), hx('#d9822e')]
        for j in range(top, y):                                         # stone wall face: rough blocks
            for i in range(x, x + w):
                g = s.g[j % 80, i % 80]
                course = (j - top) % 4 == 3; joint = (i + 3 * (((j - top) // 4) % 2)) % 6 == 0
                v = 0.55 - 0.25 * (i - x) / w - 0.22 * (course or joint) + 0.12 * (g - .5)
                put(img, i, j, _q(STONE, v, g))
        wx = x + 6                                                      # window with warm light
        for j in range(top + 3, top + 8):
            for i in range(wx, wx + 6):
                edge = i in (wx, wx + 5) or j in (top + 3, top + 7)
                put(img, i, j, WOOD[1] if edge else (FL[0] if (j - top) < 6 else FL[1]))
        dx = x + w - 13                                                 # plank door
        for j in range(top + 2, y):
            for i in range(dx, dx + 6):
                put(img, i, j, WOOD[2 - ((i - dx) % 3 == 0)] if j > top + 2 else WOOD[0])
        for i in range(x - 1, x + w + 1): put(img, i, y, hx('#2a2526'))  # foot shadow
        # roof: dark slate, rows of tiles, rising away from us to a ridge, eaves overhanging, slightly sagging
        rt = top - s.roof
        for j in range(rt, top + 2):
            f = (j - rt) / (s.roof + 2)
            l = x - 3 - int(round(0.7 * s.wob[j % 200])); r = x + w + 3 + int(round(0.7 * s.wob[(j + 50) % 200]))
            for i in range(l, r):
                g = s.g[j % 80, i % 80]
                row = (j - rt) % 3 == 2
                v = 0.55 + 0.25 * (1 - f) - 0.25 * (i - x) / w - 0.25 * row + 0.1 * (g - .5)
                if j >= top: v -= 0.25                                  # eave edge in shade
                put(img, i, j, _q(TILE, v, g))
        for i in range(x - 2, x + w + 2): put(img, i, rt - 1, _q(TILE, 0.85, s.g[0, i % 80]))   # ridge
        cx = x + 6                                                      # chimney + smoke
        for j in range(rt - 6, rt + 3):
            for i in range(cx, cx + 4): put(img, i, j, _q(STONE, 0.6 - 0.12 * (i - cx), s.g[j % 80, i % 80]))
        for k in range(18):
            sx = cx + 1 + int(round(k * 0.45 + 1.2 * np.sin(k * 0.5))); sy = rt - 8 - k
            a = 0.4 * (1 - k / 18)
            for (u, v) in ((0, 0), (1, 0), (0, -1)):
                if 0 <= sy + v < img.shape[0] and 0 <= sx + u < img.shape[1]:
                    img[sy + v, sx + u] = img[sy + v, sx + u] * (1 - a) + np.array([200, 198, 196.]) * a
