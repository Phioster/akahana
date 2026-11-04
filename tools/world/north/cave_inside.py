#!/usr/bin/env python3
"""The inside of the cave as its own screen (Philip, 2026-11-04): exactly one view, no scrolling. Rock walls all
round the edge, in the middle an open floor like a clearing, the way out at the bottom. On the floor the little
resting place: straw mat, tea bowl, a candle on a flat stone; its warm light is all there is, besides the
pale daylight falling in through the mouth. python3 cave_inside.py out.png [with_monk]"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'lib'))
from berg_objects import STONE, LOG, FL, SNOWR  # noqa: E402
from objects_north import DARK, ICE, _q, boulder  # noqa: E402

W, H = 180, 400                # the game's view in art pixels
CANDLE = (104, 196)
MAT = (70, 200)


def floor_mask(rng):
    """The open floor: a lumpy round hall, a passage down to the mouth at the bottom."""
    yy, xx = np.mgrid[0:H, 0:W]
    n = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 10) * 10
    hall = ((xx - 90) / 64.0) ** 2 + ((yy - 205) / 118.0) ** 2 < 1 + 0.18 * n
    bay = ((xx - 52) / 26.0) ** 2 + ((yy - 120) / 30.0) ** 2 < 1 + 0.2 * n       # a side bay, so it is not an egg
    wob = 6 * np.sin(yy / 23.0) + 0.6 * n
    passage = (np.abs(xx - 90 - wob) < 15 + 0.5 * n) & (yy > 300)
    m = hall | bay | passage
    m = ndi.binary_opening(m, iterations=2)
    return ndi.binary_closing(m, iterations=3)


def main(out, with_monk=False):
    rng = np.random.default_rng(71)
    yy, xx = np.mgrid[0:H, 0:W]
    floor = floor_mask(rng)
    G = rng.random((H, W))
    CL = ndi.gaussian_filter(rng.random((H, W)), 0.65)
    CL = (CL - CL.min()) / (CL.max() - CL.min())

    # light: the candle (warm, round) and the daylight through the mouth (pale, from the bottom)
    cd = np.hypot(xx - CANDLE[0], (yy - CANDLE[1]) * 1.25)
    warm = np.clip(1 - cd / 85.0, 0, 1) ** 1.6
    day = np.clip(1 - np.hypot((xx - 90) * 1.6, (yy - H) * 0.9) / 140.0, 0, 1) ** 1.5
    lit = 0.12 + 0.75 * warm + 0.55 * day

    dist_in = ndi.distance_transform_edt(~floor)                        # how deep into the rock a wall pixel is
    below_floor = np.zeros((H, W), int)                                 # rows down to the floor (wall faces look south)
    for x in range(W):
        nxt = H + 50
        for y in range(H - 1, -1, -1):
            if floor[y, x]:
                nxt = y
            below_floor[y, x] = nxt - y
    img = np.zeros((H, W, 3))
    strata = np.sin(yy * 0.85 + 0.35 * xx + 2 * ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 4))
    for y in range(H):
        for x in range(W):
            g, cl, L = G[y, x], CL[y, x], lit[y, x]
            if floor[y, x]:                                             # trodden earth and grit
                v = 0.05 + 0.5 * L + 0.1 * (cl - 0.5)
                c = _q(LOG, v, g)
                if cl > 0.86:
                    c = _q(STONE, 0.2 + 0.4 * L, g)                     # grit and pebbles
            elif below_floor[y, x] <= 14 and dist_in[y, x] <= 14 and y < 260:   # far wall's face, rising from the floor
                t = below_floor[y, x] / 16.0
                v = 0.1 + 0.55 * L * (1 - 0.5 * t) + 0.1 * strata[y, x] + 0.1 * (cl - 0.5)
                c = _q(STONE, v, g)
            else:                                                       # the rock seen from above: darker further in
                v = 0.05 + 0.35 * L * np.exp(-dist_in[y, x] / 18.0) + 0.12 * strata[y, x] + 0.15 * (cl - 0.5)
                c = _q(DARK, v + 0.15 * np.exp(-dist_in[y, x] / 10.0), g)
            warmth = 0.45 * warm[y, x] * (1 if floor[y, x] or below_floor[y, x] <= 16 else 0.5)
            img[y, x] = c * (1 - warmth) + FL[2] * warmth
            if day[y, x] > 0.05:                                        # cool daylight at the mouth
                a = 0.5 * day[y, x]
                img[y, x] = img[y, x] * (1 - a) + SNOWR[4] * a
    # crags: many rock lumps along the wall's foot, lit from the candle's side, so the edge is broken rock
    edge = floor & ~ndi.binary_erosion(floor, iterations=1)
    ey, ex = np.nonzero(edge)
    order = rng.permutation(len(ey))
    placed = []
    for k in order:
        x0, y0 = int(ex[k]), int(ey[k])
        if any(abs(x0 - px) < 7 and abs(y0 - py) < 7 for px, py in placed[-60:]):
            continue
        placed.append((x0, y0))
        rx_, ry_ = rng.uniform(5, 12), rng.uniform(4, 9)
        # push the lump's middle a little into the rock
        gy_, gx_ = np.gradient(ndi.gaussian_filter(floor.astype(float), 3))[0][y0, x0], np.gradient(ndi.gaussian_filter(floor.astype(float), 3))[1][y0, x0]
        nl = np.hypot(gx_, gy_) + 1e-6
        cx_, cy_ = x0 - gx_ / nl * rx_ * 0.45, y0 - gy_ / nl * ry_ * 0.45
        tx, ty = CANDLE[0] - cx_, CANDLE[1] - cy_
        tl = np.hypot(tx, ty) + 1e-6
        for y in range(int(cy_ - ry_) - 1, int(cy_ + ry_) + 2):
            for x in range(int(cx_ - rx_) - 1, int(cx_ + rx_) + 2):
                if not (0 <= x < W and 0 <= y < H):
                    continue
                u, v = (x - cx_) / rx_, (y - cy_) / ry_
                e = u * u + v * v
                if e > 1 + 0.15 * (CL[y, x] - 0.5):
                    continue
                nz = np.sqrt(max(0.0, 1 - min(e, 1)))
                face = (u * tx + v * ty) / tl                              # turned towards the candle?
                L = lit[y, x]
                val = 0.08 + 0.55 * L * (0.35 + 0.65 * max(0.0, face)) + 0.15 * nz * L - 0.12 * (v > 0.55)
                c = _q(STONE, val + 0.08 * (CL[y, x] - 0.5), G[y, x])
                w = 0.4 * warm[y, x] * max(0.0, face)
                img[y, x] = c * (1 - w) + FL[2] * w
    # the floor: darker damp patches and grit, so it is ground and not a flat fill
    damp = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 6) * 6 > 0.8
    m = floor & damp & ~ndi.binary_dilation(edge, iterations=3)
    img[m] = img[m] * 0.78
    # snow blown in at the mouth, icicles hanging over it
    for y in range(H - 18, H):
        for x in range(60, 121):
            if floor[y, x] and G[y, x] < (y - (H - 18)) / 18.0:
                img[y, x] = _q(SNOWR, 0.75 + 0.2 * CL[y, x], G[y, x])
    # a few stones lying about the edges, a drip of ice down one wall
    for (x, y, r) in ((40, 150, 4), (138, 262, 5), (128, 120, 3), (56, 300, 3)):
        if floor[y, x]:
            boulder(img, x, y, r, np.ones_like(G) * 0.9, CL, x * 7 + y)   # no snow in here
    for k in range(10):
        img[150 + k, 147] = _q(ICE, 0.8 - 0.05 * k, G[150 + k, 147])
    # the resting place: straw mat, tea bowl, the candle on its flat stone
    STRAW = np.array([196, 164, 104.0])
    mx, my = MAT
    for y in range(my - 6, my + 7):
        for x in range(mx - 13, mx + 14):
            hem = y in (my - 6, my + 6) or x in (mx - 13, mx + 13)
            img[y, x] = STRAW * ((0.62 if hem else 0.84 + 0.16 * ((x + 2 * y) % 3 == 0)) * (0.55 + 0.45 * lit[y, x]))
    bx, by = 90, 190
    for (u, v, c) in ((0, 0, STONE[1]), (1, 0, STONE[1]), (2, 0, STONE[1]), (3, 0, STONE[1]), (4, 0, STONE[1]),
                      (0, -1, STONE[4]), (1, -1, np.array([150, 170, 160.0])), (2, -1, np.array([170, 190, 180.0])),
                      (3, -1, np.array([150, 170, 160.0])), (4, -1, STONE[4]), (1, 1, STONE[0]), (2, 1, STONE[0]),
                      (3, 1, STONE[0])):
        img[by + v, bx + u] = c
    cx, cy = CANDLE
    for x in range(cx - 3, cx + 4):
        img[cy + 1, x] = STONE[3]
        img[cy + 2, x] = STONE[1]
    for k in range(4):
        img[cy - k, cx] = np.array([224, 214, 196.0]) if k < 3 else img[cy - k, cx]
    img[cy - 3, cx] = FL[4]
    img[cy - 4, cx] = FL[3]
    img[cy - 5, cx] = FL[2]
    if with_monk:
        here = os.path.dirname(os.path.abspath(__file__))
        sheet = np.array(Image.open(os.path.join(here, '..', '..', '..', 'assets', 'char', 'wanderer.png')).convert('RGBA'))
        f = sheet[16:32, 0:12].astype(float)                            # facing up, into the cave
        x0, y0 = 84, 262
        a = f[..., 3:] / 255.0
        img[y0:y0 + 16, x0:x0 + 12] = img[y0:y0 + 16, x0:x0 + 12] * (1 - a) + f[..., :3] * a * (0.6 + 0.4 * lit[y0 + 8, x0 + 6])
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out)


if __name__ == '__main__':
    main(sys.argv[1], len(sys.argv) > 2)
