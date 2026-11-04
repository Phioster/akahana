#!/usr/bin/env python3
"""North zone 2 draft: the gorge with its footbridge and the cave with its little find (plan step 50, places 4/5),
from the hut of zone 1 up to the first bends of the mountain path. Canvas = north rows NY0..NY1, x 0..W.
python3 zone2_draft.py out.png"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (fbm, smooth, wood_density, snow_ground, Firs, hut_things, draw_things, noise_maps,  # noqa: E402
                    footpath, through, HN)
from objects_north import Gorge, FootBridge, CaveMound  # noqa: E402

NY0, NY1, W = 250, 1000, 1000
H = NY1 - NY0
BRIDGE_X = 560
CAVE = (150, 705)             # foot of the cave mouth, north coordinates


def gorge_line(rng):
    xs = np.arange(0, 990)
    cy = 590 + 40 * np.sin(xs / 160.0) - 0.04 * xs + 6 * ndi.gaussian_filter1d(rng.normal(0, 1, len(xs)), 12) * 3
    hw = (14 + 5 * np.sin(xs / 47.0) + 4 * np.sin(xs / 113.0 + 1.3) + 3 * ndi.gaussian_filter1d(rng.normal(0, 1, len(xs)), 20) * 4) * np.minimum(1.0, np.minimum(xs / 60.0 + 0.4, (985 - xs) / 140.0))
    return xs, cy - NY0, np.maximum(hw, 0)


def main(out):
    rng = np.random.default_rng(52)
    yy, xx = np.mgrid[0:H, 0:W]
    ny = yy + NY0
    xs, cy, hw = gorge_line(rng)
    gorge = Gorge(xs, cy, hw)
    gm = gorge.mask(H, W)
    by = cy[BRIDGE_X]
    bridge = FootBridge(BRIDGE_X, int(by - hw[BRIDGE_X]) - 2, int(by + hw[BRIDGE_X]) + 1)
    cave = CaveMound(CAVE[0], CAVE[1] - NY0)
    cave_solid = cave.solid(H, W)

    # ground: snow over field6 grain, bare wind-swept rock growing in above the gorge
    wood = wood_density(rng, H, W, NY0)
    hut = (((xx - 330) / 92.0) ** 2 + ((ny - 868) / 64.0) ** 2) < 1 + 0.25 * fbm(rng, 20, (H, W))
    wood = np.where(hut, 0.0, np.minimum(wood, 0.8))
    bare = fbm(rng, 10, (H, W)) + 0.5 * fbm(rng, 3, (H, W)) > 1.7 - 1.7 * smooth((620 - ny) / 320.0)
    img = snow_ground(rng, H, W, NY0, wood, bare=bare)
    G, CL = noise_maps(rng, H, W)

    # paths (north coordinates in, canvas out)
    def P(pts):
        return [(x, y - NY0) for x, y in pts]
    south_end, north_end = (BRIDGE_X, int(by + hw[BRIDGE_X]) + 5 + NY0), (BRIDGE_X, int(by - hw[BRIDGE_X]) - 6 + NY0)
    paths = {
        'schlucht': ([(345, 864), (392, 800), (452, 730), (520, 660), (548, 612), south_end], None),
        'hoehle': ([(300, 858), (262, 806), (205, 752), (160, 716)], None),
        'serpentine': ([north_end, (590, 512), (640, 492), (600, 460), (540, 440), (480, 420)], 0.6),
        'aussicht': ([(640, 492), (700, 478), (760, 450)], 0.4),
    }
    pm = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(pm)
    for pts, fade in paths.values():
        d.line([tuple(p) for p in through(P(pts), 300)], fill=255, width=14)
    path_mask = np.array(pm) > 0

    gorge.draw(img, G, CL)                                       # the crack lies in the ground: drawn first
    cave.draw(img, G, CL)                                        # so does the hill: it shades the ground it rises from
    for k, (pts, fade) in paths.items():
        footpath(img, P(pts), G, width=1.5, bank=1.5, rng_seed=hash(k) % 1000, fade_from=fade)

    front = (np.abs(xx - CAVE[0]) < 26) & (ny > CAVE[1] - 4) & (ny < CAVE[1] + 30)    # the cave mouth stays in view
    keep = ndi.binary_dilation(gm, iterations=6) | ndi.binary_dilation(cave_solid, iterations=6) | hut | path_mask | front
    keep |= bridge.walk_mask(H, W)
    things = Firs().place(rng, wood, keep, NY0)
    things += hut_things(NY0)
    for _ in range(260):                                          # rocks: more of them the higher it goes
        x, y = int(rng.integers(6, W - 6)), int(rng.integers(10, H - 4))
        if rng.random() > 0.15 + 0.85 * smooth((700 - (y + NY0)) / 300.0) or keep[y, x]:
            continue
        things.append((y, 'rock', (x, y, int(rng.integers(3, 9)))))
    things.append((bridge.y1, 'bridge', bridge))
    for (dx, dy, h) in ((-30, -34, 16), (22, -40, 14), (-8, -46, 17)):   # small firs up on the mound: it is land
        things.append((CAVE[1] - NY0 + dy, 'pine', (CAVE[0] + dx, CAVE[1] - NY0 + dy, h, 900 + dx, 0.9)))

    def extra(kind, a):
        a.draw(img, G, CL)
    draw_things(img, things, G, CL, extra)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out)



if __name__ == '__main__':
    main(sys.argv[1])
