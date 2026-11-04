"""Shared pieces of the north drafts (zone 2 on; zone 1 keeps its own approved copy): noise, the snow ground,
paths that really pass their points, fir placement by a density map, and drawing things by their foot.
Coordinates are canvas pixels; `ny0` is the north row of canvas row 0 (north rows: today's y 0 = HN)."""
import os
import sys

import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import splprep, splev

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
import details  # noqa: E402
from berg_objects import Cabin, WoodShed, ChoppingBlock, Stump, FallenLog, Pine, STONE  # noqa: E402
from details import footpath, rock, lantern  # noqa: E402
from field6 import ground_organic, WH, L1, MG  # noqa: E402

HN = 1200
HUT = (330, 860)              # the woodcutter's clearing, north coordinates


def through(pts, n=600):
    p = np.array(pts, float).T
    tck, _ = splprep(p, s=0, k=min(3, len(pts) - 1))
    return np.array(splev(np.linspace(0, 1, n), tck)).T


details.curve = through       # footpath() then follows its points instead of one Bezier over all of them


def fbm(rng, scale, shape, octs=4):
    out = np.zeros(shape)
    a, t = 1.0, 0.0
    for o in range(octs):
        n = ndi.gaussian_filter(rng.normal(0, 1, shape), scale / (2 ** o))
        out += a * n / (n.std() + 1e-9)
        t += a
        a *= 0.5
    return out / t


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def wood_density(rng, H, W, ny0):
    """As zone 1: the needle wood is thickest around the hut's height and thins out up towards the mountains."""
    yy, xx = np.mgrid[0:H, 0:W]
    ny = yy + ny0
    east = smooth((xx - 380) / 260.0)
    rise = smooth((HN - ny) / 300.0)
    fall = smooth((HUT[1] - 40 - ny) / 320.0)
    return smooth((0.15 + 0.6 * rise + 0.3 * east) * (1 - 0.8 * fall) + 0.2 * fbm(rng, 40, (H, W)))


def snow_ground(rng, H, W, ny0, wood, bare=None):
    """field6's grain under snow (more of it higher up); needle floor under dense firs; bare rock where `bare`."""
    yy = np.mgrid[0:H, 0:W][0]
    up = np.clip((HN - (yy + ny0)) / float(HN), 0, 1)
    fog = np.clip(0.72 + 0.10 * fbm(rng, 18, (H, W)) - 0.30 * wood, 0, 1)
    flow = np.clip(0.18 + 0.10 * fbm(rng, 10, (H, W)), 0, 1)
    g = ground_organic(H, W, fog, flow, rng).astype(float)
    snow = (fbm(rng, 6, (H, W)) + 1.6 * up + 0.6 - 1.9 * wood + 0.35 * (rng.random((H, W)) - .5)) > 0
    sg = ndi.gaussian_filter(np.random.default_rng(12).random((H, W)), 0.7)
    sg = (sg - sg.min()) / (sg.max() - sg.min())
    g[snow] = np.where((sg > 0.48)[snow][:, None], WH, L1)
    g[snow & (sg < 0.18)] = MG
    floor = ~snow & (wood > 0.45)
    g[floor] = g[floor] * np.array([0.62, 0.68, 0.72])
    if bare is not None:                                            # wind-swept rock: grey stone grain, snow in the cracks
        v = 0.7 + 0.2 * fbm(rng, 3, (H, W)) + 0.15 * (sg - 0.5)        # light grey rock, never a black blot
        idx = np.clip((v * (len(STONE) - 1)).astype(int), 0, len(STONE) - 1)
        stone = STONE[idx] * 0.55 + np.array(L1) * 0.45
        crack = bare & (sg > 0.62)
        g[bare] = stone[bare]
        g[crack] = np.array(WH) * 0.92
    return g


class Firs:
    """Dart throwing on a grid: spacing from the density, nothing in `keep_out`."""
    CELL = 8

    def __init__(s):
        s.occ = {}

    def free(s, x, y, r):
        C = s.CELL
        for cy in range(int((y - r) // C), int((y + r) // C) + 1):
            for cx in range(int((x - r) // C), int((x + r) // C) + 1):
                for (tx, ty, tr) in s.occ.get((cx, cy), ()):
                    if ((x - tx) / max(r, tr)) ** 2 + ((y - ty) / (0.7 * max(r, tr))) ** 2 < 1:
                        return False
        return True

    def claim(s, x, y, r):
        s.occ.setdefault((int(x // s.CELL), int(y // s.CELL)), []).append((x, y, r))

    def place(s, rng, wood, keep_out, ny0, tries=60000):
        H, W = wood.shape
        out = []
        for _ in range(tries):
            x, y = int(rng.integers(4, W - 4)), int(rng.integers(20, H))
            d = wood[y, x]
            if rng.random() > d or keep_out[y, x]:
                continue
            r = 17 + 30 * (1 - d) ** 1.5
            if not s.free(x, y, r):
                continue
            s.claim(x, y, r)
            ny = y + ny0
            stunted = ny < 700                                       # up the slopes: crooked little firs
            h = int((15 + 7 * rng.random()) if stunted else (26 + 16 * d * rng.random() + 6 * rng.random()))
            snow = float(np.clip(0.55 + 0.4 * (HN - ny) / HN, 0.3, 0.95)) * (1 - 0.35 * d)
            out.append((y, 'pine', (x, y, h, int(rng.integers(1 << 30)), snow)))
        return out


def hut_things(ny0):
    """The approved clearing of zone 1, shifted into this canvas."""
    hx, hy = HUT[0], HUT[1] - ny0
    return [(hy, 'cabin', (hx - 20, hy)), (hy + 1, 'shed', (hx + 17, hy + 1)), (hy + 25, 'block', (hx + 30, hy + 25)),
            (hy + 34, 'stump', (hx - 34, hy + 34)), (hy + 16, 'stump', (hx - 60, hy + 16)),
            (hy - 10, 'stump', (hx + 58, hy - 10)),
            (hy + 44, 'log', (hx - 68, hy + 40, hx - 48, hy + 46)), (hy + 40, 'log', (hx + 48, hy + 42, hx + 66, hy + 34)),
            (hy + 24, 'lantern', (hx, hy + 20))]


def draw_things(img, things, G, CL, extra=None):
    """Everything that stands, nearest last. `extra(kind, args)` draws kinds this module does not know."""
    for _, kind, a in sorted(things, key=lambda t: t[0]):
        if kind == 'pine':
            x, y, h, seed, snow = a
            Pine(x, y, h, seed % 100000).draw(img, np.where(G < snow, G, 1.0), CL)
        elif kind == 'rock':
            from objects_north import boulder                       # whole little rocks, not half-buried slabs
            boulder(img, a[0], a[1], max(2, int(a[2] * 0.9)), G, CL, int(a[0] * 7 + a[1]))
        elif kind == 'cabin':
            Cabin(a[0], a[1], w=34, wall=13, roof=14, seed=11, win=5, winh=5, doorw=5).draw(img, G, CL)
        elif kind == 'shed':
            WoodShed(a[0], a[1], w=20, h=10, roof=7, seed=12).draw(img, G, CL)
        elif kind == 'block':
            ChoppingBlock(a[0], a[1], R=5, seed=13, tall=5, handle=8, head='klein').draw(img, G, CL)
        elif kind == 'stump':
            Stump(a[0], a[1], r=4, seed=int(a[0])).draw(img, G, CL)
        elif kind == 'log':
            FallenLog(*a, r=2.6, seed=int(a[0])).draw(img, G, CL)
        elif kind == 'lantern':
            lantern(img, a[0], a[1], post=7)
        elif extra is not None:
            extra(kind, a)


def noise_maps(rng, H, W):
    G = rng.random((H, W))
    CL = ndi.gaussian_filter(rng.random((H, W)), 0.65)
    return G, (CL - CL.min()) / (CL.max() - CL.min())


__all__ = ['through', 'fbm', 'smooth', 'wood_density', 'snow_ground', 'Firs', 'hut_things', 'draw_things',
           'noise_maps', 'footpath', 'rock', 'HN', 'HUT', 'STONE']
