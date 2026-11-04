#!/usr/bin/env python3
"""The inside of the cave as its own screen (Philip, 2026-11-04): exactly one view (180 x 400 art px), no
scrolling. Rock walls all round, built of single rocks like the ones outside; in the middle an open floor like
a clearing, the way out at the bottom. Drawn in the world's own ground tones and then put through the game's
mood (mood_map.mood: grade, flickering candle light, bloom, the Bayer raster at the light's edge), so it looks
like the rest of the world. On the floor: a tatami mat with a folded red blanket, a tea bowl, a candle with
wax runs on a flat stone, a little stone tower, a dried poppy in a cup; a puddle and moss at the mouth.
python3 cave_inside.py out.png [with_monk]"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..'))
from field6 import L1, MG, DG, K, R as POPPY, RD as POPPY_D  # noqa: E402
from berg_objects import SNOWR  # noqa: E402
from objects_north import ICE, boulder  # noqa: E402
import mood_map  # noqa: E402

W, H = 180, 400
CANDLE = (100, 188)            # the flame
MAT = (70, 196)                # middle of the mat
RAMP = np.array([K, DG, MG, L1], float)


def fbm(rng, scale, octs=4):
    out, a, t = np.zeros((H, W)), 1.0, 0.0
    for o in range(octs):
        n = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), scale / (2 ** o))
        out += a * n / (n.std() + 1e-9)
        t += a
        a *= 0.5
    return out / t


def floor_mask(rng):
    yy, xx = np.mgrid[0:H, 0:W]
    n = fbm(rng, 10)
    hall = ((xx - 90) / 66.0) ** 2 + ((yy - 200) / 112.0) ** 2 < 1 + 0.3 * n
    bay = ((xx - 46) / 28.0) ** 2 + ((yy - 118) / 30.0) ** 2 < 1 + 0.3 * n       # a side bay, so it is no egg
    bay2 = ((xx - 140) / 24.0) ** 2 + ((yy - 270) / 26.0) ** 2 < 1 + 0.3 * n
    passage = (np.abs(xx - 90 - 6 * np.sin(yy / 23.0)) < 15 + 2 * n) & (yy > 290)
    m = hall | bay | bay2 | passage
    return ndi.binary_closing(ndi.binary_opening(m, iterations=2), iterations=3)


def ground(rng, floor):
    """The world's flat tones and checker patterns (field6.ground), a shade darker, no grass: earth and grit."""
    yy, xx = np.mgrid[0:H, 0:W]
    chk = (xx + yy) % 2 == 0
    f = 0.45 + 0.16 * fbm(rng, 12) + ndi.gaussian_filter(rng.normal(0, 0.05, (H, W)), 1.0)
    img = np.empty((H, W, 3))
    pale, mid, dark = f > 0.56, (f <= 0.56) & (f > 0.36), f <= 0.36
    img[pale] = np.where(chk[pale, None], L1, MG)
    img[mid] = np.where(chk[mid, None], MG, DG)
    img[dark] = np.where(chk[dark, None], DG, K)
    img *= np.array([1.03, 1.0, 0.95])                                  # a touch of earth in the grey
    pebbles = (rng.random((H, W)) < 0.01) & floor
    img[pebbles] = L1
    img[np.roll(pebbles, 1, axis=0) & ~pebbles] = K                     # each with its little shadow
    return img


def rock(img, x, y, rx, ry, deep=False):
    """A rock in the old map's manner (gen_world.boulder): flat tones, lit to the upper left, dark foot."""
    yy, xx = np.mgrid[0:H, 0:W]
    e = ((xx - x) / rx) ** 2 + ((yy - y) / ry) ** 2
    sh = (e <= 1.5) & (yy > y) & (xx > x - 1)
    img[sh] = K
    m = e <= 1.0
    lit = (xx - x) + (yy - y) * 1.3 < -0.5
    base, hi, top = (DG, MG, L1) if deep else (MG, L1, WH_SOFT)
    img[m] = base
    img[m & lit] = hi
    img[m & lit & (e < 0.3)] = top
    img[m & (yy > y + ry * 0.4)] = K if deep else DG
    img[m & (np.abs(xx - x - 0.2 * rx) < 0.6) & (yy > y - ry * 0.2) & (yy < y + ry * 0.5)] = K   # a crack


WH_SOFT = np.array([206.0, 202.0, 196.0])


def mood_inside(src, light):
    """mood_map.mood without the drifting mist (none in a cave): grade, the flickering light, bloom, and the
    4x4 Bayer raster where the light falls, exactly as post.gdshader does."""
    yy, xx = np.mgrid[0:H, 0:W]
    em = (src[..., 0] > 190) & (src[..., 1] > 110) & (src[..., 2] < 140) & (src[..., 0] - src[..., 2] > 90)
    a = mood_map.grade(src)
    f = mood_map.flick(mood_map.KIND['candle'], 2 * np.pi / 8.0, (light['x'], light['y']))
    dx, dy = xx + 0.5 - light['x'], yy + 0.5 - light['y']
    d = np.hypot(dx, dy * 1.35) / light['r']
    L = light['k'] * f / (1 + 4 * d * d) * np.sqrt(np.clip(1 - d, 0, 1))
    r2 = dx * dx + dy * dy
    g = 0.0875 * np.exp(-r2 / 8) + 0.0221 * np.exp(-r2 / 72) + 0.00568 * np.exp(-r2 / 392)
    bloom = np.array([250.0, 190.0, 90.0]) * mood_map.GLOW['candle'] * f * g[..., None] * np.array([1.0, 0.8, 0.55])
    a = a * (1 + L[..., None] * mood_map.LCOL * 1.4) + bloom
    a[em] = np.maximum(a[em], src[em] * 1.05)
    eff = np.clip(L * 2.5 + bloom.sum(-1) / 90, 0, 1)
    eff[em] = 0
    bay = mood_map.BAYER[yy % 4, xx % 4]
    on = eff > bay * 0.8 + 0.1
    l2 = a.mean(-1) + 0.001
    q = np.floor(l2 / 22 + bay) * 22
    a[on] = a[on] * (q / l2)[on][:, None]
    return np.clip(a, 0, 255).astype(np.uint8)


def dist_floor_edge(floor, x, y):
    return ndi.distance_transform_edt(floor)[y, x]


def main(out, with_monk=False):
    rng = np.random.default_rng(73)
    yy, xx = np.mgrid[0:H, 0:W]
    floor = floor_mask(rng)
    img = ground(rng, floor)
    G = rng.random((H, W))
    CL = ndi.gaussian_filter(rng.random((H, W)), 0.65)
    CL = (CL - CL.min()) / (CL.max() - CL.min())
    dist_in = ndi.distance_transform_edt(~floor)
    img[~floor] = K * 0.7                                               # behind the rocks: black rock

    # the walls: like the old map's cliff foot - a row of big rocks along the floor's edge, darker ones behind
    edge = floor & ~ndi.binary_erosion(floor)
    gy, gx = np.gradient(ndi.gaussian_filter(floor.astype(float), 4))
    ey, ex = np.nonzero(edge)
    rows = []
    for depth, step, deep in ((26, 15, True), (10, 11, False)):
        last = []
        for k in rng.permutation(len(ey)):
            x0, y0 = int(ex[k]), int(ey[k])
            if any(abs(x0 - a_) < step and abs(y0 - b_) < step for a_, b_ in last):
                continue
            last.append((x0, y0))
            nl = np.hypot(gx[y0, x0], gy[y0, x0]) + 1e-6
            push = depth * rng.uniform(0.5, 1.0)
            rows.append((y0 - gy[y0, x0] / nl * push, x0 - gx[y0, x0] / nl * push,
                         rng.uniform(8, 14) * (1.2 if deep else 1), rng.uniform(6, 10) * (1.2 if deep else 1), deep))
    for y, x, rx, ry, deep in sorted(rows, key=lambda r: (not r[4], r[0])):
        rock(img, x, y, rx, ry, deep)
    for _ in range(14):                                                 # a few loose stones on the floor
        x, y = int(rng.integers(20, W - 20)), int(rng.integers(80, 360))
        if floor[y, x] and dist_floor_edge(floor, x, y) > 8:
            rock(img, x, y, rng.uniform(2, 3.5), rng.uniform(1.5, 2.5))
    # moss on the rocks by the mouth, where daylight reaches; a drip of ice down one wall
    moss = (~floor) & (yy > 300) & (dist_in < 10) & (fbm(rng, 4) > 0.3)
    img[moss] = img[moss] * 0.5 + np.array([70, 92, 60.0]) * 0.5
    for k in range(9):
        img[150 + k, 152] = ICE[min(4, 4 - k // 3)]

    # the mouth: snow blown in, icicles hanging over, a puddle of melt in front
    for y in range(H - 22, H):
        for x in range(64, 117):
            if floor[y, x] and G[y, x] < (y - (H - 22)) / 22.0:
                img[y, x] = SNOWR[5] if CL[y, x] > 0.4 else SNOWR[4]
    for x in range(70, 111, 3):
        for L in range(int(rng.integers(1, 4))):
            img[H - 30 + L, x] = ICE[4 - L]
    pud = (((xx - 84) / 9.0) ** 2 + ((yy - 340) / 3.5) ** 2 < 1) & floor
    img[pud] = np.array([52, 60, 72.0])
    img[pud & (np.abs(yy - 339) < 1) & (xx > 80) & (xx < 88)] = np.array([150, 166, 178.0])   # daylight in it

    # the tatami mat: woven straw rows, a dark cloth hem on its long sides, a folded red blanket at one end
    mx, my = MAT
    STRAW, STRAW_D, HEM = np.array([188, 168, 124.0]), np.array([150, 128, 90.0]), np.array([46, 54, 70.0])
    for y in range(my - 8, my + 9):
        for x in range(mx - 15, mx + 16):
            if y in (my - 8, my + 8):
                c = HEM if (x + y) % 5 else HEM * 1.3                  # the cloth hem, a stitch here and there
            elif x in (mx - 15, mx + 15):
                c = STRAW_D                                            # cut ends of the straw
                if G[y, x] < 0.3:
                    continue                                           # frayed
            else:
                row = (y - my) % 2 == 0
                seam = (x - mx) % 8 == 0
                c = STRAW * (0.92 if row else 1.0) * (0.82 if seam else 1.0) * (0.96 + 0.08 * CL[y, x])
            img[y, x] = c
    for x in range(mx - 14, mx + 17):                                  # it lies on the ground: a shadow under it
        img[my + 9, x] = K
    for y in range(my - 7, my + 9):
        img[y, mx + 16] = K
    for x in range(mx - 14, mx + 15):
        img[my - 7, x] = img[my - 7, x] * 1.12                         # the straw's lit upper edge
    for y in range(my - 7, my + 8):                                    # the blanket, folded over twice
        for x in range(mx + 6, mx + 14):
            fold = (y - my + 7) % 5 == 0
            img[y, x] = np.array([150, 62, 56.0]) * (1.18 if fold else 0.95 + 0.08 * CL[y, x])
    for x in range(mx + 6, mx + 14):
        img[my + 8, x] = np.array([90, 36, 34.0])                      # its shadow on the hem
    # tea bowl on the mat: dark glaze, light rim, green tea inside
    bx, by = mx - 8, my - 2
    for (u, v, c) in ((-2, 0, DG), (-1, 0, K), (0, 0, K), (1, 0, K), (2, 0, DG), (-1, 1, K), (0, 1, K), (1, 1, K),
                      (-2, -1, L1), (-1, -1, np.array([96, 120, 70.0])), (0, -1, np.array([110, 140, 80.0])),
                      (1, -1, np.array([96, 120, 70.0])), (2, -1, L1), (0, 2, DG)):
        img[by + v, bx + u] = c
    # the candle: a flat stone, the stub with wax runs, the flame (bright enough to glow by itself)
    cx, cy = CANDLE
    for (u, v) in ((-4, 4), (-3, 3), (-2, 3), (-1, 3), (0, 3), (1, 3), (2, 3), (3, 3), (4, 4), (-3, 4), (-2, 4),
                   (-1, 4), (0, 4), (1, 4), (2, 4), (3, 4)):
        img[cy + v, cx + u] = MG if v == 3 else DG
    for v in (0, 1, 2):
        img[cy + v, cx] = np.array([226, 218, 200.0])
    img[cy + 2, cx - 1] = np.array([210, 200, 182.0])
    img[cy + 2, cx + 1] = np.array([210, 200, 182.0])                  # wax runs
    img[cy - 1, cx] = np.array([253, 231, 160.0])
    img[cy - 2, cx] = np.array([242, 180, 74.0])
    img[cy - 3, cx] = np.array([217, 130, 46.0])
    # a little tower of three stones, a dried poppy in a clay cup
    for (sx, sy, rrx, rry) in ((122, 168, 4, 2.6), (122, 164, 3, 2.0), (122, 161, 2, 1.5)):
        rock(img, sx, sy, rrx, rry)
    ux, uy = 58, 176
    for (u, v) in ((-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1)):
        img[uy + v, ux + u] = np.array([132, 96, 72.0]) if v == 0 else np.array([100, 70, 52.0])
    img[uy - 1, ux] = DG
    img[uy - 2, ux] = DG                                               # its stalk
    for (u, v, c) in ((-1, -4, POPPY), (0, -4, POPPY), (1, -4, POPPY_D), (0, -5, POPPY), (-1, -3, POPPY_D),
                      (0, -3, K), (1, -3, POPPY)):
        img[uy + v, ux + u] = c

    if with_monk:
        sheet = np.array(Image.open(os.path.join(HERE, '..', '..', '..', 'assets', 'char', 'wanderer.png')).convert('RGBA'))
        f = sheet[16:32, 0:12].astype(float)
        x0, y0 = 84, 270
        a = f[..., 3:] / 255.0
        img[y0:y0 + 16, x0:x0 + 12] = img[y0:y0 + 16, x0:x0 + 12] * (1 - a) + f[..., :3] * a

    # daylight from the mouth (cool, before the grade) and the darkness of the inside
    day = np.clip(1 - np.hypot((xx - 90) * 1.5, (yy - H) * 0.85) / 150.0, 0, 1) ** 1.4
    dark = np.clip(0.62 + 0.38 * day, 0, 1)[..., None]
    img = img * dark + day[..., None] * np.array([18, 22, 30.0])
    light = {'x': cx + 0.5, 'y': cy - 1.5, 'r': 125.0, 'k': 1.5}
    Image.fromarray(mood_inside(np.clip(img, 0, 255), light)).save(out)


if __name__ == '__main__':
    main(sys.argv[1], len(sys.argv) > 2)
