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
    # the sides likewise: past zone 3's firs the edges turn to reeds and water in the mist, not snowy woods
    side = np.minimum(xx, W - 1 - xx) - 4 * fbm(NEW, W, 7, 410)
    grow = np.clip((yy - 20) / 90.0, 0, 1)
    sea_reeds = (yy > edge) | (side < 26 * grow)
    marsh = ((yy > edge + 30 + 8 * fbm(NEW, W, 8, 407)) & (fbm(NEW, W, 4, 408) > -0.3)) | (side < 15 * grow)
    open_w = (yy > edge + 52 + 6 * np.sin(xx / 23.0)) | (side < 9 * grow)
    water = m['lake'] | m['puddles'] | marsh | open_w
    shallow = (m['shallow'] | m['puddles'] | (marsh & ~open_w)) & ~(m['reed_isles'])
    water &= ~m['island']
    jx = 578                                                     # the jetty's bank: a firm tongue of land under its
    shore = int(np.argmax(m['lake'][:, jx]))                     # landward half, so no water shows round it
    tongue = (((xx - jx) / 9.0) ** 2 + ((yy - shore + 8) / 14.0) ** 2 < 1) & (yy < shore + 2)
    water &= ~tongue
    shallow &= ~tongue
    damp = ndi.distance_transform_edt(~(water & ~m['puddles'])) < 8   # pools leave the grass round them as it is
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

    # a few puddles right on the paths, to splash through
    ppud = np.zeros((NEW, W), bool)
    for pts in (z2.TRAIL_A, z2.TRAIL_B):
        c = z3.curve(pts, 4000)
        c = c[c[:, 1] > Y4 + 30]
        px_, py_ = c[int(rng.uniform(0.3, 0.8) * (len(c) - 1))]   # one each, where the ground dips
        ppud |= L.organic_pool(int(px_), int(py_ - Y4), rng.uniform(6, 8), rng, (NEW, W))
    plab0, _ = ndi.label(m['puddles'])                          # pools the paths run into by chance are gone
    onpath = np.unique(plab0[ndi.binary_dilation(path[Y4:], iterations=3) & (plab0 > 0)])
    gone0 = np.isin(plab0, onpath[onpath > 0])
    water &= ~(gone0 & ~m['lake'])
    shallow &= ~gone0
    pud = (m['puddles'] & ~gone0) | ppud
    water |= ppud
    shallow |= ppud
    plab, pn_ = ndi.label(pud)                                   # no pools sitting in a brook's bed
    inbed = np.unique(plab[ndi.binary_dilation(brooks.mask, iterations=4) & (plab > 0)])
    gone = np.isin(plab, inbed[inbed > 0])
    pud &= ~gone
    water &= ~(gone & ~m['lake'])

    brooks.y0 = Y4
    brooks.draw(img, rng)
    with_brooks = img[Y4:].copy()
    ol.paint_lake(img, Y4, water, shallow, rng, rimless=pud)     # the lake over the brooks' ends
    # the mouths: no mud lip across the brook, its banks open out, its paler water runs on into the lake
    bm = brooks.mask
    img[Y4:][bm & ~m['lake']] = with_brooks[bm & ~m['lake']]      # the lake's mud rim does not cross the brook
    near = ndi.distance_transform_edt(~m['lake']) < 12           # the last 12 px before the lake
    lip = ndi.binary_dilation(bm, iterations=3) & ~bm & near & ~m['lake']
    lipw = lip & (rng.random((NEW, W)) < 0.7)                    # banks there: wet, water seeping through
    img[Y4:][lipw] = np.array(ow.WATER)[rng.integers(2, 4, (NEW, W))][lipw]
    fan = ndi.gaussian_filter(bm.astype(float), 4) * m['lake']   # a soft plume, no outline
    fade = np.clip(1 - m['dist_in'] / 16.0, 0, 1) * np.clip(fan * 2.5, 0, 1)
    take = rng.random((NEW, W)) < fade * 0.8
    img[Y4:][take] = np.array(ow.WATER)[rng.integers(2, 4, (NEW, W))][take]
    sub_ = img[Y4:]                                              # puddles: light, the evening sky in them
    pn = rng.random((NEW, W))
    sub_[pud] = ow.WATER[3]
    sub_[pud & (pn > 0.82)] = ow.WATER[4]
    rim = ndi.binary_dilation(pud, iterations=1) & ~pud & ~m['lake'] & (rng.random((NEW, W)) < 0.5)
    sub_[rim] = sub_[rim] * 0.92                                  # barely wet at the edge, no drawn ring
    isl = np.zeros((H, W), bool)
    isl[Y4:] = m['island']
    img[isl] = ground[m['island']]

    # the fisher's hut on the east shore, half in the reeds, its landing running across them into the water
    hy_ = 512
    xl_ = int(np.nonzero(m['lake'][hy_, :W - 40])[0].max())
    xr_ = xl_ + int(np.argmax(~m['reeds'][hy_, xl_ + 1:])) + 1
    hx_ = xr_
    # the jetty: from the reeds out into the lake at the end of the middle path
    # the jetty sits east of the brook mouths, the path comes to it over a bridge (jx, shore set above)
    things = [ol.Steg(jx, Y(shore - 20), Y(shore + 30), dry=Y(shore)),   # half on the bank, half over the water
               ol.Boot(jx - 19, Y(shore + 20)),
              z3.Holzlaterne(jx - 12, Y(shore - 21)),
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
    sc = z3.curve(z2.TRAIL_S, 3000)                              # the bridge where the middle path meets the brook
    sc = sc[sc[:, 1] > Y4] - (0, Y4)
    bc = tails[1][0]
    dd = np.hypot(sc[:, None, 0] - bc[None, :, 0], sc[:, None, 1] - bc[None, :, 1])
    i, j = np.unravel_index(dd.argmin(), dd.shape)
    tg = sc[min(i + 4, len(sc) - 1)] - sc[max(i - 4, 0)]
    things.append(ow.Bruecke(int(bc[j, 0]), Y(bc[j, 1]), float(np.arctan2(tg[1], tg[0])), tails[1][1] + 1))
    # the lake less empty: more lilies, rocks breaking the surface, a drifting branch, ducks
    deep = m['lake'] & (m['dist_in'] > 14) & ~ndi.binary_dilation(m['island'] | m['reed_isles'], iterations=12)
    deep[:shore + 60, jx - 30:jx + 30] = False
    spots = np.argwhere(deep)
    pick = spots[rng.choice(len(spots), 18, replace=False)]
    for k, (y, x) in enumerate(pick[:10]):
        things.append(ol.Seerosen(int(x), Y(y), int(rng.integers(4, 9)), 60 + k))
    for k, (y, x) in enumerate(pick[10:14]):
        things.append(ol.WasserStein(int(x), Y(y), rng.uniform(3, 5), 70 + k))
    y, x = pick[14]
    things.append(ol.Treibholz(int(x), Y(y), int(rng.integers(18, 26)), rng.uniform(-0.6, 0.6), 80))
    for k, (y, x) in enumerate(pick[15:17]):
        things.append(ol.Enten(int(x), Y(y), int(rng.integers(2, 4)), 90 + k))

    # reeds: the belt round the lake, the reed islands, rims of the pools, and the reed sea at the edge
    lab, n = ndi.label(m['puddles'])                             # only the bigger pools get a reed rim
    big = np.isin(lab, [k + 1 for k, a in enumerate(ndi.sum(m['puddles'], lab, range(1, n + 1))) if a > 260])
    reed_area = (m['reeds'] | (m['lake'] & m['reed_isles']) | (ndi.binary_dilation(big, iterations=2) &
                 ~m['puddles']) | (sea_reeds & ~open_w)) & ~ndi.binary_dilation(path[Y4:], iterations=3)
    reed_area &= ~ndi.binary_dilation(brooks.mask, iterations=1)   # the brooks run open into the lake
    reed_area &= ~pud
    dshadow = ndi.binary_dilation(m['ditch'], iterations=2)      # the ditch to the backwater stays open: nothing
    for k in range(1, 16):                                       # rooted just below it may grow up over it
        dshadow[k:] |= m['ditch'][:-k]
    gaps = fbm(NEW, W, 5, 411) > 0.55                            # here and there a clump may stand in it
    reed_area &= ~(dshadow & ~gaps)
    for t_ in things:
        if isinstance(t_, ol.Steg):                              # the jetties stay clear of reeds
            x0, y0, x1, y1 = t_.box()
            reed_area[max(0, y0 - Y4):max(0, y1 - Y4 + 15), max(0, x0 + 1):x1 - 1] = False   # stalks grow up 15 px; right beside it they may
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
    for y in range(Y4 + 4, Y4 + 110, 13):                       # zone 3's side firs thin out and stop
        for x in (int(rng.integers(-6, 12)), W - int(rng.integers(-6, 12))):
            if rng.random() < (y - Y4) / 110:
                continue
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
    low[Y4:] |= pud | m['ditch']                                             # tall blades below a pool would hide it
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
    edge_fog = np.zeros((H, W))
    edge_fog[Y4:] = np.maximum(np.clip((yy - 690) / 110.0, 0, 1) ** 1.4 * 0.88,
                               np.clip((24 - side) / 24.0, 0, 1) ** 1.3 * 0.8 * grow)
    calm = np.zeros((H, W))
    calm[Y4:] = ndi.gaussian_filter(m['lake'].astype(float), 6)
    if raw:
        return np.clip(img, 0, 255), lit, sw, band, edge_fog, calm
    out = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=lit + [l for s_ in sw for l in s_.lights(2.0)], wisps=[]),
                        2.0, grass_mist=z2.GRASS_MIST, water_band=band, calm=calm).astype(float)
    for s_ in sw:
        s_.draw(out, 2.0)
    out = out * (1 - edge_fog[..., None]) + MIST * edge_fog[..., None]   # the world fades into mist
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
