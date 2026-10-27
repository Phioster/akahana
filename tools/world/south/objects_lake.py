"""Things of the lake (zone 4), drawn per pixel like objects_south and objects_water: the lake water with its
shallow, wadeable rim, water lilies, the greener broadleaf trees, the jetty, a rowing boat and the fisher's hut.

Each draw(img, G) paints onto an RGB float image in place; (x, y) is the foot.
"""
import os
import sys

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from objects2 import STONE, WOOD, hx  # noqa: E402
from objects_south import q, put, shade, BARK, STRAW  # noqa: E402
from objects_water import WATER, MUD  # noqa: E402

LEAF = [hx(c) for c in ['#1f2c1d', '#2f4329', '#456138', '#5f7f49', '#7f9f5e']]   # greener than the willows
LEAF_HI = hx('#a6c47a')
PAD = [hx(c) for c in ['#2c4226', '#426036', '#5c7f47', '#7c9e5e']]
LILY = [hx(c) for c in ['#c9a7b4', '#ead2da', '#f6ece6']]
SAND = [hx(c) for c in ['#4a5552', '#5d6a64', '#74817a']]          # the lake floor showing through the shallows
ROOF = [hx(c) for c in ['#2b231e', '#43362d', '#5e4c3e', '#7a6553']]


def paint_lake(img, y0, lake, shallow, rng):
    """Calm lake water: dark where deep, the shallow rim lighter with the floor showing (that is where one can
    wade), short level glints of ripples, a dark wet rim of mud at the shore."""
    H, W = lake.shape
    depth = np.clip(ndi.distance_transform_edt(lake) / 40.0, 0, 1)
    n = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 1.2)
    n /= n.std()
    yy, xx = np.mgrid[0:H, 0:W]
    v = 0.6 - 0.45 * depth + 0.05 * n
    ci = np.clip((v * (len(WATER) - 1)).round().astype(int), 0, len(WATER) - 1)
    col = np.array(WATER)[ci].astype(float)
    sh = shallow & (rng.random((H, W)) < 0.55)
    col[sh] = np.array(SAND)[np.clip((n[sh] * 0.8 + 1.2).astype(int), 0, 2)]   # the floor through clear water
    ripple = np.sin(xx * 0.45 + 3.0 * np.sin(yy * 0.35) + n) > 0.93            # level glints, a few px long
    ripple &= (yy % 3 == 0) & (rng.random((H, W)) < 0.6)
    col[ripple] = WATER[4]
    sub = img[y0:y0 + H]
    sub[lake] = col[lake]
    rim = ndi.binary_dilation(lake, iterations=2) & ~lake
    g = rng.random((H, W))
    sub[rim & (g < 0.8)] = np.array(MUD)[np.clip((g * 4).astype(int), 0, 2)][rim & (g < 0.8)]


class Seerosen:
    """A patch of water lilies: round pads, each with its notch, a few in flower."""
    def __init__(s, x, y, n=7, seed=3):
        s.x, s.y, s.n, s.seed = x, y, n, seed

    def box(s):
        return (s.x - 14, s.y - 8, s.x + 15, s.y + 8)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        for k in range(s.n):
            cx, cy = s.x + rng.normal(0, 7), s.y + rng.normal(0, 4)
            r = rng.uniform(2.6, 3.8)
            notch = rng.uniform(0, 6.28)
            for j in range(int(cy - r - 1), int(cy + r + 2)):
                for i in range(int(cx - r - 1), int(cx + r + 2)):
                    dx, dy = i - cx, (j - cy) * 1.4
                    e = np.hypot(dx, dy) / r
                    a = np.angle(np.exp(1j * (np.arctan2(dy, dx) - notch)))
                    if e > 1 or (abs(a) < 0.45 and e > 0.2):
                        continue
                    lit = 0.75 - 0.25 * (dx + dy) / r
                    put(img, i, j, q(PAD, lit if e < 0.8 else lit - 0.3, 0.5))
            if rng.random() < 0.35:                            # a flower: pale petals, a yellow heart
                i, j = int(round(cx)), int(round(cy)) - 1
                for (di, dj, c) in [(0, 0, 2), (-1, 0, 1), (1, 0, 1), (0, -1, 2), (0, 1, 0)]:
                    put(img, i + di, j + dj, LILY[c])
                put(img, i, j, hx('#d8b456'))


class Laubbaum:
    """A broadleaf tree, greener than the rest: a short trunk, a round crown of leaf clumps lit at the upper
    left with bright rims (as the willow's clumps, without the hanging twigs), gaps letting the limbs show."""
    def __init__(s, x, y, seed=5, size=1.0):
        s.x, s.y, s.seed, s.size = x, y, seed, size

    def box(s):
        r = int(20 * s.size)
        return (s.x - r - 2, s.y - int(52 * s.size), s.x + r + 8, s.y + 4)

    def draw(s, img, G):
        import tree as T
        rng = np.random.default_rng(s.seed)
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        sz = s.size
        a, b = 18 * sz, 15 * sz
        ex, ey = s.x + rng.uniform(-2, 2), s.y - 16 * sz - b      # the crown's middle
        for j in range(s.y - 3, s.y + 6):                        # shade on the ground, lower right
            for i in range(int(s.x - a + 6), int(s.x + a + 12)):
                if ((i - s.x - 6) / a) ** 2 + ((j - s.y - 1) / 4.5) ** 2 < 1 and g(i, j) < 0.85:
                    put(img, i, j, img[j, i] * 0.65) if 0 <= j < img.shape[0] and 0 <= i < img.shape[1] else None
        top = np.array([s.x + rng.uniform(-2, 2), ey + b * 0.3])
        strokes = [(p[0], p[1], 2.2 * sz * (1 - 0.3 * k / 30))
                   for k, p in enumerate(T.bezier(np.array([s.x, s.y], float), np.array([s.x + 2, s.y - 8 * sz]), top, 30))]
        clumps = []
        while len(clumps) < int(44 * sz):
            u, v = rng.uniform(-1.05, 1.05), rng.uniform(-1.05, 1.0)
            r2 = u * u + v * v
            if r2 > 1 + 0.12 * rng.random() or rng.random() > 0.55 + 0.45 * min(r2, 1):
                continue
            clumps.append((ex + u * a, ey + v * b))
        for cx, cy in clumps[:int(6 * sz)]:                      # limbs out to some clumps
            p2 = np.array([cx, cy])
            n = int(np.hypot(*(p2 - top)) * 1.5) + 4
            for k, p in enumerate(T.bezier(top, np.array([top[0] + (cx - top[0]) * 0.3, cy - 3]), p2, n)):
                strokes.append((p[0], p[1], 1.1 * sz * (1 - 0.6 * k / n)))
        for x, y, w in strokes:
            r = max(0.6, w)
            for j in range(int(y - r), int(y + r) + 1):
                for i in range(int(x - r), int(x + r) + 1):
                    if (i - x) ** 2 + (j - y) ** 2 <= r * r:
                        put(img, i, j, q(BARK, 0.62 - 0.35 * (i - x) / (r + 0.5), g(i, j)))
        for cy, cx in sorted((c[1], c[0]) for c in clumps):     # back (high) to front (low)
            r = rng.uniform(3.8, 5.2) * sz ** 0.5
            high = np.clip((ey + b - cy) / (2 * b), 0, 1)
            for j in range(int(cy - r - 1), int(cy + r + 1)):
                for i in range(int(cx - r - 1), int(cx + r + 2)):
                    e = ((i - cx) / r) ** 2 + ((j - cy) / (r * 0.8)) ** 2
                    if e > 1 or g(i * 3, j) > 1.15 - 0.3 * e:
                        continue
                    crown = np.clip(0.85 - ((i - ex) / a * 0.35 + (j - ey) / b * 0.5), 0.15, 1)
                    lit = 0.55 * crown + 0.45 * np.clip(0.75 - ((i - cx) * 0.5 + (j - cy) * 0.8) / r * 0.5, 0, 1)
                    lit *= 0.75 + 0.25 * high
                    if e > 0.7 and (i - cx) + (j - cy) > 0:
                        lit *= 0.55
                    c = q(LEAF, lit, g(i, j))
                    if e > 0.5 and (i - cx) + (j - cy) < -r * 0.6 and lit > 0.62 and g(i, j) < 0.6:
                        c = LEAF_HI
                    put(img, i, j, c)


class Steg:
    """A wooden jetty out of the reeds into the lake: planks across, posts at both sides standing in the
    water with a ring of ripples, its shadow on the water to the right. Runs down the screen, or with
    across=True sideways (x and y swapped while drawing)."""
    def __init__(s, x, y_from, y_to, width=9, across=False, dry=None):
        s.x, s.y0, s.y1, s.w, s.across = x, y_from, y_to, width, across
        s.dry = y_from if dry is None else dry                   # rows above this lie on the bank

    def box(s):
        if s.across:
            return (s.y0 - 4, s.x - s.w // 2 - 2, s.y1 + 3, s.x + s.w // 2 + 4)
        return (s.x - s.w // 2 - 2, s.y0 - 4, s.x + s.w // 2 + 4, s.y1 + 3)

    def draw(s, img, G):
        if s.across:                                             # draw on the transposed picture
            t = np.ascontiguousarray(img.transpose(1, 0, 2))
            Steg(s.x, s.y0, s.y1, s.w).draw(t, G.T)
            img[:] = t.transpose(1, 0, 2)
            return
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        hw = s.w // 2
        for j in range(max(s.y0 + 2, s.dry), s.y1 + 3):         # shadow on the water
            for i in range(s.x + hw + 1, s.x + hw + 3):
                put(img, i, j, img[j, i] * 0.6) if 0 <= j < img.shape[0] and 0 <= i < img.shape[1] else None
        for j in range(s.y0, s.y1 + 1):
            for i in range(s.x - hw, s.x + hw + 1):
                edge = abs(i - s.x) == hw
                gap = (j - s.y0) % 3 == 2 and g(i, j) < 0.5
                v = 0.45 if edge else (0.5 if gap else 0.78 - 0.12 * ((i - s.x) / hw) + 0.08 * ((j // 3) % 2))
                put(img, i, j, q(WOOD, v, g(i, j)))
        for j in range(s.y0 + 3, s.y1 + 2, 8):                  # posts, with the water stirring round their feet
            for i in (s.x - hw - 1, s.x + hw + 1):
                for d in range(3):
                    put(img, i, j + d, WOOD[0] if d else WOOD[2])
                if j + 3 >= s.dry:
                    put(img, i + 1, j + 3, WATER[4])
                    put(img, i - 1, j + 3, WATER[3])


class Boot:
    """A small rowing boat lying in the reeds: a dark hull rim, lighter boards inside, a seat, one oar."""
    def __init__(s, x, y, seed=2):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - 10, s.y - 5, s.x + 11, s.y + 4)

    def draw(s, img, G):
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        for j in range(s.y - 4, s.y + 4):
            for i in range(s.x - 10, s.x + 11):
                t = (i - s.x) / 9.5
                half = 3.6 * (1 - abs(t) ** 1.6) ** 0.8 if abs(t) < 1 else 0     # pointed at both ends
                e = abs(j - s.y + 0.5) / max(half, 1e-3)
                if abs(t) < 1 and e <= 1:
                    inner = abs(t) < 0.82 and e <= 0.62
                    v = (0.82 - 0.12 * ((j - s.y) > 0)) if inner else (0.28 if j > s.y else 0.55)
                    if inner and i in (s.x - 1, s.x):
                        v = 0.85                                 # the seat
                    put(img, i, j, q(WOOD, v, g(i, j)))
        for k in range(14):                                      # the oar, laid across
            put(img, s.x - 8 + k, s.y - 3 + k // 5, WOOD[3] if k > 10 else WOOD[2])
        for i in range(s.x - 9, s.x + 10, 2):                   # water lapping at the waterline
            put(img, i, s.y + 4, WATER[3])


class Huette:
    """The fisher's hut, built like the shepherd's house in the north (ruin.Cottage: stone wall, warm window,
    plank door, dark slate roof with a ridge, chimney with thin smoke), only smaller; a net hung on the side
    and two oars leaning at the wall. (x, y) = middle of the front wall's foot."""
    W_ = 28

    def __init__(s, x, y, seed=8):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - 18, s.y - 50, s.x + 20, s.y + 3)

    def lights(s):
        return [{'x': s.x - s.W_ // 2 + 9.0, 'y': s.y - 6.5, 'r': 16.0, 'k': 0.25, 'kind': 'kerze'}]

    def draw(s, img, G):
        from ruin import Cottage
        x0 = s.x - s.W_ // 2
        shade(img, G, x0 + 4, s.y, 18, 4, 0.6)
        Cottage(x0, s.y, w=s.W_, wall=11, roof=13, seed=s.seed).draw(img)
        for j in range(s.y - 10, s.y - 1):                      # a net hung on the right side
            for i in range(x0 + s.W_ + 1, x0 + s.W_ + 5):
                if (i + j) % 2 == 0:
                    put(img, i, j, STRAW[1] if (i + 2 * j) % 3 else STRAW[2])
        for k, ox in enumerate((2, 4)):                          # two oars leaning at the wall, left of the window
            for h in range(13):
                put(img, x0 + ox + (h > 9), s.y - h, WOOD[3] if h > 9 else WOOD[2 - k])


class WasserStein:
    """A rock half under water: the dry top lit at the upper left, the waterline as a pale ring of ripples,
    the part below only a darker shape in the water."""
    def __init__(s, x, y, r=4.0, seed=1):
        s.x, s.y, s.r, s.seed = x, y, r, seed

    def box(s):
        r = int(s.r) + 3
        return (s.x - r, s.y - r, s.x + r + 1, s.y + r)

    def draw(s, img, G):
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        r = s.r
        for j in range(int(s.y - r - 2), int(s.y + r + 3)):
            for i in range(int(s.x - r - 3), int(s.x + r + 4)):
                e = ((i - s.x) / r) ** 2 + ((j - s.y) / (r * 0.7)) ** 2
                if e <= 1:
                    if j > s.y + r * 0.15:                       # under the surface
                        put(img, i, j, img[j, i] * 0.72) if 0 <= j < img.shape[0] and 0 <= i < img.shape[1] else None
                    else:
                        lit = (i - s.x) + (j - s.y) * 1.3 < -0.5
                        put(img, i, j, q(STONE, 0.92 if lit else 0.58, g(i, j)))
                elif e <= 1.6 and abs(j - s.y - r * 0.2) < 1.5 and g(i, j) < 0.7:
                    put(img, i, j, WATER[4])                     # ripples at the waterline


class Treibholz:
    """A dead branch drifting, half sunk: grey wood, a stub of a side branch, ripples along it."""
    def __init__(s, x, y, length=22, ang=-0.35, seed=3):
        s.x, s.y, s.L, s.ang, s.seed = x, y, length, ang, seed

    def box(s):
        return (s.x - s.L // 2 - 3, s.y - 8, s.x + s.L // 2 + 4, s.y + 8)

    def draw(s, img, G):
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        GREY = [hx(c) for c in ['#3a3633', '#5a5550', '#7e7871', '#a39c93']]
        ca, sa = np.cos(s.ang), np.sin(s.ang)
        for k in range(s.L):
            u = k - s.L / 2
            x, y = s.x + ca * u, s.y + sa * u
            w = 1.6 * (1 - 0.4 * abs(u) / s.L * 2)
            sunk = abs(u) > s.L * 0.36                           # its ends dip under the water
            for d in (-1, 0, 1):
                if abs(d) > w:
                    continue
                i, j = int(round(x - sa * d)), int(round(y + ca * d))
                if sunk:
                    put(img, i, j, img[j, i] * 0.75) if 0 <= j < img.shape[0] and 0 <= i < img.shape[1] else None
                else:
                    put(img, i, j, q(GREY, 0.85 if d < 0 else 0.5 if d == 0 else 0.3, g(i, j)))
            if not sunk and k % 3 == 0:
                put(img, int(round(x)), int(round(y + 2)), WATER[4])
        bx, by = s.x + ca * s.L * 0.15, s.y + sa * s.L * 0.15     # a stub of a side branch
        for k in range(5):
            put(img, int(round(bx + k * 0.4)), int(round(by - k)), GREY[2 - (k > 2)])


class Enten:
    """Draft only: where a few ducks swim (in the game living ones, like the birds), each with its wake."""
    def __init__(s, x, y, n=3, seed=4):
        s.x, s.y, s.n, s.seed = x, y, n, seed

    def box(s):
        return (s.x - 14, s.y - 6, s.x + 15, s.y + 8)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        BODY = [hx(c) for c in ['#3b332c', '#5e5246', '#8a7a68']]
        HEAD = hx('#2f4a3a')
        for k in range(s.n):
            x, y = s.x + int(rng.integers(-10, 11)), s.y + int(rng.integers(-3, 4))
            d = 1 if rng.random() < 0.5 else -1                   # swimming left or right
            for t in range(3, 10):                               # the wake: a pale V behind
                for side in (-1, 1):
                    put(img, x - d * t, y + 1 + side * (t // 3), WATER[4] if t < 6 else WATER[3])
            for (i, j, c) in [(0, -1, 2), (-d, -1, 1), (0, 0, 1), (-d, 0, 1), (d, 0, 2), (-2 * d, 0, 1),
                              (-3 * d, 0, 0), (0, 1, 0), (-d, 1, 0), (d, 1, 0), (-2 * d, 1, 0), (2 * d, 0, 1)]:
                put(img, x + i, y + j, BODY[c])                   # a little bigger: body 6 x 3
            for (i, j) in [(2 * d, -1), (2 * d, -2), (3 * d, -2)]:
                put(img, x + i, y + j, HEAD)                      # the green-dark head, two pixels high
            put(img, x + 4 * d, y - 2, hx('#c9a24e'))             # the bill
