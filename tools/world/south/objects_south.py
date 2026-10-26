"""Things standing in the southern poppy field, drawn per pixel like the rest of the world: no outlines,
light from the upper left, tones scattered by a grain map instead of smooth ramps.

Each draw(img, G) paints onto an RGB float image in place; (x, y) is always the foot.
"""
import os
import sys

import numpy as np

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
