#!/usr/bin/env python3
"""North zone 3 draft: the mountain path in bends up the rocky slope, the lookout on its knoll, and the pass
between the peaks (plan step 50, places 6/7/8). Canvas = north rows 0..NY1 (zone 2's gorge at the bottom).
The peaks are heaps of the same angular rocks as the cave (facet_rock), snow on what faces up; beyond the
pass the world ends in mist, no edge. python3 zone3_draft.py out.png"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'east'))
from common import (fbm, smooth, wood_density, snow_ground, Firs, draw_things, noise_maps,  # noqa: E402
                    footpath, through)
from objects_north import Gorge, FootBridge, facet_rock, boulder  # noqa: E402
from objects_east import Jizo  # noqa: E402
from objects2 import Lantern3  # noqa: E402
from extras import Bench  # noqa: E402
from field6 import WH, L1  # noqa: E402

NY0, NY1, W = 0, 640, 1000
H = NY1 - NY0
PASS = (470, 112)
LOOK = (800, 400)
BRIDGE_X = 560

SERPENTINE = [(560, 528), (592, 508), (640, 490), (604, 462), (544, 444), (486, 424), (530, 392), (612, 366),
              (640, 346), (596, 318), (514, 300), (462, 270), (500, 236), (556, 206), (540, 176), (494, 152),
              PASS]
LOOKOUT = [(640, 490), (700, 474), (752, 446), (786, 418), LOOK]


def gorge_line(rng):
    xs = np.arange(0, 990)
    cy = 590 + 40 * np.sin(xs / 160.0) - 0.04 * xs + 6 * ndi.gaussian_filter1d(rng.normal(0, 1, len(xs)), 12) * 3
    hw = (14 + 5 * np.sin(xs / 47.0) + 4 * np.sin(xs / 113.0 + 1.3)
          + 3 * ndi.gaussian_filter1d(rng.normal(0, 1, len(xs)), 20) * 4) * np.minimum(1.0, np.minimum(xs / 60.0 + 0.4, (985 - xs) / 140.0))
    return xs, cy - NY0, np.maximum(hw, 0)


def ridge_mask(rng):
    """The peaks: high rock either side of the pass, a saddle where the path crosses; ragged, never a line."""
    yy, xx = np.mgrid[0:H, 0:W]
    n1, n2 = fbm(rng, 30, (H, W)), fbm(rng, 9, (H, W))
    gap = 120 + 40 * n1                                                  # half width of the saddle
    side = np.abs(xx - PASS[0]) - gap
    reach = 150 + 70 * np.sin(xx / 90.0) + 40 * n1 + 14 * n2 + np.clip(side, 0, 400) * 0.35   # higher away from the pass
    return (yy < reach) & (side > 0) | (yy < 40 + 20 * n2)


def main(out):
    rng = np.random.default_rng(53)
    yy, xx = np.mgrid[0:H, 0:W]
    ny = yy + NY0
    xs, cy, hw = gorge_line(np.random.default_rng(52))
    gorge = Gorge(xs, cy, hw)
    by = cy[BRIDGE_X]
    bridge = FootBridge(BRIDGE_X, int(by - hw[BRIDGE_X]) - 2, int(by + hw[BRIDGE_X]) + 1)
    ridge = ridge_mask(rng)

    wood = wood_density(rng, H, W, NY0) * 0.6 * smooth((ny - 120) / 300.0)   # up at the pass hardly a tree
    bare = fbm(rng, 10, (H, W)) + 0.5 * fbm(rng, 3, (H, W)) > 1.5 - 1.9 * smooth((560 - ny) / 360.0)
    img = snow_ground(rng, H, W, NY0, wood, bare=bare)
    G, CL = noise_maps(rng, H, W)

    paths = {'serpentine': (SERPENTINE, None), 'aussicht': (LOOKOUT, None)}
    pm = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(pm)
    for pts, _ in paths.values():
        d.line([tuple(p) for p in through(pts, 400)], fill=255, width=12)
    path_mask = np.array(pm) > 0

    gorge.draw(img, G, CL)
    for k, (pts, fade) in paths.items():
        footpath(img, pts, G, width=1.4, bank=1.5, rng_seed=7 + len(k), fade_from=fade)

    # the lookout's knoll: a snowy top, its east and south sides fall away as rock
    look_top = (((xx - LOOK[0]) / 44.0) ** 2 + ((yy - LOOK[1] + 6) / 26.0) ** 2) < 1 + 0.25 * fbm(rng, 6, (H, W))
    things = []
    knoll = (((xx - LOOK[0]) / 64.0) ** 2 + ((yy - LOOK[1] + 6) / np.where(yy > LOOK[1] - 6, 62.0, 40.0)) ** 2) < 1   # knoll + rim; below it reaches further: a fir there grows up over the rock
    keep = ndi.binary_dilation(gorge.mask(H, W), iterations=6) | path_mask | ridge | knoll | bridge.walk_mask(H, W)
    things += Firs().place(rng, wood, keep, NY0, tries=30000)
    for _ in range(320):                                                # loose rocks, more of them higher up
        x, y = int(rng.integers(6, W - 6)), int(rng.integers(10, H - 4))
        if rng.random() > 0.2 + 0.8 * smooth((560 - y) / 300.0) or keep[y, x]:
            continue
        things.append((y, 'rock', (x, y, int(rng.integers(3, 9)))))
    # stones set along the bends of the path, as if someone had kept it
    for p in SERPENTINE[2:-1:2]:
        for k in range(3):
            things.append((p[1] + 6, 'rock', (p[0] + 9 + 4 * k, p[1] + 6 - k, 3)))

    def extra(kind, a):
        if kind == 'east':
            a.draw(img, G)
        elif kind == 'facet':
            facet_rock(img, *a)
        elif kind == 'bench':
            Bench(*a).draw(img)
        elif kind == 'lantern3':
            x0, y0 = a[0] - 18, a[1] - 34
            sub = img[y0:y0 + 44, x0:x0 + 38]
            Lantern3(18, 34, None).draw(sub, 0.0, 8.0)
        elif kind == 'draw':
            a.draw(img, G, CL)
        elif kind == 'cairn':                                          # stones stacked smaller and smaller, snow on top
            cx, cy_ = a
            y = cy_
            for k, r in enumerate((4, 3, 3, 2)):
                boulder(img, cx + (k % 2), y, r, G, CL, cx * 7 + k)
                y -= int(1.5 * r) + 1

    # the ridge: heaps of angular rocks, the far ones first, snow on what faces up
    ry_, rx_ = np.nonzero(ridge & (rng.random((H, W)) < 0.012))
    for y, x in sorted(zip(ry_, rx_)):
        big = 1.0 + 0.8 * smooth((200 - y) / 200.0)
        things.append((y - 400, 'facet', (int(x), int(y), rng.uniform(9, 17) * big, rng.uniform(7, 12) * big,
                                          False, int(x * 3 + y * 7), True)))
    # the knoll at the lookout: its rocky flanks to the east and south, the top left open
    for k in range(70):
        a_ = rng.uniform(-0.5, 1.9)                                     # from east round to south-west
        x = int(LOOK[0] + np.cos(a_) * 48 + rng.normal(0, 3))
        y = int(LOOK[1] - 6 + np.sin(a_) * 28 + rng.normal(0, 2))
        if ndi.binary_dilation(path_mask, iterations=6)[min(H - 1, y), min(W - 1, x)]:
            continue                                                    # the path comes up here: no rock on it
        things.append((y, 'facet', (x, y, rng.uniform(5, 9), rng.uniform(4, 7), False, x * 5 + y, True)))
    things.append((LOOK[1] - 2, 'bench', (LOOK[0] - 6, LOOK[1] - 2)))
    things.append((LOOK[1] - 10, 'lantern3', (LOOK[0] + 20, LOOK[1] - 10)))
    # the pass: cairns, a snowed-in Jizo, a stone lantern
    for (cx, cy_) in ((PASS[0] - 30, PASS[1] + 6), (PASS[0] + 34, PASS[1] - 4), (PASS[0] - 54, PASS[1] - 18)):
        things.append((cy_, 'cairn', (cx, cy_)))                         # a little tower of stones each
    things.append((PASS[1] - 2, 'east', Jizo(PASS[0] + 16, PASS[1] - 2, seed=8, cap=True)))
    things.append((PASS[1] + 12, 'lantern3', (PASS[0] - 14, PASS[1] + 12)))
    things.append((bridge.y1, 'draw', bridge))
    draw_things(img, things, G, CL, extra)

    # snow on the Jizo's head and shoulders, he has stood here a long time
    jx, jy = PASS[0] + 16, PASS[1] - 2
    for (u, v) in ((-2, -15), (-1, -16), (0, -16), (1, -16), (2, -15), (-4, -9), (-3, -9), (3, -9), (4, -9)):
        if G[jy + v, jx + u] < 0.85:
            img[jy + v, jx + u] = WH
    # beyond the pass: the world ends in mist, thickening upward (a Bayer raster, as in the game)
    BAY = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0
    m = np.clip((70 - yy + 12 * fbm(rng, 20, (H, W))) / 70.0, 0, 1)
    on = m > BAY[yy % 4, xx % 4]
    img[on] = img[on] * 0.25 + np.array([214.0, 214, 212]) * 0.75
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out)


if __name__ == '__main__':
    main(sys.argv[1])
