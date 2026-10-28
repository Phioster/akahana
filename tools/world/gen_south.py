#!/usr/bin/env python3
"""The world grows south and east: the approved zone drafts and the placeholder east wood are put
together with the old map (whose picture stays as it is) into the generator's whole-world images, which
split_chunks.py then cuts as before. Run after gen_world.py (make_world.sh does).

In:  build/world_old/{ground,flowers}.png, walk.bin, ground_mat.bin  (gen_world's old map, moved there by
     make_world.sh) and build/world_old/world_old.json (its world.json)
Out: assets/world/{ground,flowers}.png, walk.bin, walk_cells.bin, ground_mat.bin, sprites/s*.png,
     world.json (grown, merged)
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
sys.path[:0] = [os.path.join(HERE, 'south'), os.path.join(HERE, 'lib'), HERE]
import east_wood  # noqa: E402
import layers  # noqa: E402
import reflect_map  # noqa: E402
import zone1_draft as z1  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
FULL = os.path.join(ROOT, 'build', 'world_old')
OUT = os.path.join(ROOT, 'assets', 'world')
W, H = 900, 3600
OW, OH = z1.OLD_W, z1.OLD_H
TOP = OH - z1.CTX                     # the south canvas starts at this world row
SEAM = 1190                           # from here down the old map's closed bottom edge gives way
CELL = 2
GRASS, EARTH, STONE, WOOD, SNOW, WET = range(6)   # GroundMat
FRAMES, FPS = 64, 8


def old_world():
    with open(os.path.join(FULL, 'world_old.json')) as f:
        w = json.load(f)
    g = np.array(Image.open(os.path.join(FULL, 'ground.png')).convert('RGB'))
    fl = np.array(Image.open(os.path.join(FULL, 'flowers.png')).convert('RGBA'))
    walk = np.fromfile(os.path.join(FULL, 'walk.bin'), np.uint8).reshape(OH, OW).astype(bool)
    mat = np.fromfile(os.path.join(FULL, 'ground_mat.bin'), np.uint8).reshape(OH // CELL, OW // CELL)
    return w, g, fl, walk, mat


def kept_old_sprites(sprites):
    """The old edge firs at its east and south border go: zone 1 draws the southern ones whole again,
    the east wood's fringe stands where the eastern ones were."""
    return [s for s in sprites if not (s['name'].startswith('tanne') and
                                       (s['x'] + s['w'] >= OW or s['y'] + s['h'] >= OH))]


def fringe_sprites(fringe, ground):
    """The east wood's seam firs, cut out like gen_world cuts its sprites (drawn on the ground they stand on)."""
    out = []
    for f in fringe:
        h = f.p.h
        x0, y0 = max(0, f.p.x - h), max(0, f.p.y - h - 4)
        x1, y1 = min(W, f.p.x + h), min(H, f.p.y + h // 3 + 2)
        base = ground[y0:y1, x0:x1].astype(float)
        im = base.copy()
        z1.Fir(f.p.x - x0, f.p.y - y0, h, f.p.seed, snow=f.snow).draw(im)
        a = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        a[..., :3] = np.clip(im, 0, 255).astype(np.uint8)
        a[..., 3] = (np.abs(im - base).sum(-1) > 0.5) * 255
        out.append(dict(rgba=a, x=x0, y=y0, foot=f.p.y, frames=1, w=x1 - x0, h=y1 - y0, thing=f, draft=False))
    return out


YY, XX = np.mgrid[0:H, 0:W]


def _rect(m, x0, y0, x1, y1):
    m[max(0, int(y0)):max(0, int(y1) + 1), max(0, int(x0)):max(0, int(x1) + 1)] = True


def _ell(m, cx, cy, rx, ry):
    y0, y1, x0, x1 = int(cy - ry - 1), int(cy + ry + 2), int(cx - rx - 1), int(cx + rx + 2)
    sub = m[max(0, y0):y1, max(0, x0):x1]
    yy, xx = YY[max(0, y0):y1, max(0, x0):x1], XX[max(0, y0):y1, max(0, x0):x1]
    sub |= ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1


def _line(m, pts, half, dy=0):
    pts = np.array(pts, float)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        n = int(max(abs(bx - ax), abs(by - ay))) + 1
        for t in np.linspace(0, 1, n):
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t + dy
            _rect(m, x - half, y - half, x + half, y + half)


def solid(t, m, dy, spr=None):
    """Where a standing thing really stands on the ground: the trunk, the post, the wall's foot - never its
    crown, light pool, shadow or the petals round it. Drawn into m; dy moves draft rows to world rows."""
    import objects_lake as ol
    import objects_south as os_
    import objects_water as ow
    import zone2_draft as z2
    import zone3_draft as z3
    n = type(t).__name__
    if isinstance(t, z1.Fir):
        x, y = t.p.x, t.p.y + dy
        _rect(m, x - 3, y - 3, x + 3, y + 1)
        return
    x, y = getattr(t, 'x', 0), getattr(t, 'y', 0) + dy
    if isinstance(t, (ol.Laubbaum, os_.Kirschbaum, ow.Weide)):
        _rect(m, x - 4, y - 3, x + 5, y + 1)                   # the trunk; you walk under the crown
    elif isinstance(t, ol.Huette):
        x0 = x - t.W_ // 2
        _rect(m, x0 - 2, y - 24, x0 + t.W_ + 5, y + 1)        # the walls and the depth of the house
    elif isinstance(t, z2.Bank):
        _rect(m, x - 10, y - 4, x + 11, y + 1)
    elif isinstance(t, z2.Steinlaterne):
        _rect(m, x - 5, y - 5, x + 6, y + 1)
    elif isinstance(t, (z3.Holzlaterne, os_.Fackel, os_.Vogelscheuche)):
        _rect(m, x - 2, y - 3, x + 3, y + 1)                   # a post
    elif isinstance(t, os_.Wegstein):
        _rect(m, x - t.w // 2, y - 4, x + t.w // 2, y + 1)
    elif isinstance(t, os_.Findling):
        _ell(m, x, y - t.r * 0.35, t.r, t.r * 0.55)
    elif isinstance(t, os_.Steinhaufen):
        _ell(m, x + 1, y - 3, 8, 4)
    elif isinstance(t, os_.Baumstumpf):
        _ell(m, x, y - 2, t.r + 1, (t.r + 1) * 0.6)
    elif isinstance(t, os_.Stamm):
        _line(m, [t.a, t.b], t.r - 1, dy)
    elif isinstance(t, (os_.Mauer, os_.Zaun)) and spr is not None:   # only where stones were drawn: it is a ruin
        a = spr['rgba'][:, :spr['w'], 3] > 0
        for i in range(a.shape[1]):                            # standing stones only: three or more on top of
            col = a[:, i]                                      # each other; loose crumbs on the ground don't block
            for j in range(len(col) - 1, 1, -1):
                if col[j] and col[j - 1] and col[j - 2]:
                    _rect(m, spr['x'] + i, spr['y'] + j - 3, spr['x'] + i, spr['y'] + j)
                    break
    elif isinstance(t, os_.Karren):
        _rect(m, x - 16, y - 6, x + 10, y + 1)
    # ducks, birds, candles: nothing to bump into


def fix_old_blocks(walk, sprites):
    """The old map's own objects as gen_world blocked them, mended: a lantern blocked its whole light pool
    as a bar (now only its post), the ruin's wall pieces get their foot blocked wherever drawn."""
    for s in sprites:
        nm, f = s['name'], s['foot']
        x0, x1 = s['x'], s['x'] + s['w']
        if 'laterne' in nm:
            walk[max(0, f - 6):f + 2, x0 + 3:x1 - 3] = True        # gen_world's bar, on open meadow
            cx = x0 + s['w'] // 2
            if nm == 'steinlaterne' or nm == 'laterne_huette':
                walk[f - 5:f + 2, cx - 5:cx + 7] = False
            else:
                walk[f - 3:f + 2, cx - 2:cx + 4] = False
        elif nm == 'zelt':                                     # the canvas, not the shadow beside it
            walk[f - 6:f + 3, x0 + 3:x1 - 3] = True
            walk[1092:1101, 248:268] = False
        elif nm == 'baum':                                     # the big cherry: gen_world's square sat right of and
            tx, ty = s['x'], s['y']                            # above the trunk's foot; now the foot as drawn
            walk[ty + 150:ty + 174, tx + 88:tx + 112] = True
            walk[ty + 160:ty + 173, tx + 87:tx + 109] = False
        elif nm.startswith('ruine'):
            a = np.array(Image.open(os.path.join(OUT, 'sprites', nm + '.png')).convert('RGBA'))[:, :s['w']]
            lo = max(0, f - s['y'] - 3)
            ys, xs = np.nonzero(a[lo:f - s['y'] + 1, :, 3] > 0)
            walk[s['y'] + lo + ys, x0 + xs] = False
            walk[np.clip(s['y'] + lo + ys + 1, 0, H - 1), x0 + xs] = False   # a little thicker: no slipping through


OLD_WAT = [(0x3c, 0x46, 0x50), (0x4e, 0x5a, 0x65), (0x64, 0x71, 0x7c), (0x7f, 0x8c, 0x96), (0xa3, 0xae, 0xb6),
           (0xd6, 0xdd, 0xe1)]                                 # gen_world's brook
KIND_OLD, KIND_BROOK, KIND_LAKE = 1, 2, 3
MOUTH = 14                                                     # px: how far from the lake a brook mouth blends and can be waded
WATER_K = 2 * np.pi * 22 / 256                                 # streak frequency along the stream: whole periods in
OLD_K = 2 * np.pi * 61 / 256                                   # the 256 px the along channel wraps at, so no seam


def _is(ground, pal):
    m = np.zeros(ground.shape[:2], bool)
    for c in pal:
        m |= (ground == np.array(c, np.uint8)).all(-1)
    return m


def water_map(ground, w, c, m):
    """Where water is and how it moves, per pixel, for the water shader (RGBA8):
    R flow direction (angle / 2pi * 256), G depth 0..1, B distance along the stream mod 256 px, A kind
    (1 old brook, 2 new brook, 3 lake and pools). Only pixels still painted in a water colour: bridges,
    stones, lily pads, the lake floor showing through, shadows keep still."""
    import objects_water as ow
    out = np.zeros((H, W, 4), np.uint8)
    # the old brook: its pixels by colour, its course from world.json's points along it
    old = _is(ground[:TOP, :OW], OLD_WAT)
    pts = np.array([(p['x'], p['y']) for p in w['brook'] if p['y'] < TOP and p['x'] < OW], float)
    pts = pts[np.argsort(pts[:, 0])]                           # it runs from west to east across the map
    xs = np.arange(pts[0, 0], pts[-1, 0], 0.5)
    ys = np.interp(xs, pts[:, 0], pts[:, 1])
    arc = np.r_[0, np.cumsum(np.hypot(np.diff(xs), np.diff(ys)))]
    from scipy.spatial import cKDTree
    yy, xx = np.nonzero(old)
    d, i = cKDTree(np.stack([xs, ys], 1)).query(np.stack([xx, yy], 1))
    tang = np.stack([np.gradient(xs), np.gradient(ys)], 1)
    ang = np.arctan2(tang[i, 1], tang[i, 0])
    dep = np.clip(ndi.distance_transform_edt(ndi.binary_dilation(old, iterations=2))[yy, xx] / 5.0, 0, 1)
    out[yy, xx] = np.stack([(ang / (2 * np.pi) % 1 * 256).astype(np.uint8), (dep * 255).astype(np.uint8),
                            (arc[i] % 256).astype(np.uint8), np.full(len(yy), KIND_OLD, np.uint8)], 1)
    # the new brooks: depth, flow and distance along exactly as the drafts drew them
    wat = _is(ground, [tuple(int(v) for v in col) for col in ow.WATER])
    for b in c.brooks:
        y0 = TOP + b.y0
        sel = b.mask & wat[y0:y0 + b.H, :b.W] & ~m['lake'][y0:y0 + b.H, :b.W]   # in the lake it is still water
        yy, xx = np.nonzero(sel)
        ang = np.arctan2(b.flow[yy, xx, 1], b.flow[yy, xx, 0])
        out[y0 + yy, xx] = np.stack([(ang / (2 * np.pi) % 1 * 256).astype(np.uint8),
                                     (b.depth[yy, xx] * 255).astype(np.uint8),
                                     (b.along[yy, xx] % 256).astype(np.uint8),
                                     np.full(len(yy), KIND_BROOK, np.uint8)], 1)
    # the lake, the backwater, the pools and the marsh: still water, its depth as paint_lake had it
    lake = m['lake'] & wat & (out[..., 3] == 0)
    dep = np.clip(ndi.distance_transform_edt(m['lake']) / 40.0, 0, 1)
    out[lake, 1] = (dep[lake] * 255).astype(np.uint8)
    out[lake, 3] = KIND_LAKE
    # where a brook runs out into the lake there is no hard edge (0.8.1): within MOUTH px of the lake a brook
    # pixel turns into lake water by chance, more and more towards the lake, and the depth is blended across
    # the mouth (the lake's rim is light, the brook's middle dark: that was the line)
    d_lake = ndi.distance_transform_edt(~m['lake'])
    mouth_b = (out[..., 3] == KIND_BROOK) & (d_lake < MOUTH)
    near_b = ndi.binary_dilation(out[..., 3] == KIND_BROOK, iterations=MOUTH) & (out[..., 3] == KIND_LAKE)
    region = mouth_b | near_b
    wgt = region.astype(float)
    smooth = ndi.gaussian_filter(out[..., 1].astype(float) * wgt, 4) / np.maximum(ndi.gaussian_filter(wgt, 4), 1e-3)
    out[region, 1] = np.clip(smooth[region], 0, 255).astype(np.uint8)
    yy, xx = np.nonzero(mouth_b)
    chance = 1.0 - d_lake[yy, xx] / MOUTH
    hsh = (np.sin(xx * 12.9898 + yy * 78.233) * 43758.5453) % 1.0
    out[yy[hsh < chance], xx[hsh < chance], 3] = KIND_LAKE
    return out


# how far each flat thing stands above the water, + 1 (0 in low.png = nothing): the jetty and bridges stand
# on posts, stones, lily pads, the boat and driftwood lie in it (their reflection starts right at their edge)
LOW_H = {'Steg': 3, 'Bruecke': 4, 'Brett': 2, 'Boot': 1, 'Trittsteine': 1, 'WasserStein': 1, 'Treibholz': 1,
         'Seerosen': 1}


def main():
    w, og, ofl, owalk, omat = old_world()
    with layers.collect() as c:
        pass
    eg, eh, fringe = east_wood.render()
    EH = east_wood.H

    ground = np.zeros((H, W, 3), np.uint8)
    ground[:TOP, :OW] = og[:TOP]
    ground[:TOP, OW:] = np.clip(eg[:TOP], 0, 255).astype(np.uint8)
    ground[TOP:] = np.clip(c.ground, 0, 255).astype(np.uint8)
    p = np.linspace(1, 0, EH - TOP)[:, None] ** 1.2             # the east wood's floor gives way to zone 1's
    take = np.random.default_rng(9).random((EH - TOP, W - OW)) < p   # pixel by pixel: no line between them
    band = ground[TOP:EH, OW:]
    band[take] = np.clip(eg[TOP:], 0, 255).astype(np.uint8)[take]
    flowers = np.zeros((H, W, 4), np.uint8)
    flowers[:TOP, :OW] = ofl[:TOP]
    flowers[:TOP, OW:] = eh[:TOP]
    flowers[TOP:] = c.sway
    bend = np.zeros((H, W), np.uint8)                          # height above the plant's foot (255: sways whole)
    bend[flowers[..., 3] > 0] = 255
    bend[TOP:] = c.sway_h

    # ---------------------------------------------------------------- sprites
    for f in glob.glob(os.path.join(OUT, 'sprites', 's[0-9]*.png')):
        os.remove(f)                                           # last run's south sprites
    sprites = kept_old_sprites(w['sprites'])
    new = [dict(s, y=s['y'] + TOP, foot=s['foot'] + TOP) for s in c.sprites]
    new += fringe_sprites(fringe, ground)
    blocked = np.zeros((H, W), bool)
    for n, s in enumerate(sorted(new, key=lambda s: (s['foot'], s['x']))):
        name = f's{n}'
        Image.fromarray(s['rgba']).save(os.path.join(OUT, 'sprites', name + '.png'))
        sprites.append(dict(name=name, x=int(s['x']), y=int(s['y']), w=int(s['w']), h=int(s['rgba'].shape[0]),
                            foot=int(s['foot']), frames=int(s['frames']), fps=FPS))
        if 'thing' in s:
            solid(s['thing'], blocked, TOP if s.get('draft', True) else 0, s)

    # ---------------------------------------------------------------- where one can walk, and on what
    m = {k: np.zeros((H, W), bool) for k in ('path', 'brook', 'lake', 'shallow', 'Bruecke', 'Brett', 'Steg',
                                             'Trittsteine', 'Quelle')}
    for k, v in c.masks.items():
        if k in m:
            m[k][TOP:TOP + v.shape[0]] = v[:H - TOP]
    # how high the flat things drawn into the ground stand over the water, for their reflections
    low = np.zeros((H, W), np.uint8)
    for k, v in c.masks.items():
        hgt = LOW_H.get(k, 0)
        if hgt:
            part = np.zeros((H, W), bool)
            part[TOP:TOP + v.shape[0]] = v[:H - TOP]
            low[part] = np.maximum(low[part], hgt)
    Image.fromarray(low).save(os.path.join(OUT, 'low.png'))
    stones = m['Trittsteine']
    ford = ndi.binary_dilation(stones, iterations=3) & m['brook']   # between the stones: wade, as the old ford
    mouths = m['brook'] & (ndi.distance_transform_edt(~m['lake']) < MOUTH)   # where it runs out: shallow, wade
    ford |= mouths                                             # (0.8.1: round the lake without the bridge)
    wood = m['Bruecke'] | m['Brett'] | m['Steg']
    deep = m['lake'] & ~m['shallow']
    fog = np.zeros((H, W))
    fog[TOP:] = c.edge_fog
    walk = np.ones((H, W), bool)
    walk &= ~(m['brook'] | deep | m['Quelle'] | blocked)
    walk |= wood | stones | ford
    walk &= fog < 0.3                                          # into the mist at the edges: no further
    walk[:, :10] = walk[:, W - 10:] = False
    yy, xx = np.mgrid[TOP:TOP + z1.CTX + 60, 0:W]               # zone 1's wood beside the camp: closed, too
    walk[TOP:TOP + z1.CTX + 60] &= z1.in_forest(xx, yy - TOP) < -2
    walk[H - 10:] = False
    walk[:TOP, OW - 10:] = False                                # the east wood, as the old map's edge was
    walk[:SEAM, :OW] = owalk[:SEAM]                            # the old map as it was, its bottom edge opened
    walk[:SEAM, OW - 10:OW] = False
    fix_old_blocks(walk, [s for s in sprites if not re.fullmatch(r's\d+', s['name'])])

    lab, _ = ndi.label(walk, structure=np.ones((3, 3)))        # islands nobody can reach are not ground to
    st = w['start']                                            # walk on: a tap there would find no way
    walk &= lab == lab[int(st['y']), int(st['x'])]

    mat = np.full((H, W), GRASS, np.uint8)
    mat[m['path']] = EARTH
    mat[m['shallow'] | ford] = WET
    mat[stones] = STONE
    mat[wood] = WOOD
    cells_mat = mat[::CELL, ::CELL].copy()
    cells_mat[:SEAM // CELL, :OW // CELL] = omat[:SEAM // CELL]

    # ---------------------------------------------------------------- the index
    lights = list(w['lights']) + [dict(l, y=l['y'] + TOP) for l in c.lights[len(w['lights']):]]
    brook = list(w.get('brook', []))
    for b in c.brooks:                                         # points along the new water, for its sound
        ys, xs = np.nonzero(b.depth > 0.85)
        for k in range(0, len(ys), 45):
            brook.append({'x': float(xs[k]), 'y': float(ys[k] + b.y0 + TOP)})
    flies = [dict(x=float(s.x), y=float(s.y + TOP), flies=[{k: round(float(v), 4) for k, v in f.items()}
                                                          for f in s.flies]) for s in c.swarms]
    birds = list(w.get('birds', []))
    rng = np.random.default_rng(5)
    open_ = walk & (mat == GRASS)
    open_[:TOP] = False
    for _ in range(4000):
        x, y = int(rng.integers(30, W - 30)), int(rng.integers(TOP + 40, H - 120))
        if open_[y - 6:y + 7, x - 6:x + 7].all() and all(abs(x - b['x']) + abs(y - b['y']) > 120 for b in birds):
            birds.append({'x': x, 'y': y, 'snow': False})
        if len(birds) >= len(w.get('birds', [])) + 16:
            break

    fields = np.zeros((3, H, W), np.float32)                   # the mist's own maps, for the preview and the
    fields[0, TOP:] = c.band                                   # mist shader: water band, calm lake, edge fog
    fields[1, TOP:] = c.calm
    fields[2, TOP:] = c.edge_fog
    np.savez_compressed(os.path.join(ROOT, 'build', 'mist_fields.npz'), band=fields[0], calm=fields[1],
                        edge=fields[2])
    half = fields.reshape(3, H // 2, 2, W // 2, 2).mean(axis=(2, 4))   # the game's copy: half size, it is soft
    Image.fromarray((np.clip(half, 0, 1).transpose(1, 2, 0) * 255).round().astype(np.uint8)).save(
        os.path.join(OUT, 'mist_fields.png'))
    Image.fromarray(water_map(ground, w, c, m)).save(os.path.join(OUT, 'water.png'))
    Image.fromarray(bend).save(os.path.join(OUT, 'bend.png'))
    wm = water_map(ground, w, c, m)                            # where fish and ducks may be: the lake's depth,
    lake = np.where(wm[..., 3] == 3, wm[..., 1], 0)            # half size (shipped, read by scenes/lake_life.gd)
    lake = lake.reshape(H // 2, 2, W // 2, 2).min(axis=(1, 3))
    standing = []                                              # what stands still by the water, mirrored once
    for s_ in sprites:
        pic = np.array(Image.open(os.path.join(OUT, 'sprites', s_['name'] + '.png')).convert('RGBA'))[:, :s_['w']]
        standing.append((pic, s_['x'], s_['y'], s_['foot']))
    open_water = (wm[..., 3] > 0) & (flowers[..., 3] == 0) & (low == 0)
    Image.fromarray((open_water * 255).astype(np.uint8)).save(os.path.join(OUT, 'open_water.png'))   # for the
    lake_open = open_water & (wm[..., 3] == 3)                 # wanderer's reflection (shaders/reflection)                 # a lantern by the lake: its light's path on the
    lamp_paths = []                                            # water starts where the open water really does
    for l in lights:
        i, j0 = int(l['x']), int(l['y'])
        col = lake_open[j0:j0 + 70, i] if 0 <= i < W and 0 <= j0 < H else np.zeros(0, bool)
        if len(col) >= 4:
            run = np.convolve(col, np.ones(4), 'valid') == 4
            if run.any():
                lamp_paths.append(dict(x=i, y=j0 + int(np.argmax(run))))
    w['lamp_paths'] = lamp_paths
    Image.fromarray(reflect_map.bake(H, W, open_water, flowers, bend, low, ground, standing)).save(
        os.path.join(OUT, 'refl.png'))
    Image.fromarray(lake.astype(np.uint8)).save(os.path.join(OUT, 'lake.png'))
    Image.fromarray(ground).save(os.path.join(OUT, 'ground.png'))
    Image.fromarray(flowers).save(os.path.join(OUT, 'flowers.png'))
    Image.fromarray((walk * 255).astype(np.uint8)).save(os.path.join(OUT, 'walk.png'))
    walk.astype(np.uint8).tofile(os.path.join(OUT, 'walk.bin'))
    walk.reshape(H // CELL, CELL, W // CELL, CELL).all(axis=(1, 3)).astype(np.uint8).tofile(
        os.path.join(OUT, 'walk_cells.bin'))
    cells_mat.tofile(os.path.join(OUT, 'ground_mat.bin'))
    w.update(width=W, height=H, sprites=sprites, lights=lights, brook=brook, birds=birds, fireflies=flies)
    with open(os.path.join(OUT, 'world.json'), 'w') as f:
        json.dump(w, f, indent=1)
    print('ok', len(sprites), 'sprites,', len(lights), 'lights,', len(flies), 'swarms', flush=True)


if __name__ == '__main__':
    main()
