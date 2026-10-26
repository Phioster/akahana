"""Things standing in the southern poppy field, drawn per pixel like the rest of the world: no outlines,
light from the upper left, tones scattered by a grain map instead of smooth ramps.

Each draw(img, G) paints onto an RGB float image in place; (x, y) is always the foot.
"""
import os
import sys

import numpy as np
from scipy import ndimage as ndi
from scipy import ndimage as ndi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from objects2 import STONE, MOSS3, WOOD, hx  # noqa: E402
from field6 import K, DG, MG, L1, WH  # noqa: E402

STRAW = [hx(c) for c in ['#5b4b33', '#7d6a48', '#a08b62', '#c2ad83']]
SACK = [hx(c) for c in ['#5e544a', '#7e7466', '#a0968a', '#bdb3a5']]
CLOTH = [hx(c) for c in ['#3a2f2f', '#55403d', '#6f5450', '#8a6d66']]       # faded, once red
SCARF = [hx(c) for c in ['#3b3a40', '#55545c', '#73727a']]
CARVE = [hx(c) for c in ['#1f1d1b', '#2e2b28']]
LITSTONE = list(STONE) + [hx('#c4bfb6'), hx('#dedad2')]   # stone up to the light the ground has


def q(P, v, g):
    """Palette pick with the grain deciding between two neighbours (no smooth ramps)."""
    v = min(max(v, 0.0), 0.999) * (len(P) - 1)
    k = int(v)
    return P[min(len(P) - 1, k + (g < v - k))]


def put(img, i, j, c):
    if 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
        img[j, i] = c


def shade(img, G, x, y, rx, ry, k=0.72):
    """Soft cast shadow on the ground, to the lower right, broken up by the grain."""
    for j in range(y - 1, y + ry + 1):
        for i in range(x - 1, x + 2 * rx):
            e = ((i - x - rx * 0.6) / rx) ** 2 + ((j - y - ry * 0.3) / ry) ** 2
            if e < 1 and G[j % G.shape[0], i % G.shape[1]] < 1.05 - 0.5 * e:
                put(img, i, j, img[j, i] * k)


class Wegstein:
    """An old waymark stone, mossy, with a sign cut into its face. Variant 'a': squat and rounded with a
    poppy cut into it; 'b': tall and narrow, leaning a little, a spiral cut into it."""
    GLYPH = {'a': [(1, 0), (2, 0), (3, 0), (0, 1), (4, 1), (1, 1), (3, 1), (2, 2), (2, 3), (2, 4), (1, 3)],
             'b': [(1, 0), (2, 0), (3, 0), (3, 1), (3, 2), (2, 3), (1, 3), (0, 2), (0, 1), (1, 1), (2, 1)]}

    def __init__(s, x, y, kind='a'):
        s.x, s.y, s.kind = x, y, kind
        s.w, s.h = (12, 15) if kind == 'a' else (8, 19)

    def box(s):
        return (s.x - s.w // 2 - 2, s.y - s.h - 1, s.x + s.w // 2 + s.h // 3 + 3, s.y + 3)

    def mask(s):
        """Pixels of the stone, as {(i, j): (u, t)} with u -1..1 across, t 0 (foot) .. 1 (top)."""
        x, y, w, h = s.x, s.y, s.w, s.h
        out = {}
        bump = np.random.default_rng(len(s.kind) * 7 + x).normal(0, 1, (h + 2, 2))
        for j in range(y - h + 1, y + 1):
            t = (y - j) / (h - 1)
            # rough field stone: wide foot, shoulders at different heights, a slanted broken top
            r = w / 2 * (1.08 - 0.25 * t) * (1 - max(t - 0.62, 0) ** 1.5 * 2.2)
            cx = x + (0.6 * t if s.kind == 'a' else 0.2 * (y - j))
            k = y - j
            lo = cx - r - 0.5 * bump[k, 0] - (1.2 if s.kind == 'a' and t > 0.75 else 0)
            hi = cx + r + 0.5 * bump[k, 1] - (2.2 * (t - 0.7) / 0.3 if t > 0.7 else 0)
            for i in range(int(np.floor(lo)), int(np.ceil(hi)) + 1):
                if lo <= i + 0.5 <= hi:
                    out[(i, j)] = (2 * (i + 0.5 - lo) / max(hi - lo, 1) - 1, t)
        return out

    def draw(s, img, G):
        x, y, h = s.x, s.y, s.h
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        m = s.mask()
        cast = set()                                           # cast shadow, lower right, broken by grain
        for (i, j), (u, t) in m.items():
            for d in range(1, 4):
                cast.add((i + d, y + 1 - int((y - j) * 0.12)))
        for (si, sj) in cast - set(m):
            if g(si, sj) < 0.85 and 0 <= sj < img.shape[0] and 0 <= si < img.shape[1]:
                img[sj, si] = img[sj, si] * 0.66
        for (i, j), (u, t) in m.items():
            top = (i, j - 1) not in m                          # the upper surface catches the light
            right = (i + 1, j) not in m
            v = 0.62 - 0.38 * u - 0.18 * (t < 0.1) + (0.3 if top else 0) - (0.22 if right else 0)
            c = q(LITSTONE, v, g(i, j))
            gm = g(i * 3, j * 5)
            if (t > 0.75 and u < 0.2 and gm < 0.35) or (t < 0.3 and u > 0.3 and gm < 0.35):
                c = q(MOSS3, 0.7 - 0.45 * u + (0.2 if top else 0), g(i, j))     # moss on the crown and the shaded foot
            img[j, i] = c
        fx = int(round(x + (0 if s.kind == 'a' else 0.18 * h * 0.55))) - 2
        fy = y - int(h * 0.62)
        cut = {(fx + a, fy + b) for a, b in s.GLYPH[s.kind]}
        for (i, j) in cut:                                     # the groove, its lower edge catching light
            if (i, j) in m:
                img[j, i] = CARVE[0]
                if (i + 1, j + 1) in m and (i + 1, j + 1) not in cut:
                    img[j + 1, i + 1] = STONE[3]
        for k in (-s.w // 2 - 1, -s.w // 2, s.w // 2 + 1):                 # grass round the foot
            for d in range(2):
                put(img, x + k, y - d, DG if d == 0 else MG)


class Mauer:
    """What is left of a low dry-stone field wall: a lit top and a darker face of single stones with dark
    joints, broken into pieces, low in places, moss on top, a few stones fallen out into the field."""
    def __init__(s, pts, seed=5):
        s.pts, s.seed = pts, seed

    def box(s):
        xs = [p[0] for p in s.pts]
        ys = [p[1] for p in s.pts]
        return (min(xs) - 3, min(ys) - 9, max(xs) + 4, max(ys) + 8)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        pts = np.array(s.pts, float)
        x0, x1 = int(pts[0, 0]), int(pts[-1, 0])
        xs = np.arange(x0, x1 + 1)
        base = np.round(np.interp(xs, pts[:, 0], pts[:, 1])).astype(int)
        n = len(xs)
        hgt = np.full(n, 2)                                    # courses still standing (2 px each)
        k = 0
        while k < n:                                           # whole and fallen stretches in turn
            run = rng.integers(7, 16)
            hgt[k:k + run] = rng.choice([3, 3, 2, 1, 0], p=[.35, .25, .2, .1, .1])
            k += run
        hgt[:2] = np.minimum(hgt[:2], 1)
        hgt[-2:] = np.minimum(hgt[-2:], 1)
        joints = [rng.integers(0, 5) for _ in range(4)]       # where the stones of each course begin
        for c_ in range(4):
            joints[c_] = set(np.cumsum(rng.integers(4, 8, n)) + rng.integers(0, 4))
        for k in range(n):
            x, y, h_ = xs[k], base[k], hgt[k]
            if h_ == 0:
                if g(x, y) < 0.3:                              # rubble where it has fallen
                    put(img, x, y, q(STONE, 0.5, g(x, y + 1)))
                continue
            face = 2 * h_                                      # front face, top of the wall above it
            for d in range(face):
                j = y - d
                course = d // 2
                joint = k in joints[course]
                bed = d % 2 == 0 and d > 0                     # the line where two courses meet
                v = 0.42 + 0.14 * (d % 2 == 1) + 0.08 * ((k // 5 + course) % 2)
                put(img, x, j, STONE[1] if joint or bed else q(LITSTONE, v, g(x, j)))
            for d in range(3):                                 # the top: lit, mossy here and there
                j = y - face - d
                v = 0.86 - 0.08 * d
                c = q(LITSTONE, v, g(x, j))
                if g(x * 3, j * 7) < 0.14:
                    c = q(MOSS3, 0.8 - 0.3 * d, g(x, j))
                if k in joints[min(3, h_)] and d < 2:
                    c = STONE[3]
                put(img, x, j, c)
            for d in (1, 2):                                   # shadow on the field below the face
                if g(x, y + d) < 0.9 - 0.3 * d:
                    put(img, x, y + d, img[y + d, x] * (0.6 + 0.15 * d))
        for _ in range(5):                                     # stones lying out in the field
            k = rng.integers(2, n - 2)
            x, y = xs[k] + rng.integers(-2, 4), base[k] + rng.integers(4, 8)
            for (i, j, v) in [(0, -1, 0.85), (1, -1, 0.75), (0, 0, 0.4), (1, 0, 0.3), (2, 0, 0.25)]:
                put(img, x + i, y + j, q(STONE, v, g(x + i, y + j)))
            put(img, x + 3, y, img[y, x + 3] * 0.65)


class Vogelscheuche:
    """A lone scarecrow in the poppies: a pole, a cross stick with the sleeves of an old tunic hanging
    from it, a sack head. 'a': with a broad straw hat; 'b': bare head and a scarf, a crow on its arm."""
    def __init__(s, x, y, kind='a'):
        s.x, s.y, s.kind = x, y, kind

    def box(s):
        return (s.x - 11, s.y - 30, s.x + 12, s.y + 3)

    def draw(s, img, G):
        x, y = s.x, s.y
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        for i in range(x - 1, x + 8):                          # shadow of pole and body on the field
            for j in (y + 1, y + 2):
                if g(i, j) < 0.85:
                    put(img, i, j, img[j, i] * 0.62)
        for j in range(y - 27, y + 1):                         # the pole
            put(img, x, j, q(WOOD, 0.7, g(x, j)))
            put(img, x + 1, j, q(WOOD, 0.3, g(x + 1, j)))
        arm = y - 19
        for i in range(x - 9, x + 11):                         # the cross stick
            put(img, i, arm, q(WOOD, 0.75 - 0.025 * (i - x), g(i, arm)))
            put(img, i, arm + 1, q(WOOD, 0.3, g(i, arm + 1)))
        # the tunic: shoulders over the stick, sleeves hanging ragged, body narrowing to a torn hem
        hang = {}
        for i in range(x - 8, x + 10):
            far = abs(i - x - 0.5)
            if far > 4.5:
                hang[i] = arm + 2 + int(2 + 2.5 * g(i, 7))     # sleeves
            else:
                hang[i] = y - 8 - int(1.5 * g(i, 9)) + (1 if far < 2 else 0)
        for i, bottom in hang.items():
            top = arm - (1 if abs(i - x - 0.5) < 6 else 0)
            for j in range(top, bottom + 1):
                u = (i - x - 0.5) / 9
                fold = 0.12 if (i - x) % 3 == 0 and j > arm + 3 else 0
                v = 0.72 - 0.55 * u - fold - 0.15 * (j == bottom)
                put(img, i, j, q(CLOTH, v, g(i, j)))
        for i in range(x - 3, x + 5):                          # rope belt
            put(img, i, y - 13, q(STRAW, 0.45, g(i, y - 13)))
        for (i, j) in [(-9, 2), (-9, 3), (-8, 4), (10, 2), (10, 3), (9, 4), (-3, 11), (0, 12), (3, 11), (4, 12)]:
            put(img, x + i, arm + j, q(STRAW, 0.8, g(x + i, arm + j)))        # straw out of cuffs and hem
        # the sack head, tied at the neck
        hx_, hy = x + 0.5, arm - 4
        for j in range(arm - 7, arm - 1):
            for i in range(x - 3, x + 5):
                if ((i + 0.5 - hx_) / 3.6) ** 2 + ((j + 0.5 - hy) / 3.1) ** 2 <= 1:
                    put(img, i, j, q(SACK, 0.85 - 0.12 * (i - x) - 0.06 * (j - hy), g(i, j)))
        for i in range(x - 1, x + 3):
            put(img, i, arm - 1, q(STRAW, 0.4, g(i, arm - 1)))
        put(img, x - 1, arm - 5, CARVE[0])                      # stitched eyes and mouth
        put(img, x + 2, arm - 5, CARVE[0])
        put(img, x, arm - 3, SACK[0])
        put(img, x + 1, arm - 3, SACK[0])
        if s.kind == 'a':
            for i in range(x - 5, x + 7):                       # the brim, its shadow on the face
                put(img, i, arm - 7, q(STRAW, 0.82 - 0.05 * (i - x), g(i, arm - 7)))
                put(img, i, arm - 6, img[arm - 6, i] * 0.7 if x - 3 <= i <= x + 4 else img[arm - 6, i])
            for j in (arm - 10, arm - 9, arm - 8):
                for i in range(x - 2, x + 4):
                    v = 0.9 - 0.12 * (i - x) - (0.35 if j == arm - 8 else 0)
                    put(img, i, j, q(STRAW, v, g(i, j)))
        else:
            for i in range(x - 2, x + 4):                       # scarf, its end blowing out
                put(img, i, arm - 1, q(SCARF, 0.7 - 0.1 * (i - x), g(i, arm - 1)))
            for (i, j) in [(4, -1), (5, 0), (6, 0), (7, 1)]:
                put(img, x + i, arm + j, SCARF[1])
            put(img, x, arm - 8, STRAW[2])
            put(img, x + 2, arm - 8, STRAW[1])
            cx, cy = x - 7, arm - 1                             # a crow on the left arm, looking out
            crow = ['.KK..', 'KKKKb', 'KKKK.', '.K.K.']
            for j, row in enumerate(crow):
                for i, ch in enumerate(row):
                    if ch == 'K':
                        put(img, cx + i - 2, cy + j - 3, K)
                    elif ch == 'b':
                        put(img, cx + i - 2, cy + j - 3, MG)
            put(img, cx, cy - 2, L1)                            # eye


BARK = [hx(c) for c in ['#2a221e', '#3d322b', '#55473c', '#6e5e50']]
CUT = [hx(c) for c in ['#6d5a45', '#8f7a60', '#ad987a', '#c4b195']]          # pale wood of a cut face
GRASS2 = [hx(c) for c in ['#3d3424', '#5a4a30', '#7c6844', '#9c875b', '#b5a273']]
BIRD = [hx(c) for c in ['#3a2f28', '#5c4a3c', '#8a7360']]


def _cast(img, G, pix, dx=3, k=0.64):
    """One cast shadow to the lower right of a set of pixels, each ground pixel darkened once."""
    g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
    shadow = {(i + d, j + 1) for (i, j) in pix for d in range(1, dx + 1)} - set(pix)
    for (i, j) in shadow:
        if g(i, j) < 0.88 and 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
            img[j, i] = img[j, i] * k


class Findling:
    """A big erratic boulder lying in the field, rounded, mossy on its shaded side."""
    def __init__(s, x, y, r=8, seed=3):
        s.x, s.y, s.r, s.seed = x, y, r, seed

    def box(s):
        return (s.x - s.r - 2, s.y - s.r - 2, s.x + s.r + 5, s.y + 3)

    def draw(s, img, G):
        x, y, r = s.x, s.y, s.r
        ph = np.random.default_rng(s.seed).uniform(0, 6.3, 3)
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        pix = {}
        for j in range(y - r - 1, y + 1):
            for i in range(x - r - 2, x + r + 3):
                a = np.arctan2(j - y, i - x)
                rr = r * (1 + 0.15 * np.sin(2 * a + ph[0]) + 0.08 * np.sin(3 * a + ph[1]))
                e = np.hypot(i - x, (j - y) * 1.05) / rr               # a dome standing up out of the grass
                if e <= 1:
                    pix[(i, j)] = ((i - x) / rr, (y - j) / (rr / 1.05))
        _cast(img, G, list(pix), dx=4)
        for (i, j), (u, t) in pix.items():
            top = (i, j - 1) not in pix
            v = 0.5 - 0.32 * u + 0.1 * t - 0.2 * (j >= y - 1)      # a darker mass than the speckled meadow
            c = q(STONE, v, g(i, j))
            if top and u < 0.35 and g(i, j + 3) < 0.6:
                c = LITSTONE[5]                                   # light catching the crown
            if u > 0.25 and t < 0.5 and g(i * 3, j * 5) < 0.4:
                c = q(MOSS3, 0.55 - 0.3 * u, g(i, j))
            if t > 0.7 and u < 0 and g(i * 7, j * 3) < 0.25:
                c = q(MOSS3, 0.9, g(i, j))
            img[j, i] = c
        for k in (-r - 1, r + 1, r + 2):
            put(img, x + k, y, DG)


class Steinhaufen:
    """A small heap of field stones picked off the meadow long ago."""
    def __init__(s, x, y, seed=4):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - 8, s.y - 8, s.x + 11, s.y + 3)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        stones = [(s.x + int(rng.integers(-6, 7)), s.y - int(rng.integers(0, 3)), int(rng.integers(2, 4)))
                  for _ in range(6)]
        stones += [(s.x + int(rng.integers(-3, 4)), s.y - 3 - int(rng.integers(0, 2)), 2) for _ in range(3)]
        for (x, y, r) in sorted(stones, key=lambda t: t[1]):
            Findling(x, y, r, int(rng.integers(0, 999))).draw(img, G)


class Baumstumpf:
    """An old stump in the meadow: furrowed bark, flared roots, a grey weathered cut face with rings,
    moss creeping up its shaded side."""
    def __init__(s, x, y, r=5):
        s.x, s.y, s.r = x, y, r

    def box(s):
        return (s.x - s.r - 4, s.y - 10, s.x + s.r + 6, s.y + 3)

    def draw(s, img, G):
        x, y, r = s.x, s.y, s.r
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        h = 5
        side = {}
        for j in range(y - h, y + 1):
            flare = 1.5 * max(0, (j - (y - 2))) / 2
            for i in range(int(x - r - flare), int(x + r + flare) + 1):
                side[(i, j)] = (i - x) / (r + flare)
        _cast(img, G, list(side), dx=4)
        for (i, j), u in side.items():
            fur = 0.12 if (i - x) % 2 == 0 else 0
            c = q(BARK, 0.62 - 0.4 * u - fur, g(i, j))
            if u > 0.2 and g(i * 5, j * 3) < 0.5:
                c = q(MOSS3, 0.5 - 0.3 * u, g(i, j))
            img[j, i] = c
        top = y - h
        for j in range(top - 3, top + 1):                     # the cut face: an ellipse seen from above
            for i in range(x - r, x + r + 1):
                e = ((i - x) / (r + 0.3)) ** 2 + ((j - top + 1.5) / 2.0) ** 2
                if e <= 1:
                    ring = int(np.sqrt(e) * 3) % 2
                    v = 0.75 - 0.25 * (i - x) / r - 0.25 * ring
                    put(img, i, j, q(CUT, v, g(i, j)))
        put(img, x - 1, top - 1, CUT[0])                      # the heart
        for (i, j) in [(x + r - 1, top - 4), (x + r, top - 4), (x + r, top - 5)]:   # a splinter left standing
            put(img, i, j, BARK[2])


class Stamm:
    """A fallen trunk lying in the grass, bark lit on top, a pale cut end with rings, a broken branch."""
    def __init__(s, x1, y1, x2, y2, r=3):
        s.a, s.b, s.r = np.array([x1, y1], float), np.array([x2, y2], float), r

    def box(s):
        return (int(min(s.a[0], s.b[0])) - 5, int(min(s.a[1], s.b[1])) - 8,
                int(max(s.a[0], s.b[0])) + 6, int(max(s.a[1], s.b[1])) + 4)

    def draw(s, img, G):
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        a, b, r = s.a, s.b, s.r
        d = b - a
        L = np.hypot(*d)
        n = np.array([-d[1], d[0]]) / L
        if n[1] > 0:
            n = -n                                             # n points up the screen
        pix = {}
        x0, y0, x1, y1 = s.box()
        for j in range(y0, y1):
            for i in range(x0, x1):
                p = np.array([i + 0.5, j + 0.5]) - a
                t = p @ d / L ** 2
                if not 0 <= t <= 1:
                    continue
                off = (p - t * d) @ n                          # across the trunk, + = upper side
                if abs(off) <= r:
                    pix[(i, j)] = (t, off / r)
        _cast(img, G, list(pix), dx=3)
        for (i, j), (t, v) in pix.items():
            c = q(BARK, 0.5 + 0.35 * v + (0.08 if (i + j) % 3 == 0 else 0), g(i, j))
            if v > 0.4 and g(i * 3, j * 7) < 0.3:
                c = q(MOSS3, 0.7, g(i, j))
            if t > 0.96:                                       # the cut end
                c = q(CUT, 0.6 + 0.3 * v, g(i, j))
            img[j, i] = c
        mid = a + d * 0.35 + n * (r + 0.5)                     # a broken branch stub pointing up
        for k in range(3):
            put(img, int(mid[0]) + k // 2, int(mid[1]) - k, BARK[2 if k else 1])


class Zaun:
    """A few old fence posts, all that is left of a pasture: weathered, some leaning, one fallen over."""
    def __init__(s, pts, seed=8):
        s.pts, s.seed = pts, seed

    def box(s):
        xs = [p[0] for p in s.pts]
        ys = [p[1] for p in s.pts]
        return (min(xs) - 4, min(ys) - 10, max(xs) + 6, max(ys) + 3)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        for k, (x, y) in enumerate(s.pts):
            if k == len(s.pts) - 2:                            # this one lies in the grass
                pix = [(x + i, y) for i in range(-3, 5)] + [(x + i, y - 1) for i in range(-3, 5)]
                _cast(img, G, pix, dx=1)
                for (i, j) in pix:
                    put(img, i, j, q(WOOD, 0.75 if j < y else 0.35, g(i, j)))
                continue
            h = int(rng.integers(9, 13))
            lean = rng.choice([0, 0, 1, -1])
            pix = []
            for d in range(h):
                xx = x + (lean if d > h * 0.6 else 0)
                pix += [(xx, y - d), (xx + 1, y - d)]
            _cast(img, G, pix, dx=2)
            for (i, j) in pix:
                left = (i - 1, j) not in pix
                top = (i, j - 1) not in pix
                v = (0.9 if left else 0.4) + (0.1 if top else 0)
                c = q(WOOD + [CUT[2], CUT[3]], v, g(i, j))
                if j > y - 3 and g(i * 5, j) < 0.35:
                    c = q(MOSS3, 0.5, g(i, j))
                put(img, i, j, c)


class HohesGras:
    """A clump of tall grass gone to seed, taller than the poppies, leaning with the wind."""
    def __init__(s, x, y, n=9, seed=5):
        s.x, s.y, s.n, s.seed = x, y, n, seed

    def box(s):
        return (s.x - 6, s.y - 10, s.x + 9, s.y + 1)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        for _ in range(s.n):
            bx = s.x + int(rng.integers(-4, 5))
            h = int(rng.integers(5, 10))
            lean = rng.normal(0.35, 0.25)
            for k in range(h):
                i = bx + int(round(lean * k * k / h))
                c = GRASS2[min(4, 1 + k * 3 // h)]
                put(img, i, s.y - k, c)
            if rng.random() < 0.6:                             # a seed head
                i = bx + int(round(lean * h))
                put(img, i, s.y - h, GRASS2[4])
                put(img, i + 1, s.y - h + 1, GRASS2[3])


class Voegel:
    """Draft only: where a few sparrows sit (in the game they are the living birds, hopping, flying off)."""
    def __init__(s, x, y, seed=6):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - 10, s.y - 4, s.x + 11, s.y + 3)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        for _ in range(3):
            x, y = s.x + int(rng.integers(-9, 10)), s.y + int(rng.integers(-3, 3))
            for (i, j, c) in [(0, 0, 1), (1, 0, 1), (2, 0, 0), (1, -1, 2), (0, -1, 1), (-1, 0, 0)]:
                put(img, x + i, y + j, BIRD[c])
            put(img, x + 1, y + 1, img[y + 1, x + 1] * 0.7)


class Kirschbaum:
    """A young cherry tree grown the same way as the big one (tree.py), only smaller: shorter trunk,
    fewer forks, smaller blossom clouds. Drawn small, never scaled."""
    def __init__(s, x, y, seed=17, trunk=11.5, width=4.4, depth=5):
        s.x, s.y, s.seed, s.trunk, s.width, s.depth = x, y, seed, trunk, width, depth
        s.S = 90                                             # local canvas, foot at its bottom middle

    def box(s):
        return (s.x - s.S // 2, s.y - s.S + 12, s.x + s.S // 2, s.y + 6)

    def _grow(s):
        import tree as T
        rng = np.random.default_rng(s.seed)
        S = s.S
        cx, by = S // 2, S - 12
        out = {'strokes': [], 'tips': []}
        T.grow(rng, np.array([cx, by], float), -np.pi / 2 + 0.1, s.trunk, s.width, s.depth, out)
        yy, xx = np.mgrid[0:S, 0:S]
        wood = np.zeros((S, S))
        shade = np.zeros((S, S))
        for x, y, w, _ in out['strokes']:
            r = max(0.7, w)
            m = (xx - x) ** 2 + (yy - y) ** 2 <= r * r
            wood[m] = 1
            shade[m] = np.maximum(shade[m], np.clip(0.5 - ((xx[m] - x) * 0.7 + (yy[m] - y) * 0.4) / (r + 0.5) * 0.5, 0, 1))
        for a in np.linspace(-0.4, np.pi + 0.4, 5) + rng.normal(0, 0.15, 5):      # roots
            L = rng.uniform(4, 7)
            p0 = np.array([cx, by], float)
            p2 = p0 + L * np.array([np.cos(a), 0.45 * np.sin(a) + 0.25])
            for k, p in enumerate(T.bezier(p0, (p0 + p2) / 2, p2, 14)):
                r = 1.8 * (1 - k / 14) + 0.5
                m = (xx - p[0]) ** 2 + (yy - p[1]) ** 2 <= r * r
                wood[m] = 1
                shade[m] = np.maximum(shade[m], 0.35)
        inner = [(x, y) for x, y, w, d in out['strokes'] if d <= 3 and rng.random() < 0.06]
        tips = np.array(out['tips'] + inner)
        noise = ndi.gaussian_filter(rng.normal(0, 1, (S, S)), 1.8)
        noise /= noise.std()
        fine = rng.random((S, S))
        canopy = np.zeros((S, S))
        light = np.zeros((S, S))
        for tx, ty in tips:
            R = rng.uniform(7, 11)
            d = np.sqrt((xx - tx) ** 2 + ((yy - ty) * 1.15) ** 2)
            c = np.clip(1 - d / R + 0.18 * noise, 0, 1)
            canopy = np.maximum(canopy, c)
            l = np.clip(0.55 - ((xx - tx) * 0.6 + (yy - ty) * 0.8) / R * 0.55, 0, 1) * (c > 0)
            light = np.where(c > canopy - 1e-6, np.maximum(light, l), light)
        cmask = (canopy > 0.08) | ((canopy > 0.02) & (fine < 0.35))
        limbs = np.zeros((S, S), bool)
        for x, y, w, d in out['strokes']:
            if d >= s.depth - 2:
                limbs |= (xx - x) ** 2 + (yy - y) ** 2 <= max(0.7, w) ** 2
        out['limbs'] = limbs
        light = light * 0.82                                  # deeper valleys between the blossom clouds
        layer = np.zeros((S, S, 3), np.uint8)
        T.paint(layer, S, S, wood > 0, shade, cmask, canopy, light, rng)
        T.underside(layer, S, S, out, shade, cmask, canopy, by, rng)
        # like the big crown: dark clefts between the clusters, branches showing through, a few open holes
        cl = ndi.gaussian_filter(rng.normal(0, 1, (S, S)), 1.3)
        cl /= cl.std()
        cleft = cmask & (cl < -0.75) & (light < 0.55)
        layer[cleft] = T.PK[0]
        through = cleft & ndi.binary_dilation(limbs, iterations=1)
        layer[through] = T.BARK[1]
        holes = cmask & (cl < -1.35) & (canopy < 0.55) & ~limbs
        ring = ndi.binary_dilation(cmask, iterations=3) & ~cmask
        solid = ((wood > 0) | cmask | (ring & (layer.sum(-1) > 0))) & ~holes
        return layer, solid, cmask

    def draw(s, img, G):
        layer, solid, cmask = s._grow()
        S = s.S
        ox, oy = s.x - S // 2, s.y - (S - 12)
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        # the crown's shadow falls on the meadow to the lower right, softly broken
        sh = ndi.binary_dilation(cmask, iterations=1)
        ys, xs = np.nonzero(sh)
        for j, i in zip(ys, xs):
            wi, wj = ox + i + 9, oy + j + 16
            if 0 <= wj < img.shape[0] and 0 <= wi < img.shape[1] and g(wi, wj) < 0.8 and wj > s.y - 6:
                img[wj, wi] = img[wj, wi] * 0.7
        ys, xs = np.nonzero(solid)
        for j, i in zip(ys, xs):
            wi, wj = ox + i, oy + j
            if 0 <= wj < img.shape[0] and 0 <= wi < img.shape[1]:
                img[wj, wi] = layer[j, i]
        # petals already lying in the grass, downwind
        rng = np.random.default_rng(s.seed + 1)
        PKc = [hx(c) for c in ['#c87a90', '#e6aab8']]
        for _ in range(26):
            a, r = rng.normal(0.35, 0.7), abs(rng.normal(22, 9))
            i, j = int(s.x + r * np.cos(a)), int(s.y + r * np.sin(a) * 0.6 + 4)
            if 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
                img[j, i] = PKc[rng.integers(0, 2)]
