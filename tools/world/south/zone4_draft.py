#!/usr/bin/env python3
"""Draft of zone 4 for the approval page, drawn below zones 1-3 on one canvas: the wide lake grown wild
(zone4_layout, the approved plan), its reed belt and reed islands, water lilies, the island with its tree,
small pools round about, the jetty with lantern and boat, the fisher's hut half in the reeds with its landing,
a bench under a tree by the backwater, greener broadleaf trees, the round path far out at the edges; and as the
world's southern edge a sea of reeds turning to marsh and open water that fades into thick mist.

    python3 tools/world/south/zone4_draft.py OUTDIR
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
import extras  # noqa: E402
import mood_map  # noqa: E402
import zone2_draft as z2  # noqa: E402
import zone3_draft as z3  # noqa: E402
import zone4_layout as L  # noqa: E402
from zone1_draft import Fir, W  # noqa: E402
from zone2_draft import Blade, fbm  # noqa: E402
from objects_south import Findling  # noqa: E402
import objects_water as ow  # noqa: E402
import objects_lake as ol  # noqa: E402
import ground as south_ground  # noqa: E402
from fireflies import Swarm  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
Y4 = z3.Y3 + z3.NEW                         # first row of zone 4 on the shared canvas
NEW = 800                                   # four chunk rows
MIST = np.array([180.0, 181.0, 180.0])      # the mist over the open water at the world's edge


def render(w, seed=31, raw=False):
    base, lights, swarms, band3 = z3.render(w, raw=True)
    rng = np.random.default_rng(seed)
    H = Y4 + NEW
    img = np.zeros((H, W, 3))
    img[:Y4] = base
    Y = lambda y: Y4 + int(round(y))
    m = L.masks()
    yy, xx = np.mgrid[0:NEW, 0:W]

    # ground: the grass field's floor going on from zone 3
    fog = np.clip(0.70 + 0.10 * fbm(NEW, W, 18, 404), 0, 1)
    flow = np.clip(0.22 + 0.10 * fbm(NEW, W, 10, 405), 0, 1)
    tone = south_ground.continued_tone(south_ground.tone_of(z3.STASH['ground']),
                                       south_ground.fresh_tone(NEW, W, fog, flow, rng))
    ground = south_ground.ground_from_tone(tone, fog, flow, rng) * (1 - np.array([0.12, 0.0, 0.14])) * 0.62

    # the world's southern edge: reeds ever denser, then marsh, then open water fading into mist
    edge = L.edge(np.arange(W))[None, :] + 4 * fbm(NEW, W, 6, 406)
    sea_reeds = yy > edge
    marsh = (yy > edge + 30 + 8 * fbm(NEW, W, 8, 407)) & (fbm(NEW, W, 4, 408) > -0.3)
    open_w = yy > edge + 52 + 6 * np.sin(xx / 23.0)
    water = m['lake'] | m['puddles'] | marsh | open_w
    shallow = (m['shallow'] | m['puddles'] | (marsh & ~open_w)) & ~(m['reed_isles'])
    water &= ~m['island']
    damp = ndi.distance_transform_edt(~water) < 8
    ground[damp] *= 0.85
    img[Y4:] = ground

    # brooks from zone 3 running on into the lake
    b3, _, _, _ = z3.layout()
    tails = []
    for k, (x1, y1) in (('A', (418, 150)), ('B', (505, 150))):
        c, w0, w1 = b3[k]
        tail = [(x, y - z3.NEW) for x, y in c[::40] if y > z3.NEW - 70]
        tails.append((z3.curve(tail + [(x1, y1)], 300), w1, w1 + 2))
    brooks = ow.Brooks(tails, NEW, W, y0=0)

    # paths: one line each from zone 2 on; the two short spurs
    path = np.zeros((H, W), bool)
    prng = np.random.default_rng(97)
    west = z3.curve(z2.TRAIL_A, 1200)
    spur0 = tuple(west[np.hypot(*(west - (190, Y(655))).T).argmin()])
    line = lambda p0, p1: [tuple(np.add(p0, np.subtract(p1, p0) * t)) for t in (0, 0.33, 0.67, 1)]   # path_mask needs 4 points
    east = z3.curve(z2.TRAIL_B, 1200)
    spur1 = tuple(east[np.hypot(*(east - (803, Y(518))).T).argmin()])
    routes = [z2.TRAIL_A, z2.TRAIL_B, z2.TRAIL_S, line(spur0, (190, Y(655))), line(spur1, (803, Y(518)))]
    for pts in routes:
        pm, pc, pd_, pw_ = extras.path_mask(H, W, pts, prng)
        pm[:Y4 - 4] = False
        pc[:Y4 - 4] = False
        extras.draw_path(img, pm, pc, pd_, pw_, prng)
        path |= pm

    brooks.y0 = Y4
    brooks.draw(img, rng)
    ol.paint_lake(img, Y4, water, shallow, rng)                  # the lake over the brooks' ends
    isl = np.zeros((H, W), bool)
    isl[Y4:] = m['island']
    img[isl] = ground[m['island']]

    # the fisher's hut on the east shore, half in the reeds, its landing running across them into the water
    hy_ = 512
    xl_ = int(np.nonzero(m['lake'][hy_, :W - 40])[0].max())
    xr_ = xl_ + int(np.argmax(~m['reeds'][hy_, xl_ + 1:])) + 1
    hx_ = xr_
    # the jetty: from the reeds out into the lake at the end of the middle path
    col = m['lake'][:, 471]
    shore = int(np.argmax(col))
    things = [ol.Steg(471, Y(shore - 6), Y(shore + 44)), ol.Boot(452, Y(shore + 22)),
              z3.Holzlaterne(460, Y(shore - 8)),
              ol.Huette(hx_ + 17, Y(hy_ + 6)), ol.Steg(Y(hy_), xl_ - 12, xr_ + 2, width=7, across=True),
              z2.Bank(195, Y(652)),
              ol.Laubbaum(470, Y(388), seed=11, size=0.9)]
    for k, (x, y) in enumerate([(170, 642), (85, 250), (820, 120), (845, 620), (640, 712), (300, 715),
                                (60, 640), (800, 420), (100, 420), (760, 200), (380, 640), (560, 100)]):
        near_path = path[max(0, Y(y) - 6):Y(y) + 4, max(0, x - 8):x + 9].any()
        if not (m['lake'] | m['reeds'] | sea_reeds)[min(y, NEW - 1), x] and not near_path:
            things.append(ol.Laubbaum(x, Y(y), seed=20 + k, size=rng.uniform(0.9, 1.25)))
    for k, (x, y) in enumerate([(330, 240), (352, 262), (600, 430), (585, 455), (410, 520), (620, 190), (180, 400),
                                (760, 380)]):
        if m['lake'][y, x] and not m['shallow'][y, x]:
            things.append(ol.Seerosen(x, Y(y), int(rng.integers(5, 9)), 40 + k))
    things += [Findling(120, Y(150), 7, 41), Findling(820, Y(300), 6, 42), Findling(330, Y(660), 8, 43)]

    # reeds: the belt round the lake, the reed islands, rims of the pools, and the reed sea at the edge
    reed_area = (m['reeds'] | (m['lake'] & m['reed_isles']) | (ndi.binary_dilation(m['puddles'], iterations=2) &
                 ~m['puddles']) | (sea_reeds & ~open_w)) & ~ndi.binary_dilation(path[Y4:], iterations=3)
    for t_ in things:
        if isinstance(t_, ol.Steg):                              # the jetties stay clear of reeds
            x0, y0, x1, y1 = t_.box()
            reed_area[max(0, y0 - Y4 - 4):max(0, y1 - Y4 + 15), max(0, x0 - 4):x1 + 4] = False   # stalks grow up 15 px
    ys, xs = np.nonzero(reed_area)
    pick = rng.random(len(ys)) < np.where(sea_reeds[ys, xs], 1 / 9, 1 / 16)
    for y, x in zip(ys[pick], xs[pick]):
        if rng.random() < 0.78:
            things.append(ow.Schilf(int(x), Y(y), int(rng.integers(6, 12)), int(rng.integers(0, 10 ** 6))))
        else:
            things.append(ow.Rohrkolben(int(x), Y(y), int(rng.integers(3, 6)), int(rng.integers(0, 10 ** 6))))
    for (x, y) in [(100, 160), (690, 610), (380, 600), (830, 300), (220, 580), (40, 450), (870, 560)]:
        things.append(ow.Farn(x, Y(y), int(rng.integers(0, 999)), 7))

    firs = []
    for y in range(Y4 + 4, Y(L.edge(0)), 13):                   # the side fir rows end where the reed sea begins
        for x in (int(rng.integers(-6, 12)), W - int(rng.integers(-6, 12))):
            firs.append(Fir(x, y + int(rng.integers(-3, 4)), int(rng.integers(36, 48)), int(rng.integers(0, 10 ** 6))))

    # the tall grass on all the dry land
    keep_off = np.zeros((H, W), bool)
    keep_off[Y4:] = ndi.binary_dilation(water | m['reeds'] | sea_reeds, iterations=3) | brooks.mask
    keep_off |= ndi.binary_dilation(path, iterations=2)
    low = np.zeros((H, W), bool)
    for t_ in things:
        x0, y0, x1, y1 = t_.box()
        if isinstance(t_, (ow.Schilf, ow.Rohrkolben, ow.Farn, ol.Seerosen)):
            continue
        if isinstance(t_, ol.Laubbaum):
            x0, y0, x1, y1 = t_.x - 6, t_.y - 4, t_.x + 7, t_.y + 3
        keep_off[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
        if isinstance(t_, (ol.Huette, z2.Bank, Findling, ol.Steg)):
            low[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
    below = low.copy()
    for k in range(1, 13):
        below[k:] |= low[:-k]
    keep_off |= below & ~path
    keep_off[Y4:][m['island']] = True
    dens = np.clip(0.75 + 0.32 * fbm(H, W, 16, 409), 0.35, 1)
    blades = []
    for _ in range(int(W * NEW / 8.5)):
        x, y = rng.uniform(14, W - 14), rng.uniform(0, NEW - 1)
        if keep_off[Y(y), int(x)] or rng.random() > dens[Y(y), int(x)]:
            continue
        blades.append(Blade(x, Y(y), rng))
    for _ in range(1600):
        x, y = int(rng.integers(16, W - 16)), int(rng.integers(2, NEW - 2))
        if keep_off[Y(y), x] or rng.random() > 1.2 - dens[Y(y), x]:
            continue
        things.append(z2.Wildflower(x, Y(y), int(rng.choice(3, p=[0.45, 0.33, 0.22])), rng, int(rng.integers(6, 10))))
    island_isl = np.argwhere(m['island'])                        # a few short stalks on the island
    for y, x in island_isl[rng.random(len(island_isl)) < 0.05]:
        if np.hypot(x - 470, (y - 388) * 2) > 8:
            blades.append(Blade(float(x), Y(y), rng))

    G = np.random.default_rng(3).random((H, W))
    for t_ in sorted(things + blades + firs,
                     key=lambda t_: t_.p.y if isinstance(t_, Fir) else (getattr(t_, 'order', None) or t_.box()[3])):
        if isinstance(t_, Fir):
            t_.draw(img)
        else:
            t_.draw(img, G)

    lit = lights + [l for t_ in things if hasattr(t_, 'lights') for l in t_.lights()]
    sw = swarms + SWARMS
    band = np.zeros((H, W))
    band[:Y4] = band3
    band[Y4:] = np.clip(ndi.gaussian_filter((m['lake'] | brooks.mask).astype(float), 4) * 1.3, 0, 1)
    edge_fog = np.zeros(H)
    edge_fog[Y4:] = np.clip((np.arange(NEW) - 690) / 110.0, 0, 1) ** 1.4 * 0.88
    calm = np.zeros((H, W))
    calm[Y4:] = ndi.gaussian_filter(m['lake'].astype(float), 6)
    if raw:
        return np.clip(img, 0, 255), lit, sw, band, edge_fog, calm
    out = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=lit + [l for s_ in sw for l in s_.lights(2.0)], wisps=[]),
                        2.0, grass_mist=z2.GRASS_MIST, water_band=band, calm=calm).astype(float)
    for s_ in sw:
        s_.draw(out, 2.0)
    out = out * (1 - edge_fog[:, None, None]) + MIST * edge_fog[:, None, None]   # the world fades into mist
    return np.clip(out, 0, 255).astype(np.uint8)


# fireflies over the lake shore, the reeds and the island
SWARMS = [Swarm(330, Y4 + 330, 9, 31), Swarm(600, Y4 + 520, 9, 32), Swarm(140, Y4 + 450, 8, 33),
          Swarm(720, Y4 + 300, 8, 34), Swarm(450, Y4 + 690, 10, 35), Swarm(780, Y4 + 650, 8, 36),
          Swarm(470, Y4 + 372, 7, 37)]


if __name__ == '__main__':
    out = sys.argv[1]
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    im = render(w)
    Image.fromarray(im).save(os.path.join(out, 'zone1234.png'))
    print('ok', im.shape, flush=True)
