#!/usr/bin/env python3
"""The Ostwald becomes world data: runs after gen_south.py and before split_chunks.py (make_world.sh does).

The approved drafts stay the only source of the look. Each is rendered through the south's collector
(east/collect.py): ground, swaying layer, standing things as sprites. The pieces are laid over each other
with dithered edges (the forest first, then the poppy transition, the forest fringe and the five spots).

In/Out: SRC (default assets/world) holds the south generator's whole-world images; the result goes to OUT
(default the same folder): ground, flowers, bend, low, walk*, ground_mat, water, refl, open_water, lake,
mist_fields, world.json and sprites/e*.png.
"""
import glob
import json
import os
import re
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, 'east'), os.path.join(HERE, 'south'), os.path.join(HERE, 'lib'), HERE]
import collect  # noqa: E402
import fireflies  # noqa: E402
import forest as F  # noqa: E402
import grade_field  # noqa: E402
import layers  # noqa: E402
import layout as L  # noqa: E402
import objects_east as oe  # noqa: E402
import objects_lake as ol  # noqa: E402
import objects_water as ow  # noqa: E402
import reflect_map  # noqa: E402
import spot3_graves as s3  # noqa: E402
import spot4_pond as s4  # noqa: E402
import spot5_ritual as s5  # noqa: E402
import spot6_bridge as s6  # noqa: E402
import spot7_jizo as s7  # noqa: E402
import zone0_draft as Z0  # noqa: E402
import zone1_draft as z1  # noqa: E402
import zone2_draft as z2  # noqa: E402
import zone_saum_draft as ZS  # noqa: E402
import ground as south_ground  # noqa: E402
import zone4_layout as L4  # noqa: E402
from objects_south import Findling  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
H, WW = 3600, 1800
OW, OH = z1.OLD_W, z1.OLD_H
TOP = OH - z1.CTX                    # from this world row down the south's zone 1 begins
MIX = 240                            # width of the poppy-to-wood dither east of zone 1
SOUTH_W = 900                        # the south's own width; east of it the wood has the whole height
CELL = 2
GRASS, EARTH, STONE, WOOD, SNOW, WET = range(6)
KIND_BROOK, KIND_LAKE = 2, 3
FEATHER = 22
SPOT_FEATHER = 90                    # a spot's own trees fade into the wood's over this many pixels (a hard window edge showed)
BAND = 520                           # rows of the big forest rendered in one go (the shadows are dicts: keep them small)
LOW_H = {'Steg': 3, 'Steinbruecke': 4, 'Seerosen': 1, 'WasserStein': 1, 'Treibholz': 1, 'Boot': 1}


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ the draw hook for firs
_orig_draw = F.draw


def draw_items(img, items, G):
    """forest.draw, but the firs (which it draws through a window view) become sprites while collecting."""
    c = layers._active
    if c is None:
        return _orig_draw(img, items, G)
    h, w = img.shape[:2]
    for it in items:
        k, x, y, sz, sd = it
        if k != 'fir':
            _orig_draw(img, [it], G)
        elif c.pass_ == 'full':
            record_fir(c, w, h, x, y, sz, sd)


def record_fir(c, w, h, x, y, sz, sd, snow=0.0):
    a0, b0, a1, b1 = max(0, x - sz), max(0, y - sz - 4), min(w, x + sz), min(h, y + sz // 3 + 2)
    if a1 <= a0 or b1 <= b0:
        return
    base = c.ground[b0:b1, a0:a1].astype(float)
    im = base.copy()
    f = z1.Fir(x - a0, y - b0, sz, sd, snow=snow)
    f.draw(im)
    a = np.zeros((b1 - b0, a1 - a0, 4), np.uint8)
    a[..., :3] = np.clip(im, 0, 255).astype(np.uint8)
    a[..., 3] = (np.abs(im - base).sum(-1) > 0.5) * 255
    c.sprites[('fir', x, y, sd)] = dict(thing=z1.Fir(x, y, sz, sd, snow=snow), rgba=a, x=a0, y=b0, foot=y, frames=1,
                                        w=a1 - a0, h=b1 - b0)


F.draw = draw_items


# ------------------------------------------------------------------ pieces
class Piece:
    """One rendered window laid into the world: ground, sway layer, sprites, flat masks, lights; `weight` says
    how much of it is shown at each pixel (1 inside, 0 outside, a dithered ramp between)."""
    sw = None                                                   # optional own weight for the sprites (the ground keeps `weight`)

    def __init__(self, name, x0, y0, c, weight, lights=()):
        self.name, self.x0, self.y0 = name, x0, y0
        self.ground, self.sway, self.sway_h = c.ground, c.sway, c.sway_h
        self.sprites, self.masks = c.sprites, c.masks
        self.weight = weight
        self.lights = [dict(l, x=l['x'] + x0, y=l['y'] + y0) for l in lights]
        self.h, self.w = self.ground.shape[:2]


def rect_weight(h, w, f=FEATHER):
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy))
    return smooth(d / float(f))


def spot_weight(p):
    """rect_weight with the wide feather, but no fade on a side that lies at the world's edge."""
    yy, xx = np.mgrid[0:p.h, 0:p.w]
    d = np.minimum(xx, np.minimum(yy, p.h - 1 - yy))
    if p.x0 + p.w < WW:
        d = np.minimum(d, p.w - 1 - xx)
    return smooth(d / float(SPOT_FEATHER))


def hash01(x, y):
    return (np.sin(np.asarray(x, float) * 12.9898 + np.asarray(y, float) * 78.233) * 43758.5453) % 1.0


def lights_of(res, i):
    return res[i] if len(res) > i else []


def spot_piece(name, mod, adapt):
    c = collect.collect_window(lambda: adapt(mod.render()), mod.W)
    return Piece(name, mod.X0, mod.Y0, c, rect_weight(mod.H, mod.W), lights_of(c.result, 2))


def forest_weight(x0, y0, h, w):
    """How much of the wood shows at each pixel: everywhere east of the south, a wide mix over zone 1's firs and the
    poppies, the old fir block's place filled with wood, and the west edge running out into the poppy field.
    South of y 2230 the meadow tongue and the lake's shore keep the wood away until x ~1050 (tongue) / ~1190 (lake)."""
    gx = np.arange(w)[None, :] + x0
    gy = np.arange(h)[:, None] + y0
    yr = 1.0 - smooth((gy - (TOP - 40)) / 110.0)                  # blends into zone 1's own firs
    xr = smooth((gx - (SOUTH_W - MIX)) / float(MIX))              # the poppies thin out into the wood
    blob = smooth((gx - (OW + 10)) / 70.0) * smooth((gy - (TOP - 60)) / 60.0) * (1.0 - smooth((gy - (TOP + 110)) / 80.0))   # where the south's block of firs stood
    wt = np.where(gx >= SOUTH_W, 1.0, np.maximum(np.maximum(yr, xr), blob))
    ry = smooth((gy - 2230) / 110.0)
    w2 = smooth((gy - 2880) / 140.0)
    keep = ry * ((1 - w2) * (1.0 - smooth((gx - SOUTH_W) / 150.0)) + w2 * (1.0 - smooth((gx - 960) / 460.0)))
    bach = np.zeros((h, w), bool)                                 # the brook still needs its wood ground: it runs through the tongue
    bm = L.masks().bach
    bach[:bm.shape[0], :bm.shape[1]] = bm
    bw = np.clip(ndi.gaussian_filter(ndi.binary_dilation(bach, iterations=5).astype(float), 2.0) * 1.6, 0, 1)
    wt = np.maximum(wt * (1 - keep), bw * ry)
    return wt * smooth((gx - (OW - 140)) / 140.0)                 # west edge: the poppy field runs out into the wood


def forest_piece(rows=None):
    """The whole wood (x 380..1800, y 0..3600): floor, river and brook, trees in bands, reeds along the water."""
    x0, y0, x1, y1 = L.X0, L.Y0, L.X1, L.Y1
    h, w = y1 - y0, x1 - x0
    rng = np.random.default_rng(7)
    masks = F.window_masks(x0, y0, x1, y1)
    bach = L.masks().bach
    water = masks['river'] | bach
    masks2 = {'path': masks['path'], 'clearing': masks['clearing'], 'river': water}
    img = F.floor(h, w, masks2, rng)
    shallow = water & (ndi.distance_transform_edt(water) < 4)
    ol.paint_lake(img, 0, water, shallow, rng)
    items = F.scatter(h, w, masks2, rng)
    ring = ndi.binary_dilation(water, iterations=4) & ~ndi.binary_dilation(water, iterations=1) & ~masks['path']
    ys, xs = np.nonzero(ring)
    for _ in range(int(len(ys) / 70)):
        i = int(rng.integers(0, len(ys)))
        items.append(('schilf' if rng.random() < 0.7 else 'rohr', int(xs[i]), int(ys[i]), int(rng.integers(4, 9)),
                      int(rng.integers(0, 10 ** 6))))
    items.sort(key=lambda t: t[2])
    G = rng.random((h, w))
    r_lo, r_hi = (0, h) if rows is None else (rows[0] - y0, rows[1] - y0)
    ground = img.astype(np.float32)
    fac = np.ones((h, w), np.float32)
    sway = np.zeros((h, w, 4), np.uint8)
    sway_h = np.zeros((h, w), np.uint8)
    sprites, masks_out = [], {}
    for b0 in range(r_lo, r_hi, BAND):
        b1 = min(b0 + BAND, r_hi)
        a0, a1 = max(0, b0 - 90), min(h, b1 + 24)
        mine = [(k, x, y - a0, s, sd) for k, x, y, s, sd in items if b0 <= y < b1]

        def render(a0=a0, a1=a1, mine=mine):
            im = img[a0:a1].copy()
            plain = [t for t in mine if t[0] not in ('schilf', 'rohr')]
            draw_items(im, plain, G[a0:a1])
            for k, x, y, s, sd in mine:
                if k in ('schilf', 'rohr'):
                    (ow.Schilf if k == 'schilf' else ow.Rohrkolben)(x, y, s, sd).draw(im, G[a0:a1])
            return (im,)

        c = collect.collect_window(render, w)
        base = img[a0:a1]
        ok = base.sum(-1) > 0
        f = np.ones(base.shape[:2], np.float32)
        f[ok] = (c.ground.sum(-1)[ok] / np.maximum(base.sum(-1)[ok], 1)).astype(np.float32)
        fac[a0:a1] *= f
        m = c.sway[..., 3] > 0
        sway[a0:a1][m] = c.sway[m]
        sway_h[a0:a1][m] = c.sway_h[m]
        for sp in c.sprites:
            sprites.append(dict(sp, y=sp['y'] + a0, foot=sp['foot'] + a0))
        print('  forest rows', y0 + b0, y0 + b1, len(c.sprites), 'sprites', flush=True)
    ground = np.clip(ground * fac[..., None], 0, 255)
    wt = forest_weight(x0, y0, h, w)
    p = Piece.__new__(Piece)
    p.name, p.x0, p.y0, p.h, p.w = 'forest', x0, y0, h, w
    p.ground, p.sway, p.sway_h, p.sprites, p.masks = ground, sway, sway_h, sprites, {}
    p.weight, p.lights = wt, []
    return p


def zone0_piece():
    """The poppy meadow runs out into the wood: ground, poppy heads (the sway layer), firs, ferns, gate lanterns."""
    x0, y0, w, h = Z0.X0, Z0.Y0, Z0.W, Z0.H

    def render():
        g, heads, open_ = Z0.render()
        rng = np.random.default_rng(5)
        pm = Z0.paint_path(g, rng, Z0.path_mask())
        items = Z0.things(open_, pm, rng)
        c = layers._active
        lights = []
        for kind, x, y, hh, sd in items:
            if kind == 'fir':
                if c.pass_ == 'full':
                    record_fir(c, w, h, x, y, hh, sd)
            elif kind == 'fern':
                ow.Farn(x, y, sd, hh).draw(g, None)
            elif kind == 'lantern':
                t = z2.Steinlaterne(x, y)
                t.draw(g, None)
                lights += t.lights()
        render.heads = heads
        return g, lights

    c = collect.collect_window(render, w)
    heads = render.heads
    m = heads[..., 3] > 0                                         # poppy heads sway whole
    c.sway = heads.copy()
    c.sway_h = np.where(m, 255, 0).astype(np.uint8)
    gx = np.arange(w)[None, :] + x0
    wt = rect_weight(h, w, 24) * (1 - smooth((gx - 700) / 100.0))
    return Piece('zone0', x0, y0, c, wt, c.result[1])


def ext_map(cols, w, seed):
    """Which source column and vertical roll each extension column takes: random picks, so no stripes repeat."""
    r = np.random.default_rng(seed)
    return r.integers(10, cols, w), r.integers(0, 10 ** 5, w)


def mirror_cols(src, cols, w, seed=5):
    """src's first `cols` columns, then the meadow carried on east from randomly picked columns."""
    out = np.zeros((src.shape[0], w) + src.shape[2:], src.dtype)
    out[:, :cols] = src[:, :cols]
    pick, roll = ext_map(cols, w, seed)
    for k in range(cols, w):
        out[:, k] = np.roll(src[:, pick[k]], int(roll[k]), axis=0)
    return out


def blade_layers(x0, y0, w, h, cols, bad=None, seed=5):
    """The south's swaying blades (flowers.png + bend.png) in x x0..x0+cols*, carried on east like the ground."""
    src = ZS.FULL
    fl = np.array(Image.open(os.path.join(src, 'flowers.png')).convert('RGBA'))[y0:y0 + h, x0:x0 + 80]
    bd = np.array(Image.open(os.path.join(src, 'bend.png')))[y0:y0 + h, x0:x0 + 80]
    if bad is not None:
        fl[bad] = 0
        bd[bad] = 0
    return mirror_cols(fl, cols, w, seed), mirror_cols(bd, cols, w, seed)


def saum_piece():
    """The meadow's tongue and the glade 9 at the south-east, from the south's last columns."""
    x0, y0, w, h = ZS.X0, ZS.Y0, ZS.W, ZS.H

    def render():
        g, green = ZS.render()
        return g, green

    ZS.BAKE_BLADES = False
    c = collect.collect_window(render, w)
    fl, bd = blade_layers(x0, y0, w, h, 80)
    keep = np.random.default_rng(31).random((h, w)) < np.clip(ZS.render.open_, 0, 1) ** 0.7     # blades only where the ground is meadow
    c.sway = np.where(keep[..., None], fl, 0).astype(np.uint8)
    c.sway_h = np.where(keep, bd, 0).astype(np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.minimum(np.minimum(yy, h - 1 - yy), w - 1 - xx)                # wide feather on three sides, the south's seam stays narrow
    wt = np.minimum(smooth(d / float(SPOT_FEATHER)), smooth(xx / 24.0))
    bach = L.masks().bach[y0 - L.Y0:y0 - L.Y0 + h, x0 - L.X0:x0 - L.X0 + w]           # the wood's brook runs on through the meadow tongue to brook B
    wt = wt * (1.0 - np.clip(ndi.gaussian_filter(ndi.binary_dilation(bach, iterations=5).astype(float), 2.0) * 1.6, 0, 1))
    pc = Piece('saum', x0, y0, c, wt)
    pc.ver = 2
    pc.sw = wt * smooth((np.arange(x0, x0 + w)[None, :] - (ZS.SEAM - 20)) / 130.0)          # the leaf mass fades in from the meadow, the ground stays
    return pc


UX0, UY0, UX1, UY1 = 826, 2860, 1560, 3600
Z4Y = 2800                                                      # world row of the lake zone's first row


def ufer_piece(src):
    """The lake's east shore, grown the way the south's lake zone is grown (zone4_draft): the same ground recipe handed
    over from the south's own ground, tall grass, wild flowers, ferns, stones, the reed sea along the world's edge
    (it retreats eastward), and the wood's green trees thickening slowly. The south itself ends in side reeds at x 875."""
    w, h = UX1 - UX0, UY1 - UY0
    rng = np.random.default_rng(37)
    ax = np.arange(w)[None, :] + UX0
    yl = np.arange(h)[:, None] + (UY0 - Z4Y)
    og = np.array(Image.open(os.path.join(src, 'ground.png')).convert('RGB'))[UY0:UY1, UX0 - 60:UX0].astype(float)
    fog = np.clip(0.70 + 0.10 * z2.fbm(h, w, 18, 404), 0, 1)
    flow = np.clip(0.22 + 0.10 * z2.fbm(h, w, 10, 405), 0, 1)
    fresh = south_ground.fresh_tone(h, w, fog, flow, rng)
    tone = south_ground.continued_tone(south_ground.tone_of(og).T, fresh.T, reach=60).T
    base = south_ground.ground_from_tone(tone, fog, flow, rng) * (1 - np.array([0.12, 0.0, 0.14])) * 0.62
    edge = L4.edge(ax) + 4 * z2.fbm(h, w, 6, 406) + 100 * smooth((ax - 1150) / 260.0)     # the reed sea retreats eastward
    sea = yl > edge
    marsh = (yl > edge + 30 + 8 * z2.fbm(h, w, 8, 407)) & (z2.fbm(h, w, 4, 408) > -0.3)
    open_w = yl > edge + 52 + 6 * np.sin(ax / 23.0)
    water = marsh | open_w
    shallow = marsh & ~open_w
    base[ndi.distance_transform_edt(~water) < 8] *= 0.85
    open_ = np.clip(1.0 - smooth((ax - 1000) / 340.0), 0, 1) * np.ones((h, 1))
    no = np.zeros((h, w), bool)

    def render():
        r = np.random.default_rng(29)
        floor = F.floor(h, w, {'path': no, 'clearing': no, 'river': no}, r)
        take = r.random((h, w)) < open_ ** 0.7
        g = np.where(take[..., None], base, floor)
        ol.paint_lake(g, 0, water, shallow, r)
        things = []
        reed = sea & ~open_w
        ys, xs = np.nonzero(reed)
        pick = r.random(len(ys)) < 1 / 9
        for y, x in zip(ys[pick], xs[pick]):
            if r.random() < 0.78:
                things.append(ow.Schilf(int(x), int(y), int(r.integers(6, 12)), int(r.integers(0, 10 ** 6))))
            else:
                things.append(ow.Rohrkolben(int(x), int(y), int(r.integers(3, 6)), int(r.integers(0, 10 ** 6))))
        dry = ~ndi.binary_dilation(water | sea, iterations=3)
        for k in range(7):                                        # ferns and stones as the south scatters them
            x, y = int(r.integers(20, 360)), int(r.integers(30, h - 130))
            if dry[y, x]:
                things.append(ow.Farn(x, y, int(r.integers(0, 999)), 7))
        for k, size in enumerate((7, 6, 8, 5)):
            x, y = int(r.integers(30, 420)), int(r.integers(40, h - 140))
            if dry[y, x]:
                things.append(Findling(x, y, size, 50 + k))
        spots = []
        for k in range(60):                                       # a few broadleaf trees standing alone in the grass, as in the south
            x, y = int(r.integers(40, 340)), int(r.integers(60, h - 170))
            if dry[y, x] and open_[0, x] > 0.5 and all(np.hypot(x - a, y - b) > 80 for a, b in spots) and len(spots) < 9:
                spots.append((x, y))
                things.append(ol.Laubbaum(x, y, seed=120 + len(spots), size=float(r.uniform(0.9, 1.25)), leaf=(None, None, 'gold', None, None, 'orange', None, None, None)[len(spots) - 1]))
        keep_off = ~dry
        for a, b in spots:
            keep_off[max(0, b - 4):b + 3, max(0, a - 6):a + 7] = True
        for t_ in things:
            if isinstance(t_, Findling):
                x0, y0, x1, y1 = t_.box()
                keep_off[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
        dens = np.clip(0.75 + 0.32 * z2.fbm(h, w, 16, 409), 0.35, 1)
        blades = []
        for _ in range(int(w * h / 8.5)):
            x, y = r.uniform(2, w - 2), r.uniform(0, h - 1)
            if keep_off[int(y), int(x)] or r.random() > dens[int(y), int(x)] * open_[0, int(x)]:
                continue
            blades.append(z2.Blade(x, int(round(y)), r))
        for _ in range(1100):
            x, y = int(r.integers(4, w - 4)), int(r.integers(2, h - 2))
            if keep_off[y, x] or r.random() > (1.2 - dens[y, x]) * open_[0, x]:
                continue
            things.append(z2.Wildflower(x, y, int(r.choice(3, p=[0.45, 0.33, 0.22])), r, int(r.integers(6, 10))))
        G = np.random.default_rng(3).random((h, w))
        for t_ in sorted(things + blades, key=lambda t_: getattr(t_, 'order', None) or t_.box()[3]):
            t_.draw(g, G)
        green = np.clip(smooth((1400 - ax) / 400.0) * np.ones((h, 1)), 0, 1)
        items = F.scatter(h, w, {'path': no, 'clearing': open_ > 0.45, 'river': ~dry}, r, green=green)
        items = [t for t in items if t[1] + UX0 > 884 and r.random() < smooth((t[1] + UX0 - 1060) / 340.0)]    # trees thicken slowly
        F.draw(g, sorted(items, key=lambda t: t[2]), np.random.default_rng(5).random((h, w)))
        return g, []

    c = collect.collect_window(render, w)
    yy, xx = np.mgrid[0:h, 0:w]
    wt = np.minimum(smooth(np.minimum(yy, w - 1 - xx) / float(SPOT_FEATHER)), smooth(xx / 34.0))
    cells = np.fromfile(os.path.join(src, 'ground_mat.bin'), np.uint8).reshape(H // CELL, WW // CELL)
    path0 = np.kron(cells[UY0 // CELL:UY1 // CELL, UX0 // CELL:(UX0 + 100) // CELL] == EARTH, np.ones((CELL, CELL), bool))
    wt[:, :100] *= 1.0 - ndi.binary_dilation(path0, iterations=2)                # the south's own path stays whole
    pc = Piece('ufer', UX0, UY0, c, wt)
    pc.ver = 6
    return pc


# ------------------------------------------------------------------ putting the pieces together
FOOT_ROWS = {'Halle': 9, 'Altar': 6, 'Schrein': 5, 'Riesenbaum': 5, 'Steinlaterne': 5, 'Fir': 4}


TRUNK = {'Fir': (3, 3, 1), 'Laubbaum': (4, 3, 1), 'Knorrbaum': (5, 4, 2), 'Kahlbaum': (3, 3, 1)}   # half width, rows above, below


def foot_x(t):
    return t.p.x if isinstance(t, z1.Fir) else t.x


def foot_block(sp, m):
    """Where a standing thing really stands: a tree's trunk, otherwise the pixels it has in its lowest rows
    (plinth, stone's foot), a little thicker - never a crown or a whole body."""
    t = sp['thing']
    name = type(t).__name__
    ys0 = sp['foot']
    if name in TRUNK or name == 'Riesenbaum':
        if name == 'Riesenbaum':
            hw, up, dn = int(3 * getattr(t, 'size', 2)), 5, 3
        else:
            hw, up, dn = TRUNK[name]
        cx = int(foot_x(t)) + (sp['x'] - sp.get('x_win', sp['x']))
        m[max(0, ys0 - up):ys0 + dn + 1, max(0, cx - hw):cx + hw + 1] = True
        return
    rows = FOOT_ROWS.get(name, 3)
    a = sp['rgba'][:, :sp['w'], 3] > 0
    j0 = max(0, sp['foot'] - sp['y'] - rows)
    j1 = min(a.shape[0], sp['foot'] - sp['y'] + 2)
    sub = ndi.binary_dilation(a[j0:j1], iterations=1)
    ys, xs = np.nonzero(sub)
    py, px = sp['y'] + j0 + ys, sp['x'] + xs
    ok = (py >= 0) & (py < m.shape[0]) & (px >= 0) & (px < m.shape[1])
    m[py[ok], px[ok]] = True


def place(pieces, ground, flowers, bend, low, masks, rng):
    """Lays every piece over the world arrays; returns the sprites that stay, with world coordinates."""
    kept = []
    for i, p in enumerate(pieces):
        cy1, cx1 = min(p.h, H - p.y0), min(p.w, WW - p.x0)              # the ritual window reaches past the world's edge
        sl = (slice(p.y0, p.y0 + cy1), slice(p.x0, p.x0 + cx1))
        pc = (slice(0, cy1), slice(0, cx1))
        take = rng.random((cy1, cx1)) < p.weight[pc]
        ground[sl][take] = p.ground[pc][take]
        flowers[sl][take] = p.sway[pc][take]
        bend[sl][take] = p.sway_h[pc][take]
        for k, v in p.masks.items():
            if k not in masks:
                masks[k] = np.zeros((H, WW), bool)
            masks[k][sl][take] |= v[pc][take]
        later = pieces[i + 1:]
        for sp in p.sprites:
            fx, fy = sp['x'] + sp['w'] // 2 + p.x0, sp['foot'] + p.y0
            r = float(hash01(fx, fy))
            if any(0 <= fx - q.x0 < q.w and 0 <= fy - q.y0 < q.h and q.weight[fy - q.y0, fx - q.x0] > r for q in later):
                continue
            if not (0 <= fx - p.x0 < p.w and 0 <= fy - p.y0 < p.h) or (p.weight if p.sw is None else p.sw)[min(max(fy - p.y0, 0), p.h - 1), min(max(fx - p.x0, 0), p.w - 1)] <= r:
                continue
            kept.append(dict(sp, x=sp['x'] + p.x0, x_win=sp['x'], y=sp['y'] + p.y0, foot=sp['foot'] + p.y0))
    return kept


def painted(ground, pal):
    m = np.zeros(ground.shape[:2], bool)
    for col in pal:
        m |= (ground == np.array(np.round(col), ground.dtype)).all(-1)
    return m


def main(src=None, out=None):
    src = src or os.path.join(ROOT, 'assets', 'world')
    out = out or src
    os.makedirs(os.path.join(out, 'sprites'), exist_ok=True)
    ZS.FULL = src
    rows = os.environ.get('EAST_ROWS')                          # development: only these forest rows
    rows = tuple(int(v) for v in rows.split(',')) if rows else None
    rng = np.random.default_rng(3)

    def im(n, mode=None):
        a = Image.open(os.path.join(src, n))
        return np.array(a.convert(mode) if mode else a)

    ground = im('ground.png', 'RGB').astype(np.float32)
    flowers = im('flowers.png', 'RGBA')
    bend = im('bend.png', 'L')
    low = im('low.png', 'L')
    with open(os.path.join(src, 'world.json')) as f:
        w = json.load(f)
    with open(os.path.join(ROOT, 'build', 'world_old', 'world_old.json')) as f:
        w_old = json.load(f)
    assert ground.shape == (H, WW, 3), ground.shape

    cache = os.environ.get('EAST_CACHE')                        # development: keep the rendered pieces between runs
    if cache and os.path.exists(cache):
        import pickle
        with open(cache, 'rb') as f:
            pieces, ZS.render.open_ = pickle.load(f)
    else:
        print('pieces', flush=True)
        pieces = [forest_piece(rows), zone0_piece()]
        print(' saum', flush=True)
        pieces.append(saum_piece())
        for name, mod, adapt in (('s3', s3, lambda r: r), ('s4', s4, lambda r: (r,)), ('s5', s5, lambda r: r),
                                 ('s6', s6, lambda r: r), ('s7', s7, lambda r: r)):
            print(' spot', name, flush=True)
            pieces.append(spot_piece(name, mod, adapt))
        if cache:
            import pickle
            with open(cache, 'wb') as f:
                pickle.dump((pieces, ZS.render.open_), f, protocol=4)

    if sum((p.name == 'saum' and getattr(p, 'ver', 0) >= 2) or (p.name == 'ufer' and getattr(p, 'ver', 0) >= 6) for p in pieces) < 2:     # re-render these two (cheap) after a change
        pieces = [p for p in pieces if p.name not in ('saum', 'ufer')]
        pieces[2:2] = [saum_piece(), ufer_piece(src)]
        if cache:
            import pickle
            with open(cache, 'wb') as f:
                pickle.dump((pieces, ZS.render.open_), f, protocol=4)
    pieces[0].weight = forest_weight(pieces[0].x0, pieces[0].y0, pieces[0].h, pieces[0].w)   # cheap: tunable without re-rendering the wood
    for p in [p for p in pieces if p.name in ('s3', 's4', 's5', 's6', 's7')]:   # the spots never reach into the south's ground below zone 1's top
        p.weight = spot_weight(p)
        gx = np.arange(p.x0, p.x0 + p.w)[None, :]
        gy = np.arange(p.y0, p.y0 + p.h)[:, None]
        p.weight = p.weight * np.where(gy >= TOP, smooth((gx - SOUTH_W) / 24.0), 1.0)
    masks = {}
    kept = place(pieces, ground, flowers, bend, low, masks, rng)
    lights_new = [l for p in pieces for l in p.lights]
    print('sprites', len(kept), 'lights', len(lights_new), flush=True)
    return dict(ground=ground, flowers=flowers, bend=bend, low=low, masks=masks, kept=kept, lights=lights_new,
                w=w, w_old=w_old, pieces=pieces, src=src, out=out)


def water_east(ground_u8, masks, pieces):
    """Water map of the east (RGBA8, world size, as gen_south.water_map): R flow angle, G depth, B way along mod 256,
    A kind (2 stream, 3 pond). Only pixels still painted in a water colour move."""
    from scipy.spatial import cKDTree
    out = np.zeros((H, WW, 4), np.uint8)
    x0, y0, x1, y1 = L.X0, L.Y0, L.X1, L.Y1
    reg = (slice(y0, y1), slice(x0, x1))
    wat = painted(ground_u8[reg], ow.WATER)
    lake_w, _, _ = s4.water_masks()                              # the pond's own outline (window pixels)
    pond = np.zeros_like(wat)
    pond[s4.Y0 - y0:s4.Y0 - y0 + s4.H, s4.X0 - x0:s4.X0 - x0 + s4.W] = lake_w
    pond = ndi.binary_dilation(pond, iterations=1)
    lines = [L.river(), L.bach()]
    pts, ang, arc = [], [], []
    for line in lines:
        d = np.hypot(*np.diff(line, axis=0).T)
        a = np.r_[0, np.cumsum(d)]
        t = np.gradient(line, axis=0)
        pts.append(line)
        ang.append(np.arctan2(t[:, 1], t[:, 0]))
        arc.append(a)
    pts, ang, arc = np.vstack(pts), np.concatenate(ang), np.concatenate(arc)
    tree = cKDTree(pts)
    stream = wat & ~pond
    yy, xx = np.nonzero(stream)
    d, i = tree.query(np.stack([xx + x0, yy + y0], 1))
    ok = d < 40
    yy, xx, i = yy[ok], xx[ok], i[ok]
    dep = np.clip(ndi.distance_transform_edt(ndi.binary_dilation(stream, iterations=2))[yy, xx] / 5.0, 0, 1)
    out[yy + y0, xx + x0] = np.stack([(ang[i] / (2 * np.pi) % 1 * 256).astype(np.uint8), (dep * 255).astype(np.uint8),
                                      (arc[i] % 256).astype(np.uint8), np.full(len(yy), KIND_BROOK, np.uint8)], 1)
    ur = np.zeros_like(wat)                                      # the lake shore's reed sea moves like the south's
    ur[UY0 - y0:UY1 - y0, UX0 - x0:UX1 - x0] = True
    sea = wat & ur & ~pond
    sd = np.clip(ndi.distance_transform_edt(ndi.binary_dilation(sea, iterations=2)) / 25.0, 0, 1)
    out[y0:y1, x0:x1][sea, 1] = (sd[sea] * 255).astype(np.uint8)
    out[y0:y1, x0:x1][sea, 3] = KIND_LAKE
    lake = wat & pond
    dep = np.clip(ndi.distance_transform_edt(pond) / 40.0, 0, 1)
    sub = out[reg]
    sub[lake, 1] = (dep[lake] * 255).astype(np.uint8)
    sub[lake, 3] = KIND_LAKE
    return out


def east_materials(r, own):
    """Ground material per pixel of the east window: earth on the paths, wood and stone on jetty and bridge."""
    x0, y0, x1, y1 = L.X0, L.Y0, L.X1, L.Y1
    lm = L.masks()
    mat = np.full((y1 - y0, x1 - x0), GRASS, np.uint8)
    mat[ndi.binary_dilation(lm.path, iterations=1)] = EARTH
    mk = r['masks']
    reg = (slice(y0, y1), slice(x0, x1))
    if 'Steg' in mk:
        mat[mk['Steg'][reg]] = WOOD
    if 'Steinbruecke' in mk:
        mat[mk['Steinbruecke'][reg] & ndi.binary_dilation(lm.path, iterations=3)] = STONE
    return mat


def wat_at(wm, x0, y0, w, h):
    return wm[y0:y0 + h, x0:x0 + w, 3] > 0


def finish(r):
    """Walkability, water, reflections, lights, the index: everything the game needs besides the pictures."""
    src, out, w, w_old = r['src'], r['out'], r['w'], r['w_old']
    ground, flowers, bend, low, masks, kept = r['ground'], r['flowers'], r['bend'], r['low'], r['masks'], r['kept']
    x0, y0, x1, y1 = L.X0, L.Y0, L.X1, L.Y1
    reg = (slice(y0, y1), slice(x0, x1))
    gu8 = np.clip(np.round(ground), 0, 255).astype(np.uint8)
    for k, hgt in LOW_H.items():
        if k in masks:
            low[masks[k]] = np.maximum(low[masks[k]], hgt)

    lm0 = L.masks()
    pw = np.zeros((H, WW), bool)
    pw[y0:y1, x0:x1] = lm0.path
    corridor = ndi.binary_dilation(pw, iterations=3) & (np.arange(WW)[None, :] < SOUTH_W) & (np.arange(H)[:, None] >= TOP)
    near_path = ndi.binary_dilation(pw, iterations=14)
    # ---- sprites: the placeholder wood's fringe goes, the old map's east edge firs stay outside the poppy gate
    for f in glob.glob(os.path.join(out, 'sprites', 'e[0-9]*.png')):
        os.remove(f)
    sprites = [s for s in w['sprites'] if not (re.fullmatch(r's\d+', s['name']) and s['foot'] < TOP + 20 and
                                                abs(s['x'] + s['w'] / 2 - OW) < 110)]
    path_y = float(np.interp(880, L.paths()['saum_h'][:, 0], L.paths()['saum_h'][:, 1]))
    sprites = [s for s in sprites if not (re.fullmatch(r's\d+', s['name']) and s['x'] + s['w'] >= ZS.SEAM - 40 and
                                          abs(s['foot'] - path_y) < 95 and s['x'] < ZS.SEAM + 40)]
    sprites = [s for s in sprites if not (re.fullmatch(r's\d+', s['name']) and 540 <= s['x'] + s['w'] // 2 < SOUTH_W and
                                          TOP <= s['foot'] < 1300 and near_path[min(s['foot'], H - 1), s['x'] + s['w'] // 2])]
    sprites = [s for s in sprites if not (re.fullmatch(r's\d+', s['name']) and s['foot'] >= TOP + 70 and
                                          float(hash01(s['x'], s['foot'])) < smooth((s['x'] + s['w'] // 2 - (SOUTH_W - MIX)) / float(MIX)))]
    sprites = [s for s in sprites if not (re.fullmatch(r's\d+', s['name']) and TOP - 60 <= s['foot'] < TOP + 190 and
                                          OW <= s['x'] + s['w'] // 2 < SOUTH_W)]             # the south's block of firs makes way for the wood's own trees
    sprites = [s for s in sprites if not (s['name'].startswith('tanne') and OW - 60 <= s['x'] + s['w'] // 2 < OW + 80)]   # the old closed wall of firs at the east edge is gone: the poppies run into the wood
    sprites = [s for s in sprites if not (re.fullmatch(r's\d+', s['name']) and s['x'] + s['w'] // 2 >= UX0 and s['foot'] >= UY0)]   # the south's side firs/reeds: the shore grows on instead
    cells = np.fromfile(os.path.join(src, 'ground_mat.bin'), np.uint8).reshape(H // CELL, WW // CELL)
    earth = ndi.binary_dilation(cells == EARTH, iterations=5)
    kept = [s for s in kept if not (s['x'] + s['w'] // 2 < SOUTH_W and s['foot'] >= TOP and
                                    earth[min(s['foot'] // CELL, H // CELL - 1), min((s['x'] + s['w'] // 2) // CELL, WW // CELL - 1)])]   # no wood tree on the south's paths
    clipped = []
    for s in kept:                                              # nothing hangs over the world's edge
        if s['x'] >= WW or s['x'] + s['w'] <= 0 or not 0 <= s['foot'] < H:
            continue
        if s['x'] + s['w'] > WW and s['frames'] > 1:
            continue                                            # a lantern's strip cannot be cut
        if s['x'] + s['w'] > WW:
            s = dict(s, rgba=s['rgba'][:, :WW - s['x']], w=WW - s['x'])
        clipped.append(s)
    kept = sorted(clipped, key=lambda s: (s['foot'], s['x']))
    r['lights'] = [l for l in r['lights'] if 0 <= l['x'] < WW and 0 <= l['y'] < H]
    blocked = np.zeros((H, WW), bool)
    for n, s in enumerate(kept):
        name = f'e{n}'
        Image.fromarray(s['rgba']).save(os.path.join(out, 'sprites', name + '.png'))
        sprites.append(dict(name=name, x=int(s['x']), y=int(s['y']), w=int(s['w']), h=int(s['rgba'].shape[0]),
                            foot=int(s['foot']), frames=int(s['frames']), fps=8))
        foot_block(s, blocked)

    # ---- where one can walk
    lm = L.masks()
    gx = np.arange(x0, x1)[None, :]
    gy = np.arange(y0, y1)[:, None]
    own = ((gx >= SOUTH_W) | (gy < TOP)) & (gx >= OW)                            # the south's own ground below zone 1's top stays as it is
    wm = water_east(gu8, masks, r['pieces'])
    wat = wm[reg][..., 3] > 0
    wE = ndi.binary_dilation(lm.path, iterations=2) | lm.clearing
    wE &= ~(wat | blocked[reg])
    deck = np.zeros_like(wE)
    for k in ('Steg', 'Steinbruecke'):
        if k in masks:
            deck |= masks[k][reg] & ndi.binary_dilation(lm.path | lm.clearing, iterations=3)
    deck &= ~blocked[reg]
    wE |= deck
    walk = np.fromfile(os.path.join(src, 'walk.bin'), np.uint8).reshape(H, WW).astype(bool)
    sub = walk[reg]
    sub[own] = wE[own]
    sub[~own] &= ~blocked[reg][~own]                              # trees that stand in the poppy-to-wood mix
    gz = ndi.binary_dilation(Z0.path_mask(), iterations=2)       # the poppy gate: the old map's closed strip opens
    zs = (slice(Z0.Y0, Z0.Y0 + Z0.H), slice(Z0.X0, Z0.X0 + Z0.W))
    gx0 = np.arange(Z0.X0, Z0.X0 + Z0.W)[None, :]
    walk[zs] |= gz & (gx0 >= OW - 60)
    walk |= corridor & ~(wm[..., 3] > 0) & ~blocked                  # the way to the pond leaves the wood through the south's firs
    tor = L.paths()['tor']                                       # the old map's closed 10-px strip: the gate's way runs through it
    for xg in range(OW - 24, OW + 6):
        yg = int(round(tor[0][1] + (xg - OW) * 0.17))
        walk[yg - 4:yg + 5, xg] = True
    tongue = (ZS.render.open_ > 0.45) & ~blocked[ZS.Y0:ZS.Y1, ZS.X0:ZS.X1] & ~wat_at(wm, ZS.X0, ZS.Y0, ZS.W, ZS.H)
    ts = (slice(ZS.Y0, ZS.Y1), slice(ZS.X0, ZS.X1))
    walk[ts] |= tongue & (np.arange(ZS.X0, ZS.X1)[None, :] >= 860)   # the south's closed east edge opens along the tongue
    r['tongue'] = tongue
    r['wm'] = wm
    st = w['start']
    lab, _ = ndi.label(walk, structure=np.ones((3, 3)))
    walk &= lab == lab[int(st['y']), int(st['x'])]
    r['walk'] = walk
    r['blocked'] = blocked
    r['sprites'] = sprites
    return r


def swarms():
    """The wood's fireflies: cool, two over each main place and one on each long way; the glade at the warm meadow keeps warm ones."""
    out = []
    n = 0
    for key, cool in (('3', True), ('4', True), ('5', True), ('6', True), ('7', True), ('9', False)):
        s = L.SPOTS[key]
        for k in range(1 if key == '9' else 2):
            a = 2.4 * k + int(key) * 0.7
            n += 1
            sw = fireflies.Swarm(s.x + np.cos(a) * s.r * 0.45, s.y + np.sin(a) * s.r * 0.3, 7, 400 + n, 11.0)
            out.append(dict(x=float(sw.x), y=float(sw.y), cool=cool,
                            flies=[{k_: round(float(v), 4) for k_, v in f.items()} for f in sw.flies]))
    for name in ('moos', 'wasser', 'saum_n', 'ritual_s'):
        p = L.paths()[name]
        x, y = p[len(p) // 2]
        n += 1
        sw = fireflies.Swarm(x + 10, y - 6, 6, 400 + n, 9.0)
        out.append(dict(x=float(sw.x), y=float(sw.y), cool=name != 'saum_n',
                        flies=[{k_: round(float(v), 4) for k_, v in f.items()} for f in sw.flies]))
    return out


def write(r):
    """The pictures and tables: everything the chunk cutter and the game read."""
    src, out, w = r['src'], r['out'], r['w']
    ground, flowers, bend, low, walk, wm = r['ground'], r['flowers'], r['bend'], r['low'], r['walk'], r['wm']
    x0, y0, x1, y1 = L.X0, L.Y0, L.X1, L.Y1
    reg = (slice(y0, y1), slice(x0, x1))
    gu8 = np.clip(np.round(ground), 0, 255).astype(np.uint8)

    def im(n, mode=None):
        a = Image.open(os.path.join(src, n))
        return np.array(a.convert(mode) if mode else a)

    # ---- materials: earth on the paths, wood and stone on jetty and bridge
    cells = np.fromfile(os.path.join(src, 'ground_mat.bin'), np.uint8).reshape(H // CELL, WW // CELL)
    gx = np.arange(x0, x1)[None, :]
    gy = np.arange(y0, y1)[:, None]
    own = ((gx >= SOUTH_W) | (gy < TOP)) & (gx >= OW)
    mat = east_materials(r, own)
    cm = cells[y0 // CELL:y1 // CELL, x0 // CELL:x1 // CELL]
    cm[own[::CELL, ::CELL]] = mat[::CELL, ::CELL][own[::CELL, ::CELL]]
    cm[own[::CELL, ::CELL]] = np.where(walk[reg][::CELL, ::CELL][own[::CELL, ::CELL]], cm[own[::CELL, ::CELL]], GRASS)
    # ---- water, open water, reflections, the pond for the fish
    cut = (slice(UY0, UY1), slice(UX0, SOUTH_W))                 # the south's side-reed strip is replaced by the grown shore
    water = im('water.png', 'RGBA')
    water[cut] = 0
    east_w = wm[reg][..., 3] > 0
    water[reg][east_w] = wm[reg][east_w]
    open_old = im('open_water.png', 'L') > 0
    open_old[cut] = False
    open_east = east_w & (flowers[reg][..., 3] == 0) & (low[reg] == 0)
    open_all = open_old.copy()
    open_all[reg] |= open_east
    sprs = [(s['rgba'][:, :s['w']], s['x'] - x0, s['y'] - y0, s['foot'] - y0) for s in r['kept']
            if s['x'] + s['w'] > x0 and s['y'] + s['rgba'].shape[0] > y0]
    refl = im('refl.png', 'RGBA')
    refl[cut] = 0
    rr = reflect_map.bake(y1 - y0, x1 - x0, open_east, flowers[reg], bend[reg], low[reg], gu8[reg], sprs)
    m = rr[..., 3] > 0
    refl[reg][m] = rr[m]
    lake = im('lake.png', 'L')
    lake[cut[0].start // 2:cut[0].stop // 2, cut[1].start // 2:cut[1].stop // 2] = 0
    ld = np.where(wm[..., 3] == KIND_LAKE, wm[..., 1], 0).astype(np.uint8)
    ld = ld.reshape(H // 2, 2, WW // 2, 2).min(axis=(1, 3))
    lake = np.maximum(lake, ld)
    # ---- the mist: the wood is open inside its own frame, closed outside; the tongue opens the south's east edge
    mist = im('mist_fields.png', 'RGB').copy()
    hx0, hy0, hx1, hy1 = x0 // 2, y0 // 2, x1 // 2, y1 // 2
    yy, xx = np.mgrid[hy0:hy1, hx0:hx1]
    d = np.minimum(np.minimum(yy - hy0, hy1 - 1 - yy), hx1 - 1 - xx)
    edge = 1 - smooth(d / 24.0)
    ownh = (xx * 2 >= SOUTH_W) | (yy * 2 < TOP)
    mist[hy0:hy1, hx0:hx1, 2][ownh] = np.round(edge[ownh] * 255).astype(np.uint8)
    mist[hy0:hy1, hx0:hx1, :2][ownh] = 0
    uy, ux = np.mgrid[UY0 // 2:UY1 // 2, UX0 // 2:UX1 // 2]       # the shore's own mist: the south's bottom fade, retreating with the reed sea
    prof = np.clip((uy * 2 - Z4Y - 690) / 110.0, 0, 1) ** 1.4 * 0.88 * (1.0 - smooth((ux * 2 - 1150) / 260.0))
    ed = 1 - smooth((UY1 // 2 - 1 - uy) / 24.0)                   # only the world's bottom edge closes in mist; the other sides are no frame
    mist[UY0 // 2:UY1 // 2, UX0 // 2:UX1 // 2, 2] = np.round(np.maximum(ed, prof) * 255).astype(np.uint8)
    tg = np.zeros((H, WW), bool)
    tg[ZS.Y0:ZS.Y1, ZS.X0:ZS.X1] = ndi.binary_dilation(r['tongue'], iterations=6)
    th = tg[::2, ::2]
    mist[..., 2][th & (np.arange(WW // 2)[None, :] * 2 >= 840)] = 0
    # ---- files
    Image.fromarray(gu8).save(os.path.join(out, 'ground.png'))
    Image.fromarray(flowers).save(os.path.join(out, 'flowers.png'))
    Image.fromarray(bend).save(os.path.join(out, 'bend.png'))
    Image.fromarray(low).save(os.path.join(out, 'low.png'))
    Image.fromarray((walk * 255).astype(np.uint8)).save(os.path.join(out, 'walk.png'))
    walk.astype(np.uint8).tofile(os.path.join(out, 'walk.bin'))
    walk.reshape(H // CELL, CELL, WW // CELL, CELL).all(axis=(1, 3)).astype(np.uint8).tofile(os.path.join(out, 'walk_cells.bin'))
    cells.tofile(os.path.join(out, 'ground_mat.bin'))
    Image.fromarray(water).save(os.path.join(out, 'water.png'))
    Image.fromarray((open_all * 255).astype(np.uint8)).save(os.path.join(out, 'open_water.png'))
    Image.fromarray(refl).save(os.path.join(out, 'refl.png'))
    Image.fromarray(lake).save(os.path.join(out, 'lake.png'))
    Image.fromarray(mist).save(os.path.join(out, 'mist_fields.png'))
    w['sprites'] = r['sprites']
    w['fireflies'] = list(w.get('fireflies', [])) + swarms()
    grade_field.write(out)
    f = grade_field.build()[::10, ::10, 0]                      # the wood's darkness per 20 px, for the sounds
    w['mood_w'] = int(f.shape[1])
    w['mood'] = [int(round(v * 100)) for v in f.ravel()]
    w['places'] = {'ritual': [s5.X0 + s5.CX, s5.Y0 + s5.CY + 4], 'pond': [int(L.SPOTS['4'].x), int(L.SPOTS['4'].y)],
                   'graves': [int(L.SPOTS['3'].x), int(L.SPOTS['3'].y)]}
    w['lights'] = list(w['lights']) + [l for l in r['lights']]
    with open(os.path.join(out, 'world.json'), 'w') as f:
        json.dump(w, f, indent=1)
    print('ok', len(w['sprites']), 'sprites,', len(w['lights']), 'lights', flush=True)


if __name__ == '__main__':
    a = sys.argv
    write(finish(main(a[1] if len(a) > 1 else None, a[2] if len(a) > 2 else None)))
