#!/usr/bin/env python3
"""Grows the finished world (after gen_north) by WEST_W columns on the left: the west, Wasure-zato.

Everything that was there moves right by WEST_W, pixel for pixel (as gen_north moved it down): every full-size map
gets the west's columns before it, every x in world.json moves (sprites, lights, start, brook, birds, wisps, lamp
paths, fireflies, fire, places; mood gets columns). Half-size maps grow by WEST_W / 2.

The approved drafts stay the only source of the look: west/dorf1_draft (the village, y 1380..4800) and
west/nw_draft (the north-west corner, y 0..1520) are rendered twice through the south's collector
(west/collect_west.py): a ground pass, then a normal one recording the swaying layer and the standing things
(sprites w*.png). Where today's west edge was (today's columns 0..OWN-WEST_W) the drafts' pictures take over;
the two drafts meet in clumps over rows 1400..1460.

In:  build/world_pre_west/ (the world as gen_north left it; --save-pre copies it there, so this can run alone)
Out: the same names in assets/world (then split_chunks cuts them).
"""
import glob
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PRE = os.path.join(ROOT, 'build', 'world_pre_west')
OUT = os.environ.get('WEST_OUT') or os.path.join(ROOT, 'assets', 'world')   # WEST_OUT: a trial folder first
WEST_W = 900                          # 5 chunk columns; west coordinates: today's x 0 = WEST_W
OWN = WEST_W + 60                     # the west's pictures reach this far (today's edge strip, the seam's mending,
                                      # nw_draft's clumped hand-over to today's ground: its MIX)
OWNW = WEST_W + 24                    # ... its water, walking and reflections this far (dorf1_draft's seam)
DY = 1380                             # the village draft's first row
NW_Y1 = 1520                          # the corner draft's last row
MEET = (1400, 1460)                   # rows over which the two drafts meet
CELL = 2
GRASS, EARTH, STONE, WOOD, SNOW, WET = range(6)
KIND_OLD, KIND_BROOK, KIND_LAKE = 1, 2, 3
MOOD_CELL = 20
LOW_H = {'Steg': 3, 'Bruecke': 4, 'Brett': 2, 'Boot': 1, 'Trittsteine': 1, 'WasserStein': 1, 'Treibholz': 1,
         'Seerosen': 1}
FOOT_ROWS = {'Minka': 8, 'Gewaechshaus': 15, 'Steinmetz': 8, 'Yashiro': 14, 'Teehaus': 6, 'MillHouse': 8,
             'Brunnen': 6, 'Verschneit': 8, 'Glockenhaus': 4, 'Steinlaterne': 5, 'Torii': 2}
TRUNK = {'Laubbaum': (4, 3, 1), 'Kaki': (3, 3, 1), 'Obstbaum': (3, 3, 1), 'Shinboku': (5, 4, 2)}

FULL = ['ground.png', 'flowers.png', 'bend.png', 'water.png', 'low.png', 'refl.png', 'walk.png', 'open_water.png']
HALF = ['lake.png', 'mist_fields.png', 'grade_field.png']
BINS = {'walk.bin': 1, 'walk_cells.bin': CELL, 'ground_mat.bin': CELL}


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def save_pre():
    """Keeps the world as gen_north left it (the full maps from assets/world, or build/world_full when the pipeline
    has already moved them), so gen_west can run again on its own."""
    os.makedirs(PRE, exist_ok=True)
    for n in FULL + list(BINS):
        src = os.path.join(OUT, n)
        if not os.path.exists(src):
            src = os.path.join(ROOT, 'build', 'world_full', n)
        shutil.copy(src, os.path.join(PRE, n))
    for n in HALF + ['world.json']:
        shutil.copy(os.path.join(OUT, n), os.path.join(PRE, n))


def shift_world(w, dx):
    """Every x in world.json moves right by dx (as gen_north.shift_world moves y)."""
    w = dict(w)
    w['width'] = w['width'] + dx
    w['start'] = dict(w['start'], x=w['start']['x'] + dx)
    w['sprites'] = [dict(s, x=s['x'] + dx) for s in w['sprites']]
    w['lights'] = [dict(l, x=l['x'] + dx) for l in w['lights']]
    for k in ('brook', 'birds', 'wisps', 'lamp_paths', 'fireflies'):
        w[k] = [dict(p, x=p['x'] + dx) for p in w.get(k, [])]
    if w.get('fire'):
        w['fire'] = dict(w['fire'], x=w['fire']['x'] + dx)
    w['places'] = {k: [v[0] + dx, v[1]] for k, v in w.get('places', {}).items()}
    return w


def grow(a, dx):
    """a with dx columns of nothing before it."""
    out = np.zeros((a.shape[0], a.shape[1] + dx) + a.shape[2:], a.dtype)
    out[:, dx:] = a
    return out


# ------------------------------------------------------------------ the two drafts, collected
def collect():
    sys.path[:0] = [os.path.join(HERE, 'west'), os.path.join(HERE, 'south'), os.path.join(HERE, 'lib'), HERE]
    import collect_west as cw                                          # registers the west's things first
    import dorf1_draft as D
    import nw_draft as N
    assert D.X0 == 0 and D.Y0 == DY and D.Y1 == 4800 and N.X0 == 0 and N.Y0 == 0 and N.Y1 == NW_Y1
    print('Westen: Dorf (zwei Durchgänge, je ~5 min) ...', flush=True)
    cd = cw.collect_window(lambda: (lambda r: (r['img'], r))(D.render()), D.W)
    print('Westen: Nordwestecke ...', flush=True)
    cn = cw.collect_window(lambda: N.render(), N.W)
    return D, N, cd, cn


def apply_seam_layers(D, cd):
    """dorf1_draft's last match_seam ran on its picture only: do the same to the ground, sway and sprites apart."""
    p = cd.result[1]['seam_p']
    if not p:
        return
    g = cd.ground
    ys, xs = np.mgrid[0:g.shape[0], p['seam'] - p['reach']:p['seam']]
    ys, xs = ys.ravel(), xs.ravel()
    g[ys, xs] = D.apply_seam(g[ys, xs], ys, xs, p)
    sw = cd.sway
    ys, xs = np.nonzero(sw[..., 3] > 0)
    sw[ys, xs, :3] = np.clip(D.apply_seam(sw[ys, xs, :3].astype(float), ys, xs, p), 0, 255).astype(np.uint8)
    for sp in cd.sprites:
        if sp['frames'] > 1:
            continue
        a = sp['rgba']
        yy, xx = np.nonzero(a[..., 3] > 0)
        gy, gx = yy + sp['y'], xx + sp['x']
        ok = (gy < g.shape[0]) & (gx < g.shape[1])
        a[yy[ok], xx[ok], :3] = np.clip(D.apply_seam(a[yy[ok], xx[ok], :3].astype(float), gy[ok], gx[ok], p),
                                        0, 255).astype(np.uint8)


def owners(N, cn, H):
    """Which draft each west pixel (x < OWN) comes from: 'n' the corner, 'd' the village; they meet in clumps over
    MEET, the corner's way to the hermitage stays the corner's down to where it joins the orchard path."""
    rng = np.random.default_rng(401)
    yy = np.arange(H)[:, None]
    cl = ndi.gaussian_filter(rng.normal(0, 1, (H, OWN)), 7)
    cl = 0.5 + 0.3 * cl / cl.std()
    t = smooth((yy - MEET[0]) / float(MEET[1] - MEET[0]))
    own_n = (yy < MEET[0]) | ((cl > t) & (yy < MEET[1]))            # above the meeting rows all the corner's
    path = np.zeros((H, OWN), bool)
    pm = cn.result[1]['path']
    path[:pm.shape[0], :min(OWN, pm.shape[1])] = ndi.binary_dilation(pm, iterations=4)[:, :OWN]
    own_n |= path & (yy < MEET[1])
    return own_n


def main():
    if not os.path.exists(os.path.join(PRE, 'world.json')):
        sys.exit('build/world_pre_west fehlt: erst gen_west.py --save-pre (make_world.sh macht es)')
    w0 = json.load(open(os.path.join(PRE, 'world.json')))
    assert w0['width'] == 1800, 'world_pre_west ist schon der gewachsene Westen'
    W0, H = w0['width'], w0['height']
    W = W0 + WEST_W
    im = {k: np.array(Image.open(os.path.join(PRE, k))) for k in FULL + HALF}
    walk0 = np.fromfile(os.path.join(PRE, 'walk.bin'), np.uint8).reshape(H, W0).astype(bool)
    mat0 = np.fromfile(os.path.join(PRE, 'ground_mat.bin'), np.uint8).reshape(H // CELL, W0 // CELL)

    D, N, cd, cn = collect()
    apply_seam_layers(D, cd)
    rd, rn = cd.result[1], cn.result[1]
    own_n = owners(N, cn, H)                                           # (H, OWN): the corner's pixels
    dwin = np.zeros((H, OWN), bool)
    dwin[DY:] = True
    own_d = dwin & ~own_n
    own_n &= np.arange(H)[:, None] < NW_Y1

    def place(full, nw_arr, d_arr, fill=None):
        """The two drafts' layers (window pixels) into a world-size array's west columns."""
        sub = full[:, :OWN]
        nh = min(NW_Y1, H)
        sub[:nh][own_n[:nh]] = nw_arr[:nh, :OWN][own_n[:nh]]
        dsub = sub[DY:]
        dsub[own_d[DY:]] = d_arr[:, :OWN][own_d[DY:]]

    # ---- ground, flowers, bend
    ground = grow(im['ground.png'], WEST_W)
    place(ground, np.clip(np.round(cn.ground), 0, 255).astype(np.uint8),
          np.clip(np.round(cd.ground), 0, 255).astype(np.uint8))
    # the village's swaying layer: its poppy heads (sway whole) under the recorded blades, flowers, reeds, irises;
    # in today's strip the old flowers stay (without the south-west reed belt the draft took out)
    heads = rd['heads']
    seam = rd['seam']
    old_bend = grow(im['bend.png'], WEST_W)[DY:]
    d_fl = heads.copy()
    d_bd = np.where(heads[..., 3] > 0, 255, 0).astype(np.uint8)
    d_bd[:, seam:OWN] = np.where(heads[:, seam:OWN, 3] > 0, old_bend[:, seam:OWN], 0)
    m = cd.sway[..., 3] > 0
    d_fl[m] = cd.sway[m]
    d_bd[m] = cd.sway_h[m]
    flowers = grow(im['flowers.png'], WEST_W)
    bend = grow(im['bend.png'], WEST_W)
    place(flowers, cn.sway, d_fl)
    place(bend, cn.sway_h, d_bd)
    mend_seam([ground, flowers, bend], WEST_W + 540, 1860, 2360, 24, 411)   # the Ostwald's west edge (gen_east, old)
    mend_seam([ground, flowers, bend], OWNW, 4400, H, 40, 412, True)        # the bottom shore: ours lies higher
    fill_reeds([ground, flowers, bend], OWNW, 4600, H, 24)                  # and its reed belt had a gap there

    # ---- sprites: today's (moved), the drafts' new ones, the village forest's copies of today's firs
    sd = os.path.join(OUT, 'sprites')
    os.makedirs(sd, exist_ok=True)
    for f in glob.glob(os.path.join(sd, 'w[0-9]*.png')):
        os.remove(f)
    w = shift_world(w0, WEST_W)
    w['sprites'] = [s for s in w['sprites'] if s['x'] > WEST_W + 2]  # the fir wall that stood at today's x 0
    new, blocked = [], np.zeros((H, W), bool)

    def owned(x, foot, which):
        if not (0 <= foot < H) or x >= OWN:
            return x >= OWN and which == 'd'
        return (own_n if which == 'n' else own_d)[foot, max(0, x)]

    for which, c, dy in (('n', cn, 0), ('d', cd, DY)):
        for sp in c.sprites:
            cx = sp['x'] + sp['w'] // 2
            foot = sp['foot'] + dy
            if not owned(cx, foot, which):
                continue
            new.append(dict(sp, y=sp['y'] + dy, foot=foot))
    for t in rd['forest']:                                             # today's edge firs planted over the village's forest
        cx, foot = t['x'] + WEST_W + t['w'] // 2, t['foot']
        if owned(cx, foot, 'd') and t['x'] + WEST_W >= 0:              # not out over the world's edge
            w['sprites'].append(dict(t, x=t['x'] + WEST_W))
            blocked[max(0, foot - 6):foot + 2, max(0, cx - 4):cx + 5] = True
    new.sort(key=lambda s: (s['foot'], s['x']))
    for n_, sp in enumerate(new):
        name = 'w%05d' % n_
        a = sp['rgba']
        Image.fromarray(a).save(os.path.join(sd, name + '.png'))
        w['sprites'].append(dict(name=name, x=int(sp['x']), y=int(sp['y']), w=int(sp['w']), h=int(a.shape[0]),
                                 foot=int(sp['foot']), frames=int(sp['frames']), fps=int(sp.get('fps', 8))))
        foot_block(sp, blocked)
        if type(sp['thing']).__name__ == 'Gewaechshaus':               # its door stays open: the way in (gen_glashaus)
            dx_, dy_ = sp['thing'].door()
            blocked[dy_ + DY - 12:dy_ + DY + 4, dx_ - 4:dx_ + 5] = False
    print('Westen:', len(new), 'neue Figuren', flush=True)

    # ---- flat things: masks per kind, in world pixels
    def wmask(name):
        out = np.zeros((H, W), bool)
        for c, dy, own in ((cn, 0, own_n), (cd, DY, own_d)):
            mk = c.masks.get(name)
            if mk is None:
                continue
            h = min(mk.shape[0], H - dy)
            sub = mk[:h, :OWN] & own[dy:dy + h]
            out[dy:dy + h, :OWN] |= sub
        return out

    # ---- water: the brook on from today's start brook (kind 1), the south brooks (2), the lake, pools, marsh (3)
    water = grow(im['water.png'], WEST_W)
    wv = np.zeros((H, OWNW, 4), np.uint8)
    dwin_ = slice(DY, H)
    bm = rd['brook'][:, :OWNW]
    bc = rd['brook_line']
    from scipy.spatial import cKDTree
    arc = np.r_[0, np.cumsum(np.hypot(*np.diff(bc, axis=0).T))]
    tang = np.gradient(bc, axis=0)
    yy, xx = np.nonzero(bm)
    d, i = cKDTree(bc).query(np.stack([xx, yy], 1))
    ang = np.arctan2(tang[i, 1], tang[i, 0])
    dep = np.clip(ndi.distance_transform_edt(ndi.binary_dilation(bm, iterations=2))[yy, xx] / 5.0, 0, 1)
    wv[DY + yy, xx] = np.stack([(ang / (2 * np.pi) % 1 * 256).astype(np.uint8), (dep * 255).astype(np.uint8),
                                (arc[i] % 256).astype(np.uint8), np.full(len(yy), KIND_OLD, np.uint8)], 1)
    sb = rd['sbo']
    sm = sb.mask[:, :OWNW]
    yy, xx = np.nonzero(sm)
    ang = np.arctan2(sb.flow[yy, xx, 1], sb.flow[yy, xx, 0])
    wv[DY + yy, xx] = np.stack([(ang / (2 * np.pi) % 1 * 256).astype(np.uint8), (sb.depth[yy, xx] * 255).astype(np.uint8),
                                (sb.along[yy, xx] % 256).astype(np.uint8), np.full(len(yy), KIND_BROOK, np.uint8)], 1)
    lk = rd['lk']['water'][:, :OWNW]
    still = lk & (wv[dwin_, :, 3] == 0)
    dep = np.clip(ndi.distance_transform_edt(rd['lk']['water'])[:, :OWNW] / 40.0, 0, 1)
    sub = wv[dwin_]
    sub[still, 1] = (dep[still] * 255).astype(np.uint8)
    sub[still, 3] = KIND_LAKE
    flat = np.zeros((H, W), bool)                                      # what lies on the water keeps still
    for k in LOW_H:
        flat |= wmask(k)
    wv[flat[:, :OWNW]] = 0
    wv[:, :OWNW][~own_d[:, :OWNW] & ~own_n[:, :OWNW]] = 0
    water[:, :OWNW] = wv
    wat = water[..., 3] > 0

    low = grow(im['low.png'], WEST_W)
    low[:, :OWNW] = 0
    for k, hgt in LOW_H.items():
        mk = wmask(k)
        mk[:, OWNW:] = False
        low[mk] = np.maximum(low[mk], hgt)

    # ---- open water, reflections, the lake map for the fish
    open_w = grow(im['open_water.png'], WEST_W)
    ow_new = wat[:, :OWNW] & (flowers[:, :OWNW, 3] == 0) & (low[:, :OWNW] == 0)
    open_w[:, :OWNW] = ow_new * 255
    refl = grow(im['refl.png'], WEST_W)
    refl[:, :OWNW] = 0
    sys.path.insert(0, os.path.join(HERE, 'south'))
    import reflect_map
    y0r = DY
    gu8 = ground[y0r:, :OWNW]
    sprs = [(s['rgba'][:, :s['w']], s['x'], s['y'] - y0r, s['foot'] - y0r) for s in new
            if s['frames'] == 1 and s['y'] + s['rgba'].shape[0] > y0r and s['x'] < OWNW]
    rr = reflect_map.bake(H - y0r, OWNW, ow_new[y0r:], flowers[y0r:, :OWNW], bend[y0r:, :OWNW], low[y0r:, :OWNW], gu8, sprs)
    mm = rr[..., 3] > 0
    refl[y0r:, :OWNW][mm] = rr[mm]
    lake = grow(im['lake.png'], WEST_W // 2)
    ld = np.where(water[..., 3] == KIND_LAKE, water[..., 1], 0).astype(np.uint8)
    ld = ld.reshape(H // 2, 2, W // 2, 2).min(axis=(1, 3))
    lake[:, :OWNW // 2] = ld[:, :OWNW // 2]

    # ---- where one can walk, on what
    walk = grow(walk0, WEST_W)
    xx_ = np.arange(W)[None, :]
    yy_ = np.arange(H)[:, None]
    deck = wmask('Steg') | wmask('Bruecke') | wmask('Brett') | wmask('Trittsteine')
    wn = ~wat & ~blocked
    nwp = np.zeros((H, W), bool)                                       # the corner: gorge, ridge, its rocks
    for key in ('gorge', 'ridge', 'flat_rock'):
        a = rn[key]
        nwp[:a.shape[0], :min(W, a.shape[1])] |= a[:, :min(W, a.shape[1])]
    nwp[:, OWN:] = False
    wn &= ~(nwp & np.pad(own_n, ((0, 0), (0, W - OWN))))
    wn |= deck & ~blocked
    wn &= xx_ >= 14                                                     # the world's west edge: the mist closes in
    wn &= yy_ >= 60
    walk[:, :OWNW] = wn[:, :OWNW]
    walk[:, OWNW:OWN] &= ~blocked[:, OWNW:OWN]
    st = w['start']
    lab, _ = ndi.label(walk, structure=np.ones((3, 3)))
    walk &= lab == lab[int(st['y']), int(st['x'])]
    print('Westen: begehbar', int(walk[:, :OWNW].sum()), 'px im Westen', flush=True)

    mat = np.zeros((H // CELL, W // CELL), np.uint8)
    mat[:, WEST_W // CELL:] = mat0
    mw = np.full((H, OWNW), GRASS, np.uint8)
    mw[np.pad(own_n, ((0, 0), (0, 0)))[:, :OWNW]] = SNOW
    pm = np.zeros((H, OWNW), bool)
    pm[DY:] = ndi.binary_dilation(rd['pathm'], iterations=1)[:, :OWNW]
    mw[pm & own_d[:, :OWNW]] = EARTH
    npth = np.zeros((H, OWNW), bool)
    npth[:NW_Y1] = rn['path'][:, :OWNW]
    mw[npth & own_n[:, :OWNW]] = EARTH
    for k in ('Platten', 'Treppe', 'VerschneitFlat', 'Trittsteine'):
        mw[wmask(k)[:, :OWNW]] = STONE
    mw[deck[:, :OWNW]] = WOOD
    mat[:, :OWNW // CELL] = mw[::CELL, ::CELL]
    mat[:, :OWNW // CELL][~walk[::CELL, :OWNW:CELL]] = GRASS

    # ---- the mist field: west edge, the bottom's fade, the top's wall; the bands over the lakes
    mist = grow(im['mist_fields.png'], WEST_W // 2)
    hw = OWNW // 2
    hy = (np.arange(H // 2)[:, None] * 2 + 1).astype(float)
    hx = (np.arange(hw)[None, :] * 2 + 1).astype(float)
    edge = 1 - smooth(hx / 48.0)
    bottom = np.clip((hy - 4690) / 110.0, 0, 1) ** 1.4 * 0.88
    top = np.zeros_like(hy)
    top[:30] = im['mist_fields.png'][:30, 20:21, 2] / 255.0
    lakes = np.zeros((H, OWNW))
    lakes[DY:] = (rd['lk']['water'] | ((rd['oldw'][..., 3] > 0) & (rd['gy'] > 3950)))[:, :OWNW]
    band = np.clip(ndi.gaussian_filter(lakes, 4) * 1.3, 0, 1)[::2, ::2]
    calm = ndi.gaussian_filter(lakes, 6)[::2, ::2]
    mist[:, :hw, 0] = np.round(band * 255).astype(np.uint8)
    mist[:, :hw, 1] = np.round(calm * 255).astype(np.uint8)
    mist[:, :hw, 2] = np.round(np.maximum(np.maximum(edge, bottom), top) * 255).astype(np.uint8)
    old_edge = mist[:, hw:hw + 30, 2].astype(float)                     # today's west edge had no wall: its columns
    mist[:, hw:hw + 30, 2] = np.round(np.maximum(old_edge * smooth(np.arange(30) / 30.0)[None, :],   # keep only
                                                 np.maximum(bottom, top))).astype(np.uint8)          # bottom and top

    # ---- the darkness field: the north-west wood and the village forest dark, the rest open
    grade = grow(im['grade_field.png'], WEST_W // 2)
    woodf = np.zeros((H, OWNW))
    woodf[:NW_Y1] = np.where(np.pad(own_n, ((0, 0), (0, 0)))[:NW_Y1, :OWNW], rn['wood'][:, :OWNW], 0)
    trees = np.zeros((H, OWNW))                                         # the wood's trees: firs, broadleaves, bamboo
    feet = [(s['foot'], s['x'] + s['w'] // 2) for s in w['sprites'] if s['name'].startswith('tanne') and s['x'] < OWNW]
    for sp in new:
        t_ = sp['thing']
        nm = type(t_).__name__
        if (nm == 'NwThing' and t_.item[1] == 'pine') or nm in ('Laubbaum', 'Bambus'):
            feet.append((sp['foot'], sp['x'] + sp['w'] // 2))
    for f_, cx in feet:
        if 0 <= f_ < H and 0 <= cx < OWNW:
            trees[f_, cx] = 1
    dens = ndi.gaussian_filter(trees, 14) * 900
    bam = np.zeros((H, OWNW), bool)
    bam[DY:] = rd['bamboo'][:, :OWNW]
    r = np.clip(np.maximum(np.clip((woodf - 0.45) / 0.3, 0, 1), np.clip(dens - 0.3, 0, 1)), 0, 1)
    r = np.maximum(r, ndi.gaussian_filter(bam.astype(float), 6) * 0.9)
    r = ndi.gaussian_filter(r, 10)[::2, ::2]
    old_r = grade[:, hw:hw + 1, 0] / 255.0                             # into today's own field over 40 px
    t = smooth((hx - (OWNW - 80)) / 80.0)
    grade[:, :hw, 0] = np.round(np.clip(r * (1 - t) + old_r * t, 0, 1) * 255).astype(np.uint8)
    grade[:, :hw, 1:] = 0
    deisland(grade, hw)

    # ---- world.json: the west's lights, brook sounds, places; the sounds' darkness per 20 px
    for l in rd['lights']:
        if l['x'] < WEST_W + 24:                                       # the draft adds today's lights after its own
            w['lights'].append(dict(l, x=float(l['x']), y=float(l['y'] + DY)))
    for l in rn['lights']:
        w['lights'].append(dict(l, x=float(l['x']), y=float(l['y'])))
    for p in bc[::8]:
        if p[0] < WEST_W:
            w['brook'].append({'x': float(p[0]), 'y': float(p[1] + DY)})
    for line, _, _ in rd['south_lines']:
        for p in line[::10]:
            if p[0] < WEST_W:
                w['brook'].append({'x': float(p[0]), 'y': float(p[1] + DY)})
    w['places'] = dict(w.get('places', {}), village=[D.SQUARE[0], D.SQUARE[1]], greenhouse=[D.GLASHAUS[0], D.GLASHAUS[1] + 4],
                       mill=[D.MILL[0], D.MILL[1]], hermitage=[N.HERMIT[0], N.HERMIT[1] + 40])
    f = grade[::MOOD_CELL // 2, ::MOOD_CELL // 2, 0]
    w['mood_w'] = int(f.shape[1])
    w['mood'] = [int(round(v / 255.0 * 100)) for v in f.ravel()]
    w['west_w'] = WEST_W

    # ---- files
    for name, a in (('ground.png', ground), ('flowers.png', flowers), ('bend.png', bend), ('water.png', water),
                    ('low.png', low), ('refl.png', refl), ('open_water.png', open_w), ('lake.png', lake),
                    ('mist_fields.png', mist), ('grade_field.png', grade)):
        Image.fromarray(a).save(os.path.join(OUT, name))
    Image.fromarray((walk * 255).astype(np.uint8)).save(os.path.join(OUT, 'walk.png'))
    walk.astype(np.uint8).tofile(os.path.join(OUT, 'walk.bin'))
    walk.reshape(H // CELL, CELL, W // CELL, CELL).all(axis=(1, 3)).astype(np.uint8).tofile(os.path.join(OUT, 'walk_cells.bin'))
    mat.tofile(os.path.join(OUT, 'ground_mat.bin'))
    with open(os.path.join(OUT, 'world.json'), 'w') as fh:
        json.dump(w, fh, indent=1)
    print('Westen: Welt', W, 'x', H, '-', len(w['sprites']), 'Figuren,', len(w['lights']), 'Lichter', flush=True)


def deisland(grade, hw):
    """As gen_north (Philip 2026-11-04): no light holes in the wood, no dark specks in the open smaller than a
    clearing, or he puts the lantern away and takes it out again a few steps on. The west's field turned into
    dark-or-not, cleaned, softened, and run into today's field over its last 40 half px."""
    from gen_north import ISLAND, island_free
    n = hw + 40
    r = grade[:, :n, 0] / 255.0
    dark = island_free(r > 0.45, ISLAND)
    new = ndi.gaussian_filter(dark.astype(float), 5) * 0.85
    t = smooth((np.arange(n)[None, :] - (hw - 40)) / 80.0)
    grade[:, :n, 0] = np.round(np.clip(new * (1 - t) + r * t, 0, 1) * 255).astype(np.uint8)


def mend_seam(arrs, xs, y0, y1, reach, seed, open_end=False):
    """A hard vertical seam at column xs over rows y0..y1 (Philip 0.18.0 found two on the map) closed in clumps: near
    it, pixels take their mirror image from the other side, more the closer they lie, fading out at both row ends.
    The same pixels move in every layer (ground, flowers, bend), so a blade keeps its height map."""
    rng = np.random.default_rng(seed)
    h = y1 - y0
    c = ndi.gaussian_filter(rng.normal(0, 1, (h, 2 * reach)), 3)
    c = 0.5 + 0.5 * c / (np.abs(c).max() + 1e-6)
    yy = np.arange(h)[:, None]
    fy = smooth((yy if open_end else np.minimum(yy, h - 1 - yy)) / 40.0)   # open_end: full to the last row
    dx = np.arange(2 * reach)[None, :] - reach + 0.5
    p = 0.5 * (1 - np.abs(dx) / reach) * fy
    jj, ii = np.nonzero(c < p)
    x = xs - reach + ii
    xm = 2 * xs - 1 - x
    for a in arrs:
        a[y0 + jj, x] = a[y0 + jj, xm].copy()


def fill_reeds(arrs, xs, y0, y1, reach):
    """Bare pixels in the reed belt round column xs (Philip 0.18.0: a gap in the reeds at the bottom) take the plant
    standing `reach` px to the side, the old world's first, with the ground under it."""
    fl = arrs[1]
    for x in range(xs - reach // 2, xs + reach // 2):
        for src in (x + reach, x - reach):
            take = (fl[y0:y1, x, 3] == 0) & (fl[y0:y1, src, 3] > 0)
            jj = np.nonzero(take)[0] + y0
            for a in arrs:
                a[jj, x] = a[jj, src]


def foot_block(sp, m):
    """Where a standing thing really stands (as gen_east): a tree's trunk, otherwise its lowest rows, a little thicker.
    Swaying things never get here; tall flowers and blades do not block."""
    t = sp['thing']
    name = type(t).__name__
    if name == 'NwThing':
        kind = t.item[1]
        if kind == 'pine':
            x, y = t.item[2][0], t.item[2][1]
            m[max(0, y - 2):y + 2, max(0, x - 2):x + 3] = True
            return
        name = 'rock'
    if name in TRUNK:
        hw, up, dn = TRUNK[name]
        cx, f = int(t.x), sp['foot']
        m[max(0, f - up):f + dn + 1, max(0, cx - hw):cx + hw + 1] = True
        return
    if name in ('Hortensie', 'Korb', 'Leiter', 'Kerzen', 'Ranke', 'MillWater'):
        return                                                         # small or nothing to bump into
    rows = FOOT_ROWS.get(name, 3)
    a = sp['rgba'][:, :sp['w'], 3] > 0
    j0 = max(0, sp['foot'] - sp['y'] - rows)
    j1 = min(a.shape[0], sp['foot'] - sp['y'] + 2)
    if j1 <= j0:
        return
    sub = ndi.binary_dilation(a[j0:j1], iterations=1)
    ys, xs = np.nonzero(sub)
    py, px = sp['y'] + j0 + ys, sp['x'] + xs
    ok = (py >= 0) & (py < m.shape[0]) & (px >= 0) & (px < m.shape[1])
    m[py[ok], px[ok]] = True


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--save-pre':
        save_pre()
    else:
        main()
