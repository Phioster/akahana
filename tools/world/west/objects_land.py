"""Things that stand about in the open country between the places (Philip's girlfriend, 2026-11-08: the meadows
between the areas are too empty): straw bales, a straw stook, a roadside Jizo. Drawn in the south's manner."""
import os
import sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'south'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from objects2 import hx  # noqa: E402
from objects_south import q, put, shade, STRAW, LITSTONE  # noqa: E402

STRAW_OLD = [hx(c) for c in ['#3e3424', '#5b4b33', '#7d6a48', '#a08b62', '#c2ad83', '#d6c49a']]
TWINE = [hx(c) for c in ['#3a2a1e', '#56402c']]
BIB = [hx(c) for c in ['#4a1a1a', '#7a2622', '#a83a2e', '#c4513e']]   # the Jizo's red bib, sun-faded at the top


class Heuballen:
    """Square straw bales left on the field: the lit top, the front face with the straw running across, two dark
    twine bands. n = 1, 2 side by side, or 3 (two below, one laid on top, a little turned)."""
    def __init__(s, x, y, n=1, seed=21):
        s.x, s.y, s.n, s.seed = x, y, n, seed

    def box(s):
        w = 14 if s.n == 1 else 27
        return (s.x - w // 2 - 1, s.y - (16 if s.n == 3 else 10), s.x + w // 2 + 4, s.y + 3)

    def _bale(s, img, G, x0, y0, w, rng):
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        top, front = 4, 6
        for j in range(y0 - top - front, y0):
            for i in range(x0, x0 + w):
                if j < y0 - front:                                  # the top, lit
                    t = (j - (y0 - top - front)) / top
                    v = 0.78 - 0.1 * t + 0.12 * (g(i * 3, j) - 0.5)
                    if (i == x0 or i == x0 + w - 1) and j == y0 - top - front:
                        continue                                    # round the corners
                else:                                               # the front, straw across
                    t = (j - (y0 - front)) / front
                    v = 0.55 - 0.22 * t + (0.1 if (j + int(g(i, 7) * 2)) % 2 else -0.05)
                    if i == x0 + w - 1:
                        v -= 0.15
                c = q(STRAW_OLD, v, g(i, j))
                if (i - x0) in (w // 4, w - 1 - w // 4):           # twine bands
                    c = TWINE[1 if j < y0 - front else 0]
                put(img, i, j, c)
        for k in range(int(rng.integers(2, 5))):                    # loose stalks sticking out
            i = x0 + int(rng.integers(0, w))
            put(img, i, y0 - top - front - 1, q(STRAW_OLD, 0.8, g(i, 0)))

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        if s.n == 1:
            shade(img, G, s.x - 4, s.y, 8, 2, 0.7)
            s._bale(img, G, s.x - 6, s.y, 13, rng)
        else:
            shade(img, G, s.x - 10, s.y, 14, 2, 0.7)
            s._bale(img, G, s.x - 13, s.y, 13, rng)
            s._bale(img, G, s.x + 1, s.y + 1, 13, rng)
            if s.n == 3:
                s._bale(img, G, s.x - 7, s.y - 7, 13, rng)


class Strohkegel:
    """A straw stook as stands on the fields after the rice harvest: a cone of bundled straw round a pole, tied
    under a little cap at the top, its skirt splayed on the ground. Weathered grey-gold."""
    def __init__(s, x, y, h=17, seed=31):
        s.x, s.y, s.h, s.seed = x, y, h, seed

    def box(s):
        return (s.x - 8, s.y - s.h - 3, s.x + 11, s.y + 3)

    def draw(s, img, G):
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        shade(img, G, s.x - 3, s.y, 7, 2, 0.68)
        h = s.h
        for j in range(s.y - h, s.y + 1):
            t = (s.y - j) / h                                       # 0 at the foot, 1 at the tip
            r = 6.5 * (1 - t) ** 0.8 + 0.8 + (1.2 if t < 0.12 else 0)   # the skirt splays
            for i in range(int(s.x - r), int(s.x + r) + 1):
                u = (i - s.x) / max(r, 1)
                v = 0.7 - 0.38 * u - 0.12 * (1 - t) + 0.12 * (g(i, j * 2) - 0.5)
                if int((u + 1.3) * 5 + g(i, 3) * 1.5) % 2:          # the bundles, running down
                    v -= 0.1
                if abs(t - 0.78) < 0.05:
                    c = TWINE[0]                                    # the tie under the cap
                else:
                    c = q(STRAW_OLD, v, g(i, j))
                put(img, i, j, c)
        put(img, s.x, s.y - h - 1, q(STRAW_OLD, 0.7, 0.5))           # the cap's tuft
        put(img, s.x + 1, s.y - h - 2, q(STRAW_OLD, 0.85, 0.5))


class Jizo:
    """A small roadside Jizo of weathered stone on a low base: round shaven head, the body a rounded block,
    a faded red bib tied round the neck; a pebble or two laid at its feet."""
    def __init__(s, x, y, seed=41):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - 6, s.y - 17, s.x + 9, s.y + 3)

    def draw(s, img, G):
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        x, y = s.x, s.y
        shade(img, G, x - 2, y, 5, 2, 0.66)
        for j in range(y - 2, y + 1):                                # the base
            for i in range(x - 5, x + 6):
                put(img, i, j, q(LITSTONE, 0.55 - 0.05 * (i - x) - (0.15 if j == y else 0), g(i, j)))
        for j in range(y - 10, y - 2):                               # the body
            t = (y - 3 - j) / 7
            r = 3.6 - 0.8 * t ** 2
            for i in range(int(round(x - r)), int(round(x + r)) + 1):
                u = (i - x) / r
                c = q(LITSTONE, 0.48 - 0.3 * u, g(i, j))
                if t > 0.45 and abs(u) < 0.95 and (y - 3 - j) < 7 - abs(u) * 2:
                    c = q(BIB, 0.75 - 0.3 * u - 0.15 * (1 - t), g(i, j))   # the bib, hanging in a point
                if g(i * 3, j * 5) < 0.12:
                    c = q(LITSTONE, 0.3, g(i, j))                    # lichen and pits
                put(img, i, j, c)
        cy = y - 13                                                   # the head
        for j in range(cy - 3, cy + 3):
            for i in range(x - 3, x + 4):
                d = ((i - x) / 3.0) ** 2 + ((j - cy + 0.3) / 2.9) ** 2
                if d <= 1:
                    put(img, i, j, q(LITSTONE, 0.6 - 0.28 * (i - x) / 3 - 0.18 * (j - cy) / 3, g(i, j)))
        put(img, x - 1, cy, q(LITSTONE, 0.35, 0.5))                  # closed eyes, a line each
        put(img, x + 1, cy, q(LITSTONE, 0.35, 0.5))
        put(img, x + 3, y + 1, q(LITSTONE, 0.6, 0.3))                # pebbles laid at its feet
        put(img, x - 4, y + 1, q(LITSTONE, 0.45, 0.6))
