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


BOARD = [hx(c) for c in ['#231d19', '#3a312a', '#544739', '#6f604d', '#8b7a63', '#a8977c']]   # weathered boards, silvered


def plank_px(i, j, a, top, lit, seed):
    """One pixel of an old shitami-itabari wall: overlapping horizontal boards, each with a lit lower lip and its
    shadow under the next, every board its own tone, held by thin upright battens with nail heads; here and there a
    board split or gone dark with wet."""
    row = (j - top) // 3
    r = np.random.default_rng(seed * 131 + row * 17 + (i - a) // 11)
    tone = r.normal(0, 0.55)
    y_in = (j - top) % 3
    c = lit + tone + (0.0, 0.25, -1.1)[y_in]                         # the board, its lip, the shadow under the next
    batten = (i - a) % 7 == 3
    if batten:
        c = lit + 0.9 - 0.3 * (y_in == 2)
        if y_in == 1 and row % 2 == 0:
            return hx('#706b64')                                        # a nail head
    elif r.random() < 0.12:
        c -= 1.0                                                        # a board gone dark with wet
    elif y_in == 1 and (i * 7 + row * 3) % 13 == 0:
        c -= 0.8                                                        # a split along the grain
    elif y_in == 0 and (i * 5 + row) % 9 == 0:
        c += 0.6                                                        # worn pale
    return pick(BOARD, c)


class Minka:
    """An empty farmhouse seen from above at an angle: a veranda of planks, the front wall of posts with shoji and
    plank panels (paper torn, panes gone dark), a deep roof of tiles or thatch with moss on it, fallen in here and
    there so the rafters show, creepers hanging from the eaves. About w + 10 wide, wall + roof + 6 high."""
    def __init__(s, x, y, w=44, wall=11, roof=17, seed=1, kind='kawara', ruin=0.6, pal=0, rich=False):
        s.x, s.y, s.w, s.wall, s.roof, s.seed, s.kind, s.ruin = x, y, w, wall, roof, seed, kind, ruin
        s.rich = rich                                       # boards drawn in detail (the stonemason's house)
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
            panel = 'door' if a <= door + 3 < b else ('shoji' if rng.random() < (0.25 if s.rich else 0.6) else 'planks')
            for j in range(top, y - 1):
                for i in range(a, b):
                    lit = 2.6 - 1.6 * (i - x0) / w + rng.normal(0, 0.15)
                    if panel == 'planks' and s.rich:
                        c = plank_px(i, j, a, top, lit + 0.7, s.seed + k)
                    elif panel == 'planks':
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



RUST = [hx(c) for c in ['#1f140e', '#3a2215', '#5a321e', '#7a4829', '#9c6338']]      # old iron gone to rust
TEAL = [hx(c) for c in ['#1f302d', '#2f4a45', '#476b63', '#6c9389', '#a3c3b8', '#cfe2d9']]   # old glass, green-blue
INSIDE = [hx(c) for c in ['#1a2817', '#2a4022', '#3f5e2d', '#5a803c', '#7ca154']]       # the plants behind the glass
WARMG = hx('#e0a050')


class Gewaechshaus:
    """The greenhouse, the one house still whole (Philip's picture, 2026-11-07: an old Victorian glasshouse): a tall
    middle pavilion facing the path with a rounded, pointed gable, an iron crest and a finial, an arched door between
    two stone posts; to each side a long low wing with a curved glass roof. The iron has rusted brown, the glass gone
    green; plants inside press on the panes, a lantern burns inside. A few panes cracked, a couple gone, grass and
    creepers up the footing, stone-edged beds run wild in front. (x, y) the foot of the wings' front wall."""
    PW, PWALL, GH, RD = 38, 30, 19, 6           # pavilion: width, wall, gable, how far its roof runs back
    WW, WWALL, WR = 48, 14, 18                  # each wing: width, wall, curved roof

    def __init__(s, x, y, seed=21):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - s.PW // 2 - s.WW - 4, s.y - s.PWALL - s.GH - s.RD - 16, s.x + s.PW // 2 + s.WW + 8, s.y + 22)

    def lights(s):
        return [{'x': s.x + 0.5, 'y': s.y - 11.0, 'r': 46.0, 'k': 0.75, 'kind': 'lantern'}]

    def door(s):
        return (s.x, s.y + 4)

    def draw(s, img, G):
        from scipy import ndimage as ndi
        rng = np.random.default_rng(s.seed)
        x, y = s.x, s.y
        PW, PWALL, GH, RD, WW, WWALL, WR = s.PW, s.PWALL, s.GH, s.RD, s.WW, s.WWALL, s.WR
        L, R = x - PW // 2 - WW, x + PW // 2 + WW                      # outer ends of the wings
        lx, ly = x, y - 11                                             # the lantern inside, behind the door
        leaves = ndi.gaussian_filter(rng.normal(0, 1, (80, R - L + 20)), 1.4)
        leaves /= leaves.std() + 1e-9
        top_all = y - PWALL - GH - RD - 10
        gone = set()
        cracked = set()
        panes = {}

        def pane(i, j, u, cell, roof=0.0):
            """One pixel of glass: the leaves behind, the glass's tint and glint, the lantern's warmth. roof 0 wall
            .. 1 glass facing the sky."""
            n = leaves[(j - top_all) % leaves.shape[0], (i - L + 10) % leaves.shape[1]]
            leaf = n > -0.35 + 1.0 * roof
            base = pick(INSIDE, 2.5 + 1.5 * n - 1.0 * u) if leaf else pick(TEAL, 1.2 - u + 1.5 * roof)
            glint = (i - j) % 13 in (0, 1)
            glass = pick(TEAL, 2.6 - 1.6 * u + 1.6 * roof + (1.3 if glint else 0))
            c = base * (0.62 - 0.2 * roof) + glass * (0.38 + 0.2 * roof)
            dd = np.hypot(i - lx, (j - ly) * 1.25)
            warm = max(0.0, 1 - dd / 28.0) ** 1.3
            c = c * (1 - 0.6 * warm) + WARMG * 0.62 * warm
            if cell in gone:
                c = base * 0.75 if leaf else hx('#0f1412')            # no glass: the leaves themselves, or dark
            else:
                panes.setdefault(cell, []).append((i, j, c))            # for the cracks, drawn at the end
            return c

        def growth(i0, i1, yb, hmax, seed):
            """Grass and weeds up the footing, taller in tufts."""
            g = np.random.default_rng(seed)
            for i in range(i0, i1):
                h = int(max(0, g.normal(hmax * 0.45, hmax * 0.35)))
                for dj in range(h):
                    put(img, i, yb - dj, pick(MOSS if g.random() < 0.6 else LEAF, 3.4 - 2.4 * dj / max(1, h) + g.normal(0, 0.3)))

        shade_ground(img, G, L - 2, R + 14, y - 4, y + 9, 0.6)
        # ---------- the wings: footing, a wall of tall panes, the curved roof with its ribs
        for side in (-1, 1):
            a = L if side < 0 else x + PW // 2
            b = x - PW // 2 if side < 0 else R
            outer = a if side < 0 else b - 1
            for k in range(2):
                gone.add(('w', side, int(rng.integers(0, WW // 4)), int(rng.integers(0, 4))))
            for k in range(3):
                cracked.add(('w', side, int(rng.integers(0, WW // 4)), int(rng.integers(0, 5))))
            for j in (y - 1, y):
                for i in range(a, b):
                    put(img, i, j, pick(STONE, 3.0 - 1.6 * (i - L) / (R - L) - 0.8 * (j == y) + rng.normal(0, 0.2)))
            wt = y - 2 - WWALL
            for j in range(wt, y - 1):
                for i in range(a, b):
                    u = (i - L) / (R - L)
                    bar = (i - a) % 4 == 0 or j in (wt, wt + 3) or i == b - 1
                    cell = ('w', side, (i - a) // 4, 0 if j < wt + 3 else 4)
                    put(img, i, j, pick(RUST, 2.8 - 1.6 * u) if bar else pane(i, j, u, cell))
            for k in range(WR):                                         # the roof, rising back from the wall
                j = wt - 1 - k
                t = k / (WR - 1)
                hip = int(round(k * 0.55))                              # the outer end curves round too
                i0, i1 = (a + hip, b) if side < 0 else (a, b - hip)
                for i in range(i0, i1):
                    u = (i - L) / (R - L)
                    rib = (i - a) % 4 == 0
                    purlin = k % 4 == 3
                    cell = ('w', side, (i - a) // 4, 1 + k // 4)
                    if rib or purlin or i in (i0, i1 - 1):
                        c = pick(RUST, 2.6 - 1.4 * u + 0.8 * t)
                    else:
                        c = pane(i, j, u, cell, roof=0.25 + 0.6 * t)
                    if k == 0:
                        c = pick(RUST, 1.6 - u)
                    put(img, i, j, c)
            rj = wt - WR                                                # the ridge cap
            for i in range(a + (int(WR * 0.55) if side < 0 else 0), b - (0 if side < 0 else int(WR * 0.55))):
                put(img, i, rj, pick(RUST, 3.4 - 1.6 * (i - L) / (R - L)))
            growth(a - 1, b + 1, y - 1, 6, s.seed + side)
            for d in range(int(WWALL * 1.2)):                           # creepers up the outer corner
                put(img, outer + side * (d % 3 == 0) * -1, y - 2 - d, pick(MOSS, 3.0 - 1.6 * d / WWALL))
        # ---------- the pavilion: its roof running back behind the gable, then the facade and gable in front
        yb = y + 3                                                      # it stands a little forward of the wings
        x0, x1 = x - PW // 2, x + PW // 2
        ft = yb - 1 - PWALL                                             # facade top
        rad = PW / 2 + 1

        def half(d):                                                    # the gable's half width d rows above ft
            t = d / GH                                                  # round shoulders, then drawn in to a point
            return rad * np.sqrt(max(0.0, 1 - t ** 2.4)) * (1 - 0.6 * t ** 2)
        for d in range(GH + RD + 1):                                    # roof: the gable outline swept back
            for back in range(1, RD + 1):
                dd = d - back
                if dd < 0 or dd > GH:
                    continue
                hw = half(dd)
                j = ft - d
                for i in range(int(round(x - hw)), int(round(x + hw)) + 1):
                    u = (i - x0) / PW
                    if i == x or i == x - 1:
                        c = pick(RUST, 3.2 if i < x else 2.0)              # the ridge
                    elif back % 3 == 0:
                        c = pick(RUST, 2.4 - 1.2 * u)
                    else:
                        c = pane(i, j, u, ('r', i // 4, back // 3), roof=0.75)
                    put(img, i, j, c)
        gone.add(('r', (x + 6) // 4, 1))
        for j in (yb - 1, yb):                                          # footing
            for i in range(x0 - 1, x1 + 1):
                put(img, i, j, pick(STONE, 3.4 - 2.0 * (i - x0) / PW - 0.8 * (j == yb) + rng.normal(0, 0.2)))
        dw, dh = 12, 21                                                 # the door, arched
        for j in range(ft, yb - 1):
            for i in range(x0, x1):
                u = (i - x0) / PW
                bar = (i - x0) % 5 == 0 or i == x1 - 1 or j in (ft, ft + 1, ft + 7)
                frieze = j == ft + 1 and (i % 2 == 0)
                c = pick(RUST, (3.4 if frieze else 2.6) - 1.6 * u) if bar else pane(i, j, u, ('p', (i - x0) // 5, (j - ft) // 7))
                ddx = i - x
                in_door = abs(ddx + 0.5) <= dw / 2 and (j > yb - 1 - dh + 5 or
                                                        (ddx + 0.5) ** 2 + ((j - (yb - 1 - dh + 5)) * 1.0) ** 2 <= (dw / 2) ** 2)
                if in_door:
                    edge = abs(ddx + 0.5) > dw / 2 - 1.2 or (j <= yb - 1 - dh + 5 and
                                                             (ddx + 0.5) ** 2 + (j - (yb - 1 - dh + 5)) ** 2 > (dw / 2 - 1.2) ** 2)
                    if edge:
                        c = RUST[4] if ddx < 0 else RUST[3]               # the door's frame, the brightest iron
                    elif j <= yb - 1 - dh + 5:                           # the fanlight: radial bars
                        ang = np.arctan2(j - (yb - 1 - dh + 5), ddx + 0.5)
                        c = pick(RUST, 2.6) if int(round(ang / 0.6)) % 2 == 0 and abs(ddx) > 0 else pane(i, j, u, ('f', 0))
                    elif ddx < 0:                                        # the left leaf stands open: inside, lit
                        warm = max(0.0, 1 - np.hypot(i - lx, (j - ly) * 1.2) / 9.0)
                        c = hx('#141711') * (1 - warm) + WARMG * 0.8 * warm
                        if j > yb - 4:
                            c = pick(STONE, 1.4)                         # the threshold inside
                    else:
                        c = pick(RUST, 2.4) if ddx in (2, 4) else pane(i, j, u, ('d', 0))
                put(img, i, j, c)
        for (u_, v_, c) in ((0, 0, hx('#fff0b0')), (0, 1, hx('#ffc85a')), (-1, 0, hx('#f08a2a')),
                            (1, 0, hx('#f08a2a')), (0, -1, RUST[0]), (0, -2, RUST[0])):
            put(img, lx + u_, ly + v_, c)                               # the lantern hanging inside the door
        for d in range(GH + 1):                                         # the gable: panes, bars, a rusted edge
            hw = half(d)
            j = ft - 1 - d
            for i in range(int(round(x - hw)), int(round(x + hw)) + 1):
                u = (i - x0) / PW
                bar = (i - x0) % 5 == 0 or d == 0 or d == 6
                c = pick(RUST, 2.6 - 1.4 * u) if bar else pane(i, j, u, ('g', (i - x0) // 5, d // 6), roof=0.2)
                if abs(i - (x - hw)) < 1 or abs(i - (x + hw)) < 1:
                    c = pick(RUST, 3.4 - 1.6 * u)
                put(img, i, j, c)
            if d % 3 == 1 and d < GH - 1:                               # the crest: scrolls along the edge
                for sgn in (-1, 1):
                    put(img, int(round(x + sgn * (hw + 1))), j - 1, RUST[3] if sgn < 0 else RUST[2])
        aj = ft - 1 - GH                                                # the finial: a spike with a scroll
        for d in range(1, 13):
            put(img, x, aj - d, RUST[4] if d < 8 else RUST[3])
        for (u_, v_) in ((-1, -2), (1, -2), (-2, -3), (2, -3), (-3, -2), (3, -2), (-1, -6), (1, -6)):
            put(img, x + u_, aj + v_, RUST[3])
        for px in (x0 - 1, x1):                                         # small pinnacles at the shoulders
            for d in range(4):
                put(img, px, ft - d, RUST[4] if px < x else RUST[2])
            put(img, px, ft - 4, RUST[3])
        growth(x0 - 1, x - dw // 2, yb - 1, 7, s.seed + 5)
        growth(x + dw // 2 + 1, x1 + 1, yb - 1, 7, s.seed + 6)
        for d in range(int(PWALL * 0.9)):                               # a creeper up the left of the facade
            put(img, x0 + 1 + (d % 4 == 1), yb - 2 - d, pick(MOSS, 3.2 - 1.8 * d / PWALL))
            if d % 3 == 0:
                put(img, x0 + 2, yb - 2 - d, MOSS[1])
        # ---------- cracks: a few panes with a thin jagged crack from one corner, a short branch off it; only
        # where the glass still shows (not under the weeds and creepers drawn over it since)
        cg = np.random.default_rng(s.seed + 77)
        big = sorted(panes, key=lambda k: -len(panes[k]))[:30]           # the big panes: a crack needs room to show
        for n in cg.permutation(len(big))[:6]:
            pts = panes[big[n]]
            free = {(i, j): c for i, j, c in pts if np.allclose(img[j, i], c)}
            if len(free) < 8:
                continue
            xs_ = [p[0] for p in free]
            ys_ = [p[1] for p in free]
            ci = min(xs_) if cg.random() < 0.5 else max(xs_)
            cj = min(ys_) if cg.random() < 0.5 else max(ys_)
            di, dj = (1 if ci == min(xs_) else -1), (1 if cj == min(ys_) else -1)
            walk = [(ci, cj)]
            for step in range(int(cg.integers(4, 8))):
                i_, j_ = walk[-1]
                if cg.random() < 0.6:
                    i_ += di
                if cg.random() < 0.7:
                    j_ += dj
                if (i_, j_) not in free:
                    break
                walk.append((i_, j_))
            if len(walk) > 3 and cg.random() < 0.7:                    # a branch off the middle
                i_, j_ = walk[len(walk) // 2]
                for step in range(2):
                    i_ -= di
                    if (i_, j_) in free:
                        walk.append((i_, j_))
            for k, (i_, j_) in enumerate(walk):
                if (i_, j_) in free:
                    a_ = 0.75 if k < len(walk) - 2 else 0.4            # fainter at its ends
                    img[j_, i_] = img[j_, i_] * (1 - a_) + TEAL[5] * a_
        # ---------- in front: two stone posts at the door, stone-edged beds run wild
        for px in (x - dw // 2 - 4, x + dw // 2 + 1):
            Block(px, yb + 5, w=3, h=5, d=1, seed=s.seed + px).draw(img, G)
        for (bx0, bx1) in ((x0 - WW + 6, x - dw // 2 - 8), (x + dw // 2 + 7, x1 + WW - 6)):
            # a raised bed seen from above at an angle: the top of its stone rim all round, the rim's front face
            # below it, the weeds inside standing up over the back rim
            by0, by1, fh = y + 7, y + 15, 3                             # back rim, front rim, height of the front face
            for j in range(by0, by1 + fh + 1):
                for i in range(bx0, bx1 + 1):
                    u = (i - bx0) / (bx1 - bx0)
                    if j > by1:                                          # the front face, stones with joints
                        joint = (i - bx0 + 3 * (j - by1)) % 6 == 0 or j == by1 + fh
                        c = pick(STONE, 2.0 - 0.9 * u - 0.4 * (j - by1) + rng.normal(0, 0.12) - (0.9 if joint else 0))
                    elif j in (by0, by1) or i in (bx0, bx1, bx0 + 1, bx1 - 1) and j > by0:
                        c = pick(STONE, 3.9 - 1.0 * u - 0.5 * (j == by0) + rng.normal(0, 0.12))   # the rim's top, lit
                    else:
                        n = leaves[(j * 3) % leaves.shape[0], (i * 2) % leaves.shape[1]]
                        c = pick(MOSS, 2.2 + 1.4 * n - 0.6 * (j < by0 + 2)) if n > -0.5 else pick(SOIL, 1.5 + n)
                    put(img, i, j, c)
            g = np.random.default_rng(s.seed + bx0)
            for i in range(bx0 + 2, bx1 - 1):                            # weeds over the back rim and out at the front
                if g.random() < 0.45:
                    for d in range(int(g.integers(1, 5))):
                        put(img, i, by0 + 1 - d, pick(MOSS if g.random() < 0.7 else LEAF, 3.4 - 0.5 * d + g.normal(0, 0.3)))
                if g.random() < 0.15:
                    put(img, i, by1 + 1, pick(MOSS, 2.6))
            for i in range(bx0, bx1 + 2):                               # its shadow
                if 0 <= by1 + fh + 1 < img.shape[0] and 0 <= i < img.shape[1]:
                    img[by1 + fh + 1, i] = img[by1 + fh + 1, i] * 0.65


class Block:
    """A hewn stone block, an upright box seen from above at an angle: lit top, mid front, dark side, chisel marks."""
    def __init__(s, x, y, w=6, h=4, d=3, seed=31, worked=True):
        s.x, s.y, s.w, s.h, s.d, s.seed, s.worked = x, y, w, h, d, seed, worked

    def box(s):
        return (s.x - 1, s.y - s.h - s.d - 1, s.x + s.w + s.d + 2, s.y + 2)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        x, y, w, h, d = s.x, s.y, s.w, s.h, s.d
        for i in range(x, x + w + d + 2):                              # its shadow
            if 0 <= y + 1 < img.shape[0] and 0 <= i < img.shape[1]:
                img[y + 1, i] = img[y + 1, i] * 0.65
        for j in range(h):                                             # front
            for i in range(w):
                c = pick(STONE, 2.6 - 0.6 * i / w + rng.normal(0, 0.15))
                if s.worked and (i + j * 2) % 4 == 0:
                    c = pick(STONE, 1.7)                               # chisel lines
                put(img, x + i, y - j, c)
        for k in range(1, d + 1):                                      # the side (right), going back and up
            for j in range(h):
                put(img, x + w - 1 + k, y - j - k, pick(STONE, 1.4 + rng.normal(0, 0.15)))
        for k in range(1, d + 1):                                      # the top
            for i in range(w):
                put(img, x + i + k, y - h + 1 - k, pick(STONE, 3.8 - 0.5 * i / w + rng.normal(0, 0.12)))
        for i in range(w):                                             # crisp edges: a cut block, not a boulder
            put(img, x + i, y, STONE[0])
        for j in range(h):
            put(img, x + w + d, y - j - d, STONE[0])
        for i in range(w):
            put(img, x + i + 1, y - h + 1, pick(STONE, 4.4))


class Steinmetz:
    """The stonemason's house (Philip, round 2: the workshop against a house, not standing alone): a small minka, and
    under a lean-to roof tucked beneath its eave an open workshop on its east side - the house's wall its back, a plank
    wall at the back running up to the roof, tools hanging on it, a bench, the floor pale with stone dust. Out in
    front a Jizo half out of its block. Same chisel marks as the well and the walls of the village."""
    LW = 34                                    # the workshop's width

    def __init__(s, x, y, seed=41):
        s.x, s.y, s.seed = x, y, seed
        s.house = Minka(x - 22, y, w=42, wall=14, roof=18, seed=seed, kind='kawara', ruin=0.45, pal=1, rich=True)

    def box(s):
        hb = s.house.box()
        return (hb[0], hb[1], s.x + s.LW + 14, s.y + 10)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        y = s.y
        xs = s.house.x + s.house.w // 2 - 1                            # the house's east wall
        xe = xs + s.LW
        DUST = [hx(c) for c in ['#8e8a82', '#aaa69c', '#c4c0b4']]
        fe, fb = y - 16, y - 8                                         # eave of the lean-to, back of its floor
        for j in range(fb, y + 9):                                     # stone dust on the floor and out in front
            for i in range(xs - 2, xe + 8):
                e = ((i - (xs + xe) / 2) / (s.LW / 2 + 6)) ** 2 + ((j - y) / 9.0) ** 2
                if (j <= y and i < xe) or (e < 1 and g_at(G, i, j) < 0.95 - 0.6 * e):
                    put(img, i, j, pick(DUST, 2.0 - 1.6 * min(e, 1) + g_at(G, i * 7, j) - 0.6 - 0.8 * (j < fb + 3)
                                        - 0.5 * (j > y or i >= xe)))
        # the back wall: planks from the floor right up under the roof, the full width, tools on it
        for j in range(fe + 1, fb):
            for i in range(xs, xe):
                put(img, i, j, plank_px(i, j, xs, fe + 1, 2.7 - 1.0 * (i - xs) / s.LW - 0.6 * (j < fe + 3), s.seed + 9))
        for k, tx in enumerate(range(xs + 4, xs + 16, 3)):             # chisels and a mallet on pegs
            put(img, tx, fe + 3, WOOD[0])
            for dd in range(1, 4 + k % 2):
                put(img, tx, fe + 3 + dd, hx('#9aa0a6') if dd < 3 else WOOD[4])
        for i in range(xs + 19, xs + 28):                              # a saw: the blade, its teeth, the grip
            put(img, i, fe + 4, hx('#80868c'))
            if i % 2:
                put(img, i, fe + 5, hx('#5c6268'))
        put(img, xs + 28, fe + 4, WOOD[4])
        put(img, xs + 29, fe + 4, WOOD[3])
        # the bench against the wall with a mallet, chisels and a small stone on it
        for i in range(xs + 3, xs + 19):
            put(img, i, fb + 1, WOOD[4])
            put(img, i, fb + 2, WOOD[2])
        for leg in (xs + 4, xs + 17):
            for dd in range(3, 7):
                put(img, leg, fb + dd, WOOD[1])
        for (i, j, c) in ((xs + 6, fb, WOOD[3]), (xs + 7, fb, WOOD[3]), (xs + 7, fb - 1, WOOD[4]),
                          (xs + 10, fb, hx('#9aa0a6')), (xs + 11, fb, hx('#9aa0a6')), (xs + 12, fb, WOOD[3]),
                          (xs + 14, fb, STONE[3]), (xs + 15, fb, STONE[2]), (xs + 14, fb - 1, STONE[4])):
            put(img, i, j, c)
        # the corner post at the front, the beam under the lean-to's eave
        for j in range(fe, y + 1):
            put(img, xe - 2, j, WOOD[2])
            put(img, xe - 1, j, WOOD[0])
        for i in range(xs, xe + 1):
            put(img, i, fe, WOOD[0])
        # the lean-to roof: tiles from the eave back up under the house's eave, lower towards its outer end
        mn = ndi_noise(s.seed, 14, s.LW + 10)
        for i in range(xs - 2, xe + 3):
            u = (i - xs) / s.LW
            depth = int(round(10 - 2.5 * max(0.0, u)))
            for k in range(depth):
                j = fe - 1 - k
                lit = 2.8 - 1.4 * u + (0.6, 0.0, -0.9)[(i - xs) % 3] - (0.5 if k % 3 == 0 else 0) + 0.4 * k / depth
                c = pick(ROOFS['kawara'][1], lit)
                if mn[k, min(max(0, i - xs + 2), mn.shape[1] - 1)] > 0.5:
                    c = pick(MOSS, lit * 0.8 + 0.4)
                if k == 0:
                    c = pick(ROOFS['kawara'][1], 1.0 - u)
                put(img, i, j, c)
        # then the house over it, its eave over the lean-to's top
        s.house.draw(img, G)
        # the half-made Jizo out in front: head, shoulders and folded hands cut, the rest still the rough block
        jx, jy = xe + 4, y + 5                                         # beside the corner post, out in the dust
        Block(jx - 6, jy, w=11, h=6, d=3, seed=s.seed + 1, worked=False).draw(img, G)
        body = jy - 5
        hc = body - 11.5
        for j in range(int(hc) - 5, body + 1):                         # a dark rim first, so it stands off the dust
            for i in range(-6, 7):
                t = (j - (body - 8)) / 8.0
                if (i * i + (j - hc) ** 2 < 21) or (j >= body - 8 and abs(i) <= 3.0 + t * 1.8 + 1):
                    put(img, jx + i, j, STONE[0])
        for j in range(body - 8, body + 1):                            # the robe, a bell from the head down to the block
            t = (j - (body - 8)) / 8.0
            hw = 3.0 + t * 1.8
            for i in range(int(-hw), int(hw) + 1):
                c = pick(STONE, 3.0 - 2.0 * (i + hw) / (2 * hw) + rng.normal(0, 0.12))
                if (j - body) % 3 == 0 and abs(i) < hw - 1:
                    c = pick(STONE, 1.6)                               # the robe's folds
                put(img, jx + i, j, c)
        for (i, j, c) in ((0, -4, STONE[4]), (-1, -4, STONE[3]), (1, -4, STONE[2]), (0, -3, STONE[1])):
            put(img, jx + i, body + j, c)                               # the hands folded in front
        for j in range(int(hc) - 4, int(hc) + 5):                       # the big round shaven head
            for i in range(-4, 5):
                e = i * i + (j - hc) ** 2
                if e < 14:
                    c = pick(STONE, 3.9 - 0.4 * i - 0.25 * (j - hc) + rng.normal(0, 0.1))
                    if e > 9.5:
                        c = pick(STONE, 1.5 + (i < 0) + (j < hc))
                    put(img, jx + i, j, c)
        for i in range(-4, 5):                                          # the cut line where the block still waits
            put(img, jx + i, body + 1, STONE[1] if i % 2 else STONE[2])
        for (i, j) in ((jx + 7, jy + 1), (jx + 8, jy + 2), (jx - 8, jy + 2), (jx + 5, jy + 3)):
            put(img, i, j, STONE[3])                                    # chips round it


# ======================================================================== zone 3: the shrine and the orchard
VERM = [hx(c) for c in ['#351812', '#55261b', '#7a3826', '#9c5034', '#b86c48']]       # torii vermilion, faded
PATINA = [hx(c) for c in ['#1c2a27', '#283f39', '#38584e', '#4f7766', '#6e9783']]      # copper roof gone green
SHIDE = [hx(c) for c in ['#7c7a72', '#a5a297', '#c9c5b8']]                            # paper, greyed
ROPE = [hx(c) for c in ['#4a3f2a', '#6e5f3d', '#958353', '#b3a06a']]                   # straw rope
KAKI = [hx(c) for c in ['#683014', '#9c4c20', '#c26a2c', '#d08a46']]                   # persimmons, muted in the dusk (Philip)


class Torii:
    """A village torii, vermilion faded and flaking: two round pillars on stone feet, the tie-beam (nuki) through
    them, the top beam (kasagi) black on top and swept up at the ends, a small plaque between."""
    def __init__(s, x, y, span=18, h=21, seed=61):
        s.x, s.y, s.span, s.h, s.seed = x, y, span, h, seed

    def box(s):
        return (s.x - s.span // 2 - 8, s.y - s.h - 6, s.x + s.span // 2 + 10, s.y + 3)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        x, y, h = s.x, s.y, s.h
        L, R = x - s.span // 2, x + s.span // 2
        for px in (L, R):                                              # shadows to the lower right
            for d in range(1, 6):
                if 0 <= y + 1 < img.shape[0]:
                    put(img, px + d, y + 1, img[y + 1, px + d] * 0.65) if 0 <= px + d < img.shape[1] else None
        for px in (L, R):
            for i in range(px - 1, px + 3):                           # stone foot
                put(img, i, y, pick(STONE, 3.2 - (i - px + 1) * 0.7))
                put(img, i, y - 1, pick(STONE, 3.6 - (i - px + 1) * 0.7))
            for j in range(y - h, y - 1):
                flake = g_at(G, px * 3, j * 5) < 0.12                  # the paint come off: grey wood
                put(img, px, j, WOOD[3] if flake else VERM[4])
                put(img, px + 1, j, WOOD[1] if flake else VERM[2])
        nj = y - h + 5                                                 # the nuki, through both pillars
        for i in range(L - 3, R + 5):
            put(img, i, nj, VERM[3])
            put(img, i, nj + 1, VERM[1])
        for j in range(y - h + 1, nj):                                 # the plaque
            put(img, x, j, VERM[1])
            put(img, x + 1, j, VERM[0])
        put(img, x, y - h + 2, WOOD[0])
        for i in range(L - 6, R + 8):                                  # the kasagi: vermilion under, black on top
            t = (i - (L - 6)) / (R + 8 - (L - 6))
            up = int(round(2.4 * (2 * t - 1) ** 6))                    # swept up at both ends
            j = y - h - up
            put(img, i, j, VERM[3] if t < 0.5 else VERM[2])
            put(img, i, j - 1, pick(TILE, 2.4 - 1.6 * t))
            put(img, i, j - 2, pick(TILE, 3.2 - 2.0 * t))
        for i in range(L - 4, R + 6):                                  # moss on the top beam here and there
            if g_at(G, i * 7, 3) < 0.25:
                put(img, i, y - h - 2 - int(round(2.4 * (2 * (i - L + 6) / (s.span + 14) - 1) ** 6)), MOSS[2])


class Treppe:
    """Stone steps going up north to the shrine, seen from above at an angle: each step a lit tread and a darker
    riser, the stones of a step set unevenly, moss in the corners, grass at the sides. (x, y) the foot, middle."""
    def __init__(s, x, y, w=14, n=8, seed=62):
        s.x, s.y, s.w, s.n, s.seed = x, y, w, n, seed
        s.order = -9998                                                # under everything: it is ground

    def box(s):
        return (s.x - s.w // 2 - 3, s.y - 4 * s.n - 1, s.x + s.w // 2 + 4, s.y + 1)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        x0, x1 = s.x - s.w // 2, s.x + s.w // 2
        for k in range(s.n):
            yb = s.y - 4 * k                                           # the riser's foot
            cut = [x0] + sorted(rng.choice(np.arange(x0 + 3, x1 - 2), 2, replace=False).tolist()) + [x1]
            for a, b in zip(cut, cut[1:]):
                sh = rng.normal(0, 0.25)
                for i in range(a, b):
                    u = (i - x0) / s.w
                    put(img, i, yb, pick(STONE, 1.2 - 0.6 * u + sh))                # the riser, in shade
                    put(img, i, yb - 1, pick(STONE, 1.9 - 0.8 * u + sh))
                    put(img, i, yb - 2, pick(STONE, 3.3 - 1.2 * u + sh))            # the tread, lit
                    put(img, i, yb - 3, pick(STONE, 3.7 - 1.2 * u + sh))
                put(img, b - 1, yb, STONE[0])                          # the joint between two stones
                put(img, b - 1, yb - 1, STONE[0])
            for i in (x0, x0 + 1, x1 - 1):                             # moss in the corners
                if rng.random() < 0.6:
                    put(img, i, yb - 1 - int(rng.integers(0, 3)), pick(MOSS, rng.uniform(1, 3)))
        for j in range(s.y - 4 * s.n, s.y + 1):                        # the low stone cheeks either side
            put(img, x0 - 1, j, pick(STONE, 2.6 + g_at(G, 1, j)))
            put(img, x0 - 2, j, pick(MOSS, 1.5 + g_at(G, 2, j)))
            put(img, x1, j, pick(STONE, 1.2 + g_at(G, 3, j)))
            put(img, x1 + 1, j, STONE[0])


class Komainu:
    """A stone guardian dog on its pedestal, sitting, mane and tail curled; flip faces it the other way."""
    def __init__(s, x, y, flip=False, seed=63):
        s.x, s.y, s.flip, s.seed = x, y, flip, seed

    def box(s):
        return (s.x - 5, s.y - 16, s.x + 8, s.y + 2)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        Block(s.x - 3, s.y, w=7, h=4, d=2, seed=s.seed).draw(img, G)
        f = -1 if s.flip else 1
        shape = ['..##...',                                             # head (with mane) at the front, body, tail
                 '.####..',
                 '#####.#',
                 '.#####.',
                 '.######',
                 '.######',
                 '#######']
        by = s.y - 4 - 2 - len(shape)
        for j, row in enumerate(shape):                                  # a dark rim first: it stands off the grass
            for i, ch in enumerate(row):
                if ch == '#':
                    ii = s.x - 3 + (i if f > 0 else 6 - i)
                    for (u_, v_) in ((-1, 0), (1, 0), (0, -1)):
                        put(img, ii + u_, by + j + v_, STONE[0])
        for j, row in enumerate(shape):
            for i, ch in enumerate(row):
                if ch == '#':
                    ii = s.x - 3 + (i if f > 0 else 6 - i)
                    lit = 3.4 - 0.45 * (ii - s.x + 3) - 0.15 * j + rng.normal(0, 0.15)
                    if (j in (1, 2) and (i in (1, 2) if f > 0 else i in (1, 2))):
                        lit += 0.3                                      # the mane catches the light
                    c = pick(STONE, lit)
                    if g_at(G, ii * 5, by + j) < 0.18:
                        c = pick(MOSS, lit * 0.7)
                    put(img, ii, by + j, c)
        eye = s.x - 3 + (2 if f > 0 else 4)
        put(img, eye, by + 1, STONE[0])


class Yashiro:
    """The village shrine (Sato-no-yashiro): a small hall on a stone base, its copper roof gone green with a
    little gable over the front, a deep eave over the steps; lattice doors, the offering box, the bell rope, a
    straw shimenawa sagging across the front with paper shide (one gone). Moss on the roof, left alone for years
    but still whole. (x, y) the foot of the base's front, middle."""
    def __init__(s, x, y, w=36, seed=64):
        s.x, s.y, s.w, s.seed = x, y, w, seed

    def box(s):
        return (s.x - s.w // 2 - 8, s.y - 52, s.x + s.w // 2 + 14, s.y + 4)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        w, x, y = s.w, s.x, s.y
        x0, x1 = x - w // 2, x + w // 2
        shade_ground(img, G, x0 - 4, x1 + 14, y - 4, y + 5, 0.6)
        for j in range(y - 5, y + 1):                                  # the stone base, coursed
            for i in range(x0 - 4, x1 + 4):
                u = (i - x0 + 4) / (w + 8)
                joint = (j - y) % 3 == 0 or (i + 4 * ((j - y) // 3)) % 7 == 0
                c = pick(STONE, (3.6 if j == y - 5 else 2.6) - 1.6 * u - (0.9 if joint and j != y - 5 else 0)
                         + rng.normal(0, 0.12))
                if g_at(G, i * 3, j * 7) < 0.15 and j > y - 5:
                    c = pick(MOSS, 1.6)
                put(img, i, j, c)
        for k in range(3):                                             # wooden steps up to the floor
            for i in range(x - 5, x + 6):
                put(img, i, y - 6 - k * 2, pick(WOOD, 3.6 - k * 0.3 - (i - x + 5) * 0.12))
                put(img, i, y - 7 - k * 2, pick(WOOD, 2.0 - k * 0.2))
        fl = y - 12                                                    # the floor (veranda) and the hall's wall
        for i in range(x0 - 2, x1 + 2):
            put(img, i, fl, pick(WOOD, 3.4 - 2.0 * (i - x0) / w))
            put(img, i, fl + 1, WOOD[1])
        wt = fl - 13
        for j in range(wt, fl):
            for i in range(x0, x1):
                u = (i - x0) / w
                post = (i - x0) % (w // 3) in (0, 1) or i >= x1 - 2
                if post:
                    c = pick(WOOD, 2.8 - 1.6 * u - 0.8 * ((i - x0) % (w // 3) == 1))
                elif abs(i - x) <= w // 6:                              # the lattice doors in the middle
                    c = pick(WOOD, 2.4 - u) if (i % 2 == 0 or j % 2 == 0) else HOLE
                else:
                    c = plank_px(i, j, x0, wt, 2.8 - 1.4 * u, s.seed)
                put(img, i, j, c)
        for i in range(x - 4, x + 5):                                  # the offering box on the veranda
            for d in range(4):
                c = pick(WOOD, 3.6 - 0.25 * (i - x + 4)) if d == 3 else pick(WOOD, 1.6 + 0.5 * (i % 2))
                put(img, i, fl - d, c)
        for d in range(1, 12):                                         # the bell rope, red and white, the bell
            put(img, x, wt + d, hx('#9a3a2a') if (d // 2) % 2 else SHIDE[2])
        for (u_, v_, c) in ((0, 0, hx('#b09038')), (-1, 0, hx('#8a6e28')), (1, 0, hx('#d4b04c')), (0, -1, hx('#6a5420'))):
            put(img, x + u_, wt + 1 + v_, c)
        # the shimenawa: a thick straw rope sagging across under the eave, shide hanging from it
        gone = int(rng.integers(0, 4))
        for i in range(x0 + 1, x1 - 1):
            t = (i - x0) / w
            j = wt + 2 + int(round(2.5 * np.sin(np.pi * t)))
            put(img, i, j, pick(ROPE, 3.2 - 1.6 * t))
            put(img, i, j + 1, pick(ROPE, 1.6 - t))
        for k, t in enumerate((0.2, 0.4, 0.6, 0.8)):
            if k == gone:
                continue
            i = int(x0 + t * w)
            j = wt + 4 + int(round(2.5 * np.sin(np.pi * t)))
            for d, dx in enumerate((0, 1, 0, 1, 0)):                   # the zigzag of paper
                put(img, i + dx, j + d, SHIDE[2 - (d % 2)])
        # the roof: patina copper, eave first, a small gable (chidori-hafu) over the front
        mn = ndi_noise(s.seed, 30, w + 30)
        eave = wt - 2
        for i in range(x0 - 7, x1 + 8):
            put(img, i, eave + 1, WOOD[0])
        for k in range(20):
            j = eave - k
            hw = w / 2 + 7 - k * 0.42
            for i in range(int(x - hw), int(x + hw) + 1):
                u = (i - (x - hw)) / (2 * hw)
                lit = 3.2 - 1.9 * u - 0.5 * k / 20 + 0.5 * ((i - int(x - hw)) % 4 == 0) + rng.normal(0, 0.12)
                c = pick(PATINA, lit)
                if mn[k, min(int(i - x + hw), mn.shape[1] - 1)] > 1.0:
                    c = pick(MOSS, lit * 0.8 + 0.4)
                if k == 0:
                    c = pick(PATINA, 1.0 - u)
                put(img, i, j, c)
        for i in range(int(x - w / 2 - 7 + 20 * 0.42), int(x + w / 2 + 7 - 20 * 0.42) + 1):   # the ridge
            put(img, i, eave - 20, pick(PATINA, 3.8 - 2.2 * (i - x0) / w))
            put(img, i, eave - 21, pick(PATINA, 2.6 - 1.8 * (i - x0) / w))
        for e in (int(x - w / 2 - 7 + 20 * 0.42), int(x + w / 2 + 7 - 20 * 0.42)):     # the crossed chigi at the ends
            for d in range(4):
                put(img, e - d, eave - 22 - d, PATINA[3])
                put(img, e + d, eave - 22 - d, PATINA[2])
        for d in range(9):                                             # the little front gable, a triangle on the slope
            hw = 9 - d
            for i in range(x - hw, x + hw + 1):
                c = pick(PATINA, 3.4 - 0.25 * (i - x + hw)) if abs(i - x) >= hw - 1 else pick(WOOD, 2.8 - 0.15 * (i - x + hw))
                put(img, i, eave - 2 - d, c)
        put(img, x, eave - 6, hx('#b09038'))                           # a gilt boss in the gable


class Shinboku:
    """The shrine's old sacred tree, a big camphor (the south's broadleaf, large) with a shimenawa round its trunk."""
    def __init__(s, x, y, seed=65, size=1.35):
        s.t = ol.Laubbaum(x, y, seed=seed, size=size)
        s.x, s.y, s.size = x, y, size

    def box(s):
        return s.t.box()

    def draw(s, img, G):
        s.t.draw(img, G)
        j = s.y - int(5 * s.size)
        for i in range(s.x - 3, s.x + 4):
            put(img, i, j, pick(ROPE, 3.0 - 0.4 * (i - s.x + 3)))
            put(img, i, j + 1, pick(ROPE, 1.5))
        for i in (s.x - 1, s.x + 2):
            for d, dx in enumerate((0, 1, 0, 1)):
                put(img, i + dx, j + 2 + d, SHIDE[2 - (d % 2)])


class Kaki:
    """A persimmon tree nobody harvests any more: few leaves left, the dark limbs showing, and the orange fruit
    hanging on all over; some fallen in the grass underneath."""
    def __init__(s, x, y, seed=70, size=0.6):
        s.t = ol.Laubbaum(x, y, seed=seed, size=size)
        s.x, s.y, s.seed, s.size = x, y, seed, size

    def box(s):
        b = s.t.box()
        return (b[0], b[1], b[2], s.y + 6)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed + 3)
        before = img.copy()
        s.t.draw(img, G)
        x0, y0, x1, y1 = s.t.box()
        y0, x0 = max(0, y0), max(0, x0)
        diff = np.abs(img[y0:y1, x0:x1] - before[y0:y1, x0:x1]).sum(-1) > 1
        sub = img[y0:y1, x0:x1]
        lum = sub.mean(-1)
        thin = diff & (rng.random(lum.shape) < 0.45) & (np.arange(sub.shape[0])[:, None] < sub.shape[0] - 12)
        sub[thin] = before[y0:y1, x0:x1][thin] * 0.5 + np.array(LEAF[1]) * 0.5     # the crown thinned out
        ys, xs = np.where(diff[:-12])
        for k in rng.choice(len(ys), size=min(len(ys), int(34 * s.size / 0.6)), replace=False) if len(ys) else []:
            i, j = xs[k] + x0, ys[k] + y0
            put(img, i, j, KAKI[2])
            put(img, i - 1, j, KAKI[3])
            put(img, i, j + 1, KAKI[1])
            put(img, i + 1, j + 1, KAKI[0])
        for _ in range(int(rng.integers(4, 9))):                         # fallen, some gone dark
            i = s.x + int(rng.normal(4, 7))
            j = s.y + int(rng.integers(0, 6))
            put(img, i, j, KAKI[int(rng.integers(0, 3))])
            put(img, i + 1, j, KAKI[0])


class Leiter:
    """A wooden ladder left leaning against a tree, a rung broken."""
    def __init__(s, x, y, h=16, seed=71):
        s.x, s.y, s.h, s.seed = x, y, h, seed

    def box(s):
        return (s.x - 2, s.y - s.h, s.x + 9, s.y + 2)

    def draw(s, img, G):
        broken = int(np.random.default_rng(s.seed).integers(1, s.h // 3))
        for d in range(s.h):
            lean = d // 4
            put(img, s.x + lean, s.y - d, WOOD[4])
            put(img, s.x + 5 + lean, s.y - d, WOOD[2])
            if d % 3 == 2 and d // 3 != broken:
                for i in range(1, 5):
                    put(img, s.x + lean + i, s.y - d, WOOD[3])
        for i in range(s.x + 1, s.x + 8):
            if 0 <= s.y + 1 < img.shape[0] and 0 <= i < img.shape[1]:
                img[s.y + 1, i] = img[s.y + 1, i] * 0.7


# ======================================================================== zone 4a: the mill, the bamboo, the paddies
CULM = [hx(c) for c in ['#2a3420', '#3c4a2c', '#53643a', '#6e7f4a', '#8c9a5e']]       # bamboo stems, dark .. lit
BLEAF = [hx(c) for c in ['#1a2416', '#26341e', '#344828', '#465e32', '#5c763e']]


WHEEL = [hx(c) for c in ['#17130f', '#241d18', '#33291f', '#45372b', '#5a4838', '#7a6248', '#957a58']]  # dark, wet timber
IRON = [hx(c) for c in ['#1c1d20', '#33353a', '#55585e']]


class Wasserrad:
    """The mill's waterwheel seen face on (its axle runs north-south, across the brook): two rings with the paddles
    between them, eight spokes two wide, an iron-banded hub, open between the spokes (the bank shows through, a
    little shaded), joints in the rims, moss and wet dark wood low down, two paddles broken off, a trickle into the
    brook. (x, y) its hub."""
    def __init__(s, x, y, r=17, seed=81):
        s.x, s.y, s.r, s.seed = x, y, r, seed

    def box(s):
        return (s.x - s.r - 3, s.y - s.r - 3, s.x + s.r + 4, s.y + s.r + 3)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        x, y, r = s.x, s.y, s.r
        NP = 16
        broken = set(int(k) for k in rng.choice(NP, 2, replace=False))
        tone = rng.uniform(-0.35, 0.35, NP)                            # each rim segment its own plank
        ri = r - 5                                                     # the inner ring
        for j in range(y - r - 4, y + r + 5):
            for i in range(x - r - 4, x + r + 5):
                dx, dy = i - x, j - y
                d = np.hypot(dx, dy)
                a = np.arctan2(dy, dx)
                u = (a + np.pi) / (2 * np.pi) * NP
                k = int(u) % NP
                lit = 3.2 - 1.3 * dx / r - 1.0 * dy / r + tone[k]          # light from the upper left
                lit -= 0.8 * max(0, dy / r - 0.35)                       # wet and dark low down
                sa = a % (np.pi / 4)
                sd = d * abs(np.sin(min(sa, np.pi / 4 - sa)))            # off the nearest spoke, in pixels
                pd = d * abs(np.sin(((u % 1) - 0.5) * 2 * np.pi / NP))   # off the nearest paddle
                joint = abs((u % 1) - 0.5) > 0.46
                c = None
                if r - 2 <= d < r + 0.6:                                 # outer ring
                    c = WHEEL[0] if joint else pick(WHEEL, lit + 1.1 - 1.6 * (d >= r - 0.4))
                elif ri - 1.6 <= d < ri:                                 # inner ring
                    c = WHEEL[1] if joint else pick(WHEEL, lit + 0.2)
                elif ri <= d < r - 2 and pd < 0.9 and k not in broken:   # paddles between the rings
                    c = pick(WHEEL, lit - 0.1 + 0.5 * (pd < 0.4))
                elif ri <= d < r - 2:
                    c = img[j, i] * 0.55 if 0 <= j < img.shape[0] and 0 <= i < img.shape[1] else None   # the gap: shadow
                elif r + 0.6 <= d < r + 3.2 and pd < 0.8 and k not in broken:   # paddle ends standing out
                    c = pick(WHEEL, lit - 0.4)
                elif d < 2.0:
                    c = pick(IRON, 1.6 - 0.6 * dx - 0.4 * dy)            # the axle end
                elif d < 3.6:
                    c = pick(IRON, 1.2 - 0.3 * dx / 3 - 0.3 * dy / 3) if abs(d - 2.8) < 0.5 else pick(WHEEL, lit + 0.4)
                elif d < ri - 1.6 and sd < 1.05:                         # spokes, two wide
                    c = pick(WHEEL, lit + 1.0 - 1.4 * (sd > 0.55))
                elif d < ri - 1.6 and 0 <= j < img.shape[0] and 0 <= i < img.shape[1]:
                    c = img[j, i] * 0.86                                 # open: the wheel's own shadow behind
                if c is not None:
                    if dy > r * 0.2 and g_at(G, i * 5, j * 3) < 0.22 and d >= ri - 1.6:
                        c = pick(MOSS, 1.4 + 0.8 * g_at(G, i, j))
                    put(img, i, j, c)
        for d in range(5):                                             # water running off the lowest paddles
            put(img, x - 3 + d, y + r + 2 + d % 2, hx('#a3aeb6'))
            if d % 2:
                put(img, x - 2 + d, y + r + 4, hx('#d6dde1'))


class Muehle:
    """The water mill (Suisha-goya): a small thatched house on the bank, its wheel turning no more on the brook
    side, a wooden flume on posts bringing the water from upstream onto the top of the wheel, moss on everything.
    (x, y) the house's foot; the wheel stands in front-right, in the brook."""
    def __init__(s, x, y, seed=82):
        s.x, s.y, s.seed = x, y, seed
        s.house = Minka(x, y, w=34, wall=12, roof=17, seed=seed, kind='kaya', ruin=0.55, pal=1, rich=True)
        s.wheel = Wasserrad(x - 33, y + 6, seed=seed + 1)     # upstream (west) of the house, on its gable side
        s.phase = 0                                            # the flume's water, for the slow loop

    def box(s):
        hb = s.house.box()
        return (s.x - 104, hb[1], hb[2], s.y + 26)

    def draw(s, img, G):
        s.house.draw(img, G)
        s.wheel.draw(img, G)
        wx, wy, r = s.wheel.x, s.wheel.y, s.wheel.r
        # the flume (kakehi): a plank trough on posts from a weir upstream on the bank onto the top of the wheel,
        # the ground falling away under it so the posts grow taller; water in it, glints drifting down (s.phase)
        x0, y0, x1, y1 = wx - 64, wy - 38, wx - 2, wy - r - 3          # drawn line: intake .. over the wheel
        gy0, gy1 = wy - 33, wy + r                                     # the ground under both ends
        n = x1 - x0
        for k in range(n + 1):
            t = k / n
            i, j = x0 + k, int(round(y0 + (y1 - y0) * t))
            put(img, i, j - 1, WHEEL[5] if k % 11 else WHEEL[2])       # back board's top edge, joints
            put(img, i, j, hx('#64717c') if (k + s.phase) % 9 else hx('#a3aeb6'))   # the water, seen into
            put(img, i, j + 1, hx('#4e5a65') if (k + s.phase + 4) % 18 else hx('#d6dde1'))
            put(img, i, j + 2, WHEEL[5] if k % 11 else WHEEL[2])       # front board, its top lit
            put(img, i, j + 3, WHEEL[3])
            put(img, i, j + 4, WHEEL[0])                               # its underside, in shadow
        for t in (0.08, 0.36, 0.64):                                   # the posts, clear of the wheel
            i = int(round(x0 + n * t))
            j0 = int(round(y0 + (y1 - y0) * t)) + 5
            for j in range(j0, int(round(gy0 + (gy1 - gy0) * t)) + 1):
                put(img, i, j, WHEEL[3])
                put(img, i + 1, j, WHEEL[1])
            put(img, i - 1, j0, WHEEL[2])                              # a cross piece under the trough
            put(img, i + 2, j0, WHEEL[2])
        for d in (-2, 2):                                              # the weir: two stakes in the brook
            for j in range(gy0 - 4, gy0 + 3):
                put(img, x0 - 2 + d, j, WHEEL[3] if j < gy0 else WHEEL[1])
        put(img, x0 - 2, gy0 - 2, hx('#a3aeb6'))
        for d in range(4):                                             # falling off its end onto the wheel
            if (d + s.phase) % 3:
                put(img, x1 + 1, y1 + 3 + d * 2 + s.phase % 2, hx('#d6dde1') if d == 0 else hx('#a3aeb6'))


class Bambus:
    """One clump of bamboo: a few tall culms with pale node rings, lit on their left, leaning a little, the leaves in
    fine dark sprays all up the top third. (x, y) the foot of the clump."""
    def __init__(s, x, y, n=5, h=64, seed=83):
        s.x, s.y, s.n, s.h, s.seed = x, y, n, h, seed

    def box(s):
        return (s.x - 16, s.y - int(s.h * 1.1) - 12, s.x + 18, s.y + 3)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        tops = []
        for k in range(s.n):
            x0 = s.x + int(rng.integers(-5, 6))
            lean = rng.uniform(-0.15, 0.15)
            h = int(s.h * rng.uniform(0.8, 1.1))
            node = int(rng.integers(6, 9))
            for d in range(h):
                i = int(round(x0 + lean * d))
                j = s.y - d
                ring = d % node == 0
                put(img, i, j, CULM[4] if ring else CULM[3])
                put(img, i + 1, j, CULM[3] if ring else CULM[1])
            tops.append((x0, lean, h))
        for x0, lean, h in tops:                                       # leaves: sprays down the top third
            for _ in range(70):
                d = h - rng.uniform(0, h * 0.4)
                tx, ty = x0 + lean * d, s.y - d
                a = rng.uniform(-np.pi, np.pi)
                rr = rng.uniform(1, 11)
                i, j = int(tx + np.cos(a) * rr), int(ty + np.sin(a) * rr * 0.6)
                lit = 2.8 - 0.22 * (i - tx) - 0.15 * (j - ty) + rng.normal(0, 0.5)
                for e in range(int(rng.integers(2, 4))):               # a leaf: a short stroke hanging down-out
                    put(img, i + e * (1 if a > -1.5 else -1), j + e // 2, pick(BLEAF, lit))


class Vogelscheuche:
    """A scarecrow left in a paddy, leaning: a pole, a cross arm with a tattered coat, a straw hat."""
    def __init__(s, x, y, seed=84):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - 7, s.y - 18, s.x + 9, s.y + 2)

    def draw(s, img, G):
        x, y = s.x, s.y
        for d in range(15):
            put(img, x + d // 6, y - d, WOOD[3])
        for i in range(-5, 7):
            put(img, x + 2 + i, y - 11 + (i > 3), WOOD[2])
        for j in range(y - 11, y - 5):                                 # the coat, torn at the hem
            for i in range(x - 2, x + 6):
                if j < y - 7 or (i + j) % 3:
                    put(img, i, j, pick(CLOTH, 2.2 - 0.3 * (i - x)))
        for i in range(-4, 7):                                         # the straw hat
            put(img, x + 2 + i, y - 15, pick(THATCH, 3.6 - 0.3 * i))
        for i in range(-1, 4):
            put(img, x + 2 + i, y - 16, pick(THATCH, 4.0 - 0.4 * i))
            put(img, x + 2 + i, y - 17, pick(THATCH, 3.2 - 0.4 * i))


def ndi_noise(seed, h, w):
    from scipy import ndimage as ndi
    n = ndi.gaussian_filter(np.random.default_rng(seed).normal(0, 1, (h, w)), 1.5)
    return n / (n.std() + 1e-9)
