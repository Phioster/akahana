#!/usr/bin/env python3
"""North zone 1 draft: the rock gate out of Kogarashi, the needle wood and the woodcutter's hut (plan step 50).
Canvas = north rows Y0..HN (new) on top of today's rows 0..OLD (the overlap), x 0..W.

Philip (2026-11-04): wide overhangs this time, nothing cut off - the new ground reaches down into the old in
clumps, the old ground runs up mirrored, firs of the north grow down into Kogarashi and between the east
wood's trees, the cliff wall becomes scattered rocks over a broad band.
python3 zone1_draft.py WORLD_DIR out.png"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
from berg_objects import Cabin, WoodShed, ChoppingBlock, Stump, FallenLog, Pine  # noqa: E402
import details  # noqa: E402
from details import footpath, rock, lantern  # noqa: E402
from scipy.interpolate import splprep, splev  # noqa: E402


def _through(pts, n=600):
    """A path that really passes its points (details.curve is one Bezier over all of them: it irons the bends out)."""
    p = np.array(pts, float).T
    tck, _ = splprep(p, s=0, k=min(3, len(pts) - 1))
    return np.array(splev(np.linspace(0, 1, n), tck)).T


details.curve = _through
from field6 import ground_organic, WH, L1, MG, DG  # noqa: E402

HN = 1200                     # north rows (the world grows by this)
Y0 = 500                      # first north row drawn
OLD = 300                     # today's rows drawn under it
W = 900
H = HN - Y0 + OLD
SEAM = HN - Y0                # canvas row of today's y 0
BAND = 320                    # how far the two sides reach into each other
HUT = (330, 860 - Y0)         # clearing centre (canvas)
GATE_X = 272


def fbm(rng, scale, octs=4, shape=(H, W)):
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


def today(world):
    """Today's top rows as the game shows them: ground with flowers, and the standing things (frame 0)."""
    g = np.array(Image.open(os.path.join(world, 'ground.png')).convert('RGB'))[:OLD, :W].astype(float)
    fl = np.array(Image.open(os.path.join(world, 'flowers.png')).convert('RGBA'))[:OLD, :W]
    m = fl[..., 3] > 0
    g[m] = fl[m][:, :3]
    w = json.load(open(os.path.join(world, 'world.json')))
    sprites = [s for s in w['sprites'] if s['x'] < W and s['foot'] < OLD + 40]
    return g, sprites


def paste_sprite(img, s, dy, root):
    p = os.path.join(root, s['name'] + '.png')
    if not os.path.exists(p):
        return
    a = np.array(Image.open(p).convert('RGBA'))[:, :s['w']].astype(float)
    y0, x0 = s['y'] + dy, s['x']
    h, w = a.shape[:2]
    ya, yb = max(0, y0), min(img.shape[0], y0 + h)
    xa, xb = max(0, x0), min(img.shape[1], x0 + w)
    if ya >= yb or xa >= xb:
        return
    sub = a[ya - y0:yb - y0, xa - x0:xb - x0]
    al = sub[..., 3:] / 255.0
    img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al


def snow_ground(rng, wood):
    """The north's ground: field6's grain under snow; where the wood is dense, needle floor shows through."""
    yy = np.mgrid[0:H, 0:W][0]
    up = np.clip((SEAM - yy) / (SEAM + 0.0), 0, 1)
    fog = np.clip(0.72 + 0.10 * fbm(rng, 18) - 0.30 * wood, 0, 1)
    flow = np.clip(0.18 + 0.10 * fbm(rng, 10), 0, 1)
    g = ground_organic(H, W, fog, flow, rng).astype(float)
    snow = (fbm(rng, 6) + 1.6 * up + 0.6 - 1.9 * wood + 0.35 * (rng.random((H, W)) - .5)) > 0
    sg = ndi.gaussian_filter(np.random.default_rng(12).random((H, W)), 0.7)
    sg = (sg - sg.min()) / (sg.max() - sg.min())
    g[snow] = np.where((sg > 0.48)[snow][:, None], WH, L1)
    g[snow & (sg < 0.18)] = MG
    floor = ~snow & (wood > 0.45)                                   # needles under the dense firs: cool, dark
    g[floor] = g[floor] * np.array([0.62, 0.68, 0.72])
    return g


def main(world, out):
    rng = np.random.default_rng(50)
    yy, xx = np.mgrid[0:H, 0:W]
    old_g, old_sprites = today(world)

    # ---- where the wood stands: sparse low down, dense higher and in the east; open at the hut and the gate
    east = smooth((xx - 380) / 260.0)
    up = (SEAM - yy) / 600.0
    wood = smooth(0.35 + 0.55 * up + 0.35 * east + 0.25 * fbm(rng, 40))
    clearing = (((xx - HUT[0]) / 125.0) ** 2 + ((yy - HUT[1] - 10) / 88.0) ** 2) < 1 + 0.25 * fbm(rng, 20)
    wood = np.where(clearing, 0.0, np.minimum(wood, 0.9))

    # ---- ground: the north's own, the old one mirrored upward, the two interlocking in clumps over BAND rows
    north = snow_ground(rng, wood)
    mirror = np.zeros((H, W, 3))
    k = np.clip(SEAM - yy, 0, OLD - 70)
    src = old_g.copy()                                               # paths must not be mirrored up: fill them from beside
    pathish = ((src[..., 0] - src[..., 2]) > 22) & (src[..., 0] > 140)
    pathish = ndi.binary_dilation(pathish, iterations=2)
    for _ in range(6):
        src[pathish] = np.roll(src, 9, axis=1)[pathish]
        pathish &= ((src[..., 0] - src[..., 2]) > 22) & (src[..., 0] > 140)
    mirror = src[64 + k, xx]                                         # row SEAM-d shows today's row 64+d (under the cliff)
    reach = np.where(yy < SEAM, smooth((yy - (SEAM - BAND)) / BAND), 1 - 0.6 * smooth((yy - SEAM) / 160.0))
    clumps = 0.5 + 0.28 * fbm(rng, 14) + 0.12 * fbm(rng, 3)          # patches, never single pixels
    take_old = clumps < reach
    img = np.where(take_old[..., None], mirror, north)
    img[yy >= SEAM] = np.where(take_old[yy >= SEAM][..., None], old_g[(yy - SEAM)[yy >= SEAM], xx[yy >= SEAM]],
                               north[yy >= SEAM])
    # today's cliff wall (rows 0..45, x < 560) dissolves: the north ground replaces it, rocks get strewn instead
    wall = (yy >= SEAM) & (yy < SEAM + 62 + 10 * fbm(rng, 8)) & (xx < 560 - 30 * fbm(rng, 12))
    img[wall] = north[wall]

    G = rng.random((H, W))
    CL = ndi.gaussian_filter(rng.random((H, W)), 0.65)
    CL = (CL - CL.min()) / (CL.max() - CL.min())

    # ---- paths: the old summit path runs on through the gate up to the hut; two branches leave it
    trunk = [(312, HUT[1] + 14), (296, HUT[1] + 90), (286, HUT[1] + 170), (258, SEAM - 150), (282, SEAM - 70),
             (266, SEAM + 10), (274, SEAM + 50), (277, SEAM + 100)]   # winding; overlaps the end of today's earth path
    footpath(img, trunk, G, width=1.6, bank=1.6, rng_seed=1, fade_from=0.93)
    footpath(img, [(300, HUT[1] - 4), (250, HUT[1] - 60), (190, HUT[1] - 150), (150, 0)], G, width=1.4,
             rng_seed=2, fade_from=0.55)                                   # to the cave
    footpath(img, [(345, HUT[1] + 4), (400, HUT[1] - 70), (480, HUT[1] - 150), (560, 0)], G, width=1.4,
             rng_seed=3, fade_from=0.55)                                   # to the gorge
    footpath(img, [(318, HUT[1] + 10), (352, HUT[1] + 6), (372, HUT[1] + 26)], G, width=1.0, bank=1.0,
             rng_seed=4)                                                    # door - woodpile - block
    # ---- things that stand: sorted by their foot so nearer ones overlap farther ones
    things = []
    # rocks over a broad band where the cliff wall stood, a pair framing the gate
    for (x, y, r) in [(GATE_X - 26, SEAM + 6, 9), (GATE_X + 30, SEAM + 2, 10)]:
        things.append((y, 'rock', (x, y, r)))
    for _ in range(90):
        x = int(rng.integers(8, 560))
        y = int(SEAM + 40 - rng.integers(0, 240) * rng.random())
        if abs(x - GATE_X) < 40 or clearing[min(y, H - 1), x]:
            continue
        things.append((y, "rock", (x, y, int(rng.integers(3, 8)))))
    # firs: dart throwing on a grid, spacing from the wood density (open stands low down, close but never a
    # wall up high); they grow down into today's rows, the east wood's own trees grow up between them
    occ = {}
    CELL = 8

    def free(x, y, r):
        for cy in range(int((y - r) // CELL), int((y + r) // CELL) + 1):
            for cx in range(int((x - r) // CELL), int((x + r) // CELL) + 1):
                for (tx, ty, tr) in occ.get((cx, cy), ()):
                    if ((x - tx) / max(r, tr)) ** 2 + ((y - ty) / (0.7 * max(r, tr))) ** 2 < 1:
                        return False
        return True

    def claim(x, y, r):
        occ.setdefault((int(x // CELL), int(y // CELL)), []).append((x, y, r))

    for s_ in old_sprites:                                            # today's trees keep their room
        claim(s_['x'] + s_['w'] // 2, SEAM + s_['foot'], 6 if s_['h'] > 30 else 3)
    east_trees = [s_ for s_ in old_sprites if s_['name'].startswith('e') and s_['h'] >= 36 and s_['frames'] == 1]
    for _ in range(60000):
        x = int(rng.integers(4, W - 4))
        y = int(rng.integers(30, SEAM + 260))
        d = wood[y, x] if y < SEAM else wood[SEAM - 1, x] * (1 - smooth((y - SEAM) / 260.0))
        if rng.random() > d or clearing[y, x] or (abs(x - GATE_X) < 16 and y > SEAM - 160) \
                or (abs(x - GATE_X) < 52 and abs(y - SEAM) < 24):
            continue
        r = 13 + 28 * (1 - d) ** 1.5
        if not free(x, y, r):
            continue
        claim(x, y, r)
        # in the east, low down, some of the east wood's own trees instead of a fir: the woods interlock
        mix = east[min(y, H - 1), x] * (1 - smooth((SEAM - y) / BAND)) if y < SEAM else 0.0
        if east_trees and rng.random() < 0.85 * mix:
            t = east_trees[int(rng.integers(len(east_trees)))]
            things.append((y, 'east', (t, x, y)))
            continue
        h = int(26 + 16 * d * rng.random() + 6 * rng.random())
        snow = float(np.clip(0.55 + 0.4 * (SEAM - y) / SEAM, 0.3, 0.95)) * (1 - 0.35 * d)
        things.append((y, 'pine', (x, y, h, int(rng.integers(1 << 30)), snow)))
    # the woodcutter's hut
    hx, hy = HUT
    things += [(hy, 'cabin', (hx - 28, hy)), (hy + 2, 'shed', (hx + 22, hy + 2)),
               (hy + 36, 'block', (hx + 44, hy + 36)),
               (hy + 50, 'stump', (hx - 48, hy + 50)), (hy + 22, 'stump', (hx - 86, hy + 22)),
               (hy - 14, 'stump', (hx + 84, hy - 14)),
               (hy + 62, 'log', (hx - 96, hy + 58, hx - 66, hy + 66)), (hy + 58, 'log', (hx + 70, hy + 60, hx + 96, hy + 48)),
               (hy + 34, 'lantern', (hx, hy + 30))]
    whole = [t for t in east_trees if t['y'] > 0]
    for s in old_sprites:
        if s['y'] <= 0 and whole and s['name'].startswith('e'):     # cut flat at today's top edge: a whole tree instead
            t = whole[int(rng.integers(len(whole)))]
            things.append((SEAM + s['foot'], 'east', (t, s['x'] + s['w'] // 2, SEAM + s['foot'])))
            continue
        things.append((SEAM + s['foot'], 'old', s))
    root = os.path.join(HERE, '..', '..', '..', 'assets', 'world', 'sprites')
    for _, kind, a in sorted(things, key=lambda t: t[0]):
        if kind == 'pine':
            x, y, h, seed, snow = a
            g = np.where(G < snow, G, 1.0)
            Pine(x, y, h, seed % 100000).draw(img, g, CL)
        elif kind == 'rock':
            rock(img, a[0], a[1], a[2], G, CL, int(a[0] * 7 + a[1]))
        elif kind == 'cabin':
            Cabin(a[0], a[1], w=50, wall=20, roof=19, seed=11).draw(img, G, CL)
        elif kind == 'shed':
            WoodShed(a[0], a[1], w=30, h=14, roof=10, seed=12).draw(img, G, CL)
        elif kind == 'block':
            ChoppingBlock(a[0], a[1], R=8, seed=13).draw(img, G, CL)
        elif kind == 'stump':
            Stump(a[0], a[1], r=5, seed=int(a[0])).draw(img, G, CL)
        elif kind == 'log':
            FallenLog(*a, r=3.3, seed=int(a[0])).draw(img, G, CL)
        elif kind == 'lantern':
            lantern(img, a[0], a[1], post=9)
        elif kind == 'old':
            paste_sprite(img, a, SEAM, root)
        elif kind == 'east':                                         # a copy of an east-wood tree, foot at (x, y)
            t, x, y = a
            paste_sprite(img, dict(t, x=x - t['w'] // 2, y=y - (t['foot'] - t['y'])), 0, root)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
