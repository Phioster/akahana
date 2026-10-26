#!/usr/bin/env python3
"""Draft of zone 2 for the approval page, drawn below zone 1 on one canvas: the poppies thin out, wildflowers
come in, three young cherry trees, a stone bench, a stone lantern on the new cross path, and the meadow grows
into a field of tall grass you walk through (in the game its own layer; here one still moment).

    python3 tools/world/south/zone2_draft.py OUTDIR
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
sys.path.insert(0, HERE)
import field6  # noqa: E402
from field6 import patches, CMAP, DG  # noqa: E402
import extras  # noqa: E402
from objects2 import Lantern3, hx  # noqa: E402
import mood_map  # noqa: E402
import zone1_draft as z1  # noqa: E402
from zone1_draft import Fir, W  # noqa: E402
from objects_south import (Findling, Steinhaufen, Baumstumpf, Stamm, HohesGras, Voegel, Kirschbaum,  # noqa: E402
                           Kerzen, put)
import ground as south_ground  # noqa: E402
from fireflies import Swarm  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
Y0 = z1.CTX + z1.NEW                        # first row of zone 2 on the shared canvas
NEW = 400                                   # two chunk rows
GRASS_FROM, GRASS_FULL = -170, 320          # rows into zone 2 where the first stalks show (up in zone 1) and where it is a field
GRASS_MIST = 0.45                           # mist over the green grass this thick (1 = as everywhere)
EXT = 180                                   # zone-1 rows the grass reaches up into

GREEN = [hx(c) for c in ['#283126', '#3a4635', '#4f5d43', '#677552', '#838d63', '#a3a676']]   # as the trial
DRY = [hx(c) for c in ['#7c6c4a', '#9c8a62', '#b8a67c']]
# wildflowers, muted like the poppies: chamomile, cornflower, bellflower
CHAMO = [hx(c) for c in ['#b8b4a4', '#e6e2d2', '#d8b456']]
CORN = [hx(c) for c in ['#4a5a88', '#6a80b8', '#94a8dc']]
BELL = [hx(c) for c in ['#5c5288', '#7e72b0', '#a296d0']]


def fbm(H, W_, s, seed):
    n = ndi.gaussian_filter(np.random.default_rng(seed).normal(0, 1, (H, W_)), s)
    return n / n.std()


def grass_density():
    """0 .. 1 from EXT rows above zone 2 to its end: none above GRASS_FROM, a field below GRASS_FULL, a long
    uneven front between (single stalks first, so no hard edge on the whole map)."""
    yy = np.arange(-EXT, NEW)[:, None] + 40 * fbm(NEW + EXT, W, 24, 61) + 12 * fbm(NEW + EXT, W, 6, 62)
    u = np.clip((yy - GRASS_FROM) / (GRASS_FULL - GRASS_FROM), 0, 1)
    return u ** 1.8


def poppy_keep(y):
    """Share of poppies left at zone row y: all at the seam, about one in four by the grass."""
    return float(np.clip(1 - 0.8 * (y / 150) ** 1.3, 0.2, 1)) if y < 230 else 0.08


class Blade:
    """One stalk of the tall-grass field (still: the game moves them)."""
    def __init__(s, x, y, rng):
        s.x, s.y, s.h = x, y, int(rng.integers(6, 13))
        s.bend = (rng.normal(0.6, 0.5) + 0.6 * rng.random()) / rng.uniform(0.7, 1.3)
        s.dry, s.shade = rng.random() < 0.12, rng.uniform(-0.12, 0.12)

    def box(s):
        return (s.x - 1, s.y - s.h, s.x + 2, s.y)

    def draw(s, img, G):
        for k in range(s.h):
            v = k / max(s.h - 1, 1)
            x, y = int(round(s.x + s.bend * v ** 1.6)), s.y - k
            if s.dry and v > 0.6:
                c = DRY[min(2, int((v - 0.6) / 0.4 * 3))]
            else:
                c = GREEN[min(5, max(0, int(v * 5.2 + s.shade * 6 + (0.6 if s.bend < 0 else 0))))]
            put(img, x, y, c)


class Wildflower:
    def __init__(s, x, y, kind, rng, tall=0):
        s.x, s.y, s.kind, s.v, s.tall = x, y, kind, rng.random(), tall   # tall: a long stem up out of the grass

    def box(s):
        return (s.x - 1, s.y - 3 - s.tall, s.x + 2, s.y)

    def draw(s, img, G):
        x, y = s.x, s.y
        for k in range(s.tall):
            put(img, x + (k > s.tall // 2), y - k, GREEN[2 + (k > s.tall // 2)])
        x, y = x + (s.tall > 1), y - s.tall
        put(img, x, y, DG)                                     # stem
        if s.kind == 0:                                        # chamomile: white ring, yellow eye
            for i, j in ((0, -3), (-1, -2), (1, -2), (0, -1), (-1, -3), (1, -1)):
                put(img, x + i, y + j, CHAMO[1] if (i, j) not in ((1, -2), (1, -1)) else CHAMO[0])
            put(img, x, y - 2, CHAMO[2])
        elif s.kind == 1:                                      # cornflower: a ragged blue star
            put(img, x - 1, y - 2, CORN[1])
            put(img, x + 1, y - 2, CORN[0])
            put(img, x, y - 1, CORN[1])
            put(img, x, y - 2, CORN[2] if s.v > 0.4 else CORN[1])
        else:                                                  # bellflower: a nodding bell on a bent stem
            put(img, x, y - 1, DG)
            put(img, x + 1, y - 2, DG)
            put(img, x + 1, y - 1, BELL[1])
            put(img, x + 2, y - 1, BELL[0])
            put(img, x + 1, y, BELL[2] if s.v > 0.5 else BELL[1])


class Bank:
    """extras.Bench with the box()/draw(img, G) of the south's things."""
    def __init__(s, x, y):
        s.b, s.x, s.y = extras.Bench(x, y), x, y

    def box(s):
        return (s.x - 12, s.y - 7, s.x + 13, s.y + 4)

    def draw(s, img, G):
        s.b.draw(img)


class Steinlaterne:
    """The stone lantern as the game's sprite has it (gen_world draws Lantern3 on its own small canvas,
    glow and light pool included)."""
    def __init__(s, x, y):
        s.x, s.y = x, y

    def box(s):
        return (s.x - 18, s.y - 34, s.x + 20, s.y + 10)

    def lights(s):
        return [{'x': s.x + 0.5, 'y': s.y - 15.0, 'r': 28.0, 'k': 0.65, 'kind': 'lantern'}]

    def draw(s, img, G):
        x0, y0, x1, y1 = s.box()
        Lantern3(s.x - x0, s.y - y0, None).draw(img[y0:y1, x0:x1], 0.0, 8.0)


def render(w, seed=12, raw=False):
    base = z1.render('a', w, raw=True)[0]                      # zone 1 in full, its layers in z1.STASH
    rng = np.random.default_rng(seed)
    H = Y0 + NEW
    img = np.zeros((H, W, 3))
    img[:Y0] = base
    g1, h1 = z1.STASH['ground'], z1.STASH['heads']
    # zone 1's field stopped at its bottom row and cut the last blossoms in half: lift those off again
    lab, n = ndi.label(h1[..., 3] > 0, structure=np.ones((3, 3)))
    cut = np.isin(lab, np.unique(lab[-1][lab[-1] > 0]))
    same = (np.abs(img[:Y0] - h1[..., :3]).sum(-1) < 1) & cut
    img[:Y0][same] = g1[same]

    fog = np.clip(0.70 + 0.10 * fbm(NEW, W, 18, 204), 0, 1)
    flow = np.clip(0.22 + 0.10 * fbm(NEW, W, 10, 205), 0, 1)
    tone = south_ground.continued_tone(south_ground.tone_of(g1), south_ground.fresh_tone(NEW, W, fog, flow, rng))
    ground = south_ground.ground_from_tone(tone, fog, flow, rng)
    dens_all = grass_density()
    dens = dens_all[EXT:]
    t = (np.arange(NEW) / NEW)[:, None, None]
    ground *= 1 - (0.4 * t + 0.6 * dens[..., None]) * np.array([0.12, 0.0, 0.14])   # green comes in with the grass
    ground *= 1 - 0.38 * dens[..., None]                      # dark between the stalks
    up = img[Y0 - EXT:Y0]
    bare = np.abs(up - g1[Y0 - EXT:]).sum(-1) < 1               # zone 1's ground where it shows: the green starts there
    d1 = dens_all[:EXT][..., None]
    up[bare] = (up * (1 - 0.6 * d1 * np.array([0.12, 0.0, 0.14])) * (1 - 0.38 * d1))[bare]
    free1 = bare | (np.abs(up - h1[Y0 - EXT:, :, :3]).sum(-1) < 1)  # ground or a poppy, no zone-1 thing
    img[Y0:] = ground
    STASH.update(ground=ground.copy())

    # the two trails run on south; between them the new cross path with the lantern at its fork
    trail_a = [(322, 680), (360, 760), (350, 840), (336, 930), (318, 1040), (300, H + 12)]
    trail_b = [(775, 700), (790, 760), (762, 860), (722, 960), (684, 1060), (652, H + 12)]
    cross = [(340, 912), (450, 926), (560, 936), (650, 944), (735, 958)]
    south = [(560, 936), (548, 1010), (532, 1090), (520, H + 12)]   # down to the spring in zone 3
    prng = np.random.default_rng(93)
    path = np.zeros((H, W), bool)
    for pts in (trail_a, trail_b, cross, south):
        pm, pc, pd_, pw_ = extras.path_mask(H, W, pts, prng)
        path |= pm                                             # (zone 1's part too: no grass on it)
        pm[:Y0 - 6] = False                                    # zone 1 drew its own part already
        extras.draw_path(img, pm, pc, pd_, pw_, prng)

    Y = lambda y: Y0 + y                                       # zone rows to canvas rows
    BANK = Bank(222, Y(130))
    TREES = [(200, Y(118)), (566, Y(246)), (826, Y(322))]
    things = [Kirschbaum(200, Y(118), seed=23, trunk=11.0), Kirschbaum(566, Y(246), seed=41, trunk=10.0, depth=4),
              Kirschbaum(826, Y(322), seed=57, trunk=12.0),
              BANK, Kerzen([(217, Y(123)), (220, Y(122))], 11, BANK),
              Steinlaterne(362, Y(146)),
              Findling(92, Y(300), 8, 13), Findling(612, Y(62), 6, 14), Steinhaufen(420, Y(330)),
              Baumstumpf(150, Y(240), 5), Stamm(480, Y(296), 512, Y(306)), Baumstumpf(872, Y(160), 6),
              Voegel(130, Y(200), 7), Voegel(700, Y(330), 8), Voegel(470, Y(92), 9)]
    things += [HohesGras(x, Y(y), int(rng.integers(8, 14)), int(rng.integers(0, 999))) for x, y in
               [(60, 120), (300, 60), (680, 120), (150, 30), (470, 210), (760, 200), (250, 190), (560, 160)]]
    firs = []
    for y in range(Y0 + 10, H + 30, 13):                       # the world edges keep their fir rows
        for x in (int(rng.integers(-6, 12)), W - int(rng.integers(-6, 12))):
            firs.append(Fir(x, y + int(rng.integers(-3, 4)), int(rng.integers(36, 48)), int(rng.integers(0, 10 ** 6))))
    firs += [f_ for f_ in z1.STASH['firs'] if f_.p.y > Y0 - 50]  # zone 1's lowest firs, whole this time

    blocked = path.copy()
    for t_ in things:
        x0, y0, x1, y1 = t_.box()
        if isinstance(t_, (Stamm, Steinhaufen, Findling, Baumstumpf, Bank)):
            x0, y0, x1, y1 = x0 - 2, y0 - 2, x1 + 2, y1 + 2      # lying things: nothing grows under them
        else:
            y0 = y1 - 8
        blocked[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
    for f_ in firs:
        blocked[max(0, f_.p.y - 6):max(0, f_.p.y + 2), max(0, f_.p.x - 8):max(0, f_.p.x + 9)] = True
    blocked[:, :14] = blocked[:, W - 14:] = True

    # poppies: the same field running on, thinning out row by row
    top = Y0 - 8
    fl = np.zeros((H - top, W))
    fl[8:] = flow
    fl[:8] = flow[:1]
    free = blocked[top:].copy()
    bare_top = bare[-8:]                                       # zone 1's last rows: a new head only on its bare ground
    for (x, y, k, ph) in patches(H - top, W, fl, free, rng, 420000):
        zy = y + top - Y0
        if rng.random() > poppy_keep(max(zy, 0)) or (zy > 0 and dens[min(zy + 4, NEW - 1), x + 2] > 0.6):
            continue
        head = field6.HEADS[k]
        if zy < 0 and not all(bare_top[y + j, x + i] for j, row in enumerate(head) for i, ch in enumerate(row)
                              if ch != '.' and y + j < 8):
            continue
        for s_ in range(len(head), len(head) + 2):
            for sx_ in (x + 1, x + 2):
                yy_ = y + top + s_
                if yy_ < H and (sx_ + yy_) % 2 == 0 and not blocked[yy_, sx_]:
                    img[yy_, sx_] = DG
        for j, row in enumerate(head):
            for i, ch in enumerate(row):
                if ch != '.' and y + top + j < H:
                    img[y + top + j, x + i] = CMAP[ch]

    # wildflowers: a few at first, then more, mostly in loose meadows of their own
    meadows = [(120, 90, 40), (430, 250, 50), (700, 110, 35), (240, 330, 45), (600, 380, 40), (850, 250, 35),
               (520, 60, 30), (90, 220, 30)]
    flowers = []
    for _ in range(9000):
        x, y = int(rng.integers(16, W - 16)), int(rng.integers(4, NEW - 2))
        near = max(np.clip(1 - np.hypot(x - mx, (y - my) * 1.3) / r, 0, 1) for mx, my, r in meadows)
        p = 0.05 + 0.15 * y / NEW + 0.7 * near
        if dens[y, x] > 0.7:
            p *= 0.35                                          # in the grass: fewer, on long stems
        if rng.random() > p or blocked[Y(y) - 3:Y(y) + 1, x - 1:x + 3].any():
            continue
        flowers.append(Wildflower(x, Y(y), int(rng.choice(3, p=[0.45, 0.33, 0.22])), rng,
                                  int(dens[y, x] * rng.integers(7, 11))))
        blocked[Y(y) - 3:Y(y) + 1, x - 1:x + 2] = True

    # the tall-grass field
    blades = []
    for _ in range(int(W * (NEW + EXT) / 8.5)):
        x, y = rng.uniform(14, W - 14), rng.uniform(-EXT, NEW + 8)
        yi = min(int(y), NEW - 1)
        if rng.random() > dens_all[yi + EXT, int(x)] or path[min(Y(int(y)), H - 1), int(x)]:
            continue
        if y < 0 and not free1[int(y) + EXT - 13:int(y) + EXT + 1, int(x) - 1:int(x) + 3].all():
            continue                                           # up in zone 1: only on open meadow
        foot = min(np.hypot(x - tx, (Y(y) - ty) * 1.6) for tx, ty in TREES)
        if foot < 7 or (foot < 13 and rng.random() < 0.6):     # trodden round the trunks: the trees stand on the ground
            continue
        if blocked[min(Y(int(y)), H - 1), int(x)] and rng.random() < 0.85:
            continue
        blades.append(Blade(x, Y(int(y)), rng))

    G = np.random.default_rng(3).random((H, W))
    for t_ in sorted(things + flowers + blades + firs,
                     key=lambda t_: t_.p.y if isinstance(t_, Fir) else (getattr(t_, 'order', None) or t_.box()[3])):
        if isinstance(t_, Fir):
            t_.draw(img)
        else:
            t_.draw(img, G)

    lights = [dict(l, y=l['y'] - (z1.OLD_H - z1.CTX)) for l in w['lights']]
    lit = z1.LIT + [l for t_ in things if hasattr(t_, 'lights') for l in t_.lights()]
    swarms = z1.SWARMS + SWARMS
    if raw:
        return np.clip(img, 0, 255), lights + lit, swarms
    out = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=lights + lit + [l for s_ in swarms for l in s_.lights(2.0)],
                                                   wisps=[]), 2.0, grass_mist=GRASS_MIST).astype(float)
    for s_ in swarms:
        s_.draw(out, 2.0)
    return out.astype(np.uint8)


STASH = {}                                   # zone 2's ground of the last render, for the zone below
# fireflies by the bench, the trees, a boulder and over the grass
SWARMS = [Swarm(250, Y0 + 180, 10, 11), Swarm(600, Y0 + 270, 9, 12), Swarm(800, Y0 + 350, 9, 13),
          Swarm(120, Y0 + 330, 8, 14), Swarm(470, Y0 + 90, 8, 15)]


if __name__ == '__main__':
    out = sys.argv[1]
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    im = Image.fromarray(render(w))
    im.save(os.path.join(out, 'zone12.png'))
    print('ok', im.size, flush=True)
