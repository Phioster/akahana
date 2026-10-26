#!/usr/bin/env python3
"""Draft of zone 1 for the approval page: the poppy field continued south of the camp, five chunks wide,
with the waymark stone, the wall remains and the scarecrow - in two variants, in the game's mood.

    python3 tools/world/south/zone1_draft.py OUTDIR
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..'))
import field6  # noqa: E402
from field6 import ground_organic, patches, CMAP, DG  # noqa: E402
import extras  # noqa: E402
from berg_objects import Pine  # noqa: E402
import mood_map  # noqa: E402
from objects_south import Wegstein, Mauer, Vogelscheuche  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
W, OLD_W, OLD_H = 900, 540, 1200
CTX = 160                                   # rows of the old world shown above the seam
NEW = 600                                   # zone 1: three chunk rows
SEAM = 8                                    # old rows that may take new poppies (patches kept them bare)


def old_context(w):
    full = mood_map.composite(w)                              # the old world exactly, objects included
    out = np.zeros((CTX, W, 3))
    out[:, :OLD_W] = full[OLD_H - CTX:]
    return out


def placeholder_forest(img, G, CL, rng):
    """East of the old map, rows 0-5: for now a closed edge of firs (the eastern wood comes later)."""
    h = img.shape[0]
    fog = np.full((CTX, W - OLD_W), 0.5)
    img[:CTX, OLD_W:] = ground_organic(CTX, W - OLD_W, fog, np.zeros_like(fog), rng)
    for row in range(CTX - 96, CTX + 4, 14):
        for x in range(OLD_W + 2, W + 8, 8):
            Pine(x + rng.integers(-3, 4), row + rng.integers(-3, 4), int(rng.integers(30, 42)),
                 int(rng.integers(0, 999))).draw(img, G, CL)


def edge_firs(img, G, CL, rng):
    """The west and east world edges keep their fir rows as the old map has them."""
    for y in range(CTX + 10, img.shape[0] + 30, 13):
        for x in (2 + rng.integers(-2, 3), W - 4 + rng.integers(-2, 3)):
            Pine(x, y + rng.integers(-3, 4), int(rng.integers(30, 40)), int(rng.integers(0, 999))).draw(img, G, CL)


def field(rng):
    H = NEW
    yy, xx = np.mgrid[0:H, 0:W]

    def fbm(s, seed):
        n = ndi.gaussian_filter(np.random.default_rng(seed).normal(0, 1, (H, W)), s)
        return n / n.std()
    fog = np.clip(0.70 + 0.10 * fbm(18, 104), 0, 1)
    flow = np.clip(0.20 + 0.10 * fbm(10, 105), 0, 1)
    ground = ground_organic(H, W, fog, flow, rng)
    return ground, flow


def render(kind, w, seed=7):
    rng = np.random.default_rng(seed)
    field6.HEADS[:] = field6.make_heads(np.random.default_rng(31))
    G = np.random.default_rng(3).random((CTX + NEW, W))
    CL = ndi.gaussian_filter(np.random.default_rng(4).random((CTX + NEW, W)), 2)
    CL = (CL - CL.min()) / (CL.max() - CL.min())
    img = np.zeros((CTX + NEW, W, 3))
    img[:CTX] = old_context(w)
    ctx = img[:CTX].copy()
    placeholder_forest(img, G, CL, rng)
    img[:CTX, :OLD_W] = ctx[:, :OLD_W]                         # the old world stays exactly as it is
    ground, flow = field(rng)
    img[CTX:] = ground
    for d in range(16):                                        # the ground runs on: mirrored old rows, thinning out
        take = G[CTX + d, :OLD_W] < 1 - d / 16
        img[CTX + d, :OLD_W][take] = ctx[CTX - 1 - d, :OLD_W][take]

    # a trodden trail that begins in the poppies below the camp and forks at the waymark
    trail_a = [(250, CTX + 4), (262, CTX + 70), (300, CTX + 150), (318, CTX + 260), (300, CTX + 380),
               (322, CTX + 520), (360, CTX + 600)]
    trail_b = [(300, CTX + 150), (380, CTX + 175), (480, CTX + 210), (600, CTX + 250), (700, CTX + 320),
               (760, CTX + 420), (790, CTX + 600)]
    prng = np.random.default_rng(91)
    G2 = np.random.default_rng(9).random(img.shape[:2])
    for pts in (trail_a, trail_b):
        trodden = img.copy()
        pm, pc, pd_, pw_ = extras.path_mask(img.shape[0], W, pts, prng)
        extras.draw_path(trodden, pm, pc, pd_, pw_, prng)
        fade = np.clip((np.arange(img.shape[0]) - CTX) / 50.0, 0, 1)[:, None]   # it begins in the poppies
        use = pm & (G2 < fade)
        img[use] = trodden[use]

    things = [Wegstein(306, CTX + 146, kind), Vogelscheuche(612, CTX + 330, kind),
              Mauer([(110, CTX + 300), (140, CTX + 296), (172, CTX + 304), (205, CTX + 318), (226, CTX + 336)])]
    blocked = np.zeros(img.shape[:2], bool)
    for t in things:
        x0, y0, x1, y1 = t.box()
        blocked[max(0, y1 - 8):y1, max(0, x0):x1] = True
    path = np.zeros(img.shape[:2], bool)
    for pts in (trail_a, trail_b):
        for a, b in zip(pts, pts[1:]):
            for u in np.linspace(0, 1, 80):
                px, py = int(a[0] + (b[0] - a[0]) * u), int(a[1] + (b[1] - a[1]) * u)
                path[max(0, py - 2):py + 3, max(0, px - 3):px + 4] = True

    heads = np.zeros((img.shape[0], W, 4), np.uint8)          # poppies over the whole new field
    fl = np.zeros(img.shape[:2])
    fl[CTX:] = flow
    fl[CTX - SEAM:CTX] = flow[:SEAM][::-1]                    # the old field's last rows were left bare
    F = patches(img.shape[0], W, fl, blocked | path, rng, 600000)
    for (x, y, k, ph) in F:
        head = field6.HEADS[k]
        h = len(head)
        for s_ in range(h, h + 2):
            for sx_ in (x + 1, x + 2):
                if y + s_ < img.shape[0] and (sx_ + y + s_) % 2 == 0:
                    img[y + s_, sx_] = DG
        for j, row in enumerate(head):
            for i, ch in enumerate(row):
                if ch != '.' and y + j < img.shape[0] and x + i < W:
                    heads[y + j, x + i, :3] = CMAP[ch]
                    heads[y + j, x + i, 3] = 255
    m = heads[..., 3] > 0
    old_heads = ctx[:, :OLD_W].copy()
    img[m] = heads[m][:, :3]
    img[:CTX - SEAM, :OLD_W] = old_heads[:CTX - SEAM]          # above the seam band the old world is untouched
    keep = ~m[CTX - SEAM:CTX, :OLD_W]
    img[CTX - SEAM:CTX, :OLD_W][keep] = old_heads[CTX - SEAM:][keep]

    for t in sorted(things, key=lambda t: t.box()[3]):        # upright things over the poppies
        t.draw(img, G)
    edge_firs(img, G, CL, rng)

    lights = [dict(l, y=l['y'] - (OLD_H - CTX)) for l in w['lights']]
    fake = dict(w, lights=lights, wisps=[])
    return mood_map.mood(np.clip(img, 0, 255), fake, 2.0)


if __name__ == '__main__':
    out = sys.argv[1]
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    for kind in ('a', 'b'):
        im = Image.fromarray(render(kind, w))
        im.save(os.path.join(out, f'zone1_{kind}.png'))
        print('ok', kind, im.size, flush=True)
