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


def boulder(img, x, y, r, G, CL, seed):
    """A whole little rock, not a slab: two or three rounded lumps, lit from the upper left, snow on what faces
    up, a dark foot where it sits and a soft shadow on the snow to the right. (x, y) = middle of its foot."""
    H, W, _ = img.shape
    rng = np.random.default_rng(seed)
    lumps = [(0.0, 0.0, r, 0.8 * r)]
    for _ in range(int(rng.integers(1, 3))):
        lumps.append((rng.uniform(-0.6, 0.6) * r, rng.uniform(-0.3, 0.1) * r, rng.uniform(0.5, 0.8) * r,
                      rng.uniform(0.4, 0.65) * r))
    for j in range(int(y - 0.4 * r), int(y + 2)):                     # shadow first, under and right
        for i in range(int(x - r * 0.6), int(x + r * 1.6)):
            if 0 <= i < W and 0 <= j < H and ((i - x - 0.45 * r) / (1.1 * r)) ** 2 + ((j - y + 0.2) / 1.6) ** 2 < 1:
                img[j, i] = img[j, i] * 0.78
    for j in range(int(y - 2 * r) - 1, int(y) + 1):
        for i in range(int(x - 2 * r) - 1, int(x + 2 * r) + 2):
            if not (0 <= i < W and 0 <= j < H):
                continue
            best = None
            for (dx, dy, ax, ay) in lumps:
                cx, cyy = x + dx, y - ay + dy                          # each lump sits on the ground line
                u, v = (i - cx) / ax, (j - cyy) / ay
                e = u * u + v * v
                if e < 1 and (best is None or j - cyy > best[2]):
                    best = (u, v, j - cyy)
            if best is None:
                continue
            u, v, _ = best
            nz = np.sqrt(max(0.0, 1 - u * u - v * v))
            lit = 0.45 + 0.45 * (-0.55 * u - 0.6 * v + 0.6 * nz) + 0.12 * (CL[j, i] - 0.5)
            g = G[j, i]
            if v < -0.25 and nz > 0.35 and g < 0.8:                    # snow on the top
                img[j, i] = _q(SNOWR, 0.7 + 0.3 * lit, g)
            elif j >= y - 1:
                img[j, i] = _q(STONE, 0.15, g)                         # where it sits, in its own shade
            else:
                img[j, i] = _q(STONE, lit, g)


class CaveHill:
    """The land heaves up into a snowy hill (no outline: it only shades the ground it rises from); at its
    front a face is cut, and in it the cave runs in like a mine adit, a timber frame round the mouth.
    Just inside: straw mat, tea bowl and a candle whose light falls out onto the snow."""
    def __init__(s, x, y, rx=70, ry=44, cut=16, mouth=(12, 12), seed=51):
        s.x, s.y, s.rx, s.ry, s.cut, s.mouth, s.seed = x, y, rx, ry, cut, mouth, seed   # (x, y) = foot of the mouth

    def height(s, H, W):
        yy, xx = np.mgrid[0:H, 0:W]
        cx, cy = s.x + 4, s.y - s.ry * 0.75                           # the crown lies behind the mouth
        d2 = ((xx - cx) / s.rx) ** 2 + ((yy - cy) / s.ry) ** 2
        rng = np.random.default_rng(s.seed)
        n = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 12) * 12
        return np.clip(1 - d2 + 0.08 * n, 0, None) ** 1.3                  # a smooth mound, a little uneven

    def solid(s, H, W):
        yy, xx = np.mgrid[0:H, 0:W]
        h = s.height(H, W)
        mw, mh = s.mouth
        inside = (np.abs(xx - s.x) <= mw // 2 - 2) & (yy > s.y - 8) & (yy <= s.y)
        return (h > 0.35) & ~inside

    def draw(s, img, G, CL):
        q, put, wob, hump = _tools(img, G, CL, s.seed)
        H, W, _ = img.shape
        x, y = s.x, s.y
        mw, mh = s.mouth
        h = s.height(H, W)
        # 1) the hill: the ground shaded by its slope (lit from the upper left), a few rocks breaking through
        gy, gx = np.gradient(ndi.gaussian_filter(h, 1.2))
        shade = np.clip(1 + 26.0 * (gx * 0.9 + gy * 0.45), 0.66, 1.18)    # lit upper left, shade to the lower right
        yy_, xx_ = np.mgrid[0:H, 0:W]                                   # and its shadow falls on the snow lower right
        sx = ((xx_ - (s.x + 4 + 0.35 * s.rx)) / (s.rx * 1.05)) ** 2 + ((yy_ - (s.y - s.ry * 0.45)) / (s.ry * 0.9)) ** 2
        cast = (sx < 1) & (h < 0.05) & (G < 0.85 - 0.6 * sx)
        img[cast] = img[cast] * 0.86
        on = h > 0.02
        img[on] = np.clip(img[on] * shade[on][:, None], 0, 255)
        rng = np.random.default_rng(s.seed)
        for _ in range(int(s.rx * s.ry / 220)):
            i, j = int(rng.integers(x - s.rx, x + s.rx)), int(rng.integers(y - 2 * s.ry, y))
            if 0 <= i < W and 0 <= j < H and 0.25 < h[j, i] and rng.random() < 0.6:
                boulder(img, i, j, int(rng.integers(2, 4)), G, CL, i * 13 + j)
        # 2) the cut face: earth and rock from the slope's front down to the foot, wider than the mouth
        cut = s.cut
        jag = ndi.gaussian_filter1d(rng.normal(0, 1, 4 * cut + 8), 1.5) * 1.5
        for k, i in enumerate(range(x - cut, x + cut + 1)):
            u = (i - x) / cut
            depth = int(round((mh + 3) * np.sqrt(max(0.0, 1 - u ** 2)) + 1.5 * jag[k]))   # highest over the mouth, ragged
            for j in range(y - depth, y + 1):
                t = (j - (y - depth)) / max(1, depth)
                v = 0.62 - 0.4 * t - 0.15 * u + 0.1 * np.sin(j * 0.9 + i * 0.4) + 0.12 * (CL[j % H, i % W] - .5)
                put(i, j, q(STONE, v, j, i))
            put(i, y - depth - 1, q(SNOWR, 0.85, y - depth - 1, i))       # snow lip over the cut
        # 3) the mouth, black at the back, warm low down
        for j in range(y - mh, y + 1):
            for i in range(x - mw // 2, x + mw // 2 + 1):
                depth = 1 - abs(i - x) / (mw / 2.0)
                v = 0.15 + 0.4 * (1 - depth) + 0.1 * CL[j % H, i % W]
                put(i, j, q(DARK, v, j, i))
                warm = max(0.0, 1 - np.hypot(i - x, (j - (y - mh + 5)) * 1.2) / 4.0)   # a faint halo round the far flame
                if warm > 0:
                    put(i, j, img[j, i] * (1 - 0.45 * warm) + FL[1] * 0.45 * warm)
        # 4) the timber frame: two posts and a lintel, snow on the lintel, icicles under it
        for j in range(y - mh - 1, y + 1):
            put(x - mw // 2 - 1, j, q(LOG, 0.5, j, x - mw // 2 - 1))
            put(x + mw // 2 + 1, j, q(LOG, 0.25, j, x + mw // 2 + 1))
        for i in range(x - mw // 2 - 2, x + mw // 2 + 3):
            put(i, y - mh - 1, q(LOG, 0.55 - 0.2 * (i - x) / mw, y - mh - 1, i))
            put(i, y - mh - 2, q(LOG, 0.4, y - mh - 2, i))
            put(i, y - mh - 3, q(SNOWR, 0.9, y - mh - 3, i))
        for k in range(-mw // 2 + 1, mw // 2):
            if rng.random() < 0.5:
                for L in range(int(rng.integers(1, 3))):
                    put(x + k, y - mh + L, q(ICE, 0.95 - 0.3 * L, y - mh + L, x + k))
        # 5) from outside only the candle shows, far back in the dark
        put(x, y - mh + 4, FL[3]); put(x, y - mh + 5, FL[2])
        # 6) candle light out onto the snow, and drifts heaped against the cut either side
        for j in range(y, min(H, y + 8)):
            for i in range(x - 8, x + 9):
                dd = np.hypot((i - x) / 8.0, (j - y + 1) / 6.0)
                a = max(0.0, 1 - dd) ** 1.4 * 0.25                          # only a faint warmth reaches the snow
                if a > 0.03 and G[j % H, i % W] < a * 1.6:
                    img[j, i] = img[j, i] * (1 - a) + FL[2] * a
        drift(img, q, put, x - cut - 6, x - mw // 2 - 2, y + 1, hump, wob, up=3, down=3)
        drift(img, q, put, x + mw // 2 + 3, x + cut + 7, y + 1, hump, wob, up=3, down=3)



class CaveMound:
    """The land heaves up in front of the slope, read as height the way the old map shows its cliff: a snowy
    top (flat tones, lit) whose front drops as a wall of earth and rock - highest in the middle, running out
    into the ground at both sides - and the cave mouth in that wall with a timber frame. The wall casts its
    shadow down and to the right. (x, y) = foot of the mouth."""
    def __init__(s, x, y, rx=58, top=30, wall=27, mouth=(12, 12), seed=51):
        s.x, s.y, s.rx, s.top, s.wall, s.mouth, s.seed = x, y, rx, top, wall, mouth, seed

    def _shape(s, W):
        """Never a half circle: the left reaches further than the right, the far rim and the wall go in lumps."""
        rng = np.random.default_rng(s.seed)
        left, right = s.rx * 1.15, s.rx * 0.8
        xs = np.arange(int(s.x - left), int(s.x + right) + 1)
        u = np.where(xs < s.x, (xs - s.x) / left, (xs - s.x) / right)
        lumps = ndi.gaussian_filter1d(rng.normal(0, 1, len(xs)), 7) * 9               # big bulges of the rim
        jag = ndi.gaussian_filter1d(rng.normal(0, 1, len(xs)), 2) * 3                 # small ragged steps
        dent = ndi.gaussian_filter1d(rng.normal(0, 1, len(xs)), 5) * 6
        prof = np.clip(1 - np.abs(u) ** 1.6, 0, 1)
        hgt = np.clip(s.wall * prof ** 0.7 + dent * prof + 0.5 * jag, 0, None)        # the wall, dented
        foot = s.y + (u * u) * 7 + 2.5 * np.sin(xs / 11.0) * np.abs(u) + 0.6 * jag   # the foot wanders at the sides
        back = foot - hgt - s.top * prof ** 0.5 * (1 + 0.25 * np.sin(xs / 17.0 + 1)) + lumps * prof + jag
        return xs, hgt, foot, back

    def solid(s, H, W):
        m = np.zeros((H, W), bool)
        xs, hgt, foot, back = s._shape(W)
        mw, mh = s.mouth
        for x, f, b in zip(xs, foot, back):
            if 0 <= x < W and abs(x - s.x) > mw // 2 - 2:
                m[max(0, int(b)):max(0, int(f)), x] = True
            elif 0 <= x < W:
                m[max(0, int(b)):max(0, int(f) - mh), x] = True
        return m

    def draw(s, img, G, CL):
        q, put, wob, hump = _tools(img, G, CL, s.seed)
        H, W, _ = img.shape
        xs, hgt, foot, back = s._shape(W)
        mw, mh = s.mouth
        from field6 import WH, L1, MG, DG, K
        # shadow of the wall, down and to the right on the snow
        for x, h, f in zip(xs, hgt, foot):
            for j in range(int(f), int(f + 0.45 * h) + 1):
                i = int(x + (j - f) * 0.9 + 2)
                if 0 <= i < W and 0 <= j < H and G[j, i] < 0.9:
                    img[j, i] = img[j, i] * 0.8
        for k, (x, h, f, b) in enumerate(zip(xs, hgt, foot, back)):
            if not 0 <= x < W:
                continue
            top_end = f - h
            u = (x - s.x) / s.rx
            for j in range(max(0, int(b)), min(H, int(top_end))):               # the snowy top, lit from the upper left
                t = (j - b) / max(1.0, top_end - b)
                lit = CL[j, x] * 0.6 + G[j, x] * 0.4 > 0.35 + 0.5 * u + 0.4 * t   # light fades to the right and the front
                c = (WH if CL[j, x] > 0.35 else L1) if lit else (L1 if CL[j, x] > 0.4 else MG)
                if CL[j, x] > 0.88:
                    c = MG                                                     # a rock pokes through
                if j - b < 1.5 or (u > 0.55 and G[j, x] < (u - 0.55) * 2.5):
                    c = MG if G[j, x] < 0.7 else L1                            # its far rim and the shaded right flank
                img[j, x] = c
            if 0 <= int(top_end) < H:
                img[int(top_end), x] = WH                                       # the lit lip of snow
            for j in range(max(0, int(top_end) + 1), min(H, int(f) + 1)):     # the wall: earth and rock in layers
                t = (j - top_end) / max(1.0, h)
                band = int((j + 1.6 * np.sin(x / 9.0) + 0.8 * np.sin(x / 3.7)) / 3) % 3   # wavy, roughly level layers
                c = (MG, DG, DG)[band] if u < 0.2 else (DG, DG, K)[band]
                if t > 0.8:
                    c = K                                                      # dark at the foot
                if G[j, x] < 0.08:
                    c = L1                                                     # snow caught on a ledge
                img[j, x] = c
        # the mouth, a timber frame, from outside only the candle far inside
        x, y = s.x, s.y
        for j in range(y - mh, y + 1):
            for i in range(x - mw // 2, x + mw // 2 + 1):
                img[j, i] = K * (0.5 + 0.3 * abs(i - x) / (mw / 2.0))
        for j in range(y - mh - 1, y + 1):
            put(x - mw // 2 - 1, j, q(LOG, 0.5, j, x - mw // 2 - 1))
            put(x + mw // 2 + 1, j, q(LOG, 0.25, j, x + mw // 2 + 1))
        for i in range(x - mw // 2 - 2, x + mw // 2 + 3):
            put(i, y - mh - 1, q(LOG, 0.55, y - mh - 1, i))
            put(i, y - mh - 2, q(LOG, 0.4, y - mh - 2, i))
        put(x, y - mh + 5, FL[3]); put(x, y - mh + 6, FL[2])
        put(x - 1, y - mh + 6, img[y - mh + 6, x - 1] * 0.6 + FL[1] * 0.4)
        put(x + 1, y - mh + 6, img[y - mh + 6, x + 1] * 0.6 + FL[1] * 0.4)
        drift(img, q, put, int(x - s.rx * 0.8), x - mw // 2 - 2, lambda i: int(foot[min(len(foot) - 1, max(0, i - xs[0]))]) + 1,
              hump, wob, up=3, down=3)
        drift(img, q, put, x + mw // 2 + 3, int(x + s.rx * 0.8), lambda i: int(foot[min(len(foot) - 1, max(0, i - xs[0]))]) + 1,
              hump, wob, up=3, down=3)
