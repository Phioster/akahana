"""What stands about in the empty country between the places (Philip and his girlfriend, 2026-11-08): benches,
a Jizo and a cart by the paths; straw bales and stooks in groups on the open meadows; woodpiles, stumps, logs and
stone heaps scattered. Only where nothing else stands near; the start stays as it is. Fixed dice.
-> list of (kind, x, y, seed) in world pixels."""
import numpy as np
from scipy import ndimage as ndi

REGIONS = [(40, 1900, 900, 4640), (900, 2500, 1800, 4060)]      # the west and the south's meadows
ALONG = {'bank': 10, 'jizo': 5, 'karren': 3}                    # by the paths
GROUPS = {'ballen': 4, 'kegel': 5}                               # on the open meadows, in groups
LOOSE = {'stumpf': 10, 'stamm': 7}                                 # scattered (woodpiles belong to walls, stone heaps vanish in the grass)
START_FREE = 340
ROOM = 46                                                        # nothing else this near


def place(kind_map, walk, mat, boxes, start, seed=701):
    rng = np.random.default_rng(seed)
    H, W = walk.shape
    path = np.kron(mat == 1, np.ones((2, 2), bool))[:H, :W]
    dpath = ndi.distance_transform_edt(~path)
    taken = np.zeros((H, W), bool)
    for x0, y0, x1, y1, *_ in boxes:
        taken[max(0, y0 - 8):y1 + ROOM // 2, max(0, x0 - ROOM // 2):x1 + ROOM // 2] = True
    water = ndi.binary_dilation(kind_map > 0, iterations=12)
    region = np.zeros((H, W), bool)
    for x0, y0, x1, y1 in REGIONS:
        region[y0:y1, x0:x1] = True
    yy, xx = np.ogrid[:H, :W]
    region &= np.hypot(xx - start[0], yy - start[1]) >= START_FREE
    ok = region & walk & ~water
    out = []

    def claim(x, y, r=ROOM):
        taken[max(0, y - r):y + r // 2, max(0, x - r):x + r] = True

    def pick(mask, n, kind, spread=160):
        ys, xs = np.nonzero(mask[::4, ::4])
        order = rng.permutation(len(ys))
        got, near = 0, []
        for k in order:
            x, y = int(xs[k] * 4), int(ys[k] * 4)
            if taken[y, x] or any(np.hypot(x - a, y - b) < spread for a, b in near):
                continue
            near.append((x, y))
            yield x, y
            got += 1
            if got >= n:
                return

    by_path = ok & (dpath > 9) & (dpath < 13)
    for kind, n in ALONG.items():
        for x, y in pick(by_path, n, kind, spread=220):
            out.append((kind, x, y, int(rng.integers(1, 9999))))
            claim(x, y)
    open_m = ok & (dpath > 40)
    for kind, n in GROUPS.items():
        for x, y in pick(open_m, n, kind, spread=260):
            m = int(rng.integers(2, 5))
            for k in range(m):                                    # a loose row across the field
                step = (34, 42) if kind == 'ballen' else (20, 28)   # bales two wide must not overlap
                gx = x + k * int(rng.integers(*step)) - (m - 1) * step[0] // 2
                gy = y + int(rng.integers(-6, 7)) + (k % 2) * 8
                if 0 <= gx < W and 0 <= gy < H and ok[gy, gx]:
                    out.append((kind, gx, gy, int(rng.integers(1, 9999))))
            claim(x, y, ROOM + m * 14)
    for kind, n in LOOSE.items():
        for x, y in pick(ok & (dpath > 16), n, kind, spread=200):
            out.append((kind, x, y, int(rng.integers(1, 9999))))
            claim(x, y)
    return out


def make(kind, x, y, sd):
    import objects_land as L
    import objects_south as osu
    import objects_west as ow
    r = np.random.default_rng(sd)
    if kind == 'bank':
        return ow.SanfteBank(x, y)
    if kind == 'jizo':
        return L.Jizo(x, y, seed=sd)
    if kind == 'karren':
        return osu.Karren(x, y, seed=sd)
    if kind == 'ballen':
        return L.Heuballen(x, y, n=int(r.choice([1, 1, 2, 3])), seed=sd)
    if kind == 'kegel':
        return L.Strohkegel(x, y, h=int(r.integers(14, 19)), seed=sd)
    if kind == 'holz':
        return ow.Holzstapel(x, y, seed=sd)
    if kind == 'stumpf':
        return osu.Baumstumpf(x, y, r=int(r.integers(4, 7)))
    if kind == 'stamm':
        L_ = int(r.integers(18, 28))
        a = r.uniform(-0.4, 0.4)
        return osu.Stamm(x - L_ // 2, y - int(a * L_ / 2), x + L_ // 2, y + int(a * L_ / 2), r=int(r.integers(2, 4)))
    if kind == 'steine':
        return osu.Steinhaufen(x, y, seed=sd)


# how wide the grass lies flat under each (lake_boats.flatten's L): the thing stands in the meadow, not on it
FLAT = {'bank': 22, 'jizo': 10, 'karren': 26, 'kegel': 16, 'stumpf': 10, 'stamm': 22}


def flat_width(kind, thing):
    if kind == 'ballen':
        return 16 if thing.n == 1 else 30
    return FLAT[kind]
