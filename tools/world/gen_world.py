#!/usr/bin/env python3
"""Builds the walkable world of Akahana from the same code that drew the cherry-tree wallpaper.

One continuous map, generated in a single canvas so nothing has seams:
  bottom middle  the cherry-tree meadow exactly as in the wallpaper (tree, shrine, camp, lanterns)
  across         a stream with a wooden bridge and stepping stones
  top            the foothills: ruined chapel, shepherd's cottage, firs, snow, a cliff as the end

Outputs (assets/world/):
  ground.png   flat layer: ground, paths, stems, water, bridge, fire ring
  flowers.png  poppy heads only (RGBA) - the game sways them in the wind
  sprites/*.png + world.json   everything upright, one strip per object (animation frames side by side),
               with its foot line for depth sorting
  walk.png     255 = walkable
  mist1.png, mist2.png  tileable mist noise
Run: python3 tools/world/gen_world.py   (takes a few minutes; run it niced on the phone)
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

LIB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
sys.path.insert(0, LIB)
import field6  # noqa: E402
from field6 import ground_organic, patches, HEADS, CMAP, WH, L1, MG, DG, K  # noqa: E402
import extras  # noqa: E402
from fire import Fire  # noqa: E402
from tree import PK  # noqa: E402
from objects2 import Tent2, Lantern3, ShrineB, Banner3, STONE, MOSS3, WOOD, put, hx  # noqa: E402
from berg_objects import Pine  # noqa: E402
from ruin import Ruin, Cottage  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT = os.path.join(ROOT, 'assets', 'world')
W, H = 540, 1200
SX, SY = 180, 800                    # where the wallpaper's 180x400 frame sits in the world
FRAMES = 64                          # animation frames per loop (the wallpaper loops every 8 s)
FPS = 8

rng = np.random.default_rng(31)
field6.HEADS[:] = field6.make_heads(rng)
yy, xx = np.mgrid[0:H, 0:W]


def fbm(s, seed):
    n = ndi.gaussian_filter(np.random.default_rng(seed).normal(0, 1, (H, W)), s)
    return n / n.std()


def S(x, y):
    """Wallpaper coordinates -> world coordinates."""
    return x + SX, y + SY


# ------------------------------------------------------------------ altitude, stream, tree shade
alt = np.clip((560 - yy) / 520, 0, 1)                    # 0 meadow .. 1 under the mountains

STREAM = [(-12, 690), (70, 664), (150, 700), (220, 662), (272, 646), (340, 668), (420, 640), (490, 668), (552, 650)]
from scipy.interpolate import splprep, splev  # noqa: E402
tck, _ = splprep(np.array(STREAM, float).T, s=0, k=3)
su = np.linspace(0, 1, 1400)
spx, spy = splev(su, tck)
sd = np.full((H, W), 999.0)
salong = np.zeros((H, W))
band = (yy > 600) & (yy < 740)
for k in range(0, 1400, 2):
    dd = np.hypot(xx[band] - spx[k], yy[band] - spy[k])
    cur = sd[band]
    m = dd < cur
    cur[m] = dd[m]
    sd[band] = cur
    al = salong[band]
    al[m] = su[k]
    salong[band] = al
swid = 8 + 2.0 * np.sin(salong * 23) + 1.0 * fbm(2, 3)
water = sd < swid
sbank = (sd < swid + 2.2) & ~water

tree_lay = np.load(os.path.join(LIB, 'tree_layer.npy'))
tree_sh = np.load(os.path.join(LIB, 'tree_shadow.npy'))
TX, TY = S(-16, 48)                                       # same placement as the wallpaper
shadow = np.zeros((H, W))
shadow[TY:TY + 200, TX:TX + 200] = tree_sh

# ------------------------------------------------------------------ ground
fog = np.clip(0.70 + 0.10 * fbm(18, 4) - 0.45 * shadow + 0.12 * alt, 0, 1)
flow = np.clip(0.20 + 0.10 * fbm(10, 5), 0, 1) * np.clip(1 - 1.6 * shadow, 0, 1)
flow *= np.clip(1 - 1.5 * alt, 0, 1) * np.clip((sd - swid) / 6, 0, 1)
ground = ground_organic(H, W, fog, flow, rng)

snow = (fbm(6, 8) + 2.2 * alt - 1.9 + 0.35 * (rng.random((H, W)) - .5)) > 0
sg = ndi.gaussian_filter(np.random.default_rng(12).random((H, W)), 0.7)      # clumped grain, never a checkerboard
sg = (sg - sg.min()) / (sg.max() - sg.min())
ground[snow] = np.where((sg > 0.48)[snow][:, None], WH, L1)
ground[snow & (sg < 0.18)] = MG

# ------------------------------------------------------------------ paths
prng = np.random.default_rng(91)
WALL_PATH = [(63, 294), (63, 276), (64, 258), (69, 241), (80, 229), (96, 219), (112, 208), (124, 192),
             (130, 174), (131, 160), (129, 146), (124, 137)]           # route the user drew in the wallpaper
PATHS = {
    'wallpaper': [S(*p) for p in WALL_PATH],
    'north': [S(124, 137), S(122, 112), S(116, 80), S(104, 40), S(96, 0), (272, 760), (270, 712), (270, 672),
              (271, 640), (276, 606), (290, 566), (300, 526), (296, 500), (276, 470), (258, 430), (240, 392),
              (236, 360)],
    'summit': [(236, 330), (244, 290), (262, 250), (280, 196), (272, 140), (278, 90), (270, 46)],
    'west': [S(60, 300), (196, 1080), (150, 1060), (110, 1026), (84, 990)],
    'east': [S(140, 136), (348, 930), (390, 902), (430, 872), (462, 852)],
    'ruin_side': [(300, 520), (322, 510), (340, 500), (352, 494)],
}
path_mask = np.zeros((H, W), bool)
for name, pts in PATHS.items():
    pm, pc, pd_, pw_ = extras.path_mask(H, W, pts, prng)
    pm &= ~water
    extras.draw_path(ground, pm, pc & ~water, pd_, pw_, prng)
    path_mask |= pm
court = extras.forecourt(H, W, *S(122, 135), 17, 6.5, prng)
camp = extras.forecourt(H, W, *S(60, 298), 24, 10, prng)
extras.draw_earth(ground, camp, prng)
extras.draw_gravel(ground, court, prng)

# ------------------------------------------------------------------ stream, banks, bridge, stepping stones
g = rng.random((H, W))
EARTH = [hx(c) for c in ['#2a2422', '#3b332e', '#51463e']]
ground[sbank] = np.array(EARTH)[np.clip((g[sbank] * 3).astype(int), 0, 2)]
mossy = sbank & (fbm(1.2, 6) > 0.6)
ground[mossy] = MOSS3[1]
WAT = [hx(c) for c in ['#3c4650', '#4e5a65', '#64717c', '#7f8c96', '#a3aeb6', '#d6dde1']]
rip = np.sin(salong * 900 + sd * 0.9 + 2 * fbm(1.5, 7))
wv = 0.52 - 0.22 * np.clip(1 - sd / swid, 0, 1) + 0.12 * rip + 0.06 * (g - .5)
wi = np.clip((wv * 6).astype(int), 0, 5)
ground[water] = np.array(WAT)[wi][water]
ground[water & (rip > 0.92) & (g < 0.35)] = WAT[5]
ground[water & (sd > swid - 1.2) & (g < 0.4)] = WAT[4]

BRX = 271                                                 # the north path crosses here
cols = water[:, BRX - 8:BRX + 9].any(axis=1)
by0, by1 = np.where(cols)[0].min() - 3, np.where(cols)[0].max() + 3
bridge = (xx >= BRX - 7) & (xx <= BRX + 7) & (yy >= by0) & (yy <= by1)
for j in range(by0, by1 + 1):
    for i in range(BRX - 7, BRX + 8):
        u = (i - (BRX - 7)) / 14
        if i in (BRX - 7, BRX + 7):
            c = WOOD[3] if i == BRX - 7 else WOOD[1]                       # rails
            if (j - by0) % 7 == 0:
                c = WOOD[0]                                                # posts
        else:
            board = (j - by0) % 3 == 2
            v = 0.66 - 0.28 * u - (0.3 if board else 0) + 0.08 * (g[j, i] - .5)
            c = WOOD[int(np.clip(v, 0, .99) * 5)]
        ground[j, i] = c
    if water[j, BRX + 8]:
        ground[j, BRX + 8:BRX + 11] = (ground[j, BRX + 8:BRX + 11] * 0.55).astype(np.uint8)

stones = np.zeros((H, W), bool)
stone_at = []
SX_ST = 118                                               # stepping stones further west
scol = np.where(water[:, SX_ST])[0]
for t in np.linspace(0, 1, 4):
    cy_ = scol.min() - 1 + t * (scol.max() - scol.min() + 2)
    cx_ = SX_ST + 3 * np.sin(t * 6)
    rx, ry = 3.0, 2.0
    e = ((xx - cx_) / rx) ** 2 + ((yy - cy_) / ry) ** 2
    ring = (e <= 1.8) & (e > 1.0) & water
    ground[ring] = WAT[4]
    m = e <= 1.0
    lit = (xx - cx_) + (yy - cy_) * 1.3 < -0.5
    ground[m] = MG
    ground[m & lit] = L1
    ground[m & lit & (e < 0.3)] = WH
    ground[m & (yy - cy_ > ry * 0.5)] = DG
    stones |= e <= 1.15
    stone_at.append((cx_, cy_))

# the hops between the stones are walkable too (nothing drawn): each stone alone was an island
ford = np.zeros((H, W), bool)
for (ax, ay), (bx, by) in zip(stone_at, stone_at[1:]):
    for t in np.linspace(0, 1, 24):
        px, py = ax + (bx - ax) * t, ay + (by - ay) * t
        ford |= (xx - px) ** 2 + (yy - py) ** 2 <= 2.6 ** 2

# reeds on the banks
for _ in range(700):
    k = rng.integers(0, 1400)
    side = rng.choice([-1, 1])
    x0 = int(spx[k] + rng.normal(0, 2))
    y0 = int(spy[k] + side * (9 + rng.uniform(0.5, 3)))
    if not (2 <= x0 < W - 2 and 9 <= y0 < H) or water[y0, x0] or bridge[y0, x0] or rng.random() < 0.5:
        continue
    hgt = int(rng.integers(4, 9))
    lean = rng.choice([-1, 0, 1])
    for j in range(hgt):
        put(ground, x0 + (lean if j > hgt * 0.6 else 0), y0 - j, K if j < hgt - 2 else DG)
    if rng.random() < 0.5:
        put(ground, x0 + lean, y0 - hgt, hx('#5a4634'))

# ------------------------------------------------------------------ boulders up the slope, cliff at the top
rocks = np.zeros((H, W), bool)
def boulder(x_, y_, rx, ry):
    global rocks
    e = ((xx - x_) / rx) ** 2 + ((yy - y_) / ry) ** 2
    sh = (e <= 1.6) & (yy > y_) & (xx > x_ - 1)
    ground[sh] = DG
    m = e <= 1.0
    lit = (xx - x_) + (yy - y_) * 1.3 < -0.5
    ground[m] = MG
    ground[m & lit] = L1
    ground[m & lit & (e < 0.3)] = WH
    ground[m & (yy > y_ + ry * 0.4)] = DG
    cap = m & (yy < y_ - ry * 0.3) & (alt > 0.5) & (g < 0.8)
    ground[cap] = WH
    rocks |= e <= 1.1

for _ in range(70):
    x_, y_ = int(rng.integers(20, W - 20)), int(rng.integers(50, 580))
    if rng.random() > alt[y_, 0] * 1.2 + 0.1 or path_mask[y_, x_] or rocks[y_, x_]:
        continue
    boulder(x_, y_, rng.uniform(2.5, 6), rng.uniform(1.8, 3.6))
for x_ in range(-6, W + 12, 13):                         # the cliff foot: big snow-capped rocks, a wall of them
    boulder(x_ + rng.integers(-3, 4), int(18 + rng.integers(-4, 6)), rng.uniform(9, 14), rng.uniform(8, 12))
    boulder(x_ + 6, int(36 + rng.integers(-3, 5)), rng.uniform(5, 8), rng.uniform(3.5, 5))
cliff = yy < 30

# ------------------------------------------------------------------ objects (upright -> sprites)
objects = []        # dicts: name, make(ox, oy) -> object with .draw(img, t, L), box (x0, y0, x1, y1), foot, frames
def add(name, make, box, foot, frames=1):
    objects.append(dict(name=name, make=make, box=box, foot=foot, frames=frames))

fire = Fire(*S(42, 292), FRAMES, rng)
fire_blocked = np.zeros((H, W), bool)
fire.ground(ground, fire_blocked)
fx, fy = S(42, 292)

class FireSprite:
    def __init__(s, ox, oy):
        s.f = Fire(fx + ox, fy + oy, FRAMES, np.random.default_rng(5))
        s.f.stones, s.f.tex = fire.stones, fire.tex
        s.f.fnoise, s.f.fnoise2, s.f.ctex = fire.fnoise, fire.fnoise2, fire.ctex
        s.f.puffs, s.f.look, s.f.pnoise = fire.puffs, fire.look, fire.pnoise
    def draw(s, img, t, L):
        s.f.draw(img, t)
        s.f.smoke(img, t)
fsx, fsy = fire.cx, fire.cy
add('feuer', lambda ox, oy: FireSprite(ox, oy), (fx - 16, fy - 80, fx + 80, fy + 8), fy + 5, FRAMES)

def mk(cls, x, y, *a):
    return lambda ox, oy: cls(x + ox, y + oy, *a)

tx, ty = S(76, 300)
add('zelt', lambda ox, oy: Tent2(tx + ox, ty + oy, rng), (tx - 16, ty - 30, tx + 24, ty + 4), ty, FRAMES)
lx, ly = S(58, 232)
add('steinlaterne', lambda ox, oy: Lantern3(lx + ox, ly + oy, rng), (lx - 18, ly - 34, lx + 20, ly + 10), ly, FRAMES)
shx, shy = S(122, 124)
add('schrein', lambda ox, oy: ShrineB(shx + ox, shy + oy), (shx - 26, shy - 48, shx + 30, shy + 6), shy, FRAMES)
bnx, bny = S(147, 126)
add('banner', lambda ox, oy: Banner3(bnx + ox, bny + oy, 44, rng), (bnx - 4, bny - 48, bnx + 22, bny + 3), bny, FRAMES)
bx_, by_ = S(96, 246)
class BenchW:
    def __init__(s, x, y): s.b = extras.Bench(x, y)
    def draw(s, img, t, L): s.b.draw(img)
add('bank', lambda ox, oy: BenchW(bx_ + ox, by_ + oy), (bx_ - 14, by_ - 9, bx_ + 18, by_ + 5), by_, 1)
for k, (wx, wy) in enumerate((S(110, 247), S(138, 140))):
    add(f'holzlaterne{k}', (lambda wx=wx, wy=wy: (lambda ox, oy: extras.WoodLantern(wx + ox, wy + oy)))(),
        (wx - 10, wy - 22, wx + 12, wy + 6), wy, FRAMES)
# second bench + lantern at the end of the west and east paths: places to stop and look
add('bank_west', lambda ox, oy: BenchW(84 + ox, 984 + oy), (70, 975, 102, 989), 984, 1)
add('laterne_ost', lambda ox, oy: extras.WoodLantern(468 + ox, 852 + oy), (458, 830, 480, 858), 852, FRAMES)

ruin = Ruin(196, 330, 262, 372)
class RuinPart:
    def __init__(s, ox, oy, part, j0=None):
        s.r = Ruin(196 + ox, 330 + oy, 262 + ox, 372 + oy)
        s.part, s.oy, s.j0 = part, oy, j0
    def draw(s, img, t, L):
        r = s.r
        x0, y0, x1, y1 = r.x0, r.y0, r.x1, r.y1
        if s.part == 'back':
            wcx = (x0 + x1) // 2
            r.hwall(img, x0, x1, y0, 34, window=(wcx - 5, wcx + 5, y0 - 26, y0 - 6), gable=True)
        elif s.part == 'left':
            r.vwall(img, x0, y0 + 1, y1, 16, rows=range(s.j0 + s.oy, min(s.j0 + RSEG, 372) + s.oy))
        elif s.part == 'right':
            r.vwall(img, x1 - 3, y0 + 1, y1 - 8, 13, rows=range(s.j0 + s.oy, min(s.j0 + RSEG, 364) + s.oy))
        elif s.part == 'front':
            r.hwall(img, x0, x0 + 14, y1, 9)
            r.hwall(img, x1 - 12, x1, y1, 6)
            for k in range(10):
                a = np.pi * (0.5 + 0.5 * k / 9)
                i = int(round(x0 + 20 + 7 * np.cos(a)))
                j = int(round(y1 - 10 - 9 * np.sin(a)))
                for u in range(2):
                    put(img, i + u, j, r._stone(i + u, j, 0.62 - 0.05 * u, face=True))
add('ruine_hinten', lambda ox, oy: RuinPart(ox, oy, 'back'), (190, 290, 268, 336), 330, 1)
RSEG = 4                                                   # side walls run away from us: cut into short pieces,
for j0 in range(331, 372, RSEG):                           # each sorted by its own foot, so you can stand beside them
    add(f'ruine_links_{j0}', (lambda j0=j0: (lambda ox, oy: RuinPart(ox, oy, 'left', j0)))(),
        (190, j0 - 22, 204, min(j0 + RSEG, 372) + 2), min(j0 + RSEG, 372) - 1, 1)
for j0 in range(331, 364, RSEG):
    add(f'ruine_rechts_{j0}', (lambda j0=j0: (lambda ox, oy: RuinPart(ox, oy, 'right', j0)))(),
        (254, j0 - 20, 268, min(j0 + RSEG, 364) + 2), min(j0 + RSEG, 364) - 1, 1)
add('ruine_vorne', lambda ox, oy: RuinPart(ox, oy, 'front'), (190, 352, 268, 376), 372, 1)
class CottageW:
    def __init__(s, x, y): s.c = Cottage(x, y)
    def draw(s, img, t, L): s.c.draw(img)
add('huette', lambda ox, oy: CottageW(318 + ox, 486 + oy), (310, 430, 360, 492), 486, 1)
add('laterne_huette', lambda ox, oy: Lantern3(308 + ox, 504 + oy, rng), (290, 470, 328, 514), 504, FRAMES)

class PineW:
    def __init__(s, x, y, h, seed, snow): s.p, s.snow = Pine(x, y, h, seed), snow
    def draw(s, img, t, L):
        a = img.astype(float)
        hh, ww = a.shape[:2]
        G = np.random.default_rng(s.p.seed).random((hh, ww))
        G = np.where(G < s.snow, G, 1.0)                  # less snow down in the meadow
        CL = ndi.gaussian_filter(np.random.default_rng(s.p.seed + 1).random((hh, ww)), 0.65)
        CL = (CL - CL.min()) / (CL.max() - CL.min())
        s.p.draw(a, G, CL)
        img[:] = np.clip(a, 0, 255).astype(np.uint8)

def pine(x, y, h, seed):
    snow = 0.25 + 0.75 * float(np.clip((600 - y) / 450, 0, 1))
    add(f'tanne{len(objects)}', lambda ox, oy: PineW(x + ox, y + oy, h, seed, snow),
        (x - int(h * 0.45) - 3, y - h - 2, x + int(h * 0.62) + 3, y + int(h * 0.25) + 2), y, 1)

prng2 = np.random.default_rng(61)
for side in (0, 1):                                       # forest along both edges keeps you in the world
    y = 50
    while y < H + 30:
        x = (rng.integers(-6, 12) if side == 0 else W - rng.integers(-6, 12))
        h = int(prng2.integers(36, 48))
        pine(int(x), int(y), h, int(prng2.integers(0, 1e6)))
        y += int(prng2.integers(12, 22))
for (x, y, h) in [(60, 120, 34), (84, 104, 30), (40, 160, 36), (420, 130, 38), (446, 96, 30), (470, 210, 40),
                  (120, 268, 32), (380, 300, 34), (150, 60, 28), (330, 70, 26), (400, 420, 36), (120, 420, 34),
                  (96, 470, 30), (450, 520, 34), (70, 560, 32), (480, 600, 30), (60, 760, 34), (470, 760, 36),
                  (130, 860, 30), (440, 1000, 32)]:
    pine(x, y, h, int(prng2.integers(0, 1e6)))

# ------------------------------------------------------------------ blocked areas, flowers
blocked = water | sbank | path_mask | court | camp | fire_blocked | rocks | cliff | bridge
for ob in objects:
    x0, y0, x1, y1 = ob['box']
    blocked[max(0, ob['foot'] - 6):min(H, ob['foot'] + 2), max(0, x0 + 2):min(W, x1 - 2)] = True
ta = np.zeros((H, W), bool)
ta[TY:TY + 200, TX:TX + 200] = tree_lay[..., 3] > 0
blocked |= ndi.binary_dilation(ta, iterations=1)

# petals already lying in the grass, downwind of the crown (as in the wallpaper)
cc = np.array([TX + 106, TY + 120])
for _ in range(90):
    a = rng.normal(0.35, 0.7)
    r = abs(rng.normal(55, 22))
    px_ = int(cc[0] + r * np.cos(a))
    py_ = int(cc[1] + r * np.sin(a) * 0.8 + 20)
    if 0 <= px_ < W - 1 and 0 <= py_ < H and not blocked[py_, px_]:
        ground[py_, px_] = PK[3] if rng.random() < 0.6 else PK[4]

print('flowers ...', flush=True)
F = patches(H, W, flow, blocked, rng, 1300000)
heads = np.zeros((H, W, 4), np.uint8)
for (x, y, k, ph) in F:
    head = HEADS[k]
    h = len(head)
    for s_ in range(h, h + 2):                             # stems stay rooted in the ground layer
        for sx_ in (x + 1, x + 2):
            if 0 <= sx_ < W and y + s_ < H and not blocked[y + s_, sx_] and (sx_ + y + s_) % 2 == 0:
                ground[y + s_, sx_] = DG
    for j, row in enumerate(head):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            px_, py_ = x + i, y + j
            if 0 <= px_ < W and 0 <= py_ < H and not blocked[py_, px_]:
                heads[py_, px_, :3] = CMAP[ch]
                heads[py_, px_, 3] = 255
print('flowers', len(F), flush=True)

# ------------------------------------------------------------------ render the sprites
os.makedirs(os.path.join(OUT, 'sprites'), exist_ok=True)
sprites = []
for ob in objects:
    x0, y0, x1, y1 = [int(v) for v in ob['box']]
    x0, y0 = max(0, x0), max(0, y0)
    x1, y1 = min(W, x1), min(H, y1)
    base = ground[y0:y1, x0:x1].copy()
    o = ob['make'](-x0, -y0)
    strip = []
    for t in range(ob['frames']):
        im = base.copy()
        o.draw(im, t, FRAMES)
        diff = np.any(im != base, axis=2)
        rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        rgba[..., :3] = im
        rgba[..., 3] = diff * 255
        strip.append(rgba)
    if not any(s[..., 3].any() for s in strip):
        print('empty sprite', ob['name'])
        continue
    Image.fromarray(np.concatenate(strip, axis=1)).save(os.path.join(OUT, 'sprites', ob['name'] + '.png'))
    sprites.append(dict(name=ob['name'], x=x0, y=y0, w=x1 - x0, h=y1 - y0, foot=int(ob['foot']),
                        frames=ob['frames'], fps=FPS))
# the tree is a finished layer already
Image.fromarray(tree_lay).save(os.path.join(OUT, 'sprites', 'baum.png'))
sprites.append(dict(name='baum', x=TX, y=TY, w=200, h=200, foot=TY + 170, frames=1, fps=FPS))

# ------------------------------------------------------------------ walkable mask
walk = ~(water | rocks | cliff)
walk |= bridge | stones | ford
trunk = np.zeros((H, W), bool)
trunk[TY + 150:TY + 174, TX + 88:TX + 112] = True          # only the trunk blocks, you walk under the crown
walk &= ~trunk
for ob in objects:
    x0, y0, x1, y1 = ob['box']
    f = ob['foot']
    if ob['name'].startswith('tanne'):
        cx_ = (x0 + x1) // 2 - 2
        walk[f - 4:f + 2, cx_ - 4:cx_ + 5] = False
    elif ob['name'].startswith('ruine'):
        continue
    elif ob['name'] == 'huette':
        walk[436:488, 312:358] = False
    elif ob['name'] == 'feuer':
        walk &= ~(((xx - fsx) / 10) ** 2 + ((yy - fsy) / 5.5) ** 2 <= 1)
    elif ob['name'] in ('banner',):
        walk[f - 3:f + 2, x0 + 2:x0 + 7] = False
    else:
        walk[max(0, f - 6):f + 2, x0 + 3:x1 - 3] = False
r_ = ruin                                                  # ruin walls; the gap in the front lets you in
walk[r_.y0 - 4:r_.y0 + 1, r_.x0:r_.x1] = False
walk[r_.y0:r_.y1, r_.x0 - 1:r_.x0 + 4] = False                    # a little thicker than drawn: no slipping through
walk[r_.y0:r_.y1 - 8, r_.x1 - 4:r_.x1 + 1] = False
walk[r_.y1 - 2:r_.y1 + 1, r_.x0:r_.x0 + 14] = False
walk[r_.y1 - 2:r_.y1 + 1, r_.x1 - 12:r_.x1] = False
walk[:, :10] = False
walk[:, W - 10:] = False
walk[H - 4:, :] = False
walk[:44, :] = False

# ------------------------------------------------------------------ lights (world coordinates)
lights = [
    dict(x=fsx, y=fsy - 5, r=46, k=1.25, kind='fire'),
    dict(x=lx, y=ly - 15.5, r=30, k=0.70, kind='lantern'),
    dict(x=S(110.5, 236)[0], y=S(110.5, 236)[1], r=20, k=0.55, kind='wood'),
    dict(x=S(122, 116)[0], y=S(122, 116)[1], r=24, k=0.65, kind='candle'),
    dict(x=S(138.5, 129)[0], y=S(138.5, 129)[1], r=20, k=0.55, kind='wood'),
    dict(x=468.5, y=841, r=20, k=0.55, kind='wood'),
    dict(x=308, y=488.5, r=26, k=0.60, kind='lantern'),
    dict(x=327, y=477, r=18, k=0.40, kind='candle'),        # cottage window
]

# ------------------------------------------------------------------ mist noise (tileable)
def mist_tex(sig, seed, n=256):
    m = ndi.gaussian_filter(np.random.default_rng(seed).normal(0, 1, (n, n)), sig, mode='wrap')
    m = (m - m.mean()) / m.std()
    return np.clip(m / 6 + 0.5, 0, 1)                      # store n in [-3, 3]
Image.fromarray((mist_tex([14, 22], 97) * 255).astype(np.uint8)).save(os.path.join(OUT, 'mist1.png'))
Image.fromarray((mist_tex([6, 10], 98) * 255).astype(np.uint8)).save(os.path.join(OUT, 'mist2.png'))

Image.fromarray(ground).save(os.path.join(OUT, 'ground.png'))
Image.fromarray(heads).save(os.path.join(OUT, 'flowers.png'))
Image.fromarray((walk * 255).astype(np.uint8)).save(os.path.join(OUT, 'walk.png'))
walk.astype(np.uint8).tofile(os.path.join(OUT, 'walk.bin'))           # what the game reads: 1 byte per pixel
CELL = 2                                                                   # same as Pathing.CELL in the game
walk.reshape(H // CELL, CELL, W // CELL, CELL).all(axis=(1, 3)).astype(np.uint8).tofile(os.path.join(OUT, 'walk_cells.bin'))
start = dict(x=S(63, 270)[0], y=S(63, 270)[1])              # on the path between camp and tree

# ------------------------------------------------------------------ what the ground is made of (footsteps), 2-px cells
GRASS, EARTH, STONE, WOOD, SNOW, WET = 0, 1, 2, 3, 4, 5
mat = np.zeros((H, W), np.uint8)
mat[path_mask | camp | sbank] = EARTH
mat[snow] = SNOW
rin = np.zeros((H, W), bool)
rin[ruin.y0:ruin.y1, ruin.x0:ruin.x1] = True
mat[court | rocks | rin] = STONE
mat[stones | ford | sbank] = WET                                             # stepping stones, wet bank
mat[bridge] = WOOD
mat[::CELL, ::CELL].tofile(os.path.join(OUT, 'ground_mat.bin'))       # top-left pixel of each cell is enough

# places the sound and the small life live
brook = [dict(x=float(spx[k]), y=float(spy[k])) for k in range(0, 1400, 70) if 0 <= spx[k] < W]
srng = np.random.default_rng(5)
open_ = ndi.binary_erosion(walk & ~path_mask & ~water, iterations=8) & (yy > 120)
birds = []
for _ in range(4000):
    x_, y_ = int(srng.integers(20, W - 20)), int(srng.integers(60, H - 20))
    if len(birds) < 14 and open_[y_, x_] and all(np.hypot(x_ - b['x'], y_ - b['y']) > 110 for b in birds):
        birds.append(dict(x=x_, y=y_, snow=bool(snow[y_, x_])))
def on_stream(x_):
    k = int(np.argmin(np.abs(spx - x_)))
    return dict(x=float(x_), y=float(spy[k]))
wisps = [dict(x=496.0, y=820.0)]   # just one, in the east where the forest with the ritual site will be
with open(os.path.join(OUT, 'world.json'), 'w') as f:
    json.dump(dict(width=W, height=H, frames=FRAMES, fps=FPS, start=start, sprites=sprites,
                   brook=brook, birds=birds, wisps=wisps, fire=dict(x=float(fsx), y=float(fsy)),
                   lights=[{k: (float(v) if not isinstance(v, str) else v) for k, v in l.items()} for l in lights]),
              f, indent=1)
print('ok', len(sprites), 'sprites')
