"""Things by the brooks of zone 3, drawn per pixel like objects_south: the water itself, wooden bridges, a
single plank, stepping stones, the spring, weeping willows, reeds, bulrushes and ferns.

Each draw(img, G) paints onto an RGB float image in place; (x, y) is the foot or the middle of a crossing.
"""
import os
import sys

import numpy as np
from scipy import ndimage as ndi
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from objects2 import STONE, WOOD, hx  # noqa: E402
from objects_south import q, put, BARK  # noqa: E402

WATER = [hx(c) for c in ['#1f2a31', '#2a3a44', '#3a4f5a', '#557079', '#7f989c']]       # deep .. glint
MUD = [hx(c) for c in ['#24221d', '#332f27', '#433d32']]
REED = [hx(c) for c in ['#34402a', '#4d5b39', '#6b7a4c', '#8c9862']]
PLUME = [hx(c) for c in ['#86714f', '#a8936c', '#c8b48c']]
CATTAIL = [hx(c) for c in ['#4a3122', '#6c4a33', '#8c6446']]
FERN = [hx(c) for c in ['#2f3c26', '#465a34', '#617848', '#80955c']]
WILLOW = [hx(c) for c in ['#26301f', '#3a4a2e', '#55693f', '#738a52', '#93a86a']]


class Brooks:
    """All running water of the zone: each brook a centre line (sampled curve) with a width. Gives the water
    mask, the depth across each brook and the flow direction, and paints the water (still here; in the game
    the water shader moves the streaks along `flow`)."""
    def __init__(s, lines, H, W, y0=0):
        s.H, s.W, s.y0 = H, W, y0
        yy, xx = np.mgrid[0:H, 0:W]
        pts = np.stack([xx.ravel(), yy.ravel() + y0], 1).astype(float)
        s.depth = np.zeros((H, W))                              # 0 at the bank .. 1 mid-stream
        s.along = np.zeros((H, W))
        s.flow = np.zeros((H, W, 2))
        for c, w0, w1 in lines:                                 # curve, width at start and at end
            seg = np.hypot(*np.diff(c, axis=0).T)
            arc = np.r_[0, np.cumsum(seg)]
            dist, i = cKDTree(c).query(pts)
            half = (w0 + (w1 - w0) * arc[i] / arc[-1]) / 2
            dep = np.clip(1 - dist / half, 0, 1).reshape(H, W)
            tang = np.gradient(c, axis=0)
            tang /= np.hypot(tang[:, :1], tang[:, 1:]) + 1e-9
            take = dep > s.depth
            s.depth[take] = dep[take]
            s.along[take] = arc[i].reshape(H, W)[take]
            s.flow[take] = tang[i].reshape(H, W, 2)[take]
        s.mask = s.depth > 0

    def bank(s, k=2):
        return ndi.binary_dilation(s.mask, iterations=k) & ~s.mask

    def draw(s, img, rng):
        """Water darker mid-stream, light streaks drawn out along the flow, a glint here and there."""
        H, W = s.H, s.W
        n = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 0.8)
        n /= n.std()
        yy, xx = np.mgrid[0:H, 0:W]
        across = xx * s.flow[..., 1] - yy * s.flow[..., 0]    # position across the current
        streak = np.sin(s.along * 0.55 + 2.2 * np.sin(across * 0.9) + n * 0.8)
        v = 0.62 - 0.38 * s.depth + 0.12 * n * 0.5
        v = np.where(streak > 0.82, v + 0.28, v)                # drawn-out ripples
        v = np.where((streak > 0.97) & (rng.random((H, W)) < 0.5), 0.97, v)
        ci = np.clip((v * (len(WATER) - 1)).round().astype(int), 0, len(WATER) - 1)
        sub = img[s.y0:s.y0 + H]
        sub[s.mask] = np.array(WATER)[ci][s.mask]
        b = s.bank(2)
        g = rng.random((H, W))
        mud = b & (g < 0.75)
        sub[mud] = np.array(MUD)[np.clip((g * 4).astype(int), 0, 2)][mud]
        peb = b & (g > 0.93)
        sub[peb] = STONE[3]


def _frame(x, y, ang, L, Wd, pad=6):
    """Pixels of a strip of length L and width Wd centred on (x, y) running at angle `ang`: (i, j, u, v)."""
    r = int(L / 2 + Wd + pad)
    ca, sa = np.cos(ang), np.sin(ang)
    out = []
    for j in range(y - r, y + r + 1):
        for i in range(x - r, x + r + 1):
            dx, dy = i - x, j - y
            u, v = dx * ca + dy * sa, -dx * sa + dy * ca
            if abs(u) <= L / 2 and abs(v) <= Wd / 2:
                out.append((i, j, u, v))
    return out


class Bruecke:
    """A small wooden footbridge: planks across, two beams, low rails with posts, its shadow on the water."""
    def __init__(s, x, y, ang, span):
        s.x, s.y, s.ang, s.L = x, y, ang, span + 8
        s.Wd = 7

    def box(s):
        r = int(s.L / 2 + 4)
        return (s.x - r, s.y - r - 4, s.x + r, s.y + r)

    def draw(s, img, G):
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        for i, j, u, v in _frame(s.x + 2, s.y + 3, s.ang, s.L - 2, s.Wd):     # shadow on the water and bank
            put(img, i, j, img[j, i] * 0.6) if 0 <= j < img.shape[0] and 0 <= i < img.shape[1] else None
        for i, j, u, v in _frame(s.x, s.y, s.ang, s.L, s.Wd):
            edge = abs(v) > s.Wd / 2 - 1.2
            plank = int((u + s.L) // 2)
            val = 0.42 if edge else 0.74 + 0.16 * (plank % 2) - 0.1 * (v / s.Wd)
            if not edge and int(u + s.L) % 2 == 0 and g(i, j) < 0.2:
                val -= 0.25                                     # a gap between planks
            put(img, i, j, q(WOOD, val, g(i, j)))
        ca, sa = np.cos(s.ang), np.sin(s.ang)
        for side in (-1, 1):                                    # rails: posts at the ends, a bar between their tops
            vx, vy = -sa * side * (s.Wd / 2), ca * side * (s.Wd / 2)
            ends = [(s.x + ca * u + vx, s.y + sa * u + vy) for u in (-s.L / 2 + 1, s.L / 2 - 1)]
            for (px, py) in ends:
                for h in range(4):
                    put(img, int(round(px)), int(round(py)) - h, WOOD[1] if h < 3 else WOOD[3])
            (ax, ay), (bx, by) = ends
            for t in np.linspace(0, 1, int(s.L * 1.5)):
                put(img, int(round(ax + (bx - ax) * t)), int(round(ay + (by - ay) * t)) - 3,
                    WOOD[3] if side < 0 else WOOD[2])


class Brett:
    """A single plank laid over a narrow brook."""
    def __init__(s, x, y, ang, span):
        s.x, s.y, s.ang, s.L = x, y, ang, span + 5

    def box(s):
        r = int(s.L / 2 + 2)
        return (s.x - r, s.y - r, s.x + r, s.y + r)

    def draw(s, img, G):
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        for i, j, u, v in _frame(s.x + 1, s.y + 2, s.ang, s.L - 1, 3):
            if 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
                img[j, i] = img[j, i] * 0.62
        for i, j, u, v in _frame(s.x, s.y, s.ang, s.L, 3):
            put(img, i, j, q(WOOD, 0.8 - 0.2 * (v > 0.6) + 0.12 * (v < -0.6), g(i, j)))


class Trittsteine:
    """Flat stones across the water, each with a pale ring of ripples on its downstream side."""
    def __init__(s, x, y, ang, span, seed=3):
        s.x, s.y, s.ang, s.L, s.seed = x, y, ang, span + 4, seed

    def box(s):
        r = int(s.L / 2 + 3)
        return (s.x - r, s.y - r, s.x + r, s.y + r)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        n = max(2, int(round(s.L / 6)))
        ca, sa = np.cos(s.ang), np.sin(s.ang)
        for k in range(n):
            u = -s.L / 2 + (k + 0.5) * s.L / n + rng.uniform(-0.6, 0.6)
            cx, cy = s.x + ca * u + rng.uniform(-0.8, 0.8), s.y + sa * u
            rx, ry = rng.uniform(2.8, 3.5), rng.uniform(1.9, 2.4)
            for j in range(int(cy - 5), int(cy + 6)):
                for i in range(int(cx - 6), int(cx + 7)):
                    e = ((i - cx) / rx) ** 2 + ((j - cy) / ry) ** 2
                    if e <= 1:
                        lit = (i - cx) + (j - cy) * 1.3 < -0.5
                        put(img, i, j, q(STONE, (0.95 if lit else 0.68) - 0.3 * (j > cy + 0.6), g(i, j)))
                    elif e <= 1.9 and j > cy and g(i, j) < 0.5:
                        put(img, i, j, hx('#7f989c'))          # ripples round the stone


class Quelle:
    """The spring: water welling up from under a small mossy rock into an uneven pool, deep and dark in the
    middle, shallow with pale pebbles at the rim, bubbling where it comes out; ferns and moss around. The brook
    leaves the pool at its lower edge."""
    def __init__(s, x, y, seed=7):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - 16, s.y - 16, s.x + 17, s.y + 10)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        wob = ndi.gaussian_filter(rng.normal(0, 1, (40, 40)), 2.5)
        wob /= wob.std()
        sx, sy = s.x - 2, s.y - 2                                # where it wells up, just below the rock
        for j in range(s.y - 10, s.y + 9):
            for i in range(s.x - 15, s.x + 16):
                e = ((i - s.x) / 13.5) ** 2 + ((j - s.y) / 7.5) ** 2 + 0.18 * wob[(j - s.y) % 40, (i - s.x) % 40]
                if e <= 1:
                    deep = 1 - e
                    c = q(WATER, 0.7 - 0.6 * deep, g(i, j))                  # shallow rim catches the sky
                    if e > 0.62 and g(i * 2, j) < 0.3:
                        c = q(STONE, 0.75, g(i, j))              # pebbles showing through the shallows
                    r = np.hypot(i - sx, (j - sy) * 1.6)
                    if (abs(r - 2.2) < 0.55 or abs(r - 4.6) < 0.5) and j >= sy - 1:
                        c = WATER[4] if g(i, j) < 0.75 else WATER[3]   # rings where it bubbles up
                    if r < 1.2:
                        c = hx('#b9c7c4')
                    put(img, i, j, c)
                elif e <= 1.35:
                    put(img, i, j, MUD[1] if g(i, j) < 0.6 else MUD[2])   # wet, trodden rim
        # the rock it comes from: two mossy boulders behind the pool, the water seeping from between them
        rocks = [(-8, -9, 6.5, 4.5), (2, -10, 5.0, 3.8), (9, -7, 3.5, 2.6)]
        for (dx, dy, rx, ry) in rocks:                           # their shadow first, falling to the lower right
            cx, cy = s.x + dx + 2, s.y + dy + 2
            for j in range(int(cy - ry), int(cy + ry + 2)):
                for i in range(int(cx - rx), int(cx + rx + 2)):
                    if ((i - cx) / rx) ** 2 + ((j - cy) / ry) ** 2 <= 1 and 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
                        img[j, i] = img[j, i] * 0.55
        for (dx, dy, rx, ry) in rocks:
            cx, cy = s.x + dx, s.y + dy
            for j in range(int(cy - ry - 1), int(cy + ry + 2)):
                for i in range(int(cx - rx - 1), int(cx + rx + 2)):
                    e = ((i - cx) / rx) ** 2 + ((j - cy) / ry) ** 2
                    if e <= 1:
                        lit = np.clip(0.95 - ((i - cx) / rx * 0.35 + (j - cy) / ry * 0.45), 0.25, 1)
                        c = q(STONE, lit * (0.9 if j < cy + ry * 0.5 else 0.55), g(i, j))
                        if e > 0.75 and (i - cx) + (j - cy) > 0:
                            c = STONE[0]                         # the dark rim on the side away from the light
                        if j < cy - ry * 0.2 and g(i * 3, j * 2) < 0.45:
                            c = q([hx('#3f4632'), hx('#5b6447'), hx('#7d8660')], lit, g(i, j))   # moss on top
                        put(img, i, j, c)
        for k in range(4):                                       # wet streaks down the rock to the pool
            put(img, sx + k % 2, sy - 1 - k // 2, WATER[3] if k % 2 else WATER[2])
        for (fx, fy, sd) in [(s.x - 15, s.y - 2, 1), (s.x + 14, s.y - 4, 2), (s.x + 12, s.y + 6, 3)]:
            Farn(fx, fy, seed=s.seed + sd, size=6).draw(img, G)


class Weide:
    """A weeping willow after real ones: a tall, curving trunk splitting into a few limbs that rise and arch
    out; at every limb end a clump of leaves (lit at its upper left, bright rims like the cherry crowns) with
    its own curtain of twigs hanging straight down. The clumps sit at many heights, so the curtains fall in
    tiers over each other, the hem is ragged, and trunk and limbs show through the gaps."""
    def __init__(s, x, y, seed=4, size=1.0, lean=4):
        s.x, s.y, s.seed, s.size, s.lean = x, y, seed, size, lean

    def box(s):
        a, b = 19 * s.size, 25 * s.size
        return (int(s.x - a - 4), int(s.y - 6 * s.size - 2 * b - 2), int(s.x + a + 10), s.y + 4)

    def draw(s, img, G):
        import tree as T
        rng = np.random.default_rng(s.seed)
        g = lambda i, j: G[j % G.shape[0], i % G.shape[1]]
        HI = hx('#b2c486')
        sz = s.size
        a, b = 19 * sz, 25 * sz                                     # the crown's outline: taller than wide
        ex, ey = s.x + s.lean, s.y - 6 * sz - b                      # its middle
        hem = lambda x: ey + b * np.sqrt(max(0.0, 1 - ((x - ex) / a) ** 2))
        for j in range(s.y - 4, s.y + 6):                          # its shade on the ground, lower right
            for i in range(int(s.x - a + 6), int(s.x + a + 12)):
                if ((i - s.x - 6) / a) ** 2 + ((j - s.y - 1) / 5) ** 2 < 1 and g(i, j) < 0.85:
                    put(img, i, j, img[j, i] * 0.68) if 0 <= j < img.shape[0] and 0 <= i < img.shape[1] else None
        for j in range(int(ey), s.y + 2):                          # inside the curtain it is dark
            for i in range(int(ex - a), int(ex + a) + 1):
                if j < hem(i) + 2 and ((i - ex) / a) ** 2 < 0.85 and i < ex + 0.25 * a and g(i * 2, j) < 0.8 and 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
                    img[j, i] = img[j, i] * 0.5

        clumps = []                                                 # (x, y), denser towards the outline
        while len(clumps) < int(30 * sz):
            u, v = rng.uniform(-1.1, 1.1), rng.uniform(-1.08, 0.45)
            r2 = u * u + v * v
            if r2 > 1 + 0.15 * rng.random() or rng.random() > 0.35 + 0.65 * min(r2, 1):   # a lobed, uneven outline
                continue
            clumps.append((ex + u * a * 0.9, ey + v * b * 0.95))
        for k in range(int(7 * sz)):                                 # the middle filled too, in front of the trunk
            clumps.append((ex + rng.uniform(-0.3, 0.3) * a, ey + rng.uniform(-0.6, 0.35) * b))
        top = np.array([s.x + s.lean * 0.6, s.y - 18 * sz])
        strokes = []
        for k, p in enumerate(T.bezier(np.array([s.x, s.y], float), np.array([s.x - s.lean * 0.8, s.y - 9 * sz]), top,
                                       int(26 * sz))):              # an S in the trunk
            strokes.append((p[0], p[1], 2.3 * sz * (1 - 0.3 * k / (26 * sz))))
        outer = [c for c in clumps if abs(c[0] - ex) > 0.35 * a and c[1] < ey + 0.2 * b]
        for cx, cy in outer[:int(7 * sz)]:                           # limbs to outer clumps: rise, then bow out
            p2 = np.array([cx, cy])
            p1 = np.array([top[0] + (cx - top[0]) * 0.25, min(cy, top[1]) - 0.5 * abs(top[1] - cy) - 4])
            n = int(np.hypot(*(p2 - top)) * 1.5)
            for k, p in enumerate(T.bezier(top, p1, p2, max(n, 4))):
                strokes.append((p[0], p[1], 1.0 * sz * (1 - 0.6 * k / max(n, 4))))

        def wood():
            for x, y, w in strokes:
                r = max(0.6, w)
                for j in range(int(y - r), int(y + r) + 1):
                    for i in range(int(x - r), int(x + r) + 1):
                        if (i - x) ** 2 + (j - y) ** 2 <= r * r:
                            put(img, i, j, q(BARK, 0.62 - 0.35 * (i - x) / (r + 0.5), g(i, j)))

        def clump(cx, cy, back):
            r = rng.uniform(2.6, 3.8) * sz ** 0.5
            high = np.clip((ey + b - cy) / (2 * b), 0, 1)            # 1 at the crown top
            dim = 0.6 if back else 1.0
            right = (cx - ex) / a                                    # the right side hangs thinner: light comes through
            for k in range(int(8 * sz * (1 - 0.7 * np.clip(right * 1.5, 0, 1)))):   # twigs: straight down to the hem
                u = rng.uniform(-1, 1)
                sx, sy = cx + u * r, cy + rng.uniform(0, r * 0.5)
                L = int(max(4, hem(sx) - sy + rng.uniform(-11, 4) * sz))     # a ragged hem
                if high > 0.7:                                       # the top clumps: long but uneven, so no straight edge
                    L = int(L * rng.uniform(0.5, 1.0))
                lit0 = np.clip(0.8 - 0.3 * (u + 0.3) + 0.15 * high, 0.3, 0.95) * dim
                for h in range(L):
                    t = h / L
                    i = int(round(sx + u * 1.2 * (1 - np.exp(-h / 2.5)) + 0.4 * np.sin(h * 0.25 + sx)))
                    if rng.random() < 0.9 - 0.45 * np.clip((i - ex) / a, 0, 1):
                        put(img, i, int(round(sy + h)), q(WILLOW, lit0 - 0.45 * t, g(i, int(sy + h))))
            for j in range(int(cy - r - 1), int(cy + r + 1)):        # the clump: rounded top, lit upper left
                for i in range(int(cx - r - 1), int(cx + r + 2)):
                    e = ((i - cx) / r) ** 2 + ((j - cy) / (r * 0.75)) ** 2
                    if e > 1 or g(i * 3, j) > 1.15 - 0.3 * e:
                        continue
                    lit = np.clip(0.55 + 0.35 * high - ((i - cx) * 0.5 + (j - cy) * 0.85) / r * 0.5, 0.1, 1) * dim
                    if e > 0.7 and (i - cx) + (j - cy) > 0:
                        lit *= 0.55
                    c = q(WILLOW, lit, g(i, j))
                    if not back and e > 0.5 and (i - cx) + (j - cy) < -r * 0.6 and lit > 0.6 and g(i, j) < 0.6:
                        c = HI
                    put(img, i, j, c)

        back = [rng.random() < 0.2 for _ in clumps[:len(clumps) - int(7 * sz)]] + [False] * int(7 * sz)
        for (cx, cy), bk in sorted(zip(clumps, back), key=lambda c: c[0][1]):
            if bk:
                clump(cx, cy, True)
        wood()
        for (cx, cy), bk in sorted(zip(clumps, back), key=lambda c: c[0][1]):   # high to low: the curtains tier
            if not bk:
                clump(cx, cy, False)


class Schilf:
    """A clump of reeds at the water's edge, some with a soft brown plume."""
    def __init__(s, x, y, n=8, seed=1):
        s.x, s.y, s.n, s.seed = x, y, n, seed

    def box(s):
        return (s.x - 5, s.y - 16, s.x + 6, s.y + 1)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        for _ in range(s.n):
            bx, h, lean = s.x + int(rng.integers(-4, 5)), int(rng.integers(8, 15)), rng.normal(0.3, 0.3)
            for k in range(h):
                put(img, bx + int(round(lean * k * k / h / 2)), s.y - k, REED[min(3, k * 4 // h)])
            if rng.random() < 0.45:
                tx = bx + int(round(lean * h / 2))
                for d in range(3):
                    put(img, tx + (d == 2), s.y - h - d, PLUME[min(2, d)])


class Rohrkolben:
    """Bulrushes: tall stalks with a dark brown cob and a thin spike."""
    def __init__(s, x, y, n=4, seed=2):
        s.x, s.y, s.n, s.seed = x, y, n, seed

    def box(s):
        return (s.x - 4, s.y - 17, s.x + 5, s.y + 1)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        for _ in range(s.n):
            bx, h = s.x + int(rng.integers(-3, 4)), int(rng.integers(10, 15))
            for k in range(h):
                put(img, bx, s.y - k, REED[1 + (k > h // 2)])
            for d in range(3):                                   # the cob
                put(img, bx, s.y - h - d, CATTAIL[1 + (d == 2)])
                put(img, bx + 1, s.y - h - d, CATTAIL[0])
            put(img, bx, s.y - h - 3, REED[2])
            put(img, bx, s.y - h - 4, REED[3])
            if rng.random() < 0.7:                               # a long leaf curving away
                for k in range(h - 3):
                    put(img, bx - 1 - k * k // 40, s.y - k, REED[2])


class Farn:
    """A fern: fronds fanning from one crown, each with little leaflets."""
    def __init__(s, x, y, seed=5, size=8):
        s.x, s.y, s.seed, s.size = x, y, seed, size

    def box(s):
        return (s.x - s.size - 2, s.y - s.size - 2, s.x + s.size + 3, s.y + 2)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        for a in np.linspace(-2.6, -0.5, 5) + rng.normal(0, 0.12, 5):
            L = s.size * rng.uniform(0.8, 1.1)
            for k in range(int(L)):
                t = k / L
                ang = a + 0.5 * t * np.sign(np.cos(a))         # the tips droop
                i = int(round(s.x + np.cos(ang) * k))
                j = int(round(s.y + np.sin(ang) * k * 0.8 + t * t * 2))
                lit = 0.7 - 0.4 * t - 0.15 * (np.cos(a) > 0)
                put(img, i, j, q(FERN, lit, 0.5))
                if 1 <= k < L - 1 and k % 2 == 0:             # leaflets either side
                    put(img, i, j - 1, q(FERN, lit - 0.1, 0.5))
                    put(img, i + (1 if np.cos(a) > 0 else -1), j + 1, q(FERN, lit - 0.2, 0.5))
