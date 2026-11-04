#!/usr/bin/env python3
"""North zone 4 draft: the mountain lake, half frozen, with its waterfall over a rock step; out of it the river
that today begins in the east wood at (1260, 300), and the river path down to the stone bridge (plan step 50,
places 9/10). Canvas = world x X0..X1, north rows NY0..HN plus today's rows 0..OLD under them, with the wide
overhangs of zone 1 (ground in clumps, the woods growing into each other, no line anywhere).
python3 zone4_draft.py WORLD_DIR out.png"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..', 'south'))
from common import fbm, smooth, snow_ground, wood_density, Firs, draw_things, noise_maps, footpath, through, HN  # noqa: E402
from objects_north import facet_rock, ICE  # noqa: E402
from objects_lake import paint_lake  # noqa: E402
from berg_objects import SNOWR  # noqa: E402

X0, X1 = 800, 1700
NY0 = 300
OLD = 320
W = X1 - X0
SEAM = HN - NY0                        # canvas row of today's y 0
H = SEAM + OLD
BAND = 300
LAKE = (1250, 680)                     # north coordinates
FALL_X = 1252


def C(x, y):
    """north coordinates -> canvas"""
    return x - X0, y - NY0


def today(world):
    g = np.array(Image.open(os.path.join(world, 'ground.png')).convert('RGB'))[:OLD, X0:X1].astype(float)
    fl = np.array(Image.open(os.path.join(world, 'flowers.png')).convert('RGBA'))[:OLD, X0:X1]
    m = fl[..., 3] > 0
    g[m] = fl[m][:, :3]
    w = json.load(open(os.path.join(world, 'world.json')))
    return g, [s for s in w['sprites'] if X0 - 60 < s['x'] < X1 and s['foot'] < OLD + 40]


def paste(img, s, x, foot, root):
    p = os.path.join(root, s['name'] + '.png')
    if not os.path.exists(p):
        return
    a = np.array(Image.open(p).convert('RGBA'))[:, :s['w']].astype(float)
    y0, x0 = foot - (s['foot'] - s['y']), x - s['w'] // 2
    h, w = a.shape[:2]
    ya, yb, xa, xb = max(0, y0), min(img.shape[0], y0 + h), max(0, x0), min(img.shape[1], x0 + w)
    if ya < yb and xa < xb:
        sub = a[ya - y0:yb - y0, xa - x0:xb - x0]
        al = sub[..., 3:] / 255.0
        img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al


def band(pts, width, n=500):
    im = Image.new('L', (W, H), 0)
    ImageDraw.Draw(im).line([tuple(p) for p in through(pts, n)], fill=255, width=width, joint='curve')
    return np.array(im) > 0


FALL_FRAMES = 8
FRAMES_OUT = os.environ.get('FALL_FRAMES_OUT')   # e.g. /tmp/f%02d.png: the waterfall's frames for a preview


def fall_frame(img, G, f):
    """One frame of the waterfall: the streaks run down 1 px a frame, foam and icicle-drips change."""
    # the waterfall: a ragged ribbon of white water down the rock step, streaks running down, icicles at its sides
    fx = C(FALL_X, 0)[0]
    top, bot = C(0, 556)[1], C(0, 596)[1]
    frng = np.random.default_rng(9)
    ffoam = np.random.default_rng(100 + f).random(G.shape)             # the spray flickers
    flow = np.random.default_rng(7).random((16, G.shape[1]))           # the water's grain, flowing 2 px a frame (loops in 8)
    wob = ndi.gaussian_filter1d(frng.normal(0, 1, bot - top + 1), 2) * 2
    streaks = frng.random(16)
    for y in range(top, bot):
        k = y - top
        half = 2.5 + 1.2 * k / (bot - top) + 0.8 * wob[k]               # widening as it falls
        cx = fx + 0.6 * wob[k]
        for x in range(int(cx - half - 1), int(cx + half + 2)):
            u = abs(x - cx) / half
            if u > 1.1:
                continue
            col = streaks[(x - fx) % 16]
            if u > 0.85:
                c = np.array([150, 184, 204.0])                          # the thin edge, the rock showing through
            elif col < 0.25 and (y - f + int(col * 40)) % 8 < 4:
                c = SNOWR[4]                                             # a darker streak running down
            else:
                c = SNOWR[6] if flow[(y - 2 * f) % 16, x] < 0.7 else SNOWR[5]
            img[y, x] = c
        for side in (-1, 1):                                             # icicles hanging off the step beside it
            if frng.random() < 0.35 and k < (bot - top) * 0.6:
                ix = int(cx + side * (half + 2 + frng.integers(0, 4)))
                img[y, ix] = ICE[4] if frng.random() < 0.6 else ICE[3]
    for y in range(bot - 3, bot + 9):                                    # foam and spray where it meets the lake
        for x in range(fx - 13, fx + 14):
            d = np.hypot((x - fx) / 13.0, (y - bot - 2) / 6.0)
            if d < 1 and ffoam[y, x] < (1 - d) * 0.9:
                img[y, x] = SNOWR[6] if ffoam[y, x] < 0.45 else SNOWR[5]


def main(world, out):
    rng = np.random.default_rng(54)
    yy, xx = np.mgrid[0:H, 0:W]
    ny = yy + NY0
    old_g, old_sprites = today(world)
    root = os.path.join(HERE, '..', '..', '..', 'assets', 'world', 'sprites')

    # water: the lake (west half frozen), the brook feeding the fall, the river out of it into the east wood
    lc = C(*LAKE)
    n = fbm(rng, 18, (H, W))
    lake = (((xx - lc[0]) / 150.0) ** 2 + ((yy - lc[1]) / 92.0) ** 2) < 1 + 0.35 * n
    lake = ndi.binary_opening(lake, iterations=3)
    ice = lake & (xx + 0.5 * (yy - lc[1]) < lc[0] - 55 + 30 * fbm(rng, 8, (H, W)))   # the west part; the fall drops into open water
    river_pts = [C(1252, 740), C(1272, 860), C(1238, 960), C(1270, 1070), C(1255, 1160), C(1262, 1300),
                 C(1266, 1400), C(1270, 1520)]
    rb = band(river_pts, 15)
    mouth = rb & (yy < lc[1] + 120)
    lake = ndi.binary_closing(lake | mouth, iterations=8) & ~(rb & (yy > lc[1] + 60) & ~lake)   # a funnel into the river, no snow tongues
    lake = ndi.binary_opening(lake, iterations=2)
    river = rb & ~lake
    brook = band([C(1191, 348), C(1214, 400), C(1206, 440), C(1240, 500), C(FALL_X, 556)], 4)
    step = (np.abs(yy - C(0, 566)[1] - 6 * np.sin(xx / 23.0)) < 9) & (np.abs(xx - C(FALL_X, 0)[0]) < 85 + 15 * n)
    water = lake | river | brook

    # where the wood stands: dense below (it is the east wood's own top), thinning up the slope; open water and shore
    rise = smooth((HN - ny) / 300.0)
    fall = smooth((620 - ny) / 260.0)                                    # above the lake hardly a tree
    wood = smooth((0.08 + 0.45 * rise) * (1 - 0.9 * fall) + 0.2 * fbm(rng, 40, (H, W)))   # open like zone 1, never a wall
    shore = ndi.binary_dilation(lake, iterations=14)
    wood = np.where(shore | ndi.binary_dilation(river | brook, iterations=6), 0.0, np.minimum(wood, 0.5))

    # ground: the north's, interlocking in clumps with today's (reflected upward, its paths left out), no line
    north = snow_ground(rng, H, W, NY0, wood)
    grass = (north[..., 1] - north[..., 0] > 12) & (yy < SEAM - 150)       # the ground generator's green tufts: up here dead and grey
    north[grass] = north[grass].mean(-1, keepdims=True) * np.array([1.0, 0.98, 0.97])
    src = old_g.copy()
    row = np.where(yy >= SEAM, yy - SEAM, np.clip(SEAM - yy, 0, OLD - 1))
    ref = np.where((yy >= SEAM)[..., None], old_g[np.clip(row, 0, OLD - 1), xx], src[np.clip(row, 0, OLD - 1), xx])
    reach = np.where(yy < SEAM, smooth((yy - (SEAM - BAND)) / BAND), 1 - 0.3 * smooth((yy - SEAM) / 120.0))
    clumps = 0.5 + 0.28 * fbm(rng, 14, (H, W)) + 0.12 * fbm(rng, 3, (H, W))
    img = np.where(((clumps < reach) & (reach > 0.01))[..., None], ref, north)   # no stray patch of today's ground far up
    G, CL = noise_maps(rng, H, W)

    paint_lake(img, 0, lake & ~ice, ndi.binary_dilation(~(lake | river), iterations=4) & lake & ~ice, rng, rimless=river)
    paint_lake(img, 0, river, ndi.binary_dilation(~(river | lake), iterations=3) & river, rng, rimless=lake)   # one water, no mud line at the mouth
    # the frozen half: pale ice, cracks, snow blown onto it in drifts
    v = fbm(rng, 14, (H, W))
    img[ice] = np.where((v > 0.35)[ice][:, None], np.array([150, 168, 178.0]), np.array([126, 146, 158.0]))   # dull grey-blue, never white like the fall
    cr = np.abs(fbm(rng, 9, (H, W)))
    crack = ice & (cr < 0.025) & (rng.random((H, W)) < 0.8)          # thin dark cracks running across
    img[crack] = np.array([92, 110, 124.0])
    drift = ice & (fbm(rng, 6, (H, W)) + 0.3 * (rng.random((H, W)) - .5) > 0.75)
    img[drift] = SNOWR[6]
    img[ndi.binary_dilation(ice, iterations=1) & ~ice & ~lake] = SNOWR[4]      # its edge rimed white
    # the brook above the fall: ice under a dusting of snow, open water only in a few small holes
    bv = rng.random((H, W))
    img[brook] = np.where((bv < 0.5)[brook][:, None], ICE[3], np.where((bv < 0.8)[brook][:, None], ICE[4], SNOWR[6]))
    hole = brook & (fbm(rng, 2, (H, W)) > 1.1) & ~ndi.binary_erosion(~brook, iterations=1)
    img[hole] = np.array([72, 94, 110.0])
    bank_ = ndi.binary_dilation(brook, iterations=1) & ~brook
    img[bank_ & (rng.random((H, W)) < 0.7)] = SNOWR[5]

    paths = {'fluss': [C(1300, 792), C(1296, 862), C(1264, 960), C(1294, 1070), C(1282, 1160), C(1290, 1300),
                       C(1310, 1400), C(1338, 1520)],     # along the river, a little above its east bank
             'see': [C(800, 420), C(870, 455), C(960, 520), C(1040, 610), C(1078, 660), C(1094, 690)]}
    near_lake = ndi.binary_dilation(lake, iterations=6)
    c = through(paths['see'], 400)
    stop = next(i for i, (x, y) in enumerate(c) if near_lake[int(y), int(x)])
    paths['see'] = [tuple(p) for p in c[:stop:40]] + [tuple(c[stop])]   # it ends on the shore, not out on the ice
    for k, pts in paths.items():
        footpath(img, pts, G, width=1.5, bank=1.5, rng_seed=31 + len(k))
    path_mask = band(paths['fluss'], 12) | band(paths['see'], 12)
    # down in the east wood the snow is gone: there the river path is trodden earth, as the wood's own paths
    earth = band(paths['fluss'], 3) & (rng.random((H, W)) < 0.9)
    k_ = smooth((yy - (SEAM - 260)) / 160.0)[earth]
    tone = np.where((rng.random((H, W)) < 0.5)[earth][:, None], np.array([112, 98, 82.0]), np.array([92, 80, 68.0]))
    img[earth] = img[earth] * (1 - k_[:, None]) + tone * k_[:, None]

    things = []
    keep = ((np.abs(xx - C(FALL_X, 0)[0]) < 40) & (yy > C(0, 500)[1]) & (yy < C(0, 600)[1])) | ndi.binary_dilation(water, iterations=5) | ndi.binary_dilation(brook, iterations=22) | np.roll(ndi.binary_dilation(lake | river, iterations=20), 18, axis=0) | ndi.binary_dilation(path_mask, iterations=9) | ndi.binary_dilation(step, iterations=22)   # no fir half hidden behind the step's rocks
    occ = Firs()
    for s in old_sprites:
        occ.claim(s['x'] + s['w'] // 2 - X0, SEAM + s['foot'], 6 if s['h'] > 30 else 3)
    firs = occ.place(rng, wood, keep, NY0, tries=50000)
    east_trees = [s for s in old_sprites if s['name'].startswith('e') and s['h'] >= 36 and s['frames'] == 1 and s['y'] > 0]
    for t in firs:                                                   # low down some of the east wood's own trees instead
        y, x = t[0], t[2][0]
        mix = 1 - smooth((SEAM - y) / BAND) if y < SEAM else 0.0
        if east_trees and rng.random() < 0.85 * mix:
            things.append((y, 'east', (east_trees[int(rng.integers(len(east_trees)))], x, y)))
        else:
            things.append(t)
    gone = ndi.binary_dilation(river, iterations=4) | ndi.binary_dilation(path_mask, iterations=10)
    for s in old_sprites:                                            # today's trees: whole where cut at the old top,
        cx, foot = s['x'] + s['w'] // 2 - X0, SEAM + s['foot']       # none left standing in the river or on the path
        if not (0 <= cx < W) or gone[min(H - 1, foot), cx]:
            continue
        if s['y'] <= 0 and east_trees and s['name'].startswith('e'):
            things.append((foot, 'east', (east_trees[int(rng.integers(len(east_trees)))], cx, foot)))
        else:
            things.append((foot, 'old', s))
    # the spring: the brook comes out from under a heap of rocks, a little dark pool in front
    sx_, sy_ = C(1190, 348)
    for dx, dy, r in [(-9, -6, 7), (8, -7, 7), (0, -12, 6), (-16, -1, 5), (15, -2, 5), (-4, -18, 4)]:
        things.append((sy_ + dy, 'rock', (sx_ + dx, sy_ + dy, r)))
    # the rock step the water falls over, rocks round the shore, a few loose ones up the slope
    sy, sx = np.nonzero(step & (rng.random((H, W)) < 0.05))
    for y, x in sorted(zip(sy, sx)):
        if abs(x - C(FALL_X, 0)[0]) > 5:
            things.append((y, 'facet', (int(x), int(y), rng.uniform(7, 12), rng.uniform(5, 9), False, int(x * 3 + y), True)))
    ey, ex = np.nonzero(ndi.binary_dilation(lake, iterations=3) & ~lake & (rng.random((H, W)) < 0.012) & ~keep[..., ] | (
        ndi.binary_dilation(lake, iterations=3) & ~lake & (rng.random((H, W)) < 0.006)))
    keep_mouth = ndi.binary_dilation(river, iterations=12)
    for y, x in zip(ey, ex):
        if not path_mask[y, x] and not keep_mouth[y, x]:
            things.append((y, 'rock', (int(x), int(y), int(rng.integers(3, 7)))))
    for _ in range(140):
        x, y = int(rng.integers(6, W - 6)), int(rng.integers(6, SEAM - 200))
        if not keep[y, x] and rng.random() < 0.3 + 0.7 * smooth((600 - (y + NY0)) / 300.0):
            things.append((y, 'rock', (x, y, int(rng.integers(3, 8)))))

    lane = ndi.binary_dilation(path_mask | river, iterations=3)
    ii = np.cumsum(np.cumsum(lane, 0), 1)                            # summed table: does a crown hang over the way?

    def over_way(cx, foot, w, h):
        x0, x1 = max(0, int(cx - w * 0.35)), min(W - 1, int(cx + w * 0.35))
        y0, y1 = max(0, int(foot - h * 0.7)), min(H - 1, int(foot))
        if x0 >= x1 or y0 >= y1:
            return False
        return ii[y1, x1] - ii[y0, x1] - ii[y1, x0] + ii[y0, x0] > 0

    things = [t for t in things if not (t[1] == 'old' and t[2]['h'] > 30 and over_way(t[2]['x'] + t[2]['w'] // 2 - X0, SEAM + t[2]['foot'], t[2]['w'], t[2]['h']))
              and not (t[1] == 'east' and over_way(t[2][1], t[2][2], t[2][0]['w'], t[2][0]['h']))]

    def extra(kind, a):
        if kind == 'facet':
            facet_rock(img, *a)
        elif kind == 'old':
            paste(img, a, a['x'] + a['w'] // 2 - X0, SEAM + a['foot'], root)
        elif kind == 'east':
            t, x, y = a
            paste(img, t, x, y, root)
    draw_things(img, things, G, CL, extra)

    pool = (((xx - C(1191, 0)[0]) / 5.0) ** 2 + ((yy - C(0, 352)[1]) / 3.0) ** 2) < 1
    img[pool] = np.array([60, 80, 96.0])
    img[ndi.binary_dilation(pool, iterations=1) & ~pool] = ICE[4]
    base = img.copy()
    fall_frame(img, G, 0)
    if FRAMES_OUT:
        for f in range(FALL_FRAMES):
            fr = base.copy()
            fall_frame(fr, G, f)
            Image.fromarray(np.clip(fr, 0, 255).astype(np.uint8)).save(FRAMES_OUT % f)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
