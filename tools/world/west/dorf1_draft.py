#!/usr/bin/env python3
"""West zone 1 draft (plan step 61): the way in from the camp fire, the village square with its well and the nine
empty houses in their overgrown gardens. West coordinates: the world grows by WW columns to the left, today's x 0
is WW here. Today's world (build/world_full) is drawn for real east of WW, its fir wall at the edge removed.

    python3 dorf1_draft.py OUT.png [scale]   (not zone1_draft: the south has one, z2 imports it)"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import field6  # noqa: E402
from field6 import patches, CMAP  # noqa: E402
import extras  # noqa: E402
import mood_map  # noqa: E402
import objects_west as o  # noqa: E402
import objects_lake as ol  # noqa: E402
from objects_lake import hx  # noqa: E402
import zone2_draft as z2  # noqa: E402   (the south's: Blade, Wildflower, Bank, Steinlaterne)
from objects_south import Fackel, Kerzen  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
FULL = os.path.join(ROOT, 'build', 'world_full')
WW = 900                                   # columns the world grows to the west
X0, Y0, X1, Y1 = 0, 1380, 1180, 3820       # the window drawn (west coordinates): zone 3 up to 1380, 4a down to 3820
W, H = X1 - X0, Y1 - Y0
EDGE = 24                                  # today's columns 0..EDGE are the fir wall: they go
SQUARE = (520, 2330)
GLASHAUS = (680, 2600)                     # zone 2: the greenhouse's foot (front wall middle)
STEINMETZ = (330, 2500)                    # zone 2: the stonemason's house, its workshop on the east
FIRE = (222 + WW, 2292)
# zone 3: the brook that leaves today's world at its west edge (today x 24, y 1849..1868) rises in the forest
# north-west, runs past the foot of the shrine's steps and on east; the shrine at the forest's edge, the orchard
BROOK = [(240, 1760), (290, 1795), (330, 1845), (370, 1898), (420, 1927), (480, 1940), (550, 1933), (640, 1910),
         (740, 1890), (840, 1879), (900, 1867), (WW + EDGE + 6, 1857)]
SHRINE = (424, 1878)                       # the foot of the shrine's stone base; the steps go down to 1910
FOREST = [(230, 1975), (300, 1935), (350, 1880), (378, 1836), (470, 1826), (505, 1790), (522, 1700), (560, 1640),
          (640, 1606), (760, 1578), (860, 1540), (WW + EDGE, 1520)]     # its south edge
ORCHARD = (470, 1630, 800, 1850)
# zone 4a: the old paddies stepping down south-west of the village, the brook they drain into running past the mill
# on into today's brook A (today x 20, y 3437..3451), the spring of today's brook C (y 3763..3769), the bamboo grove
TERR = (56, 2836, 432, 3112)
BROOK_A = [(250, 3112), (320, 3190), (400, 3262), (470, 3306), (540, 3340), (640, 3390), (780, 3430),
           (WW + EDGE + 6, 3447)]
BROOK_C = [(640, 3700), (720, 3734), (830, 3758), (WW + EDGE + 6, 3766)]
MILL = (500, 3288)
SPRING = (640, 3690)
BAMBOO = (120, 2250, 96, 74)
Z3_FROM = 3290                              # where the south's tall grass turns patchy (zone 3)
GRASS_FROM, GRASS_FULL = 2900, 3200        # the south's tall grass, as it comes in at the seam today
# (garden centre, house seed, roof kind, how fallen in); the house stands at the back of its plot, facing south
HOUSES = [((380, 2180), 1, 'kawara', 0.5), ((560, 2150), 2, 'kaya', 0.8), ((690, 2230), 3, 'kawara', 0.35),
          ((300, 2320), 4, 'kaya', 0.6), ((410, 2420), 5, 'kawara', 0.7), ((720, 2400), 6, 'kaya', 0.45),
          ((540, 2490), 7, 'kawara', 0.9), ((250, 2610), 8, 'kawara', 0.55), ((430, 2640), 9, 'kaya', 0.65)]
PATHS = {
    'eingang': [(FIRE[0] - 14, FIRE[1] + 10), (1040, 2312), (930, 2300), (820, 2306), (700, 2322), (600, 2334),
                (SQUARE[0] + 16, SQUARE[1] + 2)],
    'nord': [(SQUARE[0] - 6, SQUARE[1] - 14), (500, 2250), (470, 2150), (446, 2060), (432, 1990), (426, 1950),
             (424, 1916)],                                                  # zone 3: over the brook to the torii
    'obst': [(446, 2046), (488, 1992), (528, 1952), (548, 1930), (568, 1880), (588, 1800), (604, 1722),
             (660, 1632), (740, 1544), (830, 1474), (924, 1428)],          # zone 3: through the orchard to Kogarashi
    'sued': [(SQUARE[0] + 8, SQUARE[1] + 14), (560, 2420), (620, 2520), (600, 2620), (540, 2700), (470, 2770),
             (432, 2840), (440, 2920), (446, 3000), (432, 3080), (452, 3170), (482, 3240), (498, 3284)],   # 4a: by the terraces to the mill
    'muehle': [(506, 3294), (528, 3318), (548, 3346), (600, 3420), (700, 3480), (800, 3540), (WW + EDGE + 4, 3559), (972, 3561), (994, 3563)],   # into today's
    'see': [(600, 3420), (608, 3560), (612, 3640), (616, 3740), (612, 3820)],
    'bambus': [(250, 2520), (196, 2420), (150, 2300), (136, 2272)],
    'glas': [(603, 2604), (624, 2627), (656, 2630), (680, 2616)],              # zone 2: below the beds to the door
    'west': [(SQUARE[0] - 16, SQUARE[1] + 4), (420, 2360), (350, 2440), (300, 2470), (250, 2520)],
}


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def fbm(h, w, s, seed):
    n = ndi.gaussian_filter(np.random.default_rng(seed).normal(0, 1, (h, w)), s)
    return n / n.std()


def today():
    g = np.array(Image.open(os.path.join(FULL, 'ground.png')).convert('RGB')).astype(float)
    fl = np.array(Image.open(os.path.join(FULL, 'flowers.png')).convert('RGBA'))
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    return g, fl, w


def ground(og, rng):
    """Today's ground is kept east of the fir wall; west of it the light and dark patches of today's meadow run on
    into fresh ones (the south's way of growing ground: south/ground.py), so there is no seam and no stripes."""
    import ground as sg
    n = WW + EDGE - X0                                   # new columns, counted from the seam leftwards
    old_t = sg.tone_of(og[Y0:Y1, EDGE:EDGE + 80])        # (H, 80): column d = d px east of the seam
    fog = np.clip(0.70 + 0.10 * fbm(H, n, 18, 11), 0, 1)
    flow = np.clip(0.20 + 0.10 * fbm(H, n, 10, 12), 0, 1)
    new_t = sg.fresh_tone(H, n, fog, flow, rng)          # column d = d px west of the seam
    t = sg.continued_tone(old_t[:, ::-1].T, new_t.T, reach=70).T     # mirrored at the seam, then fresh
    newg = sg.ground_from_tone(t, fog, flow, rng)[:, ::-1]
    g = np.zeros((H, W, 3))
    g[:, :n] = newg
    g[:, n:] = og[Y0:Y1, EDGE:EDGE + W - n]
    return g


def draw_terraces(img, rng, pathm, outflow=None):
    """The old paddies (Furuta) stepping down south: each a band between two curving contours, of its own depth and
    reaching out its own way at both ends, a bund (aze) of earth along its top, the drop to the next one as a dark
    earth face. Only a few still hold water (dull, the old stubble rows in it, reeds), and even those half grown
    over; the rest are long dry and green. -> (all paddy pixels, the dry or grown-over ones)."""
    x0, y0, x1, y1 = [v - o_ for v, o_ in zip(TERR, (X0, Y0, X0, Y0))]
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.random.default_rng(98)
    depths = r.uniform(18, 34, 14)
    edges = [y0]
    while edges[-1] < y1 and len(edges) < len(depths):
        edges.append(edges[-1] + depths[len(edges) - 1])
    n = len(edges) - 1
    xs = xx[0].astype(float)
    cx_, R_ = (x0 + x1) / 2, (x1 - x0) * 0.62
    bow = np.clip(1 - ((xs - cx_) / R_) ** 2, 0, 1)                      # the hill's spur: every contour bows downhill
    b = np.stack([edges[k] + 14 * bow + 7 * np.sin(xs / 70.0 + k * 0.9) + 3 * np.sin(xs / 23.0 + k * 2.1)
                  for k in range(n + 1)])
    k_of = np.full((H, W), -1)
    for k in range(n):
        k_of[(yy >= b[k][None, :]) & (yy < b[k + 1][None, :])] = k
    t = (np.arange(n) + 0.5) / n                                         # the hill's shape: narrow at the top and the
    half = (x1 - x0) / 2 * np.sqrt(np.clip(1 - (2 * t - 1) ** 2 * 0.85, 0.05, 1)) * r.uniform(0.7, 1.0, n)   # foot
    mid = (x0 + x1) / 2 + 34 * np.sin(np.arange(n) * 0.8 + 1) + r.uniform(-10, 10, n)
    lo, hi = mid - half, mid + half
    kk = np.clip(k_of, 0, n - 1)
    wob = 6 * fbm(H, W, 5, 95) + 16 * fbm(H, W, 14, 105)                # ragged ends, no straight cut
    terr = (k_of >= 0) & (xx > lo[kk] + wob) & (xx < hi[kk] + wob)
    terr &= ~ndi.binary_dilation(pathm, iterations=3)                    # the path keeps its way by them
    lab, nl = ndi.label(terr)
    terr &= np.isin(lab, np.argsort(np.bincount(lab.ravel()))[::-1][1:2])  # one piece: no stray specks at the rim
    flooded = set(int(v) for v in r.choice(n, max(2, n // 3), replace=False))
    patch = fbm(H, W, 6, 96)
    din = ndi.distance_transform_edt(terr)
    fade = smooth((din - 2 + 8 * fbm(H, W, 6, 106)) / 24.0)               # the field runs out into the meadow at its rim
    wet = terr & np.isin(k_of, list(flooded)) & (patch > -0.35) & (din > 7 + 5 * fbm(H, W, 5, 107))   # pools inset
    if outflow is not None:                                              # the mill brook leaves from a pool in its band
        ox, oy = outflow
        ko = k_of[oy, ox]
        pool = ((xx - ox) / 34.0) ** 2 + ((yy - oy) / 11.0) ** 2 + 0.3 * patch < 1
        wet |= terr & (k_of == ko) & pool
    dry = terr & ~wet
    WAT = [hx(c) for c in ['#3c4650', '#4e5a65', '#5a6670', '#64717c']]
    g = rng.random((H, W))
    top = b[kk, xx]
    below = b[np.clip(k_of + 1, 0, n), xx] - yy
    into = yy - top
    v = 0.45 + 0.25 * fbm(H, W, 2, 99) * 0.4 + 0.15 * (g - 0.5) - 0.2 * (into < 4)
    img[wet] = np.array(WAT)[np.clip((v * 4).astype(int), 0, 3)][wet]
    stub = wet & (into % 3 == 1) & ((xx + 2 * (into // 3)) % 4 == 0) & (g < 0.6)     # the old stubble rows
    img[stub] = hx('#4a4a34')
    weed = wet & (patch < -0.05) & (g < 0.5)                              # weeds creeping in from the rims
    img[weed] = hx('#4f5d43')
    reed = wet & (g > 0.97)
    img[reed] = hx('#6e7048')
    tint = 1 - 0.75 * fade[..., None] * (1 - np.array([0.84, 0.9, 0.8]) * (0.92 + 0.1 * g[..., None]))
    img[dry] = (img * tint)[dry]
    lines = fade > 0.25 + 0.6 * np.random.default_rng(108).random((H, W)) * (1 - fade)          # bunds and faces peter out at the rim
    EARTH = [hx('#2a2422'), hx('#3b332e'), hx('#51463e'), hx('#6a5a48')]
    bund = terr & (into < 2) & (lines | wet)
    img[bund] = np.array(EARTH)[np.clip((2 + g * 2).astype(int), 0, 3)][bund]
    grassy = bund & (fbm(H, W, 1.5, 97) > 0.1)
    img[grassy] = hx('#5b6447')
    face = terr & (below <= 3) & (lines | ndi.binary_dilation(wet, iterations=3))
    img[face] = np.array(EARTH)[np.clip((g * 2).astype(int), 0, 1)][face]
    img[face & (g > 0.88)] = hx('#666a70')
    return terr, dry, fade


def match_seam(img, skip, seam, gy, band=40, reach=280):
    """The new columns, row by row, to the brightness of today's world just across the seam, fading out westward
    over reach px (the two grass fields are made apart and differ a little in tone)."""
    def row_mean(a, m):
        n = m.sum(1)
        v = (a * m[..., None]).sum(1) / np.maximum(n, 1)[:, None]
        ok = n > band // 3
        idx = np.arange(len(v))
        return np.stack([np.interp(idx, idx[ok], v[ok, c]) for c in range(3)], 1)
    L = row_mean(img[:, seam - band - 4:seam - 4], ~skip[:, seam - band - 4:seam - 4])
    R = row_mean(img[:, seam + 4:seam + band + 4], ~skip[:, seam + 4:seam + band + 4])
    ratio = np.clip(ndi.gaussian_filter1d(R, 24, axis=0) / np.maximum(ndi.gaussian_filter1d(L, 24, axis=0), 1),
                    0.8, 1.25)
    wy = smooth((gy[:, 0] - 2780) / 120.0)[:, None]                     # only the south: the north was approved as is
    xs = np.arange(img.shape[1])
    wx = np.clip(1 - (seam - xs) / reach, 0, 1) * (xs < seam)
    fade = wy[..., None] * wx[None, :, None]
    img = img * (1 + (ratio[:, None, :] - 1) * fade)
    base = ndi.uniform_filter(img, (9, 9, 1))                            # and the contrast: today's stalks are softer
    dev = np.abs(img - base).mean(2)
    def row_dev(x0, x1):
        m = ~skip[:, x0:x1]
        return ndi.gaussian_filter1d((dev[:, x0:x1] * m).sum(1) / np.maximum(m.sum(1), 1), 24)
    k = np.clip(row_dev(seam + 4, seam + band + 4) / np.maximum(row_dev(seam - band - 4, seam - 4), 1), 0.7, 1.15)
    return base + (img - base) * (1 + (k[:, None, None] - 1) * fade)


def path_masks(rng):
    mask = np.zeros((H, W), bool)
    for name, pts in PATHS.items():
        local = [(x - X0, y - Y0) for x, y in pts]
        m, core, d, width = extras.path_mask(H, W, local, rng)
        mask |= m
        yield name, m, core, d, width


def main(out, scale=2):
    rng = np.random.default_rng(61)
    og, ofl, w = today()
    img = ground(og, rng)
    yy, xx = np.mgrid[0:H, 0:W]
    gx, gy = xx + X0, yy + Y0
    G = np.random.default_rng(3).random((H, W))

    # ---- the square: trodden gravel round the well
    sq = extras.forecourt(H, W, SQUARE[0] - X0, SQUARE[1] - Y0, 46, 26, rng)
    extras.draw_gravel(img, sq, rng)
    # ---- paths (earth, like the old ones)
    pathm = np.zeros((H, W), bool)
    for name, m, core, d, width in path_masks(rng):
        extras.draw_path(img, m, core, d, width, rng)
        pathm |= m
    pathm |= sq
    # ---- zone 3: the brook (today's water east of the seam as it is, the new brook west of it)
    import objects_water as ow
    from scipy.interpolate import splprep, splev
    tck, _ = splprep(np.array([(x - X0, y - Y0) for x, y in BROOK], float).T, s=0, k=3)
    bc = np.array(splev(np.linspace(0, 1, 900), tck)).T
    brook = ow.Brooks([(bc, 8, 19)], H, W, y0=0)
    seam = WW + EDGE - X0
    # painted as today's brook is (gen_world: WAT, the ripples, an earth rim with moss, reeds on the banks)
    from scipy.spatial import cKDTree
    from field6 import DG, K
    seg = np.hypot(*np.diff(bc, axis=0).T)
    arc = np.r_[0, np.cumsum(seg)]
    sd, ki = cKDTree(bc).query(np.stack([xx.ravel(), yy.ravel()], 1).astype(float))
    sd, salong = sd.reshape(H, W), arc[ki].reshape(H, W)
    swid = (4 + 5.5 * np.clip(salong / 260, 0, 1)) + 1.6 * np.sin(salong * 0.06) + 0.8 * fbm(H, W, 2, 81)
    sbank_ = (sd < swid + 2.2)
    wmask = (sd < swid) & (xx < seam)
    sbank_ &= ~wmask & (xx < seam)
    g_ = rng.random((H, W))
    EARTH3 = [o.hx('#2a2422'), o.hx('#3b332e'), o.hx('#51463e')]
    MOSS3 = [o.hx('#3f4632'), o.hx('#5b6447'), o.hx('#7d8660')]
    img[sbank_] = np.array(EARTH3)[np.clip((g_[sbank_] * 3).astype(int), 0, 2)]
    mossy = sbank_ & (fbm(H, W, 1.2, 82) > 0.6)
    img[mossy] = MOSS3[1]
    WAT = [o.hx(c) for c in ['#3c4650', '#4e5a65', '#64717c', '#7f8c96', '#a3aeb6', '#d6dde1']]
    rip = np.sin(salong * 1.5 + sd * 0.9 + 2 * fbm(H, W, 1.5, 83))
    wv = 0.52 - 0.22 * np.clip(1 - sd / swid, 0, 1) + 0.12 * rip + 0.06 * (g_ - .5)
    wi = np.clip((wv * 6).astype(int), 0, 5)
    img[wmask] = np.array(WAT)[wi][wmask]
    img[wmask & (rip > 0.92) & (g_ < 0.35)] = WAT[5]
    img[wmask & (sd > swid - 1.2) & (g_ < 0.4)] = WAT[4]
    for _ in range(int(arc[-1] * 1.2)):                                  # reeds on the banks
        k = int(rng.integers(0, len(bc)))
        side = rng.choice([-1, 1])
        x0_ = int(bc[k, 0] + rng.normal(0, 2))
        y0_ = int(bc[k, 1] + side * (swid[min(H - 1, max(0, int(bc[k, 1]))), min(W - 1, max(0, int(bc[k, 0])))] + rng.uniform(0.5, 3)))
        if not (2 <= x0_ < seam - 2 and 9 <= y0_ < H) or wmask[y0_, x0_] or rng.random() < 0.5:
            continue
        hgt = int(rng.integers(4, 9))
        lean = int(rng.choice([-1, 0, 1]))
        for j in range(hgt):
            o.put(img, x0_ + (lean if j > hgt * 0.6 else 0), y0_ - j, K if j < hgt - 2 else DG)
        if rng.random() < 0.5:
            o.put(img, x0_ + lean, y0_ - hgt, o.hx('#5a4634'))
    brook.mask = wmask
    # ---- zone 4a: the south's grass field comes in (tinted and darkened as zone2_draft does), the paddies, the brooks
    dens_s = smooth((gy - GRASS_FROM + 40 * fbm(H, W, 24, 91) + 12 * fbm(H, W, 6, 92)) / (GRASS_FULL - GRASS_FROM)) ** 1.8
    newc = (xx < seam)[..., None]
    newc = newc & ~ndi.binary_dilation(pathm, iterations=1)[..., None]   # the paths stay light, as today's do
    img = np.where(newc, img * (1 - 0.6 * dens_s[..., None] * np.array([0.12, 0.0, 0.14])) * (1 - 0.38 * dens_s[..., None]), img)
    if os.environ.get('WEST_DEBUG'):
        np.save(os.environ['WEST_DEBUG'] + '_ground.npy', img.astype(np.float32))
    B = ndi.gaussian_filter1d(img, 16, axis=0)                           # the ground dips dark in the last columns
    xa, xb = seam - 56, seam + 6                                         # before the seam: bridge them, column by column
    t_ = ((np.arange(xa, seam) - xa) / (xb - xa))[None, :, None]
    target = B[:, xa:xa + 1] * (1 - t_) + B[:, xb:xb + 1] * t_
    wsouth = smooth((gy[:, 0] - 2780) / 120.0)[:, None, None]               # the north was approved as it is
    img[:, xa:seam] *= 1 + (np.clip(target / np.maximum(B[:, xa:seam], 1), 0.7, 1.5) - 1) * wsouth
    img = match_seam(img, pathm | brook.mask, seam, gy)                  # the ground first: today's is lighter
    if os.environ.get('WEST_DEBUG'):
        np.save(os.environ['WEST_DEBUG'] + '_ground2.npy', img.astype(np.float32))
    terr, terr_dry, terr_fade = draw_terraces(img, rng, pathm, (BROOK_A[0][0] - X0, BROOK_A[0][1] - Y0))
    southw = []
    for pts, w0, w1 in ((BROOK_A, 6, 12), (BROOK_C, 4, 7)):
        tk, _ = splprep(np.array([(x - X0, y - Y0) for x, y in pts], float).T, s=0, k=3)
        southw.append((np.array(splev(np.linspace(0, 1, 900), tk)).T, w0, w1))
    sb = ow.Brooks(southw, H, W, y0=0)
    sb.mask[:, seam:] = False
    sb.depth[:, seam:] = 0
    near_b = (ndi.distance_transform_edt(~sb.mask) < 7) & (xx < seam)   # the dark bank, fading out at the seam
    img[near_b] *= (1 - 0.15 * np.clip((seam - xx) / 40.0, 0, 1))[near_b][:, None]
    sb.draw(img, rng)
    oldw = np.array(Image.open(os.path.join(FULL, 'water.png')).convert('RGBA'))[Y0:Y1, EDGE:EDGE + W - seam].astype(float)
    water = brook.mask | sb.mask
    water[:, seam:] |= oldw[..., 3] > 0
    LAWN = np.array([0.60, 0.74, 0.56])

    # ---- houses and their gardens
    things, lights = [], []
    blocked = pathm | ndi.binary_dilation(water, iterations=2)      # no grass, no poppies here
    plots = np.zeros((H, W))                     # 1 inside a garden plot
    for (cx, cy), seed, kind, ruin in HOUSES:
        r = np.random.default_rng(seed * 11)
        hx_, hy_ = cx - X0 + int(r.integers(-6, 7)), cy - Y0 - 10
        hw = int(r.integers(40, 50))
        house = o.Minka(hx_, hy_, w=hw, seed=seed, kind=kind, ruin=ruin,
                        roof=17 if kind == 'kawara' else 19, pal=seed // 2 + seed % 2)
        things.append(house)
        blocked[hy_ - 34:hy_ + 4, hx_ - hw // 2 - 6:hx_ + hw // 2 + 8] = True
        left, right, top, bot = cx - 55 - X0, cx + 55 - X0, cy - 48 - Y0, cy + 50 - Y0
        e = ((xx - (left + right) / 2) / 56.0) ** 2 + ((yy - (top + bot) / 2) / 50.0) ** 2 + 0.15 * fbm(H, W, 6, seed)
        plots = np.maximum(plots, smooth((1.05 - e) / 0.25))
        # the plot's rim: a fence or a dry-stone wall all along the front, a gap where the stones lead out, the
        # sides half fallen
        gate = hx_ + int(r.integers(-8, 9))
        Fence = (lambda pts, k: o.Bambuszaun(pts, seed=seed + k, ruin=ruin)) if r.random() < 0.65 else \
            (lambda pts, k: o.Steinmauer(pts, seed=seed + k))
        things.append(Fence([(left, bot), (gate - 6, bot + 1)], 0))
        things.append(Fence([(gate + 6, bot + 1), (right, bot)], 1))
        for side, k in ((left, 2), (right, 3)):
            if r.random() < 0.75:
                y_a = top + int(r.integers(30, 50))
                things.append(o.Bambuszaun([(side, y_a), (side + int(r.integers(-1, 2)), bot - 3)], seed=seed + k,
                                           ruin=min(1, ruin + 0.3)))
        things.append(o.Platten((hx_ + int(r.integers(-4, 5)), hy_ + 5), (gate, bot + 4), seed=seed))
        blocked[hy_ + 3:bot + 6, gate - 4:gate + 5] = True
        # the garden: hydrangeas along the house, a bed, a fruit tree, things left behind
        for k in range(int(r.integers(4, 7))):
            things.append(o.Hortensie(hx_ + int(r.choice([-1, 1])) * int(r.integers(hw // 2 + 4, hw // 2 + 14)),
                                      hy_ + int(r.integers(2, 30)), int(r.integers(5, 8)),
                                      str(r.choice(['blau', 'lila', 'rosa'])), seed * 7 + k))
        bx = int(r.integers(left + 6, right - 30))
        things.append(o.Beet(bx, hy_ + int(r.integers(24, 40)), w=int(r.integers(14, 22)), rows=int(r.integers(3, 5)),
                             seed=seed))
        blocked[hy_ + 10:hy_ + 42, bx - 1:bx + 24] = True
        if r.random() < 0.8:
            things.append(o.Obstbaum(int(r.choice([left + 14, right - 14])), hy_ + int(r.integers(28, 44)), seed=seed))
        if seed in (1, 4, 6, 8):                     # candles left on the veranda of a few houses (Philip, round 2)
            side = -1                                # left of the door, on the veranda (Philip)
            cx_ = hx_ + side * int(r.integers(8, hw // 2 - 4))
            pts = [(cx_, hy_ + 1), (cx_ + 3, hy_ + 2), (cx_ - 3, hy_ + 2)]
            k = Kerzen(pts[:int(r.integers(2, 4))], seed=seed, on=house)   # the south's candles, two or three, drawn after the house
            things.append(k)
            lights += k.lights()
        prop = r.random()
        if prop < 0.35:
            things.append(z2.Bank(hx_ + int(r.choice([-1, 1])) * (hw // 2 - 8), hy_ + 7))   # beside the stones, not on them
        elif prop < 0.65:
            things.append(o.Waescheleine(hx_ + hw // 2 + 2, hy_ + 18, seed=seed))
        else:
            things.append(o.Korb(hx_ + int(r.integers(-hw // 2, hw // 2)), hy_ + 5))

    lawn = plots[..., None] * ~pathm[..., None]
    img = img * (1 - lawn) + img * LAWN * lawn                   # short garden grass: greener, a little darker
    # ---- zone 2: the greenhouse and the stonemason
    gh = o.Gewaechshaus(GLASHAUS[0] - X0, GLASHAUS[1] - Y0)
    things.append(gh)
    lights += gh.lights()
    x0b, y0b, x1b, y1b = gh.box()
    blocked[max(0, y0b):y1b, max(0, x0b):x1b] = True
    st = o.Steinmetz(STEINMETZ[0] - X0, STEINMETZ[1] - Y0)
    things.append(st)
    x0b, y0b, x1b, y1b = st.box()
    blocked[max(0, y0b):y1b, max(0, x0b):x1b] = True
    for k, (bx_, by_, bw, bh) in enumerate([(376, 2512, 7, 4), (388, 2508, 5, 6), (352, 2514, 9, 3), (392, 2518, 6, 3)]):
        things.append(o.Block(bx_ - X0, by_ - Y0, w=bw, h=bh, seed=50 + k))
        blocked[by_ - Y0 - 10:by_ - Y0 + 3, bx_ - X0 - 2:bx_ - X0 + bw + 6] = True
    # ---- zone 3: the shrine at the forest's edge, the orchard, the forest
    sx, sy = SHRINE[0] - X0, SHRINE[1] - Y0
    z3 = [o.Yashiro(sx, sy), o.Treppe(sx, sy + 32, n=8), o.Torii(sx, sy + 36),
          o.Komainu(sx - 20, sy + 34), o.Komainu(sx + 19, sy + 34, flip=True), o.Shinboku(sx + 54, sy - 10)]
    for t in z3:
        things.append(t)
        x0b, y0b, x1b, y1b = t.box()
        blocked[max(0, y0b):y1b, max(0, x0b):x1b] = True
    for (x, y) in ((SHRINE[0] - 32, SHRINE[1] + 2), (SHRINE[0] + 33, SHRINE[1] + 2)):
        t = z2.Steinlaterne(x - X0, y - Y0)
        things.append(t)
        lights += t.lights()
        blocked[y - Y0 - 14:y - Y0 + 4, x - X0 - 5:x - X0 + 6] = True
    for (x, y), (a_, b_) in zip(((424, 1928), (548, 1931)), (('B', 0), ('P', 0))):
        tc = bc[np.hypot(bc[:, 0] - (x - X0), bc[:, 1] - (y - Y0)).argmin()]
        Kind = ow.Bruecke if a_ == 'B' else ow.Brett
        t = Kind(int(round(tc[0])), int(round(tc[1])), np.pi / 2 - 0.15, 11)
        things.append(t)
    orch = np.zeros((H, W))
    ox0, oy0, ox1, oy1 = [v - o_ for v, o_ in zip(ORCHARD, (X0, Y0, X0, Y0))]
    e = ((xx - (ox0 + ox1) / 2) / ((ox1 - ox0) / 2)) ** 2 + ((yy - (oy0 + oy1) / 2) / ((oy1 - oy0) / 2)) ** 2
    orch = smooth((1.05 - e - 0.2 * fbm(H, W, 12, 71)) / 0.3)
    r3 = np.random.default_rng(73)
    for row, ty in enumerate(range(oy0 + 34, oy1 - 10, 50)):              # the old rows, gone loose
        for tx in range(ox0 + 22 + (row % 2) * 26, ox1 - 10, 52):
            x_, y_ = tx + int(r3.integers(-7, 8)), ty + int(r3.integers(-6, 7))
            near = pathm[max(0, y_ - 9):y_ + 10, max(0, x_ - 9):x_ + 10].any()
            if orch[y_, x_] < 0.4 or near:
                continue
            k = r3.random()
            t = o.Kaki(x_, y_, seed=80 + row * 10 + tx % 97, size=r3.uniform(0.65, 0.85)) if k < 0.6 else \
                o.Obstbaum(x_, y_, seed=90 + row * 10 + tx % 89, size=r3.uniform(0.6, 0.75))
            things.append(t)
            blocked[y_ - 3:y_ + 4, x_ - 4:x_ + 5] = True
            if r3.random() < 0.12:
                things.append(o.Leiter(x_ + 4, y_ - 1))
            elif r3.random() < 0.15:
                things.append(o.Korb(x_ + int(r3.integers(-10, 10)), y_ + 5))
    # the forest: today's edge firs (the wall that stood at x 0) planted all over the north-west
    tannen = [sp for sp in w['sprites'] if sp['name'].startswith('tanne') and sp['x'] <= 2 and 1300 < sp['y'] < 2000]
    fx = np.array([p[0] for p in FOREST]) - X0
    fy = np.array([p[1] for p in FOREST]) - Y0
    edge_y = np.interp(np.arange(W), fx, fy) + 14 * fbm(1, W, 6, 74)[0]
    keepout = ndi.binary_dilation(pathm | water, iterations=6)
    lane = ndi.binary_dilation(pathm, structure=np.ones((3, 9)), iterations=2)
    for d in range(2, 48, 2):                                            # a fir's top reaches ~50 px above its foot:
        keepout[d:] |= lane[:-d]                                         # none just below the path, the lane stays open
    keepout[sy - 60:sy + 40, sx - 40:sx + 80] = True                     # the shrine's clearing
    r4 = np.random.default_rng(75)
    forest_things = []
    clear = fbm(H, W, 16, 76)                                            # glades, and the forest thinner here and there
    for fy_ in range(-30, H, 12):
        for fx_ in range(-10, seam + 16, 15):
            x_, y_ = fx_ + int(r4.integers(-5, 6)) + (6 if (fy_ // 11) % 2 else 0), fy_ + int(r4.integers(-4, 5))
            if not (0 <= x_ < W and 0 <= y_ < H) or keepout[y_, x_]:
                continue
            past = y_ - edge_y[x_]                                       # > 0: out in the meadow
            if past > 0 and (past > 40 or r4.random() > 0.08 * (1 - past / 40)):
                continue                                                 # a few strays beyond the edge
            if clear[y_, x_] > 0.8 or r4.random() < 0.45 + 0.35 * smooth(clear[y_, x_] + 0.2):
                continue                                                 # thinner, more glades (Philip, round 2)
            if r4.random() < (0.09 if past > -70 else 0.03):              # now and then a broadleaf from the south
                lb = ol.Laubbaum(x_, y_, seed=int(r4.integers(0, 9999)), size=r4.uniform(0.7, 1.05))
                things.append(lb)
                blocked[max(0, y_ - 6):y_ + 3, max(0, x_ - 8):x_ + 9] = True
                continue
            if x_ + X0 > WW - 60 and r4.random() < 0.45 + 0.4 * (x_ + X0 > WW):
                continue                                                  # thinning out to today's scattered firs
            tpl = tannen[int(r4.integers(0, len(tannen)))]
            sp = dict(tpl, x=x_ + X0 - WW - tpl['w'] // 2, y=y_ + Y0 - (tpl['foot'] - tpl['y']),
                      foot=y_ + Y0)
            forest_things.append(sp)
            blocked[max(0, y_ - 6):y_ + 2, max(0, x_ - 6):x_ + 7] = True
    # ---- zone 4a: the mill, its bridge, the spring, a scarecrow, the bamboo grove
    ca, aw0, aw1 = southw[0]
    arc = np.r_[0, np.cumsum(np.hypot(*np.diff(ca, axis=0).T))]

    def brook_at(x_):                                                   # the mill brook's centre and half width at x
        i_ = int(np.abs(ca[:, 0] - x_).argmin())
        return ca[i_, 1], (aw0 + (aw1 - aw0) * arc[i_] / arc[-1]) / 2
    things.append(o.Muehle(MILL[0] - X0, MILL[1] - Y0, brook=brook_at))
    def glade(cx, cy, rx, ry, seed):                                    # trodden round a place, no hard edge
        return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 + 0.35 * fbm(H, W, 6, seed)
    gl = glade(MILL[0] - X0 - 26, MILL[1] - Y0 - 8, 56, 34, 109)
    ca = southw[0][0]
    tc = ca[np.hypot(ca[:, 0] - (548 - X0), ca[:, 1] - (3342 - Y0)).argmin()]
    things.append(ow.Bruecke(int(round(tc[0])), int(round(tc[1])), np.pi / 2 - 0.5, 15))
    things.append(ow.Quelle(SPRING[0] - X0, SPRING[1] - Y0))
    gl = np.minimum(gl, glade(SPRING[0] - X0 + 1, SPRING[1] - Y0 - 6, 20, 15, 110))
    blocked |= gl < 0.7
    things.append(o.Vogelscheuche(200 - X0, 2968 - Y0))
    bx, by, brx, bry = BAMBOO
    eb = ((xx - (bx - X0)) / brx) ** 2 + ((yy - (by - Y0)) / bry) ** 2 + 0.25 * fbm(H, W, 8, 93)
    img[eb < 1.0] *= 0.62                                                 # dark under the bamboo, leaf litter
    lit_ = rng.random((H, W)) < 0.06
    img[(eb < 1.0) & lit_] = o.hx('#5a5236')
    lane_b = ndi.binary_dilation(pathm, structure=np.ones((3, 7)), iterations=2)
    keep_b = lane_b.copy()
    for d in range(2, 46, 2):
        keep_b[d:] |= lane_b[:-d]
    keep_b[by - Y0 - 30:by - Y0 + 18, bx - X0 - 16:bx - X0 + 20] = True   # the clearing with the lantern
    r5 = np.random.default_rng(94)
    for cy_ in range(by - Y0 - bry - 10, by - Y0 + bry + 10, 9):
        for cx_ in range(bx - X0 - brx - 10, bx - X0 + brx + 10, 12):
            x_, y_ = cx_ + int(r5.integers(-3, 4)), cy_ + int(r5.integers(-2, 3))
            if not (0 <= x_ < W and 0 <= y_ < H) or eb[y_, x_] > 1.0 - 0.15 * r5.random() or keep_b[y_, x_]:
                continue
            things.append(o.Bambus(x_, y_, n=int(r5.integers(3, 6)), h=int(r5.integers(56, 80)), seed=int(r5.integers(0, 9999))))
            blocked[max(0, y_ - 4):y_ + 2, max(0, x_ - 6):x_ + 7] = True
    blocked |= eb < 1.0                                                   # no meadow grass under the bamboo
    t = z2.Steinlaterne(bx - X0 + 4, by - Y0 + 8)
    things.append(t)
    lights += t.lights()
    blocked |= terr & ~terr_dry
    # ---- the well, lanterns at the square and the way in, a torch by the first house
    things.append(o.Brunnen(SQUARE[0] - X0, SQUARE[1] - Y0 + 4))
    for (x, y) in ((SQUARE[0] - 34, SQUARE[1] - 10), (SQUARE[0] + 40, SQUARE[1] + 12), (860, 2290)):
        t = z2.Steinlaterne(x - X0, y - Y0)
        things.append(t)
        lights += t.lights()
        blocked[y - Y0 - 14:y - Y0 + 4, x - X0 - 5:x - X0 + 6] = True
    f = Fackel(660 - X0, 2318 - Y0)
    things.append(f)
    lights += f.lights()

    # ---- the meadow: today's poppies stay, the new ones thin out westward; the grass rises in the village
    heads = np.zeros((H, W, 4), np.uint8)
    fl = ofl[Y0:Y1, :X1 - WW]
    heads[:, WW - X0:] = fl
    heads[:, WW - X0:WW - X0 + EDGE] = 0
    field6.HEADS[:] = field6.make_heads(np.random.default_rng(31))
    keep = 0.79 * (1 - smooth((WW + 40 - gx) / 260.0)) + 0.05 + 0.08 * smooth(-fbm(H, W, 30, 5)) + 0.6 * orch
    keep = keep * (1 - 0.92 * dens_s)
    for (x, y, kk, ph) in patches(H, W, np.full((H, W), 0.5), ndi.binary_dilation(blocked, iterations=2), rng, 110000):
        if x + X0 >= WW + EDGE or rng.random() > keep[min(y + 2, H - 1), min(x + 2, W - 1)]:
            continue
        for j, row in enumerate(field6.HEADS[kk]):
            for i, ch in enumerate(row):
                if ch != '.' and y + j < H and x + i < W:
                    heads[y + j, x + i, :3] = CMAP[ch]
                    heads[y + j, x + i, 3] = 255
    m = heads[..., 3] > 0
    img[m] = heads[m][:, :3]
    # tall grass only in loose drifts between the gardens; inside the plots it is short and full of flowers
    dens = smooth((WW - 40 - gx + 30 * fbm(H, W, 20, 7)) / 220.0) * np.clip(0.18 + 0.32 * fbm(H, W, 14, 8), 0, 1)
    dens = np.clip(dens * (1 - 0.85 * plots), 0, 1)
    dens = np.where(xx < seam, np.maximum(np.maximum(dens, dens_s), 0.45 * terr_dry * terr_fade ** 2), dens)
    dens[terr & ~terr_dry] = 0
    dens *= np.clip((gl - 0.7) / 0.9, 0, 1) ** 1.5                     # the grass grows back in round the glades
    grass_free = ndi.binary_dilation(blocked, iterations=2)
    bank_s = ndi.binary_dilation(sb.mask, iterations=5) & ~ndi.binary_dilation(sb.mask, iterations=1) & ~pathm
    grass_free &= ~bank_s                                               # up to the water, as today's brooks
    d3 = np.clip(0.78 + 0.32 * fbm(H, W, 16, 306), 0.38, 1)             # the south's zone 3: patchier from Z3_FROM on
    patch3 = 1 - (1 - d3) * np.clip((gy - Z3_FROM) / 90.0, 0, 1)
    for _ in range(int(W * H / 3)):                         # short garden grass: dark tufts close together
        x, y = int(rng.integers(2, W - 2)), int(rng.integers(4, H))
        if rng.random() > plots[y, x] ** 1.5 or grass_free[y, x]:
            continue
        for d in range(int(rng.integers(1, 3))):
            img[y - d, x + (d and rng.random() < 0.3)] = o.MOSS[1 + d] * 0.9
    for _ in range(int(W * H / 7)):
        x, y = rng.uniform(2, W - 2), rng.uniform(14, H)
        xi, yi = int(x), min(int(y), H - 1)
        if rng.random() > dens[yi, xi] * (1 - 0.18 * dens_s[yi, xi]) * patch3[yi, xi] or grass_free[yi, xi]:   # 1 in 8.5
            continue
        b_ = z2.Blade(x, yi, rng)
        b_.h = max(4, int(round(b_.h * (1 - 0.3 * dens_s[yi, xi]))))   # as short as today's, where they crowd
        things.append(b_)
    for _ in range(16000):
        x, y = int(rng.integers(4, W - 4)), int(rng.integers(6, H - 2))
        if rng.random() > 0.05 + 0.4 * dens[y, x] * (1 - 0.75 * dens_s[y, x]) + 0.9 * plots[y, x] ** 2 or grass_free[y, x]:
            continue
        things.append(z2.Wildflower(x, y, int(rng.choice(3, p=[0.45, 0.33, 0.22])), rng, int(dens[y, x] * 6)))

    # ---- today's standing things in the window, without the fir wall at the edge
    sprites = [s for s in w['sprites'] if s['x'] + WW < X1 + 40 and s['x'] + WW + s['w'] > X0
               and Y0 - 160 < s['y'] < Y1 and s['x'] > 2]           # the edge wall: every fir standing at x 0

    class Old:
        def __init__(s, sp):
            s.sp = sp

        def box(s):
            return (0, 0, 0, s.sp['foot'] - Y0)

        def draw(s, img, G):
            sp = s.sp
            a = np.array(Image.open(os.path.join(ROOT, 'assets', 'world', 'sprites', sp['name'] + '.png'))
                         .convert('RGBA'))[:, :sp['w']].astype(float)
            x_, y_ = sp['x'] + WW - X0, sp['y'] - Y0
            ya, yb = max(0, y_), min(H, y_ + a.shape[0])
            xa, xb = max(0, x_), min(W, x_ + a.shape[1])
            if ya >= yb or xa >= xb:
                return
            sub = a[ya - y_:yb - y_, xa - x_:xb - x_]
            al = sub[..., 3:] / 255.0
            img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al
    things += [Old(s) for s in sprites + forest_things]
    for l in w['lights']:
        if X0 <= l['x'] + WW < X1 and Y0 <= l['y'] < Y1:
            lights.append(dict(l, x=l['x'] + WW - X0, y=l['y'] - Y0))
    for t in sorted(things, key=lambda t: getattr(t, 'order', None) or t.box()[3]):
        t.draw(img, G)
    if os.environ.get('WEST_DEBUG'):
        np.save(os.environ['WEST_DEBUG'] + '_pre.npy', img.astype(np.float32))
    img = match_seam(img, water | pathm, seam, gy)
    if os.environ.get('WEST_DEBUG'):
        np.save(os.environ['WEST_DEBUG'] + '_post.npy', img.astype(np.float32))
    ww = dict(w, lights=lights, wisps=[])
    out_img = mood_map.mood(np.clip(img, 0, 255), ww, 2.0, grass_mist=0.45)
    Image.fromarray(np.clip(out_img, 0, 255).astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2)
    print('ok')
