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
X0, X1, Y1 = 0, 1180, 4800                 # the window drawn (west coordinates): zone 3 up to 1380, 4b to the world's end
Y0 = int(os.environ.get('WEST_Y0', 1380))   # a later first row only to look at the south quickly (other noise)
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
# zone 4b: the west lake with its own shore (plan step 65, round 3), the iris bay in the north with the zigzag
# bridge from the fisherman's hut, the teahouse on the north-east shore, the shore path on to today's
LAKE = [(872, 4150), (850, 4128), (800, 4078), (735, 4066), (690, 4098), (640, 4084), (590, 4110),
        (540, 4150), (490, 4170), (468, 4215), (500, 4262), (520, 4300), (470, 4318), (418, 4340), (402, 4400),
        (430, 4452), (408, 4510), (440, 4560), (512, 4578), (560, 4630), (640, 4660), (730, 4648), (790, 4672),
        (840, 4640), (870, 4590), (858, 4520), (884, 4460), (876, 4380), (890, 4300), (868, 4230),
        (886, 4190)]
IRISES = [(530, 4150), (570, 4132), (610, 4118), (650, 4106), (700, 4110), (750, 4090), (790, 4094)]
HUT = (548, 4072)
BRIDGE = [(578, 4094), (578, 4112), (604, 4112), (604, 4140), (586, 4140), (586, 4172), (622, 4172), (622, 4204)]
TEA_X = 834
POOLS = [(300, 4262, 30, 'iris'), (175, 4480, 24, 'schilf'), (330, 4640, 18, 'schilf'), (140, 4060, 16, 'schilf')]
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
    'see': [(600, 3420), (608, 3560), (612, 3640), (616, 3740), (610, 3860), (600, 3950), (590, 4020), (582, 4070)],
    'ufer': [(592, 4026), (640, 4024), (700, 4018), (760, 4020), (820, 4032), (866, 4066), (896, 4116), (910, 4180),
             (916, 4250), (922, 4290), (930, 4320), (930, 4342)],
    'tuempel': [(608, 3884), (540, 3930), (460, 3990), (390, 4070), (338, 4150), (318, 4196)],   # 4b: to the pool                   # 4b: round the lake into today's
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


def draw_lake(img, rng, xx, yy, gx, gy, seam):
    """Zone 4b: the west lake (the south's lake water: objects_lake.paint_lake), a shallow rim, the wide shallows of
    the iris bay in the north; and at the world's southern edge today's reed sea, marsh and open water running on
    west (zone4_layout.edge, in today's x). -> masks."""
    from PIL import ImageDraw
    from scipy.interpolate import splprep, splev
    from scipy.spatial import cKDTree
    import zone4_layout as L4
    p = np.array(LAKE + [LAKE[0]], float).T
    tck, _ = splprep(p, s=0, k=3, per=True)
    sh = np.array(splev(np.linspace(0, 1, 1600), tck)).T - (X0, Y0)
    pts = np.stack([xx.ravel(), yy.ravel()], 1)
    mk = Image.new('L', (xx.shape[1], xx.shape[0]), 0)
    ImageDraw.Draw(mk).polygon([tuple(q) for q in sh], fill=1)
    lake = np.array(mk) > 0
    tx = TEA_X - X0                                                     # the teahouse: its front on the bank, a
    rows = [y_ for x_ in range(tx - 20, tx + 21, 4) for y_ in [int(np.argmax(lake[4040 - Y0:, x_]))] if y_ > 0]
    ty = 4040 - Y0 + min(rows) + 1                                      # cove under its deck
    lake |= (((xx - tx) / 26.0) ** 2 + ((yy - ty - 10) / 12.0) ** 2 + 0.2 * fbm(*xx.shape, 3, 127) < 1) & (yy > ty)
    lake = ndi.binary_opening(lake, iterations=1)                                  # no single-pixel jags
    din = ndi.distance_transform_edt(lake)
    tk, _ = splprep(np.array(IRISES, float).T, s=0, k=3)
    ic = np.array(splev(np.linspace(0, 1, 300), tk)).T - (X0, Y0)
    di = cKDTree(ic).query(pts)[0].reshape(xx.shape)
    bc_ = np.mean(BRIDGE, 0) - (X0, Y0)
    bay = (di < 15 + 6 * fbm(*xx.shape, 5, 121)) | (((xx - bc_[0]) / 48.0) ** 2 + ((yy - bc_[1] + 6) / 54.0) ** 2
                                                    + 0.3 * fbm(*xx.shape, 5, 128) < 1)   # the iris shallows
    edge = 4000 + L4.edge(gx - WW) - Y0 + 4 * fbm(*xx.shape, 6, 122)              # today's edge, in its own x
    west = xx < seam
    sea_reeds = (yy > edge) & west
    marsh = (yy > edge + 30 + 8 * fbm(*xx.shape, 8, 123)) & (fbm(*xx.shape, 4, 124) > -0.3) & west
    open_w = (yy > edge + 52 + 6 * np.sin((gx - WW) / 23.0)) & west
    shallow = (lake & ((din < 5 + 3 * fbm(*xx.shape, 4, 125)) | bay)) | (marsh & ~open_w)
    r7 = np.random.default_rng(171)
    pools = np.zeros(xx.shape, bool)                                     # pools in the meadow west of the lake
    for x_, y_, r_, _ in POOLS:
        if 0 <= y_ - Y0 < xx.shape[0]:
            pools |= L4.organic_pool(x_ - X0, y_ - Y0, r_ * 1.8, r7, xx.shape)
    water = lake | marsh | open_w | pools
    shallow |= pools & (ndi.distance_transform_edt(pools) < 4)
    ol.paint_lake(img, 0, water, shallow, rng)
    return dict(lake=lake, din=din, bay=bay & lake, sea_reeds=sea_reeds, marsh=marsh, open_w=open_w,
                water=water, shallow=shallow, pools=pools, shore=ndi.distance_transform_edt(~lake), tea=(tx, ty))


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
    seam_ = WW + EDGE - X0                                              # under today's south-west reed belt the
    gy_ = np.arange(H)[:, None] + Y0                                    # ground runs light past the seam: to its
    sub = img[:, seam_:seam_ + 14]                                      # neighbours' tone, grass only
    near = img[:, seam_ + 16:seam_ + 26]
    lightp = lambda a: (a[..., 0] > a[..., 1] + 3) & (a.mean(2) > 112)
    okm = ~ndi.binary_dilation(lightp(img[:, seam_:seam_ + 26]), iterations=2)
    def vmean(a, m):
        return ndi.gaussian_filter1d((a.mean(2) * m).sum(1), 16) / np.maximum(ndi.gaussian_filter1d(m.sum(1).astype(float), 16), 0.5)
    cols = np.stack([vmean(sub[:, k:k + 1], okm[:, k:k + 1]) for k in range(14)], 1)
    tgt = vmean(near, okm[:, 16:26])[:, None]
    gain = np.clip(tgt / np.maximum(cols, 1), 0.8, 1.3) ** (smooth((gy_ - 3990) / 60.0))
    img[:, seam_:seam_ + 14] = np.where(okm[:, :14, None], sub * gain[..., None], sub)
    yy, xx = np.mgrid[0:H, 0:W]
    gx, gy = xx + X0, yy + Y0
    G = np.random.default_rng(3).random((H, W))

    # ---- the square: trodden gravel round the well
    sq = extras.forecourt(H, W, SQUARE[0] - X0, SQUARE[1] - Y0, 46, 26, rng)
    if sq.any():                                     # (outside a WEST_Y0 window)
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
    mb = ~ndi.binary_dilation(pathm | brook.mask, iterations=2)          # measured and changed on the grass only
    B = ndi.gaussian_filter1d(img * mb[..., None], 16, axis=0) / np.maximum(
        ndi.gaussian_filter1d(mb.astype(float), 16, axis=0), 0.05)[..., None]   # the ground dips dark in the last columns
    xa, xb = seam - 56, seam + 6                                         # before the seam: bridge them, column by column
    t_ = ((np.arange(xa, seam) - xa) / (xb - xa))[None, :, None]
    target = B[:, xa:xa + 1] * (1 - t_) + B[:, xb:xb + 1] * t_
    wsouth = smooth((gy[:, 0] - 2780) / 120.0)[:, None, None]               # the north was approved as it is
    img[:, xa:seam] *= 1 + (np.clip(target / np.maximum(B[:, xa:seam], 1), 0.7, 1.5) - 1) * wsouth * mb[:, xa:seam, None]
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
    lk = draw_lake(img, rng, xx, yy, gx, gy, seam)
    oldw = np.array(Image.open(os.path.join(FULL, 'water.png')).convert('RGBA'))[Y0:Y1, EDGE:EDGE + W - seam].astype(float)
    water = brook.mask | sb.mask | lk['water']
    water[:, seam:] |= oldw[..., 3] > 0
    oldw_full = np.zeros((H, W, 4))
    oldw_full[:, seam:] = oldw
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
            if not 0 <= y_ < H or orch[y_, x_] < 0.4 or near:
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
    # ---- zone 4b: the fisherman's hut with its zigzag bridge through the irises, the teahouse, the lake's things
    lake, shore, din = lk['lake'], lk['shore'], lk['din']
    def first_water(x_, below):                                         # the first lake row at column x below a row
        col = lake[below:, x_]
        return below + int(np.argmax(col)) if col.any() else None
    hx0, hy0 = HUT[0] - X0, HUT[1] - Y0
    things.append(o.Minka(hx0, hy0, w=26, wall=9, roof=15, seed=31, kind='kaya', ruin=0.55, pal=1))
    things.append(o.Netzgestell(hx0 - 36, hy0 + 3))
    blocked[hy0 - 30:hy0 + 7, hx0 - 38:hx0 + 22] = True
    br = [(x - X0, y - Y0) for x, y in BRIDGE]
    steg = o.yatsuhashi(br, width=7, dry=first_water(br[0][0], br[0][1]))
    things += steg
    bridge_m = np.zeros((H, W), bool)
    for t in steg:
        x0b, y0b, x1b, y1b = t.box()
        bridge_m[max(0, y0b):y1b, max(0, x0b):x1b] = True
    bx_, by_ = br[-1][0] + 15, br[-1][1] - 4
    things.append(ol.Boot(bx_, by_))                                     # moored at the bridge's end
    bridge_m[by_ - 6:by_ + 6, bx_ - 12:bx_ + 13] = True
    things.append(o.Platten((hx0 + 4, hy0 + 5), (br[0][0] + 2, br[0][1] - 10), seed=31))   # from the hut to the path
    blocked[hy0 + 2:br[0][1] - 6, hx0:br[0][0] + 5] = True
    tx, ty = lk['tea']
    tea = o.Teehaus(tx, ty, deck=6)
    things.append(tea)
    x0b, y0b, x1b, y1b = tea.box()
    blocked[max(0, y0b + 10):y1b, max(0, x0b):x1b] = True
    bridge_m[max(0, y0b):y1b + 18, max(0, x0b):x1b] = True              # reeds below it would hide the deck
    bpx, bpy = POOLS[0][0] - X0 + 6, POOLS[0][1] - Y0 - POOLS[0][2] - 12   # the bench by the iris pool stays clear
    bridge_m[bpy - 6:bpy + 10, bpx - 6:bpx + 18] = True
    r6 = np.random.default_rng(130)
    deep = lake & (din > 14) & ~ndi.binary_dilation(lk['bay'] | bridge_m, iterations=10)
    spots = np.argwhere(deep)
    pick = spots[r6.choice(len(spots), 17, replace=False)]
    for k, (y_, x_) in enumerate(pick[:12]):
        things.append(ol.Seerosen(int(x_), int(y_), int(r6.integers(4, 9)), 140 + k))
    for k, (y_, x_) in enumerate(pick[12:16]):
        things.append(ol.WasserStein(int(x_), int(y_), r6.uniform(3, 5), 150 + k))
    things.append(ol.Treibholz(int(pick[16][1]), int(pick[16][0]), int(r6.integers(18, 26)), r6.uniform(-0.6, 0.6), 155))
    kind_n = fbm(H, W, 6, 131)                                           # the irises: patches of one colour each
    free_i = ~ndi.binary_dilation(bridge_m, iterations=2)
    ipool = np.zeros((H, W), bool)
    for x_, y_, r_, kind in POOLS:
        if kind == 'iris' and 0 <= y_ - Y0 < H:
            ipool |= lk['pools'] & (np.hypot(xx - (x_ - X0), yy - (y_ - Y0)) < 2.5 * r_)
    ipool = ndi.binary_dilation(ipool, iterations=3) & ~ndi.binary_erosion(ipool, iterations=4)   # the rim only
    iris_area = (lk['bay'] | (ndi.binary_dilation(lk['bay'], iterations=4) & ~lake) | ipool) & free_i
    iris_area &= ~ndi.binary_dilation(pathm, iterations=3)
    ys_, xs_ = np.nonzero(iris_area & (r6.random((H, W)) < 1 / 26 * np.clip(0.6 + 0.5 * fbm(H, W, 4, 132), 0.15, 1.2)))
    for y_, x_ in zip(ys_, xs_):
        v = kind_n[y_, x_]
        things.append(o.Iris(int(x_), int(y_), seed=int(r6.integers(0, 10 ** 6)),
                             kind='weiss' if v > 1.1 else 'indigo' if v < -1.1 else 'lila', wet=bool(lake[y_, x_])))
    westness = np.clip((660 - gx) / 260.0, 0, 1) + np.clip((gy - 4420) / 200.0, 0, 1) * 0.5
    belt = (((lake & (din < 6)) | (~lake & (shore < 4))) & (fbm(H, W, 10, 126) > 0.35 - 0.9 * westness)
            & ~lk['bay'] & ~ndi.binary_dilation(lk['bay'], iterations=6))
    pr = lk['pools'] & ~ndi.binary_dilation(ipool, iterations=8)
    prim = ndi.binary_dilation(pr, iterations=3) & ~ndi.binary_erosion(pr, iterations=2) & (fbm(H, W, 5, 133) > -0.2)
    reed_land = (belt | prim | (lk['sea_reeds'] & ~lk['open_w'])) & ~ndi.binary_dilation(pathm | bridge_m, iterations=3)
    reed_land &= ~ndi.binary_dilation(sb.mask | brook.mask, iterations=2)
    ys_, xs_ = np.nonzero(reed_land)
    pk = r6.random(len(ys_)) < np.where(lk['sea_reeds'][ys_, xs_], 1 / 9, 1 / 16)
    for y_, x_ in zip(ys_[pk], xs_[pk]):
        if r6.random() < 0.78:
            things.append(ow.Schilf(int(x_), int(y_), int(r6.integers(6, 12)), int(r6.integers(0, 10 ** 6))))
        else:
            things.append(ow.Rohrkolben(int(x_), int(y_), int(r6.integers(3, 6)), int(r6.integers(0, 10 ** 6))))
    blocked |= reed_land | iris_area
    pb = lk['pools'].copy()                                             # tall blades rooted below a pool would hide it
    for k in range(1, 11):
        blocked[k:] |= pb[:-k]
    wet6 = ndi.binary_dilation(water, iterations=6)
    from objects_south import Findling
    meadow = [(o.Kaki, 250, 4330, 0.8), (o.Kaki, 90, 4290, 0.7)]
    for cls_, x, y, sz in meadow:                                       # two old persimmons nobody picks
        if not wet6[y - Y0, x - X0]:
            things.append(cls_(x - X0, y - Y0, seed=175 + x % 7, size=sz))
            blocked[y - Y0 - 3:y - Y0 + 4, x - X0 - 4:x - X0 + 5] = True
    gl4 = []
    for k, (x, y) in enumerate([(205, 3990), (395, 4380)]):            # the drying racks of the old fields
        things.append(o.Hasagi(x - X0, y - Y0, w=30 - 8 * k, seed=170 + k))
        gl4.append((x - X0 + 15 - 4 * k, y - Y0 + 2, 24 - 4 * k, 12, 190 + k))   # trodden round, no tall blades
    for k, (x, y, r_) in enumerate([(60, 3930, 7), (230, 4120, 6), (120, 4380, 8), (260, 4560, 6), (40, 4600, 7),
                                    (370, 4290, 5), (90, 4700, 6)]):
        if not wet6[y - Y0, x - X0]:
            things.append(Findling(x - X0, y - Y0, r_, 180 + k))
            blocked[y - Y0 - r_:y - Y0 + 3, x - X0 - r_:x - X0 + r_ + 2] = True
    pcx, pcy = POOLS[0][0] - X0, POOLS[0][1] - Y0                       # a bench by the iris pool, the trail's end
    things.append(o.SanfteBank(pcx + 6, pcy - POOLS[0][2] - 12))
    gl4.append((pcx + 6, pcy - POOLS[0][2] - 13, 20, 11, 192))
    for cx_, cy_, rx_, ry_, sd_ in gl4:                                 # soft glades, as round the mill
        gl = np.minimum(gl, glade(cx_, cy_, rx_, ry_, sd_))
    blocked |= gl < 0.7
    for k, (x, y) in enumerate([(380, 4040), (440, 4200), (230, 4420), (330, 4560), (150, 4640), (520, 3930),
                                (720, 3960), (130, 4180), (300, 4700), (600, 4720), (40, 4150), (170, 4280),
                                (60, 4500), (210, 4720), (380, 3960), (290, 3870)]):
        x_, y_ = x - X0, y - Y0
        if not (0 <= y_ < H) or wet6[y_, x_] or pathm[y_ - 8:y_ + 5, x_ - 9:x_ + 10].any():
            continue
        things.append(ol.Laubbaum(x_, y_, seed=160 + k, size=r6.uniform(0.9, 1.2), leaf=ol.LEAVES[k % 8]))
        blocked[y_ - 4:y_ + 3, x_ - 6:x_ + 7] = True
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
    REEDS = np.array(ow.REED + ow.PLUME + ow.CATTAIL)                 # today's reed belt at the old south-west edge
    sx_ = slice(WW + EDGE - X0, WW + EDGE + 14 - X0)                  # reaches past the fir wall's columns: gone too
    hs = heads[:, sx_, :3].astype(float)
    is_reed = (np.abs(hs[..., None, :] - REEDS[None, None]).sum(-1).min(-1) < 6) & (heads[:, sx_, 3] > 0)
    is_reed &= (gy[:, sx_] > 3990)
    heads[:, sx_][is_reed] = 0
    refill = np.zeros((H, W))                                          # where it stood our grass grows in instead
    refill[:, sx_] = np.clip(ndi.gaussian_filter(is_reed.astype(float), 3) * 2.2, 0, 1)
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
    dens = np.maximum(dens, dens_s * refill)
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
        if -9999 < t.box()[3] < -60:                                     # (above a WEST_Y0 window)
            continue
        t.draw(img, G)
    if os.environ.get('WEST_DEBUG'):
        np.save(os.environ['WEST_DEBUG'] + '_pre.npy', img.astype(np.float32))
    img = match_seam(img, water | pathm, seam, gy)
    if os.environ.get('WEST_DEBUG'):
        np.save(os.environ['WEST_DEBUG'] + '_post.npy', img.astype(np.float32))
    ww = dict(w, lights=lights, wisps=[])
    lakes = lk['water'] | ((oldw_full[..., 3] > 0) & (gy > 3950))       # the mist's band and the calm over the lakes
    band = np.clip(ndi.gaussian_filter(lakes.astype(float), 4) * 1.3, 0, 1)
    calm = ndi.gaussian_filter(lakes.astype(float), 6)
    out_img = mood_map.mood(np.clip(img, 0, 255), ww, 2.0, grass_mist=0.45, water_band=band, calm=calm)
    fog = np.clip((gy - 4690) / 110.0, 0, 1) ** 1.4 * 0.88                # the world's end in mist, as the south's
    out_img = out_img * (1 - fog[..., None]) + np.array([180.0, 181.0, 180.0]) * fog[..., None]
    Image.fromarray(np.clip(out_img, 0, 255).astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2)
    print('ok')
