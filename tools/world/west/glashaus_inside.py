#!/usr/bin/env python3
"""The inside of the greenhouse (Garasu-muro) as its own place, like the cave, three screens wide (540 x 400 art
px, as wide as it is outside), the door at the bottom of the middle. Philip's mood (2026-11-08, his pictures): a
jungle under glass. Warm gold-green evening light falls slanting through the tinted panes and the crowns in shafts,
a little haze; the floor hardly shows - narrow trodden ways wind through ferns, big-leaved plants and pink and red
blooms, big palms and trees lean their crowns over them, lianas with red flower clusters hang down. In the middle a
pond with giant lily pads and a small black iron bridge over it; in a clearing a potting bench with tools, seed
trays and little pots, stone bowls with small water lilies beside it.

The picture is split as the game needs it: ground (what he walks on and behind), canopy (what hangs over him:
crowns, lianas), the walkable mask. python3 glashaus_inside.py out.png [with_monk]"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi
from scipy.interpolate import splprep, splev

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import objects_west as o  # noqa: E402
from objects_west import hx, pick, put, g_at, RUST, TEAL, WOOD, STONE, MOSS, SOIL  # noqa: E402

W, H = 540, 400
TOP = 34                                    # the back wall's foot
SIDE = 18
DOOR = (256, 284)
LANTERN = (281, 352)
TERRA = [hx(c) for c in ['#3a1d14', '#5e2f1e', '#86452a', '#a85f3a', '#c27c52']]
CREAM = [hx(c) for c in ['#5e5646', '#857a64', '#a89b80', '#c4b89c']]
JUNGLE = [hx(c) for c in ['#0f1a10', '#1a2c18', '#28421f', '#3a5c28', '#557a34', '#7a9a44', '#a2b858']]
PINK = [hx(c) for c in ['#5a1a2a', '#8e2a44', '#c4446a', '#e07a96', '#f2b0c0']]
REDF = [hx(c) for c in ['#4a1414', '#7e2020', '#b03428', '#d8603a']]
GOLD = np.array([255.0, 206.0, 120.0])
POND = (270, 168)
BENCH = (70, 286)                           # the potting bench's front middle
WAYS = [                                    # the trodden ways (points), from the door
    [(270, 398), (268, 360), (262, 326), (272, 296), (300, 262), (306, 228), (292, 204)],      # up to the bridge
    [(240, 150), (226, 120), (236, 84), (262, 60), (300, 52)],                                 # beyond it, round the back
    [(262, 326), (220, 318), (176, 300), (134, 302), (96, 300)],                               # left: to the bench
    [(134, 302), (118, 250), (90, 214), (60, 170), (52, 120)],                                 # left, on up
    [(272, 296), (330, 316), (380, 300), (430, 312), (470, 290), (488, 246)],                  # right
    [(430, 312), (412, 260), (430, 200), (468, 160), (484, 110)],
]
BRIDGE = ((292, 204), (240, 150))           # its two ends on the banks
_c = ndi.gaussian_filter(np.random.default_rng(13).normal(0, 1, (H, W)), 1.6)
CLUMP = np.clip(_c / _c.std() - np.roll(_c / _c.std(), 2, axis=0), -1.5, 1.5) / 1.5   # lit tops of leaf clumps


def fbm(rng, s, shape=(H, W)):
    n = ndi.gaussian_filter(rng.normal(0, 1, shape), s)
    return n / (n.std() + 1e-9)


def curve(pts, n=400):
    tck, _ = splprep(np.array(pts, float).T, s=0, k=min(3, len(pts) - 1))
    return np.array(splev(np.linspace(0, 1, n), tck)).T


def masks(rng):
    """The ways, the pond, the bridge, the clearings (bench, door), the floor between the walls."""
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    for pts in WAYS:
        d.line([tuple(p) for p in curve(pts)], fill=255, width=11)
    ways = np.array(im) > 0
    yy, xx = np.mgrid[0:H, 0:W]
    n = fbm(rng, 6)
    pond = (((xx - POND[0]) / 62.0) ** 2 + ((yy - POND[1]) / 40.0) ** 2 + 0.18 * n) < 1
    bridge = np.zeros((H, W), bool)
    (ax, ay), (bx, by) = BRIDGE
    for t in np.linspace(0, 1, 200):
        x, y = ax + (bx - ax) * t, ay + (by - ay) * t
        bridge[int(y) - 4:int(y) + 5, int(x) - 4:int(x) + 5] = True
    clear = (((xx - BENCH[0]) / 46.0) ** 2 + ((yy - BENCH[1] + 6) / 26.0) ** 2 + 0.2 * n) < 1
    clear |= (((xx - 270) / 34.0) ** 2 + ((yy - 380) / 22.0) ** 2) < 1          # inside the door
    floor = (xx >= SIDE) & (xx < W - SIDE) & (yy >= TOP + 2) & (yy < H - 12)
    ways &= ~pond
    return ways & floor, pond, bridge, clear & floor, floor


def ground(rng, ways, clear):
    """Leaf litter and dark soil everywhere; on the ways and in the clearings the old tiles still show, broken."""
    G = rng.random((H, W))
    soil = np.array([SOIL[0], SOIL[1], SOIL[2], hx('#4a3a22')])[np.clip((G * 4).astype(int), 0, 3)]
    img = soil * (0.85 + 0.15 * fbm(rng, 3)[..., None].clip(-1, 1))
    litter = G > 0.9
    img[litter] = np.array([hx('#5a3a1c'), hx('#7a5426'), hx('#9a7a36')])[(G[litter] * 30).astype(int) % 3]
    open_ = ways | clear
    yy, xx = np.mgrid[0:H, 0:W]
    tx, ty = xx // 4, yy // 4
    tile = np.where(((tx + ty) % 2)[..., None] == 1, np.array(TERRA[3]), np.array(CREAM[2])) * (0.85 + 0.25 * G[..., None])
    joint = (xx % 4 == 0) | (yy % 4 == 0)
    tile[joint] *= 0.6
    keep = open_ & (fbm(rng, 2.5) > -0.4) & ~((tx * 31 + ty * 17) * 7919 % 97 < 10)
    img[keep] = tile[keep]
    img[open_ & joint & (G < 0.25)] = MOSS[2]
    edge = ndi.binary_dilation(open_, iterations=2) & ~open_                      # the ways are trodden: a dark rim
    img[edge] *= 0.7
    return img, G


def pond_paint(img, pond, G):
    d = ndi.distance_transform_edt(pond)
    for y, x in zip(*np.nonzero(pond)):
        v = 0.25 + 0.5 * min(1, d[y, x] / 14.0)
        c = np.array(hx('#0c1a16')) * (1 - v) + np.array(hx('#1f3a30')) * v
        if (x + 2 * y) % 17 == 0 and G[y, x] < 0.5:
            c = c * 0.6 + GOLD * 0.4                                    # the evening on the water
        img[y, x] = c
    rim = ndi.binary_dilation(pond, iterations=3) & ~pond
    for y, x in zip(*np.nonzero(rim)):
        img[y, x] = pick(STONE, 1.6 + 1.6 * G[y, x] + (0.8 if y < POND[1] else 0))   # an old stone kerb


class Victoria:
    """A giant water lily pad: round, its rim turned up (lit on the far side, the inside of the rim in shade), the
    veins radiating from its middle."""
    def __init__(s, x, y, r):
        s.x, s.y, s.r = x, y, r

    def draw(s, img, G):
        x, y, r = s.x, s.y, s.r
        for j in range(int(y - r * 0.75) - 2, int(y + r * 0.75) + 3):
            for i in range(x - r - 1, x + r + 2):
                d = np.hypot(i - x, (j - y) / 0.72)
                if d > r:
                    continue
                a = np.arctan2(j - y, i - x)
                if d > r - 1.6:                                        # the upturned rim
                    c = pick(JUNGLE, 4.8 if j > y else 3.2) if (i + j) % 5 else pick(REDF, 2.2)
                elif d > r - 3:
                    c = pick(JUNGLE, 2.0 if j > y else 3.6)
                else:
                    vein = abs((a * 12 / np.pi) % 1 - 0.5) < 0.08
                    c = pick(JUNGLE, 3.8 - 0.8 * (i - x) / r + (0.7 if vein else 0) + 0.3 * (g_at(G, i, j) - 0.5))
                put(img, i, j, c)


class Farnwedel:
    """Ferns and big leaves as one dense bush, lit at the upper left."""
    def __init__(s, x, y, seed, size=1.0):
        s.x, s.y, s.seed, s.size = x, y, seed, size

    def draw(s, img, G):
        r = np.random.default_rng(s.seed)
        n = int(r.integers(5, 9))
        for k in range(n):
            a = -np.pi / 2 + (k / (n - 1) - 0.5) * 2.6 + r.uniform(-0.15, 0.15)
            L = r.uniform(8, 14) * s.size
            broad = r.random() < 0.35
            for t in np.linspace(0, 1, int(L * 2)):
                px, py = s.x + np.cos(a) * L * t, s.y + np.sin(a) * L * t * 0.8 + 2.5 * t * t
                wd = (2.6 if broad else 1.6) * s.size * np.sin(np.pi * min(1.0, t * 1.1))
                for dd in np.arange(-wd, wd + 0.01, 0.6):
                    qx, qy = px - np.sin(a) * dd, py + np.cos(a) * dd * 0.8
                    if not broad and abs(dd) > 0.6 and int(t * 20) % 2:
                        continue                                       # a fern's leaflets, not a blade
                    lit = 2.4 + 1.8 * t * (np.cos(a) < 0) + 0.8 * t - 1.3 * (dd > 0) + 0.7 * (g_at(G, int(qx), int(qy)) - 0.5)
                    put(img, int(round(qx)), int(round(qy)), pick(JUNGLE, lit))


class Bluete:
    """A clump of tropical blooms: pink or red over their dark leaves."""
    def __init__(s, x, y, seed, red=False):
        s.x, s.y, s.seed, s.red = x, y, seed, red

    def draw(s, img, G):
        r = np.random.default_rng(s.seed)
        P = REDF if s.red else PINK
        for _ in range(int(r.integers(5, 10))):
            fx, fy = s.x + int(r.integers(-4, 5)), s.y - int(r.integers(2, 8))
            for (u, v) in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                put(img, fx + u, fy + v, pick(P, (3.6 if (u, v) == (-1, 0) or v == -1 else 2.4) + 0.4 * r.random()))
            put(img, fx, fy, hx('#f0d070') if not s.red else P[3])


class Palme:
    """A tall palm: its ringed trunk leaning a little, the crown a wide fan of fronds arching out and down."""
    def __init__(s, x, y, seed, h=56, R=34):
        s.x, s.y, s.seed, s.h, s.R = x, y, seed, h, R

    def trunk(s, img, G):
        r = np.random.default_rng(s.seed)
        lean = r.uniform(-0.25, 0.25)
        for j in range(s.h):
            cx = s.x + lean * j
            for i in range(-2, 3):
                put(img, int(round(cx + i)), s.y - j, pick(WOOD, 3.4 - 0.8 * (i + 2) - (0.9 if j % 4 == 0 else 0)))
        for i in range(s.x - 5, s.x + 6):
            put(img, i, s.y + 1, img[min(H - 1, s.y + 1), i] * 0.6)
        return s.x + lean * s.h, s.y - s.h

    def crown(s, img, G, top):
        r = np.random.default_rng(s.seed + 1)
        cx, cy = top
        for k in range(14):
            a = k / 14.0 * 2 * np.pi + r.uniform(-0.12, 0.12)
            L = s.R * r.uniform(0.75, 1.05)
            for t in np.linspace(0, 1, int(L * 1.6)):
                px = cx + np.cos(a) * L * t
                py = cy + np.sin(a) * L * t * 0.6 + 14 * t * t           # arching down
                lit = 4.6 - 2.4 * t - 1.0 * (np.sin(a) > 0.3) + 0.8 * (np.cos(a) < -0.3)
                put(img, int(round(px)), int(round(py)), pick(JUNGLE, lit))
                if 0.15 < t < 0.97 and int(t * L) % 2 == 0:              # leaflets hanging from the midrib
                    for sd in (-1, 1):
                        for q in (1, 2, 3):
                            put(img, int(round(px - np.sin(a) * q * sd * 0.8)), int(round(py + q * 0.7)),
                                pick(JUNGLE, lit - 0.6 - 0.25 * q))
        for (u, v) in ((0, 0), (1, 0), (0, 1), (-1, 0)):
            put(img, int(cx) + u, int(cy) + v, pick(WOOD, 2.0))


class Baum:
    """A broad tree under the glass (a fig, a camphor): a dark trunk, a heavy round crown of leaf clumps."""
    def __init__(s, x, y, seed, h=40, R=36):
        s.x, s.y, s.seed, s.h, s.R = x, y, seed, h, R

    def trunk(s, img, G):
        for j in range(s.h):
            w = 3 if j < s.h * 0.7 else 2
            for i in range(-w, w + 1):
                put(img, s.x + i, s.y - j, pick(WOOD, 3.2 - 0.6 * (i + w)))
        for i in range(s.x - 7, s.x + 8):
            put(img, i, s.y + 1, img[min(H - 1, s.y + 1), i] * 0.6)
        return s.x, s.y - s.h

    def crown(s, img, G, top):
        r = np.random.default_rng(s.seed)
        cx, cy = top
        blobs = [(cx + r.uniform(-1, 1) * s.R * 0.6, cy + r.uniform(-0.6, 0.5) * s.R * 0.5, r.uniform(0.4, 0.62) * s.R)
                 for _ in range(9)]
        for bx, by, br in sorted(blobs, key=lambda b: b[1]):
            for j in range(int(by - br * 0.75) - 1, int(by + br * 0.75) + 2):
                for i in range(int(bx - br) - 1, int(bx + br) + 2):
                    d = np.hypot(i - bx, (j - by) / 0.75) / br
                    if d < 1 - 0.18 * g_at(G, i * 3, j * 7):
                        cl = CLUMP[j % H, i % W]                       # leaf clumps, lit on their tops
                        lit = 4.0 - 1.8 * (i - bx + br) / (2 * br) - 1.4 * (j - by + br) / (2 * br) + 1.0 * cl \
                            + 0.6 * (g_at(G, i, j) - 0.5)
                        put(img, i, j, pick(JUNGLE, lit))


class Liane:
    """A liana hanging from the roof, leaves along it, red flowers in clusters."""
    def __init__(s, x, y0, L, seed):
        s.x, s.y0, s.L, s.seed = x, y0, L, seed

    def draw(s, img, G):
        r = np.random.default_rng(s.seed)
        for j in range(s.L):
            x = int(round(s.x + 2.5 * np.sin((j + s.seed) / 9.0)))
            put(img, x, s.y0 + j, pick(WOOD, 1.6))
            put(img, x + 1, s.y0 + j, pick(WOOD, 0.8))
            if j % 3 == 0:
                for u in (-2, -1, 2, 3):
                    if (u + j) % 2:
                        put(img, x + u, s.y0 + j + (u > 0), pick(JUNGLE, 2.8 + 1.4 * r.random()))
            if r.random() < 0.06:
                for (u, v) in ((0, 0), (1, 0), (0, 1), (-1, 1), (1, 1)):
                    put(img, x + u, s.y0 + j + v, pick(REDF, 2.0 + 1.6 * r.random()))


class Werkbank:
    """The potting bench in its clearing: a heavy top, a seed tray, small pots with seedlings, a trowel, a hand fork
    and shears on a rail, a watering can and a sack beside it."""
    def draw(s, img, G):
        x, y = BENCH
        x0, x1, top = x - 22, x + 22, y - 12
        for j in range(top, top + 7):
            for i in range(x0, x1):
                put(img, i, j, WOOD[4] if j == top else o.plank_px(i, j, x0, top, 3.0 - 0.8 * (i - x0) / 44, 7))
        for i in range(x0, x1):
            put(img, i, top + 7, WOOD[1])
            put(img, i, top + 8, WOOD[0])
        for i in (x0 + 1, x1 - 3):
            for j in range(top + 9, y + 1):
                put(img, i, j, WOOD[2])
                put(img, i + 1, j, WOOD[0])
        for i in range(x0, x1 + 2):
            put(img, i, y + 1, img[min(H - 1, y + 1), i] * 0.55)
        for i in range(x0 + 3, x0 + 15):                                # a seed tray with rows of seedlings
            for j in range(top + 1, top + 5):
                put(img, i, j, SOIL[1] if (i + j) % 3 else JUNGLE[4 + (i % 2)])
        for k, px in enumerate((x0 + 19, x0 + 24, x0 + 28, x0 + 33)):   # little clay pots
            for j in range(top - 3, top + 3):
                for i in (-1, 0, 1):
                    put(img, px + i, j, pick(TERRA, 3.2 - 1.0 * (i + 1) - (1.4 if j == top - 3 else 0)))
            if k % 2 == 0:
                put(img, px, top - 4, JUNGLE[5])
                put(img, px - 1, top - 5, JUNGLE[4])
        for i in range(x0 + 2, x1 - 2):
            put(img, i, top - 10, WOOD[3])                              # the rail at the back
        for hx_, tool in ((x0 + 6, 'trowel'), (x0 + 12, 'fork'), (x0 + 38, 'shears')):
            for j in range(top - 9, top - 3):
                put(img, hx_, j, WOOD[3] if j < top - 6 else hx('#6a6e78'))
            if tool == 'fork':
                put(img, hx_ - 1, top - 3, hx('#6a6e78'))
                put(img, hx_ + 1, top - 3, hx('#6a6e78'))
            elif tool == 'shears':
                put(img, hx_ + 1, top - 4, hx('#6a6e78'))
        for j in range(y - 6, y + 1):                                   # the watering can
            for i in range(x1 + 3, x1 + 9):
                put(img, i, j, pick([hx('#2f3a3c'), hx('#4e5f60'), hx('#7a8c8a')], 2.4 - 0.4 * (i - x1 - 3)))
        for k in range(5):
            put(img, x1 + 9 + k, y - 4 - k // 2, hx('#4e5f60'))
        for j in range(y - 8, y + 1):                                   # the sack
            for i in range(x0 - 9, x0 - 1):
                if (i - (x0 - 5)) ** 2 / 14 + (j - (y - 4)) ** 2 / 20 < 1:
                    put(img, i, j, pick([hx('#4a3e2c'), hx('#6b5a3e'), hx('#8a7650')], 2.4 - 0.4 * (i - x0 + 9)))


class Schale:
    """A stone bowl with small water lilies."""
    def __init__(s, x, y, r=6):
        s.x, s.y, s.r = x, y, r

    def draw(s, img, G):
        x, y, r = s.x, s.y, s.r
        for j in range(y - 3, y + 4):
            for i in range(x - r, x + r + 1):
                d = np.hypot(i - x, (j - y) * r / 3.5)
                if d <= r:
                    put(img, i, j, pick(STONE, 3.4 - 1.2 * (i - x + r) / (2 * r)) if d > r - 1.5 else hx('#1f3a30'))
        for j in range(y + 4, y + 7):
            for i in range(x - r + 1, x + r):
                put(img, i, j, pick(STONE, 1.8 - 0.6 * (j - y - 4)))
        for (u, v) in ((-2, 0), (-1, 0), (2, -1), (1, 1)):
            put(img, x + u, y + v, JUNGLE[4])
        put(img, x + 1, y - 1, PINK[4])


def bridge(img):
    """A small arched footbridge of black iron over the pond: boards, a railing of thin bars either side."""
    (ax, ay), (bx, by) = BRIDGE
    n = int(np.hypot(bx - ax, by - ay))
    ux, uy = (bx - ax) / n, (by - ay) / n
    nx, ny = -uy, ux
    for k in range(n + 1):
        lift = 6 * np.sin(np.pi * k / n)
        cx, cy = ax + ux * k, ay + uy * k - lift
        put(img, int(round(cx + nx * 6)), int(round(cy + ny * 6 + lift + 3)), hx('#0a1210'))   # its shadow
        for dd in np.arange(-5, 5.01, 0.5):
            put(img, int(round(cx + nx * dd)), int(round(cy + ny * dd)), pick(WOOD, 3.0 - 0.2 * dd + (0.7 if k % 3 == 0 else 0)))
        for side in (-6, 6):                                           # the railings: black iron, a top rail, bars
            rx, ry = cx + nx * side, cy + ny * side
            for q in (8, 9):
                put(img, int(round(rx)), int(round(ry - q)), hx('#101012') if q == 9 else hx('#3a3a40'))
            if k % 3 == 0:
                for q in range(9):
                    put(img, int(round(rx)), int(round(ry - q)), hx('#141416'))


def walls(img, G, rng):
    """The back wall and the end walls: rusted iron, panes tinted green with the low evening sun behind them; the
    bottom wall with the door."""
    sky = fbm(rng, 4)

    def pane(y, x):
        warm = np.clip(1 - (x + 0.6 * y) / 700.0, 0, 1)                  # the sun low in the west
        base = np.array(hx('#6e7a48')) * (1 - warm) + GOLD * 0.85 * warm
        c = base * (0.55 if sky[y, x] > 0.4 else 1.0)                    # leaves outside against it
        glass = pick(TEAL, 2.4 + (1.2 if (x - y) % 13 in (0, 1) else 0))
        return c * 0.6 + glass * 0.4

    for y in range(H):
        for x in range(W):
            if y < TOP + 2:
                if y >= TOP - 4:
                    img[y, x] = pick(STONE, 3.4 if y == TOP - 4 else 2.2 + 0.3 * G[y, x])
                else:
                    pav = 160 <= x < 380                                # the pavilion: pointed arches
                    u = (x - 160) % 20
                    arch = 4 + 9 * (abs(u - 10) / 10.0) ** 0.7
                    bar = (u in (0, 1) or abs(y - arch) < 1.0) if pav else (x % 14 in (0, 1) or y in (0, 1, 12))
                    img[y, x] = pick(RUST, 2.6 - 1.2 * x / W) if bar else pane(y, x)
            elif x < SIDE or x >= W - SIDE:
                inner = (SIDE - 1 - x) if x < SIDE else (x - (W - SIDE))
                if inner < 4:
                    img[y, x] = pick(STONE, (3.3 if inner == 0 else 2.6 - 0.3 * inner) + 0.3 * G[y, x])
                elif y % 26 in (0, 1) or inner in (4, 5):
                    img[y, x] = pick(RUST, 2.4 if x < SIDE else 1.6)
                else:
                    img[y, x] = pane(y, x)
            elif y >= H - 12 and not (DOOR[0] <= x < DOOR[1]):
                img[y, x] = pick(STONE, 3.4 if y == H - 12 else 2.0 + 0.4 * G[y, x]) if y < H - 8 else \
                    (pick(RUST, 2.2) if x % 14 in (0, 1) else pane(y, x))
    for y in range(H - 14, H):
        for x in (DOOR[0] - 2, DOOR[0] - 1, DOOR[1], DOOR[1] + 1):
            img[y, x] = pick(RUST, 3.0 if x in (DOOR[0] - 2, DOOR[1]) else 1.4)


def lantern(img):
    x, y = LANTERN
    for j in range(y - 2, y + 18):
        put(img, x + 6, j, RUST[2])
        put(img, x + 7, j, RUST[0])
    for i in range(x, x + 7):
        put(img, i, y - 2, RUST[2])
    for j in range(y, y + 7):
        for i in range(x - 2, x + 3):
            edge = i in (x - 2, x + 2) or j in (y, y + 6)
            put(img, i, j, RUST[1] if edge else (hx('#fde7a0') if j < y + 4 else hx('#f2b44a')))


def light(img, cover, rng):
    """The evening sun through glass and leaves: slanting shafts of warm gold, dimmer under thick crowns, a
    gold-green haze over all."""
    yy, xx = np.mgrid[0:H, 0:W]
    along = xx * 0.55 + yy * 0.83                                       # across the shafts (from the upper left)
    shafts = np.clip(np.sin(along / 23.0) * 0.5 + 0.5 + 0.35 * fbm(np.random.default_rng(5), 14), 0, 1) ** 3
    shafts *= np.clip(np.sin(along / 61.0 + 1.0) * 0.6 + 0.6, 0, 1)
    sh = shafts * (1 - 0.55 * ndi.gaussian_filter(cover.astype(float), 3))
    img = img * (0.66 + 0.6 * sh[..., None]) + GOLD * 0.14 * sh[..., None]
    return img * 0.9 + np.array([150.0, 156.0, 96.0]) * 0.1


def render(with_monk=False):
    """-> (ground picture, canopy RGBA (alpha 0/1), walkable mask, lantern light), before the game's mood."""
    rng = np.random.default_rng(97)
    ways, pond, br, clear, floor = masks(rng)
    img, G = ground(rng, ways, clear)
    pond_paint(img, pond, G)
    open_ = ways | clear | pond | br
    dist = ndi.distance_transform_edt(~open_)
    walls(img, G, rng)
    things = []
    r = np.random.default_rng(98)
    for (x, y, rad) in ((244, 160, 19), (298, 182, 15), (312, 150, 12), (226, 186, 10), (276, 140, 9),
                        (318, 190, 7)):
        things.append((y, Victoria(x, y, rad)))
    for _ in range(5200):                                              # the undergrowth: dense away from the ways
        x, y = int(r.integers(SIDE + 2, W - SIDE - 2)), int(r.integers(TOP + 6, H - 13))
        d = dist[y, x]
        if d < 3 or r.random() > np.clip((d - 2) / 6.0, 0, 1):
            continue
        if r.random() < 0.95:
            things.append((y, Farnwedel(x, y, int(r.integers(1 << 30)), r.uniform(0.7, 1.25))))
        else:
            things.append((y, Bluete(x, y, int(r.integers(1 << 30)), red=r.random() < 0.35)))
    for k, (x, y) in enumerate(((40, 120), (130, 90), (200, 56), (350, 64), (420, 100), (510, 140), (34, 250),
                                (180, 236), (362, 236), (506, 270), (120, 372), (440, 372))):
        if k % 3 == 1:
            things.append((y, Baum(x, y, 300 + k, h=int(r.integers(30, 44)), R=int(r.integers(30, 40)))))
        else:
            things.append((y, Palme(x, y, 300 + k, h=int(r.integers(44, 64)), R=int(r.integers(28, 38)))))
    things.append((BENCH[1], Werkbank()))
    for (x, y) in ((104, 280), (114, 292), (34, 300)):
        things.append((y, Schale(x, y)))
    things.sort(key=lambda t: t[0])
    canopy = np.zeros((H, W, 4))

    def over(draw):                                                    # drawn into the canopy layer
        mark = np.full((H, W, 3), -1.0)
        draw(mark)
        m = mark[..., 0] >= 0
        canopy[m, :3] = mark[m]
        canopy[m, 3] = 1

    for _, t in things:
        if isinstance(t, (Palme, Baum)):
            top = t.trunk(img, G)
            over(lambda m, t=t, top=top: t.crown(m, G, top))
        else:
            t.draw(img, G)
    bridge(img)
    lantern(img)
    for k in range(16):                                                 # lianas from the roof
        x = int(r.integers(SIDE + 4, W - SIDE - 4))
        over(lambda m, x=x, k=k: Liane(x, 0, int(np.random.default_rng(k).integers(40, 150)), 500 + k).draw(m, G))
    cover = canopy[..., 3] > 0
    img = light(img, cover, rng)
    canopy[..., :3] = light(canopy[..., :3], cover, rng)
    walk = walk_mask(ways, clear, br)
    if with_monk:
        sheet = np.array(Image.open(os.path.join(HERE, '..', '..', '..', 'assets', 'char', 'wanderer.png')).convert('RGBA'))
        f = sheet[16:32, 0:12].astype(float)
        x0, y0 = 264, 360
        a = f[..., 3:] / 255.0
        img[y0:y0 + 16, x0:x0 + 12] = img[y0:y0 + 16, x0:x0 + 12] * (1 - a) + f[..., :3] * a
    lt = {'x': LANTERN[0] + 0.5, 'y': LANTERN[1] + 3.5, 'r': 120.0, 'k': 1.0}
    return np.clip(img, 0, 255), canopy, walk, lt


def walk_mask(ways, clear, br):
    yy, xx = np.mgrid[0:H, 0:W]
    m = ndi.binary_erosion(ways, iterations=2) | ndi.binary_erosion(clear, iterations=3) | br
    m |= (xx >= DOOR[0]) & (xx < DOOR[1]) & (yy >= H - 14)
    x, y = BENCH
    m[y - 14:y + 3, x - 32:x + 34] = False
    c = m.reshape(H // 2, 2, W // 2, 2).all(axis=(1, 3))
    lab, _ = ndi.label(c)
    out = lab[-1, DOOR[0] // 2:DOOR[1] // 2]
    keep = lab == np.bincount(out[out > 0]).argmax()
    return m & keep.repeat(2, 0).repeat(2, 1)


def grade_inside(img):
    """The preview's grade for in here: the game's, but warm (the interior keeps its gold)."""
    return (img * 0.86 + img.mean(-1, keepdims=True) * 0.14) * np.array([0.98, 0.93, 0.74])


def main(out, with_monk=False):
    img, canopy, walk, lt = render(with_monk)
    m = canopy[..., 3] > 0
    img[m] = canopy[m, :3]
    Image.fromarray(np.clip(grade_inside(img), 0, 255).astype(np.uint8)).save(out)


if __name__ == '__main__':
    main(sys.argv[1], len(sys.argv) > 2)
