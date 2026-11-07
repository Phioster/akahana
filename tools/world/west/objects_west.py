"""Things of the abandoned village in the west (Wasure-zato, plan step 61): the empty houses, the roofed well, the
overgrown gardens. Same interface as the south's things: box(), draw(img, G). (x, y) is always the foot.

Philip (2026-11-07): the houses abandoned as in docs/west_vorlage/verlassen.png (moss, fallen-in roofs, broken
windows, creepers), the gardens wild but lovely, no lit windows."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
from objects_lake import hx, put  # noqa: E402
import objects_lake as ol  # noqa: E402

WOOD = [hx(c) for c in ['#221c18', '#342b25', '#4b3f36', '#65574a', '#82725f']]       # old timber, greyed brown
PAPER = [hx(c) for c in ['#6a665d', '#8c877b', '#aaa496']]                            # shoji paper gone grey
HOLE = hx('#0c0d0f')
TILE = [hx(c) for c in ['#1d1f24', '#2a2d33', '#3a3e46', '#4f545d', '#676c75']]        # kawara, dark .. lit
THATCH = [hx(c) for c in ['#2d281f', '#41392b', '#5a4f3a', '#74674b', '#8f805d']]
ROOFS = {                                             # each house its own roof: tiles weather apart, thatch greys
    'kawara': [TILE,
               [hx(c) for c in ['#24201e', '#352f2b', '#4a423c', '#625850', '#7c7168']],   # brown-grey tiles
               [hx(c) for c in ['#1f2429', '#2c343b', '#3e4952', '#56636d', '#728089']]],  # blue, weathered pale
    'kaya': [THATCH,
             [hx(c) for c in ['#2a2722', '#3d3830', '#555046', '#6e695c', '#8a8574']],     # grey old thatch
             [hx(c) for c in ['#33291c', '#4c3d27', '#6a5636', '#8a7347', '#a68e5c']]],    # still golden
}
MOSS = [hx(c) for c in ['#27321f', '#36462a', '#4b5f37', '#647a48', '#82975c']]
STONE = [hx(c) for c in ['#33353a', '#4a4d53', '#666a70', '#868a8f', '#a4a7aa']]
SOIL = [hx(c) for c in ['#231e19', '#332b23', '#45392d']]
BAMBOO = [hx(c) for c in ['#3e3d2a', '#5a583c', '#7a7651', '#9a9568']]
HYDRANGEA = {
    'blau': [hx(c) for c in ['#33405f', '#4d5f8c', '#7286b6', '#9eaed4']],
    'lila': [hx(c) for c in ['#423250', '#634a78', '#8a6aa2', '#ae92c4']],
    'rosa': [hx(c) for c in ['#5a3444', '#84506a', '#ad7690', '#cfa0b4']],
}
LEAF = [hx(c) for c in ['#1c2618', '#2a3822', '#3c4f2e', '#52683c']]
FRUIT = [hx(c) for c in ['#7a2e1e', '#a8442a', '#cc6a3a']]
CLOTH = [hx(c) for c in ['#4e4a46', '#6e6860', '#8e877c']]


def pick(P, v):
    return P[int(np.clip(v, 0, len(P) - 1e-6))]


def g_at(G, i, j):
    return G[j % G.shape[0], i % G.shape[1]]


def shade_ground(img, G, x0, x1, y0, y1, k=0.7):
    """A soft shadow on the ground to the lower right (light from the upper left), dithered at its rim."""
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    for j in range(int(y0), int(y1)):
        for i in range(int(x0), int(x1)):
            e = ((i - cx) / ((x1 - x0) / 2)) ** 2 + ((j - cy) / ((y1 - y0) / 2)) ** 2
            if e < 1 and (e < 0.6 or g_at(G, i, j) < 0.5) and 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
                img[j, i] = img[j, i] * k


class Minka:
    """An empty farmhouse seen from above at an angle: a veranda of planks, the front wall of posts with shoji and
    plank panels (paper torn, panes gone dark), a deep roof of tiles or thatch with moss on it, fallen in here and
    there so the rafters show, creepers hanging from the eaves. About w + 10 wide, wall + roof + 6 high."""
    def __init__(s, x, y, w=44, wall=11, roof=17, seed=1, kind='kawara', ruin=0.6, pal=0):
        s.x, s.y, s.w, s.wall, s.roof, s.seed, s.kind, s.ruin = x, y, w, wall, roof, seed, kind, ruin
        s.pal = ROOFS[kind][pal % len(ROOFS[kind])]
        s.mossy = 0.5 + np.random.default_rng(seed + 40).random()     # 0.5 barely .. 1.5 grown over

    def box(s):
        return (s.x - s.w // 2 - 8, s.y - s.wall - s.roof - 8, s.x + s.w // 2 + 14, s.y + 6)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        w, x0, y = s.w, s.x - s.w // 2, s.y
        x1 = x0 + w
        shade_ground(img, G, x0 - 2, x1 + 12, y - 4, y + 6, 0.62)
        # veranda: two rows of planks along the front, a stone step at the door
        for j in (y - 1, y):
            for i in range(x0 - 2, x1 + 2):
                if rng.random() < 0.08 * s.ruin:
                    continue                                          # a plank gone
                lit = 3.2 - 2.0 * (i - x0) / w - 0.8 * (j == y) + 0.3 * ((i // 5) % 2) + rng.normal(0, 0.2)
                put(img, i, j, pick(WOOD, lit))
        door = x0 + w // 2 - 3 + int(rng.integers(-6, 7))
        for i in range(door - 1, door + 8):
            put(img, i, y + 1, pick(STONE, 3.4 - 2.0 * (i - door) / 8))
            put(img, i, y + 2, STONE[1])
        top = y - 1 - s.wall
        # the front wall: posts, panels between them
        posts = sorted(set([x0, x1 - 1] + [x0 + k * w // 4 for k in (1, 2, 3)]))
        for k in range(len(posts) - 1):
            a, b = posts[k] + 2, posts[k + 1]
            panel = 'door' if a <= door + 3 < b else ('shoji' if rng.random() < 0.6 else 'planks')
            for j in range(top, y - 1):
                for i in range(a, b):
                    lit = 2.6 - 1.6 * (i - x0) / w + rng.normal(0, 0.15)
                    if panel == 'planks':
                        c = pick(WOOD, lit + (-1.2 if (i - a) % 4 == 3 else 0.3))
                    elif panel == 'door':
                        open_ = i < a + (b - a) * (0.35 + 0.4 * s.ruin)  # slid half open: dark inside
                        c = HOLE if open_ and j > top + 1 else pick(WOOD, lit - 0.6)
                    else:                                             # shoji: a frame grid, paper in the cells
                        grid = (i - a) % 3 == 0 or (j - top) % 3 == 0
                        if grid:
                            c = pick(WOOD, lit - 0.4)
                        else:
                            cell = ((i - a) // 3, (j - top) // 3)
                            torn = np.random.default_rng(s.seed * 97 + cell[0] * 13 + cell[1]).random() < 0.55 * s.ruin
                            c = HOLE if torn else pick(PAPER, lit - 0.2)
                    put(img, i, j, c)
            for j in range(top, y - 1):                               # the post itself
                put(img, posts[k], j, pick(WOOD, 3.0 - 1.6 * (posts[k] - x0) / w))
                put(img, posts[k] + 1, j, pick(WOOD, 1.6 - 1.2 * (posts[k] - x0) / w))
        for j in range(top, y - 1):
            put(img, x1 - 1, j, WOOD[0])
            put(img, x1, j, WOOD[0])
        for i in range(x0 - 1, x1 + 2):                               # the beam under the eaves
            put(img, i, top - 1, WOOD[1])
        # the roof from above: the front slope rising from the eave to the ridge, a little wider at the eave
        ov = 5
        sag = s.ruin * 2.2
        holes = []                                                    # never a symmetric pair: two read as eyes
        for k in range(1 if s.ruin < 0.75 else 2):
            u = rng.uniform(0.15, 0.4) if k == 0 else rng.uniform(0.62, 0.85)
            if rng.random() < 0.5:
                u = 1 - u
            holes.append((x0 + u * w, top - 3 - rng.uniform(0.3, 0.75) * s.roof,
                          rng.uniform(3.5, 6.5) * (0.6 if k else 1), rng.uniform(1.6, 3.0) * (0.7 if k else 1),
                          rng.uniform(0, 6.28)))
        moss = np.random.default_rng(s.seed + 5)
        mn = moss.normal(0, 1, (s.roof + 10, w + 2 * ov + 10))
        from scipy import ndimage as ndi
        mn = ndi.gaussian_filter(mn, 1.6)
        mn /= mn.std() + 1e-9
        eave = top - 2
        for k in range(s.roof):
            j = eave - k
            hw = w / 2 + ov - k * (0.18 if s.kind == 'kawara' else 0.35)
            cx = s.x
            dip = sag * np.sin(np.pi * (np.arange(-1, 2) + 1) / 2)       # unused, keeps the line below readable
            for i in range(int(cx - hw), int(cx + hw) + 1):
                u = (i - (cx - hw)) / (2 * hw)
                drop = int(round(sag * np.sin(np.pi * u) * (k / s.roof)))  # the ridge sags in the middle
                jj = j + drop
                lit = 3.3 - 2.0 * u - 0.6 * k / s.roof + rng.normal(0, 0.15)
                if s.kind == 'kawara':
                    ch = (i - int(cx - hw)) % 3                         # the tile channels: round, lit, shaded
                    lit += (0.6, 0.0, -0.9)[ch]
                    if k % 3 == 0:
                        lit -= 0.5                                      # the courses
                    c = pick(s.pal, lit)
                else:
                    lit += 0.5 * ((i * 7 + k * 3) % 5 == 0) - 0.4 * ((i + k * 2) % 4 == 0)
                    c = pick(s.pal, lit)
                mv = mn[min(k, mn.shape[0] - 1), min(int(i - cx + w / 2 + ov), mn.shape[1] - 1)]
                if mv > 1.5 - 1.5 * s.ruin * s.mossy - 0.4 * (k > s.roof * 0.6):
                    c = pick(MOSS, lit * 0.9 + 0.3)
                for hx_, hy_, rx, ry, ph in holes:                      # fallen in: rafters over the dark inside
                    ang = np.arctan2(jj - hy_, i - hx_)
                    rr = 1 + 0.35 * np.sin(3 * ang + ph) + 0.2 * np.sin(5 * ang + 2 * ph)   # ragged, not round
                    e = ((i - hx_) / rx) ** 2 + ((jj - hy_) / ry) ** 2
                    if e < rr * (0.85 + 0.3 * g_at(G, i * 5, jj)):
                        rafter = (i - int(hx_)) % 4 == 0                  # rafters run from eave to ridge
                        c = pick(WOOD, 2.2 - u) if rafter else (WOOD[0] if g_at(G, i, jj * 3) < 0.3 else HOLE)
                    elif e < rr * 1.5 and g_at(G, i * 3, jj) < 0.35:
                        c = pick(s.pal, lit - 1.2)   # loose, slipped tiles round it
                if k == 0:
                    c = pick(s.pal, 1.2 - u)   # the eave's dark edge
                put(img, i, jj, c)
            if k == 0:
                for i in range(int(cx - hw), int(cx + hw) + 1):           # the eave's underside in shadow on the wall
                    put(img, i, eave + 1, WOOD[0])
        # the ridge: a heavier line with raised ends
        rj = eave - s.roof
        hw = w / 2 + ov - s.roof * (0.18 if s.kind == 'kawara' else 0.35)
        for i in range(int(s.x - hw), int(s.x + hw) + 1):
            u = (i - (s.x - hw)) / (2 * hw)
            jj = rj + int(round(sag * np.sin(np.pi * u)))
            put(img, i, jj, pick(s.pal, 3.6 - 2.2 * u))
            put(img, i, jj - 1, pick(s.pal, 2.4 - 1.8 * u))
        for e, lit in ((int(s.x - hw), 3.6), (int(s.x + hw), 1.4)):
            for d in range(1, 3):
                put(img, e, rj - 1 - d, pick(s.pal, lit))
        # creepers from the eave down the wall, mostly at the corners
        for _ in range(int(3 + 6 * s.ruin)):
            i = int(rng.choice([rng.integers(x0 - 3, x0 + 8), rng.integers(x1 - 8, x1 + 3), rng.integers(x0, x1)],
                               p=[0.4, 0.4, 0.2]) if False else 0)
            r = rng.random()
            i = int(rng.integers(x0 - 3, x0 + 8)) if r < 0.4 else int(rng.integers(x1 - 8, x1 + 3)) if r < 0.8 \
                else int(rng.integers(x0, x1))
            n = int(rng.integers(2, s.wall + 2))
            for d in range(n):
                put(img, i + (d % 4 == 3), eave + 1 + d, pick(MOSS, 3.2 - 2.2 * d / n + rng.normal(0, 0.3)))
                if rng.random() < 0.3:
                    put(img, i + 1, eave + 1 + d, MOSS[1])


class Brunnen:
    """The roofed well in the middle of the village: a round wall of hewn stones, dark water, two posts carrying a
    small tiled roof, a wooden bucket on its rope."""
    def __init__(s, x, y, seed=3):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - 12, s.y - 26, s.x + 14, s.y + 4)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        x, y = s.x, s.y
        shade_ground(img, G, x - 6, x + 12, y - 2, y + 4, 0.65)
        for j in range(-5, 1):                                        # the round wall, block courses
            hw = 7 - (j == 0)
            for i in range(-hw, hw + 1):
                seam = (i + (j % 2) * 2) % 4 == 0 or j == -3
                lit = 3.4 - 2.4 * (i + hw) / (2 * hw) - (0.9 if seam else 0) + rng.normal(0, 0.15)
                put(img, x + i, y + j, pick(STONE, lit))
        for i in range(-6, 7):                                        # the opening seen from above
            for j in range(-8, -5):
                e = (i / 6.5) ** 2 + ((j + 6.5) / 1.8) ** 2
                if e < 1:
                    put(img, x + i, y + j, hx('#141b20') if e < 0.55 else pick(STONE, 3.2 - 0.25 * i))
        for j in range(-20, -5):                                      # posts
            put(img, x - 8, y + j, WOOD[3])
            put(img, x - 7, y + j, WOOD[1])
            put(img, x + 8, y + j, WOOD[2])
            put(img, x + 9, y + j, WOOD[0])
        for i in range(-8, 10):
            put(img, x + i, y - 18, WOOD[2] if i < 2 else WOOD[1])   # the cross beam with its roller
        for j in range(-17, -11):
            put(img, x + 1, y + j, hx('#8a7c62'))                     # the rope
        for j in range(-11, -8):                                      # the bucket
            for i in range(-1, 3):
                put(img, x + i, y + j, WOOD[3] if i < 1 else WOOD[1])
        put(img, x - 1, y - 11, WOOD[4])
        for k in range(6):                                            # the little roof
            hw = 12 - k * 1.3
            for i in range(int(-hw), int(hw) + 1):
                u = (i + hw) / (2 * hw)
                lit = 3.2 - 2.0 * u + (0.5, -0.7)[(i + 20) % 2] - 0.3 * k + rng.normal(0, 0.15)
                c = pick(TILE, lit)
                if g_at(G, x + i, y - 21 - k) > 0.72 - 0.1 * k:
                    c = pick(MOSS, lit * 0.8 + 0.4)
                put(img, x + i, y - 20 - k - (1 if abs(i) > hw - 2 and k < 2 else 0), c)


class Hortensie:
    """A hydrangea bush gone wild: dark leaves, round flower heads lit at the upper left."""
    def __init__(s, x, y, r=6, hue='blau', seed=4):
        s.x, s.y, s.r, s.hue, s.seed = x, y, r, hue, seed

    def box(s):
        return (s.x - s.r - 2, s.y - int(s.r * 1.6) - 3, s.x + s.r + 4, s.y + 3)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        r = s.r
        cx, cy = s.x, s.y - r * 0.75
        shade_ground(img, G, s.x - r + 1, s.x + r + 5, s.y - 2, s.y + 3, 0.7)
        for j in range(int(cy - r), s.y + 1):
            for i in range(s.x - r, s.x + r + 1):
                e = ((i - cx) / r) ** 2 + ((j - cy) / (r * 0.85)) ** 2
                if e < 1 and g_at(G, i * 3, j) < 1.3 - 0.4 * e:
                    put(img, i, j, pick(LEAF, 3.4 - 1.6 * (i - cx + j - cy) / r - 1.2 * e + rng.normal(0, 0.3)))
        P = HYDRANGEA[s.hue]
        heads = [(cx + rng.uniform(-0.75, 0.75) * r, cy + rng.uniform(-0.8, 0.5) * r, rng.uniform(1.6, 2.4))
                 for _ in range(int(r * 0.9) + 2)]
        for hx_, hy_, hr in sorted(heads, key=lambda t: t[1]):
            for j in range(int(hy_ - hr), int(hy_ + hr) + 1):
                for i in range(int(hx_ - hr), int(hx_ + hr) + 1):
                    d = ((i - hx_) ** 2 + (j - hy_) ** 2) / (hr * hr)
                    if d < 1:
                        put(img, i, j, pick(P, 3.5 - 1.8 * ((i - hx_) + (j - hy_)) / hr - 1.4 * d
                                            + 0.6 * (g_at(G, i, j) - 0.5)))


class Beet:
    """An old garden bed gone wild, flat on the ground: soft furrows of dark earth with ragged ends (no frame: a hard
    outline read as a crate), what still comes up in them (leafy heads, a few pale ones, beans on a cane), weeds over
    the rims."""
    def __init__(s, x, y, w=16, rows=4, seed=6):
        s.x, s.y, s.w, s.rows, s.seed = x, y, w, rows, seed

    def box(s):
        return (s.x - 3, s.y - s.rows * 4 - 8, s.x + s.w + 4, s.y + 2)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        for r in range(s.rows):
            j0 = s.y - r * 4
            a = s.x + int(rng.integers(-2, 3))
            b = s.x + s.w + int(rng.integers(-3, 2))
            for i in range(a, b):                                       # the furrow: a soft strip, frayed at its ends
                edge = min(i - a, b - 1 - i)
                if edge < 2 and g_at(G, i, j0) < 0.5:
                    continue
                put(img, i, j0, img[j0, i] * 0.2 + SOIL[1] * 0.8 if 0 <= j0 < img.shape[0] and 0 <= i < img.shape[1] else SOIL[1])
                if g_at(G, i * 3, j0) < 0.7:
                    put(img, i, j0 - 1, img[j0 - 1, i] * 0.35 + SOIL[2] * 0.65 if 0 <= j0 - 1 < img.shape[0] and 0 <= i < img.shape[1] else SOIL[2])
            crop = rng.choice(['kohl', 'kraut', 'bohne'], p=[0.45, 0.4, 0.15])
            for i in range(a + 1, b - 1, int(rng.integers(3, 5))):
                if rng.random() < 0.3:
                    continue                                            # gaps where nothing came up
                if crop == 'bohne':                                     # a cane with a climbing bean
                    for d in range(7):
                        put(img, i, j0 - 1 - d, BAMBOO[2] if d < 6 else BAMBOO[3])
                        if d > 1 and (d + i) % 2 == 0:
                            put(img, i + 1 - 2 * (d % 4 == 0), j0 - 1 - d, pick(LEAF, 2.5 + rng.normal(0, 0.4)))
                    continue
                pale = crop == 'kohl' and rng.random() < 0.4
                P = MOSS if pale else LEAF
                for (u, v, k) in ((0, -3, 3.4), (-1, -2, 3.0), (1, -2, 2.0), (0, -2, 2.6), (-1, -1, 2.2), (1, -1, 1.2),
                                  (0, -1, 1.8), (2, -1, 1.0), (-2, -1, 1.8)):
                    if crop == 'kraut' and abs(u) == 2:
                        continue
                    put(img, i + u, j0 + v, pick(P, k + (0.8 if pale else 0) + rng.normal(0, 0.3)))
        for _ in range(s.w):                                            # weeds and grass over the rims
            i = s.x + int(rng.integers(-3, s.w + 3))
            j = s.y - int(rng.integers(-1, s.rows * 4 + 2))
            for d in range(int(rng.integers(1, 4))):
                put(img, i + (d == 2), j - d, MOSS[1 + min(d, 2)])


class Bambuszaun:
    """A low fence of bamboo canes along a line: canes close together, two rails, gaps where canes fell, a few
    leaning. pts = [(x, y), ...] along its foot."""
    def __init__(s, pts, h=6, seed=7, ruin=0.5):
        s.pts, s.h, s.seed, s.ruin = pts, h, seed, ruin

    def box(s):
        xs, ys = [p[0] for p in s.pts], [p[1] for p in s.pts]
        return (min(xs) - 2, min(ys) - s.h - 2, max(xs) + 3, max(ys) + 1)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        for (ax, ay), (bx, by) in zip(s.pts, s.pts[1:]):
            n = int(max(abs(bx - ax), abs(by - ay)))
            for k in range(0, n, 2):
                x = int(round(ax + (bx - ax) * k / n))
                y = int(round(ay + (by - ay) * k / n))
                if rng.random() < 0.18 * s.ruin:
                    continue
                lean = int(rng.random() < 0.12 * s.ruin) * int(rng.choice([-1, 1]))
                h = s.h - int(rng.integers(0, 2))
                for d in range(h):
                    put(img, x + (lean if d > h // 2 else 0), y - d, pick(BAMBOO, 3.2 - 1.4 * (d % 3 == 2) - 0.8 * (lean != 0)))
                put(img, x + 1, y, BAMBOO[0])
            for k in range(n):
                x = int(round(ax + (bx - ax) * k / n))
                y = int(round(ay + (by - ay) * k / n))
                for r in (2, s.h - 2):                                 # the rails
                    if rng.random() > 0.1 * s.ruin:
                        put(img, x, y - r, BAMBOO[1])


class Steinmauer:
    """A low dry-stone garden wall along a line: two courses of rounded stones, moss on the top course."""
    def __init__(s, pts, seed=8):
        s.pts, s.seed = pts, seed

    def box(s):
        xs, ys = [p[0] for p in s.pts], [p[1] for p in s.pts]
        return (min(xs) - 3, min(ys) - 6, max(xs) + 4, max(ys) + 2)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        for (ax, ay), (bx, by) in zip(s.pts, s.pts[1:]):
            n = int(max(abs(bx - ax), abs(by - ay), 1))
            k = 0
            while k < n:
                sw = int(rng.integers(3, 5))
                x = int(round(ax + (bx - ax) * k / n))
                y = int(round(ay + (by - ay) * k / n))
                for course in (0, 1):
                    off = 2 * course
                    for i in range(sw):
                        for d in range(2):
                            j = y - course * 2 - d
                            lit = 3.6 - 1.2 * (i / sw) - 1.0 * (d == 0) + 0.4 * course + rng.normal(0, 0.2)
                            c = pick(STONE, lit)
                            if course == 1 and d == 1 and g_at(G, x + i, j) < 0.45:
                                c = pick(MOSS, lit - 0.6)
                            put(img, x + i + off - 1, j, c)
                    put(img, x + sw + off - 1, y - course * 2, STONE[0])    # the joints
                k += sw
            for i in range(n):                                          # its shadow
                x = int(round(ax + (bx - ax) * i / n))
                y = int(round(ay + (by - ay) * i / n))
                if 0 <= y + 1 < img.shape[0] and 0 <= x < img.shape[1]:
                    img[y + 1, x] = img[y + 1, x] * 0.72


class Obstbaum:
    """A small fruit tree (the south's broadleaf, smaller) still bearing: red-orange fruit among the leaves."""
    def __init__(s, x, y, seed=9, size=0.55):
        s.t = ol.Laubbaum(x, y, seed=seed, size=size)
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return s.t.box()

    def draw(s, img, G):
        before = img.copy()
        s.t.draw(img, G)
        x0, y0, x1, y1 = s.t.box()
        rng = np.random.default_rng(s.seed + 1)
        y0, x0 = max(0, y0), max(0, x0)
        sub = np.abs(img[y0:y1, x0:x1] - before[y0:y1, x0:x1]).sum(-1) > 1
        ys, xs = np.where(sub[:-12])
        for k in rng.choice(len(ys), size=min(len(ys), 14), replace=False) if len(ys) else []:
            i, j = xs[k] + x0, ys[k] + y0
            put(img, i, j, FRUIT[1])
            put(img, i - 1, j, FRUIT[2])
            put(img, i, j + 1, FRUIT[0])


class Waescheleine:
    """Two posts and a sagging line with a few faded rags still on it."""
    def __init__(s, x, y, w=16, seed=10):
        s.x, s.y, s.w, s.seed = x, y, w, seed

    def box(s):
        return (s.x - 1, s.y - 12, s.x + s.w + 2, s.y + 1)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        for d in range(11):
            put(img, s.x, s.y - d, WOOD[3])
            put(img, s.x + s.w, s.y - d, WOOD[2])
        for i in range(s.w + 1):
            put(img, s.x + i, s.y - 10 + int(round(1.4 * np.sin(np.pi * i / s.w))), WOOD[1])
        for k in range(2):
            a = int(s.w * (0.25 + 0.4 * k))
            cw, ch = int(rng.integers(3, 5)), int(rng.integers(3, 6))
            for i in range(cw):
                top = s.y - 10 + int(round(1.4 * np.sin(np.pi * (a + i) / s.w))) + 1
                for j in range(ch - (i == cw - 1 and k == 1)):
                    put(img, s.x + a + i, top + j, pick(CLOTH, 2.6 - 1.4 * i / cw - 0.3 * j))


class Korb:
    """A forgotten woven basket."""
    def __init__(s, x, y):
        s.x, s.y = x, y

    def box(s):
        return (s.x - 3, s.y - 4, s.x + 4, s.y + 1)

    def draw(s, img, G):
        for j in range(-3, 1):
            for i in range(-2, 3):
                lit = 3.0 - 0.6 * i - 0.5 * ((i + j) % 2) - 0.6 * (j == 0)
                put(img, s.x + i, s.y + j, pick(THATCH, lit))
        for i in range(-2, 3):
            put(img, s.x + i, s.y - 4, THATCH[1] if abs(i) == 2 else SOIL[0])


class Platten:
    """Flat stepping stones from a door to the path: worn, lit at the top left, grass between them."""
    def __init__(s, a, b, seed=11):
        s.a, s.b, s.seed = a, b, seed

    def box(s):
        return (min(s.a[0], s.b[0]) - 4, min(s.a[1], s.b[1]) - 3, max(s.a[0], s.b[0]) + 4, -9999)   # flat: drawn first

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        (ax, ay), (bx, by) = s.a, s.b
        n = max(1, int(np.hypot(bx - ax, by - ay) / 6))
        for k in range(n + 1):
            x = ax + (bx - ax) * k / n + rng.normal(0, 0.8)
            y = ay + (by - ay) * k / n + rng.normal(0, 0.5)
            rx, ry = rng.uniform(2.6, 3.6), rng.uniform(1.5, 2.0)
            for j in range(int(y - ry) - 1, int(y + ry) + 2):
                for i in range(int(x - rx) - 1, int(x + rx) + 2):
                    e = ((i - x) / rx) ** 2 + ((j - y) / ry) ** 2
                    if e < 1:
                        put(img, i, j, pick(STONE, 4.4 - 1.2 * (i - x) / rx - 1.0 * (j - y) / ry - 1.2 * e))
                    elif e < 1.5 and 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
                        img[j, i] = img[j, i] * 0.6                           # the dark seam round it
                    elif e < 1.6 and j > y and 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
                        img[j, i] = img[j, i] * 0.75

