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
SHEET_MAX = 8192                      # widest sprite sheet (GPU textures: 16384 on this phone, 8192/4096 on older ones;
                                      # Fable 2026-11-08: the mill wheel's 288 frames were 25632 px, never drawn)
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
    sd_dir = sd
    os.makedirs(sd, exist_ok=True)
    for f in glob.glob(os.path.join(sd, 'w[0-9]*.png')) + glob.glob(os.path.join(sd, 'wb[0-9]*.png')) \
            + glob.glob(os.path.join(sd, 'wt[0-9]*.png')):
        os.remove(f)
    w = shift_world(w0, WEST_W)
    w['sprites'] = [s for s in w['sprites'] if s['x'] > WEST_W + 2]  # the fir wall that stood at today's x 0
    for s in w['sprites']:                                             # Fable: Ostwald trees cut at gen_east's window
        if s['foot'] > s['y'] + s['h'] and s.get('frames', 1) == 1:    # edges kept the whole tree's foot below their
            s['foot'] = s['y'] + s['h'] - 1                            # picture: he stood in the gap, the crown over him
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
        if sp['foot'] >= sp['y'] + a.shape[0]:                         # foot below the picture (the mill's water sorts
            a = np.concatenate([a, np.zeros((sp['foot'] - sp['y'] - a.shape[0] + 1,) + a.shape[1:], a.dtype)], 0)   # with the house): pad
        fr, sw = int(sp['frames']), int(sp['w'])
        cols = min(fr, SHEET_MAX // sw)
        if cols < fr:                                                   # several rows, row-major (Sprite2D vframes)
            rows = -(-fr // cols)
            sheet = np.zeros((rows * a.shape[0], cols * sw, 4), a.dtype)
            for k in range(fr):
                sheet[(k // cols) * a.shape[0]:(k // cols + 1) * a.shape[0], (k % cols) * sw:(k % cols + 1) * sw] = a[:, k * sw:(k + 1) * sw]
            Image.fromarray(sheet).save(os.path.join(sd, name + '.png'))
        else:
            Image.fromarray(a).save(os.path.join(sd, name + '.png'))
        ent = dict(name=name, x=int(sp['x']), y=int(sp['y']), w=sw, h=int(a.shape[0]),
                   foot=int(sp['foot']), frames=fr, fps=int(sp.get('fps', 8)))
        if cols < fr:
            ent['cols'] = int(cols)
        w['sprites'].append(ent)
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
    oc = water[:, OWNW]                                                 # today's brook where it leaves the seam
    orow = np.nonzero(oc[:, 3] == KIND_OLD)[0]
    along = arc[i]
    if len(orow):
        r0 = int(np.median(orow))
        k0 = int(np.hypot(bc[:, 0] - OWNW, bc[:, 1] - (r0 - DY)).argmin())
        d_old = (int(water[r0, OWNW + 4, 2]) - int(water[r0, OWNW, 2]) + 128) % 256 - 128
        d_new = 1 if k0 > len(bc) // 2 else -1                          # does our arc grow towards the seam?
        if (d_old > 0) != (d_new > 0):
            along = -along
            a_seam = -arc[k0]
        else:
            a_seam = arc[k0]
        along = along + (float(np.mean(oc[orow, 2])) - a_seam)          # the streaks go on without a jump
        g_old = float(np.mean(oc[orow, 1])) / 255.0
        tg = smooth((xx - (OWNW - 16)) / 16.0)
        dep = dep * (1 - tg) + g_old * tg
    wv[DY + yy, xx] = np.stack([(ang / (2 * np.pi) % 1 * 256).astype(np.uint8), (dep * 255).astype(np.uint8),
                                (np.round(along) % 256).astype(np.uint8), np.full(len(yy), KIND_OLD, np.uint8)], 1)
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
    kind = water[..., 3].reshape(H // CELL, CELL, W // CELL, CELL)
    moving = ((kind == KIND_OLD) | (kind == KIND_BROOK)).all(axis=(1, 3))
    wet_walk = moving & (mat == GRASS) & walk.reshape(H // CELL, CELL, W // CELL, CELL).any(axis=(1, 3))
    if wet_walk.any():                                                  # Fable: he walked in that brook
        print('Westen: Bachzellen gesperrt', int(wet_walk.sum()), flush=True)
        walk &= ~np.kron(wet_walk, np.ones((CELL, CELL), bool))
        lab, _ = ndi.label(walk, structure=np.ones((3, 3)))
        walk &= lab == lab[int(st['y']), int(st['x'])]

    # ---- the Ostwald's west edge (Philip 0.18.2): its bare floor strip and the pale clearing get trees from next door,
    # the clearing's ground darkens to the wood floor, the old lantern there loses the meadow it was cut with
    cbox = (WEST_W + 500, 1920, WEST_W + 820, 2090)
    cm = wood_clearing(ground, cbox)
    grown = edge_wood(w['sprites'], w['lights'], ground, walk, mat, (WEST_W + 430, 1800, WEST_W + 570, 2300))
    grown += edge_wood(w['sprites'] + grown, w['lights'], ground, walk, mat, cbox, seed=433, where=cm)
    for t in grown:                                                     # their trunks block, as today's trees do
        cx, f = t['x'] + t['w'] // 2, t['foot']
        walk[max(0, f - 3):f + 1, max(0, cx - 3):cx + 4] = False
    w['sprites'] += grown
    lab, _ = ndi.label(walk, structure=np.ones((3, 3)))
    walk &= lab == lab[int(st['y']), int(st['x'])]
    mat[~walk.reshape(H // CELL, CELL, W // CELL, CELL).any(axis=(1, 3)) & (mat == EARTH)] = GRASS
    strip_meadow(os.path.join(OUT, 'sprites', 'laterne_ost.png'))
    print('Westen: Ostwald-Rand', len(grown), 'Bäume', flush=True)

    # ---- old boats in both lakes (Philip's girlfriend 2026-11-08, approved): rafts and wrecks lie flat in the water
    # (their dry part stops the water's motion), boats on the bank stand as sprites with the grass laid down round them
    import lake_boats as LB
    import objects_lake as ol
    boxes = [(s['x'], s['y'], s['x'] + s['w'], s['foot']) for s in w['sprites']]
    boats = LB.place(water[..., 3], walk, mat, boxes, flowers[..., 3] > 0)
    Gb = np.random.default_rng(3).random((H, W))
    gf = ground.astype(float)
    nb = 0
    for kind, bx, by, ang, bs in boats:
        if kind in ('floss', 'wrack'):
            t = ol.Floss(bx, by, ang=ang, L=28, seed=bs) if kind == 'floss' else ol.Wrack(bx, by, ang=ang, L=30, seed=bs)
            t.draw(gf, Gb)
            dry = t.dry(H, W)
            water[dry] = 0
            open_w[dry] = 0
            refl[dry] = 0
            low[dry] = np.maximum(low[dry], 1)
            continue
        t = ol.UferBoot(bx, by, ang=ang * 0.4, seed=bs)
        LB.flatten(flowers, bend, water[..., 3], bx, by, t.L, bs)
        b0 = t.box()
        w['sprites'] = [q for q in w['sprites'] if not (q['h'] < 24 and q['x'] < b0[2] + 4 and q['x'] + q['w'] > b0[0] - 4
                                                        and b0[1] - 6 < q['foot'] < b0[3] + 6)]   # small reeds at it
        x0b, y0b, x1b, y1b = b0[0] - 2, b0[1] - 8, b0[2] + 22, b0[3] + 4
        tl = ol.UferBoot(bx - x0b, by - y0b, ang=ang * 0.4, seed=bs)     # drawn on a small canvas
        gl = Gb[y0b:y1b, x0b:x1b]
        canv = []
        for bg in (0.0, 255.0):                                         # alike on black and on white = the boat itself
            c = np.full((y1b - y0b, x1b - x0b, 3), bg)
            tl.draw(c, gl)
            canv.append(c)
        alpha = np.all(np.abs(canv[0] - canv[1]) < 1, axis=2)
        t.draw(gf, Gb)                                                  # its shade stays on the ground
        rgba = np.zeros((y1b - y0b, x1b - x0b, 4), np.uint8)
        rgba[alpha, :3] = np.clip(canv[0][alpha], 0, 255).astype(np.uint8)
        rgba[alpha, 3] = 255
        name = 'wb%03d' % nb
        nb += 1
        Image.fromarray(rgba).save(os.path.join(sd_dir, name + '.png'))
        w['sprites'].append(dict(name=name, x=int(x0b), y=int(y0b), w=int(x1b - x0b), h=int(y1b - y0b),
                                 foot=int(by + 1), frames=1, fps=8))
        walk[by - 8:by + 2, bx - t.L // 2 + 2:bx + t.L // 2 - 1] = False
    print('Westen: Boote', len(boats), flush=True)

    # ---- more broadleaf and cherry trees in the open meadows (Philip and his girlfriend 2026-11-08, approved):
    # sprites like the rest; only their shade and fallen petals go into the ground (the canopy cutout shows it)
    import more_trees as MT
    import objects_south as osu
    boxes = [(q['x'], q['y'], q['x'] + q['w'], q['foot'], q['name']) for q in w['sprites']]
    trees = MT.place(water[..., 3], walk, mat, boxes, start=(w['start']['x'], w['start']['y']))
    for nt, (kind, tx, ty, ts, form) in enumerate(trees):
        mk = (lambda X, Y: osu.Kirschbaum(X, Y, seed=ts, **form)) if kind == 'kirsch' else \
             (lambda X, Y: ol.Laubbaum(X, Y, seed=ts, **form))
        b0 = mk(tx, ty).box()
        x0b, y0b = max(0, b0[0] - 8), max(0, b0[1] - 8)
        x1b, y1b = min(W, b0[2] + 8), min(H, b0[3] + 6)
        tl = mk(tx - x0b, ty - y0b)
        gl = Gb[y0b:y1b, x0b:x1b]
        canv = []
        for bg in (0.0, 255.0):                                         # alike on black and on white = the tree
            c = np.full((y1b - y0b, x1b - x0b, 3), bg)
            tl.draw(c, gl)
            canv.append(c)
        alpha = np.all(np.abs(canv[0] - canv[1]) < 1, axis=2)
        alpha[ty - y0b + 2:] = False                                    # petals and roots below the foot: ground
        onground = gf[y0b:y1b, x0b:x1b].copy()
        tl.draw(onground, gl)
        sub = gf[y0b:y1b, x0b:x1b]
        sub[~alpha] = onground[~alpha]                                  # shade and petals, not the tree itself
        rgba = np.zeros((y1b - y0b, x1b - x0b, 4), np.uint8)
        rgba[alpha, :3] = np.clip(canv[0][alpha], 0, 255).astype(np.uint8)
        rgba[alpha, 3] = 255
        ys = np.nonzero(alpha.any(1))[0]
        xs = np.nonzero(alpha.any(0))[0]
        rgba = rgba[ys[0]:ys[-1] + 1, xs[0]:xs[-1] + 1]
        name = 'wt%03d' % nt
        Image.fromarray(rgba).save(os.path.join(sd_dir, name + '.png'))
        w['sprites'].append(dict(name=name, x=int(x0b + xs[0]), y=int(y0b + ys[0]), w=int(rgba.shape[1]),
                                 h=int(rgba.shape[0]), foot=int(ty + 1), frames=1, fps=8))
        walk[ty - 3:ty + 2, tx - 3:tx + 4] = False                       # the trunk
    ground[:] = np.clip(np.round(gf), 0, 255).astype(np.uint8)
    print('Westen: neue Baeume', len(trees), flush=True)

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
    brk = np.zeros((H, OWNW))                                           # the brooks get their band too (today's old brook
    brk[DY:] = (rd['brook'] | rd['sbo'].mask)[:, :OWNW]                 # had one; Fable: it broke off at the seam)
    band = np.clip(ndi.gaussian_filter(np.maximum(lakes, brk), 4) * 1.3, 0, 1)[::2, ::2]
    oldr = mist[:, hw:hw + 1, 0] / 255.0                                # into today's band over the last 12 half px
    t4 = smooth((np.arange(hw)[None, :] - (hw - 12)) / 12.0)
    band = band * (1 - t4) + np.maximum(band, oldr) * t4
    calm = ndi.gaussian_filter(lakes, 6)[::2, ::2]
    mist[:, :hw, 0] = np.round(band * 255).astype(np.uint8)
    mist[:, :hw, 1] = np.round(calm * 255).astype(np.uint8)
    mist[:, :hw, 2] = np.round(np.maximum(np.maximum(edge, bottom), top) * 255).astype(np.uint8)
    old_edge = mist[:, hw:hw + 30, 2].astype(float)                     # today's west edge had no wall: its columns
    mist[:, hw:hw + 30, 2] = np.round(np.maximum(old_edge * smooth(np.arange(30) / 30.0)[None, :],   # keep only
                                                 np.maximum(bottom, top) * 255)).astype(np.uint8)    # bottom and top

    a0, a1 = (WEST_W + 824) // 2 - 16, (WEST_W + 824) // 2 + 16          # Fable: the south's 0.88 against the east's 1.0
    t5 = smooth(np.arange(a1 - a0) / float(a1 - a0 - 1))[None, :]
    low5 = mist[H // 2 - 40:, a0, 2:3].astype(float)
    high5 = mist[H // 2 - 40:, a1, 2:3].astype(float)
    mist[H // 2 - 40:, a0:a1, 2] = np.round(low5 * (1 - t5) + high5 * t5).astype(np.uint8)

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


def edge_wood(sprites, lights, ground, walk, mat, box, seed=421, where=None):
    """Trees for a bare strip of wood floor (Philip 0.18.2: the Ostwald's floor ran west past its trees, between the
    poppies and the wood only dark ground): copies of the trees standing right next to it, thinning out where the
    floor turns to meadow. Paths, their lanes, lights and other feet keep their room. -> new sprite entries"""
    x0, y0, x1, y1 = box
    rng = np.random.default_rng(seed)
    near = [s for s in sprites if s.get('frames', 1) == 1 and s['h'] > 40 and s['name'].startswith(('e', 'tanne'))
            and x1 <= s['x'] + s['w'] // 2 < x1 + 260 and y0 <= s['foot'] < y1]
    tpl = []
    for s in near:
        with Image.open(os.path.join(OUT, 'sprites', s['name'] + '.png')) as im:
            a = np.array(im)[..., 3] > 0
        if not (a[:, 0].any() or a[:, -1].any() or a[0].any() or a[-1].any()):
            tpl.append(s)
    if not tpl:
        return []
    g = ground[y0:y1, x0:x1].astype(float).mean(2)
    floor = ndi.gaussian_filter((g < 80).astype(float), 6) > 0.5 if where is None else where   # the dark wood floor
    fdist = ndi.distance_transform_edt(floor)                            # how deep into it
    path = np.kron(mat[y0 // CELL:y1 // CELL, x0 // CELL:x1 // CELL] == EARTH, np.ones((CELL, CELL), bool))
    path = ndi.binary_dilation(path, iterations=6)
    keep = path.copy()
    for d in range(2, 44, 2):                                            # a crown reaches ~45 px above its foot
        keep[d:] |= path[:-d]
    taken = np.zeros_like(keep)
    for l in lights:                                                     # a lamp stays in its clearing
        lx, ly = int(l['x']) - x0, int(l['y']) - y0
        if -30 <= lx < x1 - x0 + 30 and -30 <= ly < y1 - y0 + 50:
            yy_, xx_ = np.ogrid[:y1 - y0, :x1 - x0]
            taken |= (xx_ - lx) ** 2 + ((yy_ - ly - 14) / 1.6) ** 2 < 26 ** 2
            py, px = np.nonzero(path)                                    # and lanes on to the nearest path each side
            for side in (px < lx, px > lx):
                if not side.any():
                    continue
                cand = np.nonzero(side)[0]
                k = cand[int(np.argmin((px[cand] - lx) ** 2 + (py[cand] - ly) ** 2))]
                n_ = int(np.hypot(px[k] - lx, py[k] - ly)) + 1
                for t_ in np.linspace(0, 1, n_):
                    cx_, cy_ = int(lx + (px[k] - lx) * t_), int(ly + 14 + (py[k] - ly - 14) * t_)
                    taken[max(0, cy_ - 8):max(0, cy_ + 44), max(0, cx_ - 9):max(0, cx_ + 10)] = True
    for s in sprites:
        fx, fy = s['x'] + s['w'] // 2 - x0, s['foot'] - y0
        if 0 <= fx < x1 - x0 and 0 <= fy < y1 - y0:
            taken[max(0, fy - 10):fy + 6, max(0, fx - 9):fx + 10] = True
    out = []
    for fy in range(8, y1 - y0 - 4, 11):
        for fx in range(6, x1 - x0 - 6, 13):
            x_, y_ = fx + int(rng.integers(-5, 6)), fy + int(rng.integers(-4, 5))
            if not (0 <= x_ < x1 - x0 and 0 <= y_ < y1 - y0) or not floor[y_, x_] or keep[y_, x_] or taken[y_, x_]:
                continue
            if not walk[y_ + y0, x_ + x0] or rng.random() > 0.25 + 0.6 * smooth(fdist[y_, x_] / 30.0):
                continue
            t = tpl[int(rng.integers(0, len(tpl)))]
            fo = t['foot'] - t['y']
            out.append(dict(t, x=int(x_ + x0 - t['w'] // 2), y=int(y_ + y0 - fo), foot=int(y_ + y0)))
            taken[max(0, y_ - 10):y_ + 6, max(0, x_ - 9):x_ + 10] = True
    return out


def wood_clearing(ground, box, seed=431):
    """A pale bare clearing inside the dark wood (Philip 0.18.2: "too empty"): its light ground darkened towards the
    wood floor round it, in clumps. -> the clearing's mask (box pixels), where edge_wood then plants."""
    x0, y0, x1, y1 = box
    g = ground[y0:y1, x0:x1].astype(float)
    m = ndi.binary_opening(ndi.gaussian_filter(g.mean(2), 3) > 92, iterations=2)
    m = ndi.binary_dilation(m, iterations=3)
    dark = g[~ndi.binary_dilation(m, iterations=8)]
    floor = np.median(dark.reshape(-1, 3), 0) if len(dark) else np.array([60.0, 66, 62])
    rng = np.random.default_rng(seed)
    c = ndi.gaussian_filter(rng.random(m.shape), 2)
    k = (0.55 + 0.35 * (c - c.min()) / (np.ptp(c) + 1e-6)) * ndi.gaussian_filter(m.astype(float), 2)
    g = g * (1 - k[..., None]) + (floor * (g.mean(2, keepdims=True) / max(1.0, g.mean())) ** 0.0 * 1.0) * k[..., None] \
        + (g - g.mean(2, keepdims=True)) * 0.35 * k[..., None]               # keep a little of its grain
    ground[y0:y1, x0:x1] = np.clip(g, 0, 255).astype(ground.dtype)
    return m


def strip_meadow(path_png):
    """An old lantern sprite (gen_world's laterne_ost) carries a disc of meadow round its lamp and a stone pad: on the
    Ostwald's dark floor it shows as a pale patch (Philip 0.18.2). Keep the post, the lamp and its flame only."""
    a = np.array(Image.open(path_png).convert('RGBA'))
    rgb = a[..., :3].astype(int)
    sat = rgb.max(2) - rgb.min(2)
    pale = (rgb.mean(2) > 110) & (sat < 60)
    a[pale, 3] = 0
    Image.fromarray(a).save(path_png)


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
