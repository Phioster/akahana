"""The north as one world (Einbau-Schritt 2/3): the four approved zone drafts put together on a single canvas
and split into what the game draws apart.

Canvas rows are world rows after the north grew on top: 0..HN is the north, HN..HN+OLD today's top rows
(the overhang: the north's ground and firs reach down into them in clumps, today's ground runs up mirrored).
The drafts stay the source of the look; this module only places their pieces once each and records:

- ground: everything flat (snow, paths, gorge, mound, water, ice, ridge rocks), shadows multiplied in;
- sprites: every standing thing with its foot (pines, rocks, the hut and its things, lanterns, Jizo,
  cairns, bench, the waterfall as an 8-frame strip, copies of east-wood trees);
- walk, ground material, the water map, lights.

    n = build(pre)    # pre: dict of today's full arrays and world.json (rows of today's world)
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..', 'east'), os.path.join(HERE, '..', 'south')]
from common import fbm, smooth, snow_ground, Firs, noise_maps, footpath, through, HN, HUT  # noqa: E402
from objects_north import Gorge, FootBridge, CaveMound, facet_rock, boulder, ICE  # noqa: E402
from berg_objects import Cabin, WoodShed, ChoppingBlock, Stump, FallenLog, Pine, SNOWR  # noqa: E402
from details import lantern as iron_lantern  # noqa: E402
from objects_lake import paint_lake  # noqa: E402
from objects_east import Jizo  # noqa: E402
from objects2 import Lantern3  # noqa: E402
from extras import Bench  # noqa: E402
import importlib.util  # noqa: E402


def _load(name):
    """The north's drafts by path: the south has drafts of the same name on sys.path."""
    spec = importlib.util.spec_from_file_location('north_' + name, os.path.join(HERE, name + '.py'))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


z2 = _load('zone2_draft')
z4 = _load('zone4_draft')

OLD = 320                       # today's rows the overhang reaches into
BAND = 300
GRASS, EARTH, STONE, WOOD, SNOW, WET = 0, 1, 2, 3, 4, 5
KIND_BROOK, KIND_LAKE = 2, 3
SENTINEL = np.array([255.0, 0.0, 255.0])
KOGA_X = 440                    # west of this today's top is Kogarashi (cliff band), east of it the Ostwald
CLIFF = 64                      # Kogarashi: today's rows above this are the cliff wall, mirrored away
RIM = 40                        # Ostwald: its closed rim at today's top

# ---------------------------------------------------------------- places (north coordinates = canvas rows)
GATE_X = 272
CAVE = z2.CAVE
BRIDGE_X = z2.BRIDGE_X
PASS = (470, 112)
LOOK = (800, 400)
LAKE = z4.LAKE
FALL_X = z4.FALL_X
SPRING = (1190, 348)


class North:
    pass


def _band(pts, width, H, W, n=600):
    im = Image.new('L', (W, H), 0)
    ImageDraw.Draw(im).line([tuple(p) for p in through(pts, n)], fill=255, width=width, joint='curve')
    return np.array(im) > 0


def paths(gorge_cy, gorge_hw):
    by, bh = gorge_cy[BRIDGE_X], gorge_hw[BRIDGE_X]
    s_end, n_end = (BRIDGE_X, int(by + bh) + 5), (BRIDGE_X, int(by - bh) - 6)
    hy = HUT[1]
    return {                                                     # name: (points, width) - the round way and its spurs
        # the hut's yard (Philip 2026-11-04: paths ended under the shed, things stood on them): the way from the
        # gate ends at the door, a short one to the woodpile, the spurs leave the yard round the hut's sides
        'tor': ([(326, hy + 5), (322, hy + 30), (300, hy + 90), (286, hy + 170), (258, HN - 150), (282, HN - 70),
                 (266, HN + 10), (274, HN + 50), (277, HN + 100)], 1.6),
        'hof': ([(323, hy + 26), (342, hy + 16), (357, hy + 6)], 1.0),
        'schlucht': ([(324, hy + 28), (370, hy + 30), (394, hy + 10), (404, 830), (452, 730), (520, 660), (548, 612),
                      s_end], 1.5),
        'hoehle': ([(320, hy + 30), (286, hy + 22), (270, hy - 6), (250, 820), (205, 752), (160, 716)], 1.5),
        'serpentine': ([n_end, (592, 508), (640, 490), (604, 462), (544, 444), (486, 424), (530, 392), (612, 366),
                        (640, 346), (596, 318), (514, 300), (462, 270), (500, 236), (556, 206), (540, 176),
                        (494, 152), PASS], 1.4),
        'aussicht': ([(640, 490), (700, 474), (752, 446), (786, 418), (794, 410)], 1.4),   # ends before the bench
        'see': ([(806, 410), (830, 420), (870, 455), (960, 520), (1040, 610), (1078, 660), (1094, 690), (1140, 694)], 1.5),
        'fluss': ([(1300, 792), (1296, 862), (1264, 960), (1294, 1070), (1282, 1160), (1290, 1300), (1310, 1400),
                   (1338, 1520), (1372, 1600), (1440, 1700), (1420, 1780), (1374, 1852)], 1.5),
    }


def gorge():
    xs, cy, hw = z2.gorge_line(np.random.default_rng(52))
    return xs, cy + z2.NY0, hw


def ridge_mask(rng, H, W):
    """The peaks: high rock either side of the pass (zone 3), carried east above the lake, never reaching down
    onto the spring or the lookout; the top rows all rock under mist."""
    yy, xx = np.mgrid[0:H, 0:W]
    n1, n2 = fbm(rng, 30, (H, W)), fbm(rng, 9, (H, W))
    gap = 120 + 40 * n1
    side = np.abs(xx - PASS[0]) - gap
    reach = 150 + 70 * np.sin(xx / 90.0) + 40 * n1 + 14 * n2 + np.clip(side, 0, 400) * 0.35
    cap = np.where(xx > 700, 250 + 25 * n1 - 60 * smooth((xx - 1050) / 200.0) * smooth((1400 - xx) / 200.0), 9999)
    reach = np.minimum(reach, cap)
    return ((yy < reach) & (side > 0)) | (yy < 40 + 20 * n2)


def build(pre, W=1800):
    H = HN + OLD
    rng = np.random.default_rng(70)
    yy, xx = np.mgrid[0:H, 0:W]
    n = North()

    # ------------------------------------------------------------ the shape of the land
    gx, gcy, ghw = gorge()
    G0 = Gorge(gx, gcy, ghw)
    gmask = G0.mask(H, W)
    bridge = FootBridge(BRIDGE_X, int(gcy[BRIDGE_X] - ghw[BRIDGE_X]) - 2, int(gcy[BRIDGE_X] + ghw[BRIDGE_X]) + 1)
    mound = CaveMound(CAVE[0], CAVE[1], style='earth')
    mound_solid = mound.solid(H, W)
    ridge = ridge_mask(rng, H, W)
    knoll = (((xx - LOOK[0]) / 64.0) ** 2 + ((yy - LOOK[1] + 6) / np.where(yy > LOOK[1] - 6, 62.0, 40.0)) ** 2) < 1
    P = paths(gcy, ghw)
    path_mask = np.zeros((H, W), bool)
    for pts, _ in P.values():
        path_mask |= _band(pts, 12, H, W)

    # water of zone 4
    n4 = fbm(rng, 18, (H, W))
    lake = (((xx - LAKE[0]) / 150.0) ** 2 + ((yy - LAKE[1]) / 92.0) ** 2) < 1 + 0.35 * n4
    lake = ndi.binary_opening(lake, iterations=3)
    river_pts = [(1252, 740), (1272, 860), (1238, 960), (1270, 1070), (1255, 1160), (1262, 1300), (1266, 1400),
                 (1262, 1470), (1260, 1500)]
    rb = _band(river_pts, 15, H, W)
    mouth = rb & (yy < LAKE[1] + 120)
    lake = ndi.binary_closing(lake | mouth, iterations=8) & ~(rb & (yy > LAKE[1] + 60) & ~lake)
    lake = ndi.binary_opening(lake, iterations=2)
    river = rb & ~lake & (yy < HN + 304)                               # it meets today's river at (1260, 300)
    ice = lake & (xx + 0.5 * (yy - LAKE[1]) < LAKE[0] - 55 + 30 * fbm(rng, 8, (H, W)))
    brook_pts = [(1193, 353), (1203, 372), (1214, 400), (1206, 440), (1240, 500), (FALL_X, 556)]
    brook = _band(brook_pts, 5, H, W)
    step = (np.abs(yy - 566 - 6 * np.sin(xx / 23.0)) < 9) & (np.abs(xx - FALL_X) < 85 + 15 * n4)
    pool = (((xx - 1191) / 5.0) ** 2 + ((yy - 351) / 3.0) ** 2) < 1
    water = lake | river | brook | pool

    # ------------------------------------------------------------ where the wood stands
    east = smooth((xx - 380) / 260.0)
    rise = smooth((HN - yy) / 300.0)
    fall = smooth((HUT[1] - 40 - yy) / 320.0)
    w12 = smooth((0.15 + 0.6 * rise + 0.3 * east) * (1 - 0.8 * fall) + 0.2 * fbm(rng, 40, (H, W)))
    w12 = w12 * np.where(yy < 640, (0.6 + 0.4 * smooth((yy - 500) / 140.0)) * smooth((yy - 120) / 300.0), 1.0)   # zone 3: hardly a tree up at the pass
    w4 = smooth((0.08 + 0.45 * rise) * (1 - 0.9 * smooth((620 - yy) / 260.0)) + 0.2 * fbm(rng, 40, (H, W)))
    e = smooth((xx - 850) / 200.0)
    wood = (1 - e) * w12 + e * w4
    below = yy >= HN                                                   # today's rows: the north's firs only reach in
    wood = np.where(below, wood[HN - 1:HN].repeat(H, 0) * (1 - smooth((yy - HN) / 260.0)), wood)
    clearing = (((xx - HUT[0]) / 92.0) ** 2 + ((yy - HUT[1] - 8) / 64.0) ** 2) < 1 + 0.25 * fbm(rng, 20, (H, W))
    wood = np.where(clearing, 0.0, np.minimum(wood, np.where(e > 0.5, 0.5, 0.8)))
    round_mound = (((xx - CAVE[0]) / 130.0) ** 2 + ((yy - CAVE[1] + 20) / 85.0) ** 2) < 1 + 0.2 * fbm(rng, 15, (H, W))
    wood = np.where(round_mound, wood * 0.3, wood)                     # the hill stands free in the snow (zone 2)
    bare = (fbm(rng, 10, (H, W)) + 0.5 * fbm(rng, 3, (H, W)) > 1.5 - 1.9 * smooth((560 - yy) / 360.0)) & (e < 0.5)

    # ------------------------------------------------------------ ground: the north's, today's mirrored up, in clumps
    north = snow_ground(rng, H, W, 0, wood, bare=bare)
    grass = (north[..., 1] - north[..., 0] > 12) & (yy < HN - 150)
    north[grass] = north[grass].mean(-1, keepdims=True) * np.array([1.0, 0.98, 0.97])
    old = pre['ground'][:OLD].astype(float)
    ax = np.where(xx < KOGA_X, HN + CLIFF, HN + RIM)                    # mirror axis per column
    src = old.copy()
    pathish = ((src[..., 0] - src[..., 2]) > 22) & (src[..., 0] > 140)  # today's paths are not mirrored up
    pathish = ndi.binary_dilation(pathish, iterations=2)
    for _ in range(6):
        src[pathish] = np.roll(src, 9, axis=1)[pathish]
        pathish &= ((src[..., 0] - src[..., 2]) > 22) & (src[..., 0] > 140)
    row = np.where(yy >= ax, yy - HN, np.clip(2 * (ax - HN) - (yy - HN), 0, OLD - 1)).clip(0, OLD - 1)
    ref = np.where((yy >= ax)[..., None], old[row, xx], src[row, xx])
    reach = np.where(yy < ax, smooth((yy - (ax - BAND)) / BAND), 1 - 0.3 * smooth((yy - ax) / 120.0))
    clumps = 0.5 + 0.28 * fbm(rng, 14, (H, W)) + 0.12 * fbm(rng, 3, (H, W))
    take_old = (clumps < reach) & (reach > 0.01)
    img = np.where(take_old[..., None], ref, north)
    n.mirrored = (yy >= HN) & (yy < ax)                                # today's rows that now show the mirror
    n.replaced = (yy >= HN) & ~(take_old & (yy >= ax))                 # today's rows whose ground changed
    G, CL = noise_maps(rng, H, W)

    # ------------------------------------------------------------ flat things, into the ground
    G0.draw(img, G, CL)
    mound.draw(img, G, CL)
    for k, (pts, wd) in P.items():
        if k == 'see':                                                 # it ends on the shore, not out on the ice
            c = through(pts, 400)
            near = ndi.binary_dilation(lake, iterations=6)
            stop = next((i for i, (x, y) in enumerate(c) if near[int(y), int(x)]), len(c) - 1)
            pts = [tuple(p) for p in c[:stop:40]] + [tuple(c[stop])]
            P[k] = (pts, wd)
        footpath(img, pts, G, width=wd, bank=1.5, rng_seed=31 + len(k), fade_from=0.93 if k == 'tor' else None)
    earth = _band(P['fluss'][0], 3, H, W) & (yy > HN - 260)            # in the east wood the river path is earth
    k_ = smooth((yy - (HN - 260)) / 160.0)[earth]
    img[earth] = img[earth] * (1 - k_[:, None]) + np.array([104, 90, 76.0]) * k_[:, None]
    paint_lake(img, 0, lake & ~ice, ndi.binary_dilation(~(lake | river), iterations=4) & lake & ~ice, rng, rimless=river)
    paint_lake(img, 0, river, ndi.binary_dilation(~(river | lake), iterations=3) & river, rng, rimless=lake)
    v = fbm(rng, 14, (H, W))
    img[ice] = np.where((v > 0.35)[ice][:, None], np.array([150, 168, 178.0]), np.array([126, 146, 158.0]))
    crack = ice & (np.abs(fbm(rng, 9, (H, W))) < 0.025) & (rng.random((H, W)) < 0.8)
    img[crack] = np.array([92, 110, 124.0])
    img[ice & (fbm(rng, 6, (H, W)) + 0.3 * (rng.random((H, W)) - .5) > 0.75)] = SNOWR[6]
    img[ndi.binary_dilation(ice, iterations=1) & ~ice & ~lake] = SNOWR[4]
    bv = rng.random((H, W))
    inner = ndi.binary_erosion(brook, iterations=1)
    img[brook] = ICE[3]
    img[inner] = np.where((bv < 0.75)[inner][:, None], np.array([58, 80, 98.0]), np.array([84, 110, 128.0]))
    img[inner & (bv > 0.93)] = ICE[4]
    img[ndi.binary_dilation(brook, iterations=1) & ~brook & (rng.random((H, W)) < 0.7)] = SNOWR[5]
    img[pool] = np.array([60, 80, 96.0])
    img[ndi.binary_dilation(pool, iterations=1) & ~pool] = ICE[4]
    # rock that is land, not a thing: the ridge heaps, the fall's step, the knoll's flanks (nobody walks behind them)
    flat_rock = np.zeros((H, W), bool)

    def frock(*a):
        ys, xs = facet_rock(*a)
        ok = (ys >= 0) & (ys < H) & (xs >= 0) & (xs < W)
        flat_rock[ys[ok], xs[ok]] = True
    ry_, rx_ = np.nonzero(ridge & (rng.random((H, W)) < 0.012))
    for y, x in sorted(zip(ry_, rx_)):
        big = 1.0 + 0.8 * smooth((200 - y) / 200.0)
        frock(img, int(x), int(y), rng.uniform(9, 17) * big, rng.uniform(7, 12) * big, False,
                                int(x * 3 + y * 7), True)
    sy, sx = np.nonzero(step & (rng.random((H, W)) < 0.05))
    for y, x in sorted(zip(sy, sx)):
        if abs(x - FALL_X) > 5:
            frock(img, int(x), int(y), rng.uniform(7, 12), rng.uniform(5, 9), False, int(x * 3 + y), True)
    path_near = ndi.binary_dilation(path_mask, iterations=6)
    for k in range(70):
        a_ = rng.uniform(-0.5, 1.9)
        x = int(LOOK[0] + np.cos(a_) * 48 + rng.normal(0, 3))
        y = int(LOOK[1] - 6 + np.sin(a_) * 28 + rng.normal(0, 2))
        if not path_near[y, x]:
            frock(img, x, y, rng.uniform(5, 9), rng.uniform(4, 7), False, x * 5 + y, True)
    bridge.draw(img, G, CL)
    # beyond the pass the world ends in mist, thickening upward (a Bayer raster, as in the game; zone 3)
    BAY = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0
    mist = np.clip((70 - yy + 12 * fbm(rng, 20, (H, W))) / 70.0, 0, 1)
    on = mist > BAY[yy % 4, xx % 4]
    img[on] = img[on] * 0.25 + np.array([214.0, 214, 212]) * 0.75
    n.ground = img.copy()                                              # shadows of the standing things go in here
    n.wood = wood

    # ------------------------------------------------------------ standing things
    things = []
    keep = (ndi.binary_dilation(gmask, iterations=6) | ndi.binary_dilation(mound_solid, iterations=6) | clearing
            | ndi.binary_dilation(path_mask, iterations=6) | ridge | knoll | bridge.walk_mask(H, W)
            | ndi.binary_dilation(water, iterations=5) | np.roll(ndi.binary_dilation(lake | river, iterations=20), 18, axis=0)
            | ndi.binary_dilation(brook, iterations=22) | ndi.binary_dilation(step, iterations=22)
            | ((np.abs(xx - FALL_X) < 40) & (yy > 500) & (yy < 600))
            | ((np.abs(xx - CAVE[0]) < 26) & (yy > CAVE[1] - 4) & (yy < CAVE[1] + 30))
            | ((np.abs(xx - GATE_X) < 16) & (yy > HN - 160)) | ((np.abs(xx - GATE_X) < 52) & (np.abs(yy - HN) < 24))
            | (yy < 60))
    old_sprites = pre['sprites']
    occ = Firs()
    for s in old_sprites:                                              # today's things keep their room
        if s['foot'] < OLD + 60:
            occ.claim(s['x'] + s['w'] // 2, HN + s['foot'], 6 if s['h'] > 30 else 3)
    firs = occ.place(rng, wood, keep, 0, tries=90000)
    east_trees = [s for s in old_sprites if s['name'].startswith('e') and s['h'] >= 36 and s['frames'] == 1 and s['y'] > 0]
    for t in firs:                                                     # low in the east: the east wood's own trees instead
        y, x = t[0], t[2][0]
        mix = east[y, x] * (1 - smooth((HN - y) / BAND)) if y < HN else east[min(y, H - 1), x]
        if east_trees and rng.random() < 0.85 * mix:
            things.append((y, 'copy', (east_trees[int(rng.integers(len(east_trees)))], x, y)))
        else:
            things.append(t)
    # today's east trees cut flat at the old top edge: whole ones instead (their entries are dropped)
    n.drop = set()
    whole = east_trees
    for s in old_sprites:
        if s['y'] <= 0 and s['name'].startswith('e'):
            n.drop.add(id(s))
            if s['h'] >= 30 and whole:
                things.append((HN + s['foot'], 'copy', (whole[int(rng.integers(len(whole)))], s['x'] + s['w'] // 2, HN + s['foot'])))
    gone = ndi.binary_dilation(river, iterations=4) | ndi.binary_dilation(path_mask, iterations=8)
    for s in old_sprites:                                              # today's trees on the new river or the river path
        cx, f = s['x'] + s['w'] // 2, HN + s['foot']
        if s['foot'] < OLD + 40 and 0 <= cx < W and f < H and gone[f, cx] and s['name'].startswith('e'):
            n.drop.add(id(s))
    # rocks: a broad band where the cliff wall stood, the gate's pair, loose ones more often higher up
    for (x, y, r) in [(GATE_X - 26, HN + 6, 9), (GATE_X + 30, HN + 2, 10)]:
        things.append((y, 'rock', (x, y, r)))
    for _ in range(90):
        x = int(rng.integers(8, 560))
        y = int(HN + 40 - rng.integers(0, 240) * rng.random())
        if abs(x - GATE_X) < 40 or keep[y, x]:
            continue
        things.append((y, 'rock', (x, y, int(rng.integers(3, 8)))))
    near_path = ndi.binary_dilation(path_mask, iterations=8)
    for _ in range(900):
        x, y = int(rng.integers(6, W - 6)), int(rng.integers(60, HN - 100))
        if keep[y, x] or near_path[y, x] or rng.random() > 0.1 + 0.9 * smooth((700 - y) / 300.0):
            continue
        things.append((y, 'rock', (x, y, int(rng.integers(3, 9)))))
    # the hut's clearing (zone 1)
    hx, hy = HUT
    things += [(hy, 'cabin', (hx - 20, hy)), (hy + 1, 'shed', (hx + 17, hy + 1)), (hy + 10, 'block', (hx + 44, hy + 10)),
               (hy + 50, 'stump', (hx - 34, hy + 50)), (hy + 44, 'stump', (hx + 40, hy + 44)),
               (hy - 26, 'stump', (hx + 26, hy - 26)),
               (hy + 64, 'log', (hx - 74, hy + 58, hx - 54, hy + 64)), (hy + 62, 'log', (hx + 50, hy + 64, hx + 68, hy + 56)),
               (hy + 26, 'iron', (hx + 8, hy + 16))]
    for (dx, dy, h) in ((-30, -34, 16), (22, -40, 14), (-8, -46, 17)):   # small firs up on the mound
        things.append((CAVE[1] + dy, 'pine', (CAVE[0] + dx, CAVE[1] + dy, h, 900 + dx, 0.9)))
    # zone 3: the lookout's bench and lantern, the pass with its cairns, Jizo and lantern; stones kept at the bends
    things += [(LOOK[1] - 2, 'bench', (LOOK[0] - 6, LOOK[1] - 2)), (LOOK[1] - 10, 'lantern3', (LOOK[0] + 20, LOOK[1] - 10)),
               (PASS[1] - 2, 'jizo', (PASS[0] + 16, PASS[1] - 2)), (PASS[1] + 12, 'lantern3', (PASS[0] - 14, PASS[1] + 12))]
    for (cx, cy_) in ((PASS[0] - 30, PASS[1] + 6), (PASS[0] + 34, PASS[1] - 4), (PASS[0] - 54, PASS[1] - 18)):
        things.append((cy_, 'cairn', (cx, cy_)))
    bend = ndi.binary_dilation(path_mask, iterations=5)
    for p in P['serpentine'][0][2:-1:2]:
        for k in range(3):
            for off in range(0, 30, 3):
                x, y = p[0] + 9 + 4 * k + off, p[1] + 6 - k
                if not bend[y, x]:
                    things.append((y, 'rock', (x, y, 3)))
                    break
    # zone 4: the spring's stones, the waterfall
    for dx, dy, r in [(-7, -2, 9), (6, -3, 8), (0, -10, 8), (-14, 2, 6), (11, 1, 5), (-3, -17, 6), (-7, 6, 5)]:
        things.append((SPRING[1] + dy, 'rock', (SPRING[0] + dx, SPRING[1] + dy, r)))
    things.append((597, 'fall', None))

    # ------------------------------------------------------------ record them: sprite, shadow, where they block
    scratch = np.zeros((H, W, 3))
    block = np.zeros((H, W), bool)
    n.sprites, n.copies, n.lights = [], [], []
    canvas = img

    def box(x0, y0, x1, y1):
        return max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(H, int(y1))

    def rect(x0, y0, x1, y1):
        x0, y0, x1, y1 = box(x0, y0, x1 + 1, y1 + 1)
        block[y0:y1, x0:x1] = True

    def ell(cx, cy, rx, ry):
        x0, y0, x1, y1 = box(cx - rx - 1, cy - ry - 1, cx + rx + 2, cy + ry + 2)
        sub = ((xx[y0:y1, x0:x1] - cx) / rx) ** 2 + ((yy[y0:y1, x0:x1] - cy) / ry) ** 2 <= 1
        block[y0:y1, x0:x1] |= sub

    def record(draw, bx, foot, core=None):
        x0, y0, x1, y1 = box(*bx)
        if x0 >= x1 or y0 >= y1:
            return
        before = canvas[y0:y1, x0:x1].copy()
        draw(canvas)
        after = canvas[y0:y1, x0:x1].copy()
        scratch[y0:y1, x0:x1] = SENTINEL
        draw(scratch)
        p = scratch[y0:y1, x0:x1]
        hit = np.abs(p - SENTINEL).sum(-1) > 0.5
        shade = hit & (p[..., 1] < 1.0) & (np.abs(p[..., 0] - p[..., 2]) < 2.0)
        cover = hit & ~shade
        g = n.ground[y0:y1, x0:x1]
        g[shade] *= (p[shade, 0] / 255.0)[:, None]
        if core is not None:                                       # a lantern: only its stone is the sprite,
            keep_ = np.zeros(cover.shape, bool)                    # its glow and light pool go into the ground
            for X, Y in core:
                if y0 <= Y < y1 and x0 <= X < x1:
                    keep_[Y - y0, X - x0] = True
            glow = cover & ~keep_
            g[glow] += after[glow] - before[glow]
            cover &= keep_
        if not cover.any():
            return
        rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        rgba[cover, :3] = np.clip(after[cover], 0, 255).astype(np.uint8)
        rgba[cover, 3] = 255
        n.sprites.append(dict(rgba=rgba, x=x0, y=y0, w=x1 - x0, h=y1 - y0, foot=int(foot), frames=1))

    for _, kind, a in sorted(things, key=lambda t: t[0]):
        if kind == 'pine':
            x, y, h, seed, snow = a
            gm = np.where(G < snow, G, 1.0)
            record(lambda im, x=x, y=y, h=h, seed=seed, gm=gm: Pine(x, y, h, seed % 100000).draw(im, gm, CL),
                   (x - 16, y - h - 8, x + 17, y + 6), y)
            rect(x - 2, y - 2, x + 2, y + 1)
        elif kind == 'rock':
            x, y, r = a
            rr = max(2, int(r * 0.9))
            record(lambda im, x=x, y=y, rr=rr: boulder(im, x, y, rr, G, CL, int(x * 7 + y)),
                   (x - rr - 4, y - 2 * rr - 4, x + rr + 6, y + 6), y)
            ell(x, y - rr * 0.4, rr, max(1.5, rr * 0.55))
        elif kind == 'cabin':
            c = Cabin(a[0], a[1], w=34, wall=13, roof=14, seed=11, win=5, winh=5, doorw=5)
            record(lambda im, c=c: c.draw(im, G, CL), (c.x - 12, c.y - 50, c.x + 48, c.y + 12), c.y)
            rect(c.x - 2, c.y - 18, c.x + 36, c.y + 1)
            n.lights.append(dict(x=float(c.x + 10), y=float(c.y - 6), r=22.0, k=0.55, kind='lantern'))
        elif kind == 'shed':
            c = WoodShed(a[0], a[1], w=20, h=10, roof=7, seed=12)
            record(lambda im, c=c: c.draw(im, G, CL), (c.x - 8, c.y - 30, c.x + 30, c.y + 8), c.y)
            rect(c.x, c.y - 8, c.x + 20, c.y + 1)
        elif kind == 'block':
            c = ChoppingBlock(a[0], a[1], R=5, seed=13, tall=5, handle=8, head='klein')
            record(lambda im, c=c: c.draw(im, G, CL), (c.x - 14, c.y - 24, c.x + 16, c.y + 8), c.y)
            ell(c.x, c.y - 2, 5, 3)
        elif kind == 'stump':
            c = Stump(a[0], a[1], r=4, seed=int(a[0]))
            record(lambda im, c=c: c.draw(im, G, CL), (c.x - 10, c.y - 12, c.x + 12, c.y + 6), c.y)
            ell(c.x, c.y - 2, 5, 3)
        elif kind == 'log':
            c = FallenLog(*a, r=2.6, seed=int(a[0]))
            x0_, x1_ = min(a[0], a[2]), max(a[0], a[2])
            y0_, y1_ = min(a[1], a[3]), max(a[1], a[3])
            record(lambda im, c=c: c.draw(im, G, CL), (x0_ - 8, y0_ - 10, x1_ + 8, y1_ + 8), y1_)
            for t in np.linspace(0, 1, 12):
                ell(a[0] + (a[2] - a[0]) * t, a[1] + (a[3] - a[1]) * t, 2.5, 2)
        elif kind == 'iron':
            x, y = a
            record(lambda im, x=x, y=y: iron_lantern(im, x, y, post=7), (x - 4, y - 6, x + 5, y + 12), y + 10)
            rect(x - 1, y + 8, x + 2, y + 10)
            n.lights.append(dict(x=float(x), y=float(y), r=26.0, k=0.6, kind='lantern'))
        elif kind == 'lantern3':
            x, y = a
            L3 = Lantern3(x, y, None)
            record(lambda im, L3=L3: L3.draw(im, 0.0, 8.0), (x - 18, y - 34, x + 20, y + 10), y, core=L3.core())
            rect(x - 4, y - 4, x + 4, y + 1)
            n.lights.append(dict(x=x + 0.5, y=y - 9.5, r=22.0, k=0.6, kind='lantern'))
        elif kind == 'bench':
            x, y = a
            record(lambda im, x=x, y=y: Bench(x, y).draw(im), (x - 14, y - 10, x + 16, y + 6), y)
            rect(x - 10, y - 4, x + 11, y + 1)
        elif kind == 'jizo':
            j = Jizo(a[0], a[1], seed=8, cap=True)

            def dj(im, j=j):
                j.draw(im, G)
                for (u, v_) in ((-2, -15), (-1, -16), (0, -16), (1, -16), (2, -15), (-4, -9), (-3, -9), (3, -9), (4, -9)):
                    if G[j.y + v_, j.x + u] < 0.85:
                        im[j.y + v_, j.x + u] = SNOWR[6]           # snow on his head and shoulders
            record(dj, j.box(), j.y)
            rect(j.x - 4, j.y - 3, j.x + 4, j.y + 1)
        elif kind == 'cairn':
            cx, cy_ = a

            def dc(im, cx=cx, cy_=cy_):
                y = cy_
                for k, r in enumerate((4, 3, 3, 2)):
                    boulder(im, cx + (k % 2), y, r, G, CL, cx * 7 + k)
                    y -= int(1.5 * r) + 1
            record(dc, (cx - 8, cy_ - 30, cx + 10, cy_ + 6), cy_)
            ell(cx, cy_ - 1, 4, 2.5)
        elif kind == 'copy':
            t, x, y = a
            if x - t['w'] // 2 < 0 or x - t['w'] // 2 + t['w'] > W:
                continue                                           # it would reach over the world's edge
            n.copies.append(dict(t, x=int(x - t['w'] // 2), y=int(y - (t['foot'] - t['y'])), foot=int(y)))
            rect(x - 3, y - 3, x + 3, y + 1)
        elif kind == 'fall':
            fx = FALL_X
            x0, y0, x1, y1 = box(fx - 24, 550, fx + 25, 612)
            base = n.ground[y0:y1, x0:x1].copy()
            strip = []
            for f in range(z4.FALL_FRAMES):                            # drawn on the ground, then cut out
                sub = n.ground.copy()
                z4.fall_frame(sub[z4.NY0:, z4.X0:], G[z4.NY0:, z4.X0:], f)   # zone 4 drew in its own canvas
                fr = sub[y0:y1, x0:x1]
                a_ = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
                a_[..., :3] = np.clip(fr, 0, 255).astype(np.uint8)
                a_[..., 3] = np.any(np.abs(fr - base) > 0.5, axis=2) * 255
                strip.append(a_)
            n.sprites.append(dict(rgba=np.concatenate(strip, 1), x=x0, y=y0, w=x1 - x0, h=y1 - y0, foot=y1 - 8,
                                  frames=z4.FALL_FRAMES, fps=8))
    n.lights.append(dict(x=float(CAVE[0]), y=float(CAVE[1] - 4), r=14.0, k=0.45, kind='lantern'))   # the candle inside

    core = np.zeros((H, W), bool)                                      # the paths' trodden middle
    for pts, _ in P.values():
        core |= _band(pts, 3, H, W)
    hit = block & core & (yy < HN)
    if hit.any():
        ys, xs = np.nonzero(hit)
        raise SystemExit('Norden: etwas steht auf einem Weg bei %s' % sorted(set(zip((xs // 10 * 10).tolist(), (ys // 10 * 10).tolist())))[:12])
    # ------------------------------------------------------------ where one can walk, and on what
    walk = np.ones((H, W), bool)
    walk &= ~(gmask & ~bridge.walk_mask(H, W))
    walk &= ~(water | ridge | flat_rock | step | mound_solid | ndi.binary_dilation(ice, iterations=1))
    walk &= ~block
    walk &= ~((yy < PASS[1] - 26))                                     # beyond the pass: mist and rock
    walk[:, :10] = walk[:, W - 10:] = False
    n.walk = walk
    mat = np.full((H, W), SNOW, np.uint8)
    for pts, wd in P.values():
        mat[_band(pts, 4, H, W)] = EARTH
    mat[bridge.walk_mask(H, W)] = WOOD
    mat[flat_rock] = STONE
    n.mat = mat
    n.path_mask = path_mask

    # ------------------------------------------------------------ the water map (RGBA: flow, depth, along, kind)
    wm = np.zeros((H, W, 4), np.uint8)
    for m_, pts in ((river, river_pts), (brook & ~pool, brook_pts)):
        c = through(pts, 1200)
        from scipy.spatial import cKDTree
        ys, xs = np.nonzero(m_)
        d, i = cKDTree(c).query(np.stack([xs, ys], 1))
        tang = np.gradient(c, axis=0)
        ang = np.arctan2(tang[i, 1], tang[i, 0])
        arc = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
        dep = np.clip(1 - d / 8.0, 0.2, 1)
        wm[ys, xs] = np.stack([(ang / (2 * np.pi) % 1 * 256).astype(np.uint8), (dep * 255).astype(np.uint8),
                               (arc[i] % 256).astype(np.uint8), np.full(len(ys), KIND_BROOK, np.uint8)], 1)
    still = (lake & ~ice) | pool
    dep = np.clip(ndi.distance_transform_edt(lake) / 40.0, 0, 1)
    wm[still, 1] = (dep[still] * 255).astype(np.uint8)
    wm[still, 3] = KIND_LAKE
    n.water = wm
    n.open_water = lake & ~ice
    return n
