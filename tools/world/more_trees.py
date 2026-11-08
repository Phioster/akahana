"""More broadleaf and cherry trees in the open meadows (Philip and his girlfriend, 2026-11-08): cherries mostly in the
poppy meadow, broadleaves (a few turned) in the south's grassland and by the west lake, both round the village.
Chosen by rule from the finished maps with fixed dice: open walkable land, off the paths, away from water, houses
and whatever stands already. -> list of (kind, x, y, seed, leaf) in world pixels."""
import numpy as np
from scipy import ndimage as ndi

# region (x0, y0, x1, y1), share of cherries, trees per 100 x 100 px
REGIONS = [((960, 1520, 1440, 3000), 0.35, 0.4),          # the poppy meadow (Philip: "too many cherries")
           ((900, 3000, 1800, 4060), 0.05, 0.45),          # the south's grassland
           ((40, 1900, 900, 3300), 0.25, 0.4),             # round the village
           ((40, 3300, 900, 4640), 0.05, 0.4)]             # the west lake's meadows
KEEP_FREE = [('baum', 110)]                                # the camp's great cherry stands alone
NO_TREES = [(0, 2870, 360, 3140)]                        # the rice terraces stay open
START_FREE = 340                                           # round the start no new tree at all: only the great cherry (Philip)
LEAVES = [None, None, None, 'orange', None, 'rost', None, 'gold']


def place(kind_map, walk, mat, boxes, start=None, seed=601):
    rng = np.random.default_rng(seed)
    H, W = walk.shape
    path = np.kron(mat == 1, np.ones((2, 2), bool))[:H, :W]
    bad = ndi.binary_dilation(path, iterations=10) | ndi.binary_dilation(kind_map > 0, iterations=14) | ~walk
    for x0, y0, x1, y1, *name in boxes:
        for nm, r in KEEP_FREE:
            if name and name[0] == nm:
                cx, cy = (x0 + x1) // 2, y1
                bad[max(0, cy - r):cy + r // 2, max(0, cx - r):cx + r] = True
        big = (x1 - x0) > 34                                         # houses and big trees keep more room
        m = 40 if big else 14
        bad[max(0, y0 - m):y1 + m, max(0, x0 - m):x1 + m] = True
    for x0, y0, x1, y1 in NO_TREES:
        bad[y0:y1, x0:x1] = True
    out, taken = [], []

    def crowded(x, y):                                                 # crowns must not grow into each other
        return any(((x - a) / 48.0) ** 2 + ((y - b) / 32.0) ** 2 < 1 for a, b in taken)
    for (rx0, ry0, rx1, ry1), cherry, dens in REGIONS:
        n = int((rx1 - rx0) * (ry1 - ry0) / 10000 * dens)
        tries = 0
        got = 0
        while got < n and tries < n * 60:
            tries += 1
            x, y = int(rng.integers(rx0, rx1)), int(rng.integers(ry0, ry1))
            if bad[y, x] or crowded(x, y):
                continue
            group = 1 + (rng.random() < 0.35) + (rng.random() < 0.15)  # now and then two or three together
            kind = 'kirsch' if rng.random() < cherry else 'laub'
            if start is not None and np.hypot(x - start[0], y - start[1]) < START_FREE:
                continue
            for k in range(group):
                if k:                                                  # the next one a crown's width away
                    a_ = rng.uniform(0, 2 * np.pi)
                    gx, gy = int(x + np.cos(a_) * rng.uniform(50, 64)), int(y + np.sin(a_) * rng.uniform(34, 44))
                else:
                    gx, gy = x, y
                if not (0 <= gx < W and 0 <= gy < H) or bad[gy, gx] or (k and crowded(gx, gy)):
                    continue
                taken.append((gx, gy))
                sd = int(rng.integers(1, 9999))
                if kind == 'kirsch':                                   # each grown its own: trunk, forks, spread
                    form = dict(trunk=float(rng.uniform(9.0, 12.5)), width=float(rng.uniform(2.8, 3.4)),
                                depth=int(rng.choice([5, 5, 6])), fill=0.05)   # slim trunk, blossom before it (Philip)
                else:                                                  # broadleaves from young to old
                    form = dict(size=float(rng.choice([0.9, 1.05, 1.2, 1.35, 1.5], p=[0.2, 0.3, 0.25, 0.15, 0.1])),
                                leaf=LEAVES[int(rng.integers(0, len(LEAVES)))], dense=True)
                out.append((kind, gx, gy, sd, form))
            got += 1
    return out
