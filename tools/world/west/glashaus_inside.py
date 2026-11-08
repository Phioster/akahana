#!/usr/bin/env python3
"""The inside of the greenhouse (Garasu-muro) as its own screen, like the cave: exactly one view (180 x 400 art
px), the door at the bottom. Glass walls of rusted iron and green glass all round on a low stone parapet, the night
and the leaves outside behind them; an aisle of old Victorian floor tiles from the door up to a round stone basin
with water lilies and a dry little fountain; raised beds left and right gone wild (ferns, hydrangeas, big-leaved
plants, creepers spilling onto the floor), two palms in clay pots, a potting bench with pots and a watering can,
a chair by the basin. The lantern one sees from outside burns by the door; moonlight falls through the roof in
the panes' pattern. Put through the game's mood like the cave. python3 glashaus_inside.py out.png [with_monk]"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..'),
                os.path.join(HERE, '..', 'north')]
import objects_west as o  # noqa: E402
from objects_west import hx, pick, put, RUST, TEAL, INSIDE, WOOD, STONE, MOSS, SOIL, LEAF  # noqa: E402
import objects_lake as ol  # noqa: E402
import objects_water as ow  # noqa: E402
from field6 import L1, MG, DG, K  # noqa: E402

W, H = 180, 400
WALL_L, WALL_R, BACK = 20, 160, 66          # the floor between the side walls, below the back wall's parapet
DOOR = (76, 104)                            # the door opening in the bottom wall
BASIN = (90, 150, 20)
LANTERN = (101, 352)                        # its glass (the light)
TERRA = [hx(c) for c in ['#3a1d14', '#5e2f1e', '#86452a', '#a85f3a', '#c27c52']]
CREAM = [hx(c) for c in ['#5e5646', '#857a64', '#a89b80', '#c4b89c']]
BEDS = [(22, 72, 68, 130), (22, 176, 68, 300), (22, 316, 68, 370),
        (112, 72, 158, 130), (112, 176, 158, 236), (112, 316, 158, 370)]
BENCH = (116, 250, 156, 266)


def fbm(rng, s, shape=(H, W)):
    n = ndi.gaussian_filter(rng.normal(0, 1, shape), s)
    return n / (n.std() + 1e-9)


def floor_stone(rng):
    """Big worn flags under everything, the world's grain darker (as the cave takes field6's)."""
    tone = 0.5 + 0.18 * fbm(rng, 8) + 0.08 * fbm(rng, 1.2)
    img = np.array([DG, MG, L1], float)[np.digitize(tone, [0.42, 0.66])] * np.array([0.92, 0.9, 0.86])
    yy, xx = np.mgrid[0:H, 0:W]
    joint = ((yy % 14) == 0) | (((xx + 9 * ((yy // 14) % 2)) % 18) == 0)
    img[joint] *= 0.72
    return img


def aisle(img, G, rng):
    """Encaustic tiles, terracotta and cream in a checker with a dark border, some gone, some cracked, moss in the joints."""
    x0, x1 = DOOR[0] - 2, DOOR[1] + 2
    bx, by, br = BASIN
    for y in range(BACK + 4, H):
        for x in range(x0, x1):
            ring = abs(np.hypot(x - bx, (y - by) * 1.0) - (br + 9)) < 9
            if not (ring or (x0 <= x < x1 and (y > by + br + 6 or y < by - br - 6))):
                continue
            if x in (x0, x1 - 1) and not ring:
                c = pick(STONE, 1.2)                                   # the border
            else:
                tx, ty = (x - x0) // 4, (y - BACK) // 4
                cell = tx * 31 + ty * 17
                c = pick(TERRA, 2.6 + 0.6 * G[y, x]) if (tx + ty) % 2 else pick(CREAM, 2.2 + 0.7 * G[y, x])
                if (x - x0) % 4 == 0 or (y - BACK) % 4 == 0:
                    c = c * 0.62                                       # the joints
                    if G[y, x] < 0.12:
                        c = pick(MOSS, 1.6)
                if (cell * 7919) % 97 < 4:
                    c = pick(SOIL, 1.0 + G[y, x])                      # a tile gone: soil
                elif (cell * 104729) % 89 < 3 and (x + y) % 3 == 0:
                    c = c * 0.55                                       # a crack across it
            img[y, x] = c


def basin(img, G, rng):
    bx, by, r = BASIN
    for y in range(by - r - 4, by + r + 6):
        for x in range(bx - r - 4, bx + r + 5):
            d = np.hypot(x - bx, (y - by) * 1.05)
            if d < r - 3:
                v = 0.5 - 0.35 * (1 - d / r) + 0.15 * G[y, x]
                img[y, x] = pick(TEAL, 0.6 + 2.0 * v)                  # dark still water
                if (y - x) % 11 == 0 and G[y, x] < 0.5 and d < r - 5:
                    img[y, x] = TEAL[4]
            elif d < r:
                up = y < by
                img[y, x] = pick(STONE, (3.4 if up else 2.2) - 0.8 * (x - bx) / r + 0.4 * G[y, x])   # the rim
            elif d < r + 2 and y > by:
                img[y, x] = pick(STONE, 1.0)                           # its outer face, in shade
            elif d < r + 4 and y > by:
                img[y, x] = img[y, x] * 0.7                            # its shadow on the tiles
    ol.Seerosen(bx - 7, by + 5, 6, 77).draw(img, G)
    ol.Seerosen(bx + 9, by - 6, 3, 78).draw(img, G)
    for j in range(by - 9, by + 1):                                    # the dry fountain: an iron stem, a bowl
        put(img, bx, j, pick(RUST, 2.8 - 0.1 * (j - by + 9)))
        put(img, bx + 1, j, RUST[1])
    for i in range(bx - 4, bx + 6):
        put(img, i, by - 10, pick(RUST, 3.6 - 0.5 * (i - bx + 4)))
        put(img, i, by - 9, RUST[0])


def bed(img, G, rng, x0, y0, x1, y1, things):
    """A raised bed: dark soil, a stone kerb on the aisle side and the front (lit top, darker face), all grown over."""
    aisle_right = x0 < W // 2
    for y in range(y0, y1):
        for x in range(x0, x1):
            img[y, x] = pick(SOIL, 0.6 + 1.6 * G[y, x])
    for x in range(x0, x1):                                            # the front kerb
        img[y1 - 3, x] = pick(STONE, 3.3 + 0.3 * G[y1 - 3, x])
        img[y1 - 2, x] = pick(STONE, 2.0)
        img[y1 - 1, x] = pick(STONE, 1.4)
        img[min(H - 1, y1), x] = img[min(H - 1, y1), x] * 0.7
    ex = x1 - 1 if aisle_right else x0
    for y in range(y0, y1 - 1):                                        # the kerb along the aisle
        img[y, ex] = pick(STONE, 2.9 if aisle_right else 2.4)
        img[y, ex + (-1 if aisle_right else 1)] = pick(STONE, 3.4)
    r = np.random.default_rng(x0 * 7 + y0)
    for _ in range(int((x1 - x0) * (y1 - y0) / 55)):                   # what grows in it, back to front
        x, y = int(r.integers(x0 + 3, x1 - 3)), int(r.integers(y0 + 6, y1 - 2))
        k = r.random()
        if k < 0.45:
            things.append(ow.Farn(x, y, int(r.integers(0, 9999)), int(r.integers(6, 11))))
        elif k < 0.6:
            things.append(o.Hortensie(x, y, int(r.integers(4, 7)), str(r.choice(['blau', 'lila', 'rosa'])),
                                      int(r.integers(0, 999))))
        else:
            things.append(Blattpflanze(x, y, int(r.integers(0, 9999)), r.uniform(0.7, 1.2)))
    for _ in range(int((y1 - y0) / 9)):                                # creepers spilling over the kerb
        y = int(r.integers(y0 + 4, y1 - 4))
        things.append(Ranke(ex, y, -1 if not aisle_right else 1, int(r.integers(0, 999))))


class Blattpflanze:
    """A big-leaved plant (a banana, an elephant ear): broad leaves on stalks fanning up from one crown."""
    def __init__(s, x, y, seed, size=1.0):
        s.x, s.y, s.seed, s.size = x, y, seed, size

    def box(s):
        r = int(14 * s.size)
        return (s.x - r, s.y - r - 4, s.x + r, s.y + 2)

    def draw(s, img, G):
        r = np.random.default_rng(s.seed)
        n = int(r.integers(4, 7))
        for k in range(n):
            a = -np.pi / 2 + r.uniform(-1.2, 1.2)
            L = (8 + 6 * r.random()) * s.size
            for t in np.linspace(0, 1, int(L * 1.5)):
                px, py = s.x + np.cos(a) * L * t, s.y + np.sin(a) * L * t * 0.8
                wdt = 2.6 * s.size * np.sin(np.pi * min(1, t * 1.15)) if t > 0.3 else 0.4
                for d in np.arange(-wdt, wdt + 0.1, 0.5):
                    qx, qy = px - np.sin(a) * d, py + np.cos(a) * d * 0.8
                    lit = 2.6 - 1.2 * (d / max(wdt, 0.5)) - 0.8 * (np.cos(a) > 0.3) + (0.8 if abs(d) < 0.3 else 0)
                    put(img, int(round(qx)), int(round(qy)), pick(LEAF + [hx('#6e8a48')], lit))


class Ranke:
    """A creeper hanging over a bed's kerb and running out across the floor."""
    def __init__(s, x, y, dirx, seed):
        s.x, s.y, s.dx, s.seed = x, y, dirx, seed

    def box(s):
        return (s.x - 14, s.y - 3, s.x + 14, s.y + 5)

    def draw(s, img, G):
        r = np.random.default_rng(s.seed)
        x, y = float(s.x), float(s.y)
        for k in range(int(r.integers(6, 14))):
            x += s.dx * r.uniform(0.6, 1.2)
            y += r.uniform(-0.4, 0.7)
            put(img, int(x), int(y), MOSS[2])
            if k % 2 == 0:
                put(img, int(x), int(y) - 1, MOSS[3 + (k % 4 == 0)])


class Palme:
    """A palm in a big clay pot: the pot's rim lit, fronds arching out all round."""
    def __init__(s, x, y, seed):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - 20, s.y - 30, s.x + 21, s.y + 3)

    def draw(s, img, G):
        x, y = s.x, s.y
        for j in range(y - 9, y + 1):                                  # the pot, narrowing to its foot
            hw = 6 - (j - (y - 9)) * 0.25
            for i in range(int(x - hw), int(x + hw) + 1):
                put(img, i, j, pick(TERRA, 3.4 - 2.4 * (i - x + hw) / (2 * hw) - (1.2 if j == y - 8 else 0)))
        for i in range(x - 6, x + 7):
            put(img, i, y - 9, pick(TERRA, 4.2 - 0.2 * (i - x + 6)))
            put(img, i, y + 1, img[min(img.shape[0] - 1, y + 1), i] * 0.6)
        r = np.random.default_rng(s.seed)
        cx, cy = x, y - 11
        for k in range(9):
            a = -np.pi / 2 + (k - 4) * 0.42 + r.uniform(-0.1, 0.1)
            L = r.uniform(14, 20)
            for t in np.linspace(0, 1, 40):
                px = cx + np.cos(a) * L * t
                py = cy + np.sin(a) * L * t * 0.7 + 9 * t * t               # arching down
                put(img, int(round(px)), int(round(py)), pick(LEAF, 3.2 - 1.5 * t))
                if 0.2 < t < 0.95 and int(t * 40) % 2 == 0:              # leaflets either side
                    for sd in (-1, 1):
                        put(img, int(round(px - np.sin(a) * 2 * sd)), int(round(py + 1 + (sd > 0))),
                            pick(LEAF, 2.4 - t))


class Bank:
    """The potting bench against the right glass wall: weathered top, pots on it, a sack, a trowel."""
    def box(s):
        x0, y0, x1, y1 = BENCH
        return (x0 - 2, y0 - 10, x1 + 2, y1 + 4)

    def draw(s, img, G):
        x0, y0, x1, y1 = BENCH
        for j in range(y0, y0 + 7):                                    # the top
            for i in range(x0, x1):
                put(img, i, j, o.plank_px(i, j, x0, y0, 3.2 - 0.8 * (i - x0) / (x1 - x0), 5) if j > y0 else WOOD[4])
        for j in range(y0 + 7, y0 + 10):
            for i in range(x0, x1):
                put(img, i, j, WOOD[1] if j == y0 + 7 else WOOD[0])    # its front edge
        for i in (x0 + 1, x1 - 3):
            for j in range(y0 + 10, y1):
                put(img, i, j, WOOD[2])
                put(img, i + 1, j, WOOD[0])
        for i in range(x0, x1):
            put(img, i, y1, img[y1, i] * 0.6)
        for k, (px, sz) in enumerate(((x0 + 5, 3), (x0 + 11, 2), (x0 + 15, 2), (x0 + 26, 3))):   # clay pots
            for j in range(-sz - 1, 1):
                for i in range(-sz, sz + 1):
                    put(img, px + i, y0 + 4 + j, pick(TERRA, 3.2 - 1.2 * (i + sz) / (2 * sz) - (1.5 if j == -sz else 0)))
            if k == 0:
                for d in (-1, 0, 1):
                    put(img, px + d, y0 + 4 - sz - 2, MOSS[3])          # a seedling, gone leggy
        for j in range(y0 - 3, y0 + 5):                                # the sack, slumped
            for i in range(x1 - 10, x1 - 3):
                if (i - (x1 - 6.5)) ** 2 / 12 + (j - (y0 + 1)) ** 2 / 16 < 1:
                    put(img, i, j, pick([hx('#4a3e2c'), hx('#6b5a3e'), hx('#8a7650')], 2.2 - 0.4 * (i - x1 + 10)))
        for i in range(x0 + 19, x0 + 23):
            put(img, i, y0 + 3, IRON_ if i < x0 + 21 else WOOD[3])     # the trowel


IRON_ = hx('#55585e')


class Giesskanne:
    def box(s):
        return (104, 270, 116, 282)

    def draw(s, img, G):
        x, y = 108, 280
        for j in range(y - 6, y + 1):
            for i in range(x - 3, x + 4):
                put(img, i, j, pick([hx('#2f3a3c'), hx('#4e5f60'), hx('#7a8c8a')], 2.4 - 0.5 * (i - x + 3)))
        for k in range(5):
            put(img, x + 4 + k, y - 4 - k // 2, hx('#4e5f60'))            # the spout
        for i in range(x - 2, x + 3):
            put(img, i, y - 8, hx('#2f3a3c'))                           # the handle
        put(img, x - 3, y - 7, hx('#2f3a3c'))
        put(img, x + 3, y - 7, hx('#2f3a3c'))


class Stuhl:
    """A wooden chair turned to the basin."""
    def box(s):
        return (124, 150, 138, 168)

    def draw(s, img, G):
        x, y = 128, 164
        for j in range(y - 13, y - 4):                                  # the back
            for i in (x, x + 7):
                put(img, i, j, WOOD[3] if i == x else WOOD[2])
        for i in range(x, x + 8):
            put(img, i, y - 13, WOOD[4])
            put(img, i, y - 10, WOOD[3])
        for j in range(y - 5, y - 2):                                   # the seat
            for i in range(x, x + 8):
                put(img, i, j, WOOD[4] if j == y - 5 else WOOD[3])
        for i in (x, x + 7):
            for j in range(y - 2, y + 1):
                put(img, i, j, WOOD[1])
        for i in range(x, x + 9):
            put(img, i, y + 1, img[y + 1, i] * 0.65)


def glass_walls(img, G, rng):
    """Back wall face on, side walls at the angle, the bottom wall with the door: iron, green glass, the dark garden
    behind, a stone parapet under it all. One pane gone in the right wall, its shards on the floor."""
    leaves = fbm(rng, 2.2)
    yy, xx = np.mgrid[0:H, 0:W]

    def pane(y, x, roof=0.0):
        leaf = leaves[y, x] > 0.1 + roof
        base = pick(INSIDE, 1.6 + 1.2 * leaves[y, x]) if leaf else pick(TEAL, 0.6 + roof)
        glint = (x - y) % 13 in (0, 1)
        glass = pick(TEAL, 1.8 + roof + (1.1 if glint else 0))
        return base * 0.6 + glass * 0.4

    for y in range(0, BACK):                                           # the back wall
        for x in range(W):
            bar = x % 14 in (0, 1) or y in (20, 21, 42, 43) or y < 3
            img[y, x] = pick(RUST, 2.6 - 1.2 * x / W) if bar else pane(y, x, 0.3 * (y < 20))
    for y in range(BACK - 6, BACK + 2):                                # its parapet
        for x in range(W):
            img[y, x] = pick(STONE, 3.4 if y == BACK - 6 else 2.4 - 0.15 * (y - BACK + 6) + 0.3 * G[y, x])
    gone = range(196, 218)
    for y in range(BACK, H):                                           # the side walls
        for x in list(range(0, WALL_L)) + list(range(WALL_R, W)):
            left = x < WALL_L
            inner = (WALL_L - 1 - x) if left else (x - WALL_R)
            if inner < 4:                                              # the parapet's top, along the floor
                img[y, x] = pick(STONE, (3.3 if inner == 0 else 2.6 - 0.3 * inner) + 0.3 * G[y, x])
            elif (y - BACK) % 26 in (0, 1) or inner in (4, 5):
                img[y, x] = pick(RUST, 2.4 if left else 1.6)            # iron
            elif not left and y in gone:
                img[y, x] = INSIDE[1] if leaves[y, x] > -0.2 else hx('#0f1412')   # no glass: the leaves come in
            else:
                img[y, x] = pane(y, x)
    for y in range(H - 12, H):                                         # the bottom wall either side of the door
        for x in range(WALL_L, W - WALL_L):
            if DOOR[0] <= x < DOOR[1]:
                continue
            top = y == H - 12
            img[y, x] = pick(STONE, 3.4 if top else 2.0 + 0.4 * G[y, x]) if y < H - 8 else \
                (pick(RUST, 2.2) if (x % 14 in (0, 1)) else pick(TEAL, 1.4 + (x - y) % 13 // 12))
    for y in range(H - 14, H):                                         # the door's iron posts
        for x in (DOOR[0] - 2, DOOR[0] - 1, DOOR[1], DOOR[1] + 1):
            img[y, x] = pick(RUST, 3.0 if x in (DOOR[0] - 2, DOOR[1]) else 1.4)
    for k in range(9):                                                 # shards of the gone pane
        x, y = int(rng.integers(WALL_R - 14, WALL_R - 2)), int(rng.integers(200, 226))
        img[y, x] = TEAL[5] if k % 2 else TEAL[3]


def moon(img, floor):
    """Moonlight through the roof: pale panes on the floor, the iron's shadow between them."""
    yy, xx = np.mgrid[0:H, 0:W]
    u = (xx + 0.35 * yy) % 28
    v = yy % 30
    lit = floor & (u > 3) & (v > 3)
    img[lit] = img[lit] * 1.08 + np.array([6, 9, 14.0])
    img[floor & ~lit] *= 0.82


def lantern(img):
    """An iron lantern on a hook by the door, its glass burning (bright enough to glow by itself)."""
    x, y = LANTERN
    for j in range(y - 2, y + 18):                                     # the post
        put(img, x + 6, j, RUST[2])
        put(img, x + 7, j, RUST[0])
    for i in range(x, x + 7):
        put(img, i, y - 2, RUST[2])                                    # the hook
    for j in range(y, y + 7):
        for i in range(x - 2, x + 3):
            edge = i in (x - 2, x + 2) or j in (y, y + 6)
            put(img, i, j, RUST[1] if edge else (hx('#fde7a0') if j < y + 4 else hx('#f2b44a')))
    put(img, x, y - 1, RUST[3])
    for i in range(x - 3, x + 9):
        put(img, i, y + 19, img[min(H - 1, y + 19), i] * 0.65)


def render(with_monk=False):
    """-> (picture before the mood, walkable mask, the lantern's light)."""
    rng = np.random.default_rng(91)
    G = rng.random((H, W))
    yy, xx = np.mgrid[0:H, 0:W]
    img = floor_stone(rng)
    floor = (xx >= WALL_L) & (xx < WALL_R) & (yy >= BACK + 2)
    aisle(img, G, rng)
    things = []
    for b in BEDS:
        bed(img, G, rng, *b, things)
    basin(img, G, rng)
    moon(img, floor & ~np.zeros_like(floor))
    for _ in range(90):                                                # fallen leaves
        x, y = int(rng.integers(WALL_L, WALL_R)), int(rng.integers(BACK + 4, H - 14))
        img[y, x] = pick([hx('#5a3a1c'), hx('#8a5a26'), hx('#b08a3a')], 1 + 2 * G[y, x])
    for k in range(18):                                                # a pot knocked over, its soil spilled
        put(img, 82 + k // 3, 300 + (k % 3), pick(SOIL, 1.4 + G[300, 82 + k // 3]))
    things += [Palme(46, 168, 5), Palme(136, 304, 6), Bank(), Giesskanne(), Stuhl()]
    for t in sorted(things, key=lambda t: t.box()[3]):
        t.draw(img, G)
    glass_walls(img, G, rng)
    for k in range(8):                                                 # the fallen pot itself
        put(img, 79 + k, 297 + (k > 3), pick(TERRA, 3.0 - 0.3 * k))
    lantern(img)
    if with_monk:
        sheet = np.array(Image.open(os.path.join(HERE, '..', '..', '..', 'assets', 'char', 'wanderer.png')).convert('RGBA'))
        f = sheet[16:32, 0:12].astype(float)
        x0, y0 = 84, 360
        a = f[..., 3:] / 255.0
        img[y0:y0 + 16, x0:x0 + 12] = img[y0:y0 + 16, x0:x0 + 12] * (1 - a) + f[..., :3] * a
    img *= 0.8                                                         # the inside is darker than the night outside
    light = {'x': LANTERN[0] + 0.5, 'y': LANTERN[1] + 3.5, 'r': 150.0, 'k': 1.4}
    return np.clip(img, 0, 255), walk_mask(), light


def walk_mask():
    yy, xx = np.mgrid[0:H, 0:W]
    m = (xx >= WALL_L + 1) & (xx < WALL_R - 1) & (yy >= BACK + 4) & (yy < H - 12)
    m |= (xx >= DOOR[0]) & (xx < DOOR[1]) & (yy >= H - 14)
    for x0, y0, x1, y1 in BEDS:
        m[y0 - 2:y1 + 1, x0 - 1:x1 + 1] = False
    bx, by, r = BASIN
    m &= np.hypot(xx - bx, (yy - by) * 1.05) > r + 2
    for x0, y0, x1, y1 in (BENCH, (38, 158, 55, 170), (128, 294, 145, 306), (104, 272, 117, 282), (124, 152, 138, 166),
                           (LANTERN[0] - 3, LANTERN[1] - 2, LANTERN[0] + 9, LANTERN[1] + 20)):
        m[y0:y1, x0:x1] = False
    c = m.reshape(H // 2, 2, W // 2, 2).all(axis=(1, 3))
    lab, _ = ndi.label(c)
    out = lab[-1, DOOR[0] // 2:DOOR[1] // 2]
    keep = lab == np.bincount(out[out > 0]).argmax()
    return m & keep.repeat(2, 0).repeat(2, 1)


def main(out, with_monk=False):
    sys.path.insert(0, os.path.join(HERE, '..', 'north'))
    import cave_inside as C
    img, walk, light = render(with_monk)
    C.H, C.W = H, W
    Image.fromarray(C.mood_inside(img, light)).save(out)


if __name__ == '__main__':
    main(sys.argv[1], len(sys.argv) > 2)
