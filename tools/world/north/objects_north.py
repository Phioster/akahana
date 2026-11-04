"""Things of the north drawn per pixel in the cherry-tree style (no outlines, light from the upper left,
grain from G/CL): the gorge with its frozen brook, the plank footbridge over it, the rock with the cave."""
import os
import sys

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from berg_objects import STONE, SNOWR, LOG, FL, pal, _tools, drift  # noqa: E402

ICE = pal(['#3b4c5c', '#5a7488', '#86a2b6', '#b4cad8', '#dce8ee'])
DARK = pal(['#0e0f14', '#16181f', '#1f222b', '#2a2e38'])


def _q(P, v, g):
    v = min(max(v, 0), 0.999) * (len(P) - 1)
    k = int(v)
    return P[min(len(P) - 1, k + (g < v - k))]


class Gorge:
    """A crack across the slope seen from above at an angle: its far wall shows a rock face, the floor lies
    in shadow with a frozen brook, the near lip hangs over with snow. cy(x), hw(x) = centre row, half width."""
    def __init__(s, xs, cy, hw, seed=31):
        s.xs, s.cy, s.hw, s.seed = np.asarray(xs), np.asarray(cy, float), np.asarray(hw, float), seed

    def mask(s, H, W):
        m = np.zeros((H, W), bool)
        for x, c, h in zip(s.xs, s.cy, s.hw):
            if 0 <= x < W and h > 0.5:
                m[max(0, int(c - h)):max(0, int(c + h)), x] = True
        return m

    def draw(s, img, G, CL):
        H, W, _ = img.shape
        rng = np.random.default_rng(s.seed)
        n = len(s.xs) + 8
        lipt = ndi.gaussian_filter1d(rng.normal(0, 1, n), 1.5) * 1.6       # jagged far lip
        lipb = ndi.gaussian_filter1d(rng.normal(0, 1, n), 1.5) * 1.2       # jagged near lip
        fh = 0.8 + 0.5 * (ndi.gaussian_filter1d(rng.normal(0, 1, n), 6) * 2.2)   # the wall's visible height varies
        crack = ndi.gaussian_filter1d(rng.normal(0, 1, n), 1.0)
        icew = 0.18 + 0.12 * ndi.gaussian_filter1d(rng.normal(0, 1, n), 8) * 2.5
        for k, (x, c, h) in enumerate(zip(s.xs, s.cy, s.hw)):
            if not 0 <= x < W or h <= 0.5:
                continue
            yt, yb = int(round(c - h + lipt[k])), int(round(c + h + lipb[k]))
            face = max(2, int(round(h * np.clip(fh[k], 0.6, 1.4))))
            for j in range(max(0, yt - 3), min(H, yb + 3)):
                g, cl = G[j, x], CL[j, x]
                if j < yt:                                           # snow cornice on the far lip, lumpy
                    if g < 0.45 + 0.15 * (j - yt + 3):
                        img[j, x] = _q(SNOWR, 0.8 + 0.12 * cl, g)
                elif j < yt + face:                                  # far wall: layered rock with cracks
                    t = (j - yt) / face
                    layer = 0.12 * np.sin((j + 0.4 * x) * 0.9 + lipt[k])
                    v = 0.66 - 0.5 * t + layer + 0.18 * (cl - 0.5) - (0.25 if crack[k] > 1.1 else 0)
                    img[j, x] = _q(STONE, v, g)
                    if t < 0.3 and g < 0.35 - t:
                        img[j, x] = _q(SNOWR, 0.72, g)              # snow lodged on ledges
                elif j < yb - 1:                                     # floor in shadow; the brook frozen, half snowed over
                    mid = (yt + face + yb - 1) / 2.0
                    dd = abs(j - mid) / max(1.0, (yb - 1 - yt - face) / 2.0)
                    if dd < icew[k]:
                        img[j, x] = _q(ICE, 0.6 - 0.5 * dd + 0.3 * (cl - 0.5), g)
                        if cl > 0.7:
                            img[j, x] = _q(SNOWR, 0.8, g)          # snow drifted onto the ice
                    else:
                        img[j, x] = _q(DARK, 0.55 - 0.3 * dd + 0.25 * cl, g)
                        if cl > 0.82:
                            img[j, x] = _q(STONE, 0.35, g)          # stones on the floor
                elif j < yb + 1:
                    img[j, x] = _q(DARK, 0.75, g)                    # the near overhang's dark underside
                elif g < 0.75 - 0.3 * (j - yb):
                    img[j, x] = _q(SNOWR, 0.9, g)                    # snow pushed out over the edge


class FootBridge:
    """Narrow plank bridge across the gorge (runs north-south on screen): planks, a rope rail either side,
    a post with a snow cap at each end, its shadow on the floor below."""
    def __init__(s, x, y_far, y_near, w=7, seed=41):
        s.x, s.y0, s.y1, s.w, s.seed = x, y_far, y_near, w, seed

    def walk_mask(s, H, W):
        m = np.zeros((H, W), bool)
        m[s.y0 - 3:s.y1 + 4, s.x - s.w // 2:s.x + s.w // 2 + 1] = True
        return m

    def draw(s, img, G, CL):
        q, put, wob, hump = _tools(img, G, CL, s.seed)
        x0, x1 = s.x - s.w // 2, s.x + s.w // 2
        for j in range(s.y0 + 3, s.y1 + 3):                         # its shadow falls on the gorge floor
            for i in range(x0 + 2, x1 + 4):
                if 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
                    img[j, i] = img[j, i] * 0.6
        for j in range(s.y0 - 2, s.y1 + 3):
            for i in range(x0, x1 + 1):
                gap = (j - s.y0) % 3 == 2
                v = 0.5 - 0.25 * (i - x0) / max(1, s.w) - (0.25 if gap else 0) + 0.08 * np.sin(j * 1.7 + i)
                put(i, j, q(LOG, v, j, i))
                if not gap and G[j % img.shape[0], i % img.shape[1]] < 0.22:
                    put(i, j, q(SNOWR, 0.85, j, i))                  # snow left on the planks
            put(x0 - 1, j, q(LOG, 0.2, j, x0 - 1))                    # rope rails
            put(x1 + 1, j, q(LOG, 0.15, j, x1 + 1))
        for (px, py) in ((x0 - 1, s.y0 - 3), (x1 + 1, s.y0 - 3), (x0 - 1, s.y1 + 3), (x1 + 1, s.y1 + 3)):
            for k in range(4):                                       # posts, snow on their heads
                put(px, py - k, q(LOG, 0.35 - 0.1 * (px > s.x), py - k, px))
            put(px, py - 4, q(SNOWR, 0.92, py - 4, px))


class CaveRock:
    """A rock outcrop whose face looks south, a dark cave mouth in it with icicles; just inside a little
    resting place: a straw mat, a tea bowl and a candle whose warm light falls out onto the snow."""
    def __init__(s, x, y, rx=40, face=24, mouth=(16, 13), seed=51):
        s.x, s.y, s.rx, s.face, s.mouth, s.seed = x, y, rx, face, mouth, seed   # (x, y) = middle of the face's foot

    def solid(s, H, W):
        """Rock you cannot walk on: the whole outcrop except the cave floor a few steps in."""
        yy, xx = np.mgrid[0:H, 0:W]
        top = s.y - s.face
        m = (np.abs(xx - s.x) < 1.25 * s.rx) & (yy >= top - s.rx) & (yy < s.y) & \
            ((((xx - s.x) / (1.3 * s.rx)) ** 2 + ((yy - s.y + s.face / 2.0) / (s.face / 2.0 + s.rx * 0.6)) ** 2) < 1)
        mw, mh = s.mouth
        inside = (np.abs(xx - s.x) < mw // 2 - 2) & (yy > s.y - mh + 6) & (yy <= s.y)
        return m & ~inside

    def draw(s, img, G, CL):
        q, put, wob, hump = _tools(img, G, CL, s.seed)
        H, W, _ = img.shape
        x, y, rx, face = s.x, s.y, s.rx, s.face
        top = y - face
        rng = np.random.default_rng(s.seed)
        jag = ndi.gaussian_filter1d(rng.normal(0, 1, 2 * rx + 20), 2.0) * 2.5
        mw, mh = s.mouth
        # candle light on the snow in front of the mouth (under everything else)
        for j in range(y - 2, min(H, y + 16)):
            for i in range(x - 18, x + 19):
                d = np.hypot((i - x) / 16.0, (j - y + 1) / 12.0)
                a = max(0.0, 1 - d) ** 1.4 * 0.55
                if a > 0.03 and G[j % H, i % W] < a * 1.6:
                    img[j, i] = img[j, i] * (1 - a) + FL[2] * a
        # the top of the outcrop: three humps of snow-covered rock seen from above
        humps = [(x - rx * 0.62, top + 3, rx * 0.48, rx * 0.36), (x + rx * 0.05, top - 6, rx * 0.62, rx * 0.5),
                 (x + rx * 0.7, top + 1, rx * 0.45, rx * 0.34), (x - rx * 0.2, top + 6, rx * 0.4, rx * 0.25)]
        x0, x1 = int(x - 1.3 * rx), int(x + 1.3 * rx)
        ys0 = int(top - rx)
        rim = {}
        for j in range(ys0, top + 4):
            for i in range(x0, x1 + 1):
                e = min(((i - hx) / ax) ** 2 + ((j - hy) / ay) ** 2 for hx, hy, ax, ay in humps)
                if e > 1 + 0.12 * jag[(i - x0) % len(jag)]:
                    continue
                rim[i] = max(rim.get(i, j), j)
                rocky = CL[j % H, i % W] + 0.25 * e > 0.62                 # rock shows through, snow lies in the hollows
                v = (0.68 - 0.3 * (i - x) / rx - 0.25 * e) if rocky else (0.9 - 0.2 * (i - x) / rx)
                put(i, j, q(STONE if rocky else SNOWR, v, j, i))
        # the face: hangs down from each column's rim to the ragged foot, layered, darker low and right
        for i, r0 in rim.items():
            foot = y + int(round(0.8 * jag[(i * 5) % len(jag)])) if abs(i - x) > mw // 2 + 1 else y
            for j in range(r0 + 1, foot):
                t = (j - r0) / max(1, foot - r0)
                layer = 0.1 * np.sin(j * 0.8 + 0.3 * i)
                v = 0.62 - 0.38 * t - 0.2 * (i - x) / rx + layer + 0.12 * (CL[j % H, i % W] - 0.5)
                put(i, j, q(STONE, v, j, i))
                if t < 0.1 and G[j % H, i % W] < 0.55:
                    put(i, j, q(SNOWR, 0.75, j, i))
        # the mouth: an arch, black at the back, a warm glow low down from the candle
        for j in range(y - mh, y + 1):
            for i in range(x - mw // 2, x + mw // 2 + 1):
                u = (i - x) / (mw / 2.0)
                arch = y - mh + int(round(mh * 0.45 * (1 - np.sqrt(max(0.0, 1 - u * u)))))
                if j < arch:
                    continue
                depth = 1 - abs(u)
                v = 0.2 + 0.4 * (1 - depth) + 0.1 * CL[j % H, i % W]
                put(i, j, q(DARK, v, j, i))
                warm = max(0.0, 1 - np.hypot(i - (x + 2), (j - (y - 2)) * 1.4) / 7.0)
                if warm > 0:
                    put(i, j, img[j, i] * (1 - 0.6 * warm) + FL[1] * 0.6 * warm)
        for k in range(-mw // 2 + 1, mw // 2):                       # icicles from the arch's brow
            if rng.random() < 0.55:
                u = k / (mw / 2.0)
                j0 = y - mh + int(round(mh * 0.45 * (1 - np.sqrt(max(0.0, 1 - u * u)))))
                for L in range(int(rng.integers(1, 4))):
                    put(x + k, j0 + L, q(ICE, 0.95 - 0.25 * L, j0 + L, x + k))
        # the little resting place just inside: straw mat, tea bowl, candle
        for i in range(x - 5, x + 1):
            put(i, y - 1, FL[0] * 0.55 + LOG[4] * 0.45)                  # straw mat, in the dim
        put(x - 3, y - 2, LOG[4] * 0.8)
        put(x - 4, y - 2, STONE[3]); put(x - 3, y - 3, STONE[4])       # the tea bowl
        put(x + 2, y - 2, np.array([224, 214, 196.0]))                 # the candle and its flame
        put(x + 2, y - 3, FL[4]); put(x + 2, y - 4, FL[3])
        # snow drifts at the foot of the face either side of the mouth
        drift(img, q, put, int(x - 1.2 * rx), x - mw // 2 - 1, y, hump, wob, up=3, down=3)
        drift(img, q, put, x + mw // 2 + 2, int(x + 1.2 * rx), y, hump, wob, up=3, down=3)
