#!/usr/bin/env python3
"""Grows the finished world (after gen_east) by NORTH_H rows on top: the north, Yukimine-toge.

Everything that was there moves down by NORTH_H, pixel for pixel: every full-size map gets the north's rows
above it, every coordinate in world.json moves (sprites, lights, start, brook, birds, wisps, fireflies,
lamp paths, fire, places; mood gets rows). Half-size maps (lake, mist, grade) grow by NORTH_H / 2.

In:  build/world_pre_north/ (the world as gen_east left it, copied there by the pipeline, so this step can run
     alone: ground, flowers, bend, water, low, refl, walk.png, walk.bin, walk_cells.bin, ground_mat.bin,
     open_water, lake, mist_fields, grade_field, world.json)
Out: the same names in assets/world (then split_chunks cuts them).
"""
import json
import os
import shutil
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
PRE = os.path.join(ROOT, 'build', 'world_pre_north')
OUT = os.path.join(ROOT, 'assets', 'world')
NORTH_H = 1200                       # 6 chunk rows; north coordinates: today's y 0 = NORTH_H
CELL = 2
SNOW = 4                             # GroundMat
MOOD_CELL = 20

FULL = ['ground.png', 'flowers.png', 'bend.png', 'water.png', 'low.png', 'refl.png', 'walk.png', 'open_water.png']
HALF = ['lake.png', 'mist_fields.png', 'grade_field.png']
BINS = {'walk.bin': 1, 'walk_cells.bin': CELL, 'ground_mat.bin': CELL}
MOVED = ['ground.png', 'flowers.png', 'bend.png', 'water.png', 'low.png', 'refl.png', 'walk.png', 'walk.bin',
         'walk_cells.bin', 'ground_mat.bin']          # these the pipeline moves out of assets after split_chunks


def save_pre(src=OUT):
    """Keeps the world as gen_east left it, so gen_north can run again on its own."""
    os.makedirs(PRE, exist_ok=True)
    for n in FULL + HALF + list(BINS) + ['world.json']:
        shutil.copy(os.path.join(src, n), os.path.join(PRE, n))


def shift_world(w, dy):
    """Every coordinate in world.json moves down by dy."""
    w = dict(w)
    w['height'] = w['height'] + dy
    w['start'] = dict(w['start'], y=w['start']['y'] + dy)
    w['sprites'] = [dict(s, y=s['y'] + dy, foot=s['foot'] + dy) for s in w['sprites']]
    w['lights'] = [dict(l, y=l['y'] + dy) for l in w['lights']]
    for k in ('brook', 'birds', 'wisps', 'lamp_paths', 'fireflies'):
        w[k] = [dict(p, y=p['y'] + dy) for p in w.get(k, [])]
    if w.get('fire'):
        w['fire'] = dict(w['fire'], y=w['fire']['y'] + dy)
    w['places'] = {k: [v[0], v[1] + dy] for k, v in w.get('places', {}).items()}
    if w.get('mood'):
        rows = dy // MOOD_CELL
        w['mood'] = [0] * (rows * w['mood_w']) + list(w['mood'])
    return w


ISLAND = 2500                         # half-size px (about 100 x 100 world px): smaller light or dark patches go


def island_free(dark, least):
    """dark with every light hole and every dark speck smaller than `least` filled in by its surroundings."""
    from scipy import ndimage as ndi
    out = dark.copy()
    for want in (False, True):
        lab, k = ndi.label(out == want)
        if not k:
            continue
        size = np.bincount(lab.ravel())
        edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]).tolist())
        small = [i for i in range(1, k + 1) if size[i] < least and i not in edge]
        out[np.isin(lab, small)] = not want
    return out


def grow(a, top):
    return np.concatenate([top, a], 0)


def main():
    if not os.path.exists(os.path.join(PRE, 'world.json')):
        sys.exit('build/world_pre_north fehlt: erst gen_east laufen lassen (make_world.sh speichert sie)')
    sys.path.insert(0, os.path.join(HERE, 'north'))
    import north_world as NW
    w = json.load(open(os.path.join(PRE, 'world.json')))
    W, H = w['width'], w['height']
    im = {k: np.array(Image.open(os.path.join(PRE, k))) for k in FULL + HALF}
    walk = np.fromfile(os.path.join(PRE, 'walk.bin'), np.uint8).reshape(H, W).astype(bool)
    mat = np.fromfile(os.path.join(PRE, 'ground_mat.bin'), np.uint8).reshape(H // CELL, W // CELL)
    n = NW.build(dict(ground=im['ground.png'], sprites=w['sprites']), W)
    O = NW.OLD
    ov = slice(0, O)                                                 # today's rows the north reaches into
    nov = slice(NORTH_H, NORTH_H + O)
    rep = n.replaced[nov]

    ground = im['ground.png'].copy()
    ground[ov] = np.clip(n.ground[nov], 0, 255).astype(np.uint8)
    out = {'ground.png': grow(ground, np.clip(n.ground[:NORTH_H], 0, 255).astype(np.uint8))}
    for k in ('flowers.png', 'bend.png', 'low.png', 'refl.png'):     # nothing sways, nothing mirrors up there yet
        a = im[k].copy()
        a[ov][rep] = 0
        out[k] = grow(a, np.zeros((NORTH_H,) + a.shape[1:], a.dtype))
    wat = im['water.png'].copy()
    new = n.water[nov, :, 3] > 0
    wat[ov][new] = n.water[nov][new]
    out['water.png'] = grow(wat, n.water[:NORTH_H])
    ow = im['open_water.png'].copy()
    ow[ov][n.open_water[nov]] = 255
    out['open_water.png'] = grow(ow, (n.open_water[:NORTH_H] * 255).astype(np.uint8))

    # walking: today's rows keep theirs, the north's new blockers added; its closed top rim (Kogarashi's cliff,
    # the wood's rim) opens as the mirror of the rows below it
    jj = np.arange(O)[:, None]
    axis = np.where(np.arange(W)[None, :] < NW.KOGA_X, NW.CLIFF, NW.RIM)
    src_row = np.where(jj < axis, 2 * axis - jj, jj).clip(0, H - 1)
    old_w = walk[src_row, np.arange(W)[None, :]]
    for s in w['sprites']:                                           # trees taken away free their trunk again
        if id(s) in n.drop and 0 <= s['foot'] < O:
            cx = s['x'] + s['w'] // 2
            old_w[max(0, s['foot'] - 3):s['foot'] + 2, max(0, cx - 4):cx + 5] = True
    walk2 = walk.copy()
    walk2[ov] = old_w & n.walk[nov]
    walk2 = grow(walk2, n.walk[:NORTH_H])
    from scipy import ndimage as ndi
    lab, _ = ndi.label(walk2, structure=np.ones((3, 3)))           # islands nobody can reach are no ground
    st = w['start']
    walk2 &= lab == lab[int(st['y']) + NORTH_H, int(st['x'])]
    out['walk.png'] = (walk2 * 255).astype(np.uint8)

    mat2 = mat.copy()
    jc = np.arange(O // CELL)[:, None]
    ac = axis[:, ::CELL] // CELL
    mat2[:O // CELL] = mat[np.where(jc < ac, 2 * ac - jc, jc), np.arange(W // CELL)[None, :]]
    nm = n.mat[::CELL, ::CELL]
    newp = (nm[NORTH_H // CELL:] == NW.EARTH)
    mat2[:O // CELL][newp] = NW.EARTH
    mat2 = grow(mat2, nm[:NORTH_H // CELL])

    for name, a in out.items():
        Image.fromarray(a).save(os.path.join(OUT, name))
    # the north's darkness (step 4): deep in the dense needle wood it is dark enough for the lantern, the snow
    # and the pass stay light; towards today's top it runs into today's own field (the Ostwald dark, Kogarashi light)
    # Philip 2026-11-04: little light holes in the wood made him put the lantern away and take it out again a few
    # steps on. So: broad, then every light island smaller than a clearing is filled dark and every dark speck
    # in the open taken out, then softened again.
    wd = ndi.gaussian_filter(n.wood[:NORTH_H:2, ::2], 18)
    dark = wd > 0.56                                                 # only the dense wood (zone 1: about 0.8; the open slopes 0.5)
    dark = island_free(dark, ISLAND)
    r = ndi.gaussian_filter(dark.astype(float), 5) * 0.85
    gy = np.arange(NORTH_H // 2)[:, None] * 2.0
    t = np.clip((gy - (NORTH_H - 300)) / 300.0, 0, 1)
    t = t * t * (3 - 2 * t)
    old_r = im['grade_field.png'][:1, :, 0] / 255.0
    r = r * (1 - t) + np.maximum(r, old_r) * t
    north_grade = np.zeros((NORTH_H // 2, W // 2, 3), np.uint8)
    north_grade[..., 0] = np.round(r * 255).astype(np.uint8)
    for name in HALF:
        a = im[name]
        top = np.zeros((NORTH_H // 2,) + a.shape[1:], a.dtype)
        if name == 'mist_fields.png':
            # B is the mist wall at the world's edge: the old one along today's top moves up to the new top,
            # the one along the east edge runs on up (taking today's top row on (0.11.0) made a wall 1200 px high)
            a = a.copy()
            side = a[100:101, :, 2]                                  # the east edge's wall, from a row away from the top
            prof = a[:30, 450, 2].astype(float)[:, None]             # the top wall's fall-off
            a[:30, :, 2] = side                                      # today's top: no wall any more
            top[..., 2] = side
            top[:30, :, 2] = np.maximum(side, prof).astype(np.uint8)
        if name == 'grade_field.png':
            top = north_grade
        Image.fromarray(grow(a, top)).save(os.path.join(OUT, name))
    walk2.astype(np.uint8).tofile(os.path.join(OUT, 'walk.bin'))
    walk2.reshape(-1, CELL, W // CELL, CELL).all(axis=(1, 3)).astype(np.uint8).tofile(os.path.join(OUT, 'walk_cells.bin'))
    mat2.tofile(os.path.join(OUT, 'ground_mat.bin'))

    keep = [s for s in w['sprites'] if id(s) not in n.drop]
    w['sprites'] = keep
    w = shift_world(w, NORTH_H)
    if w.get('mood'):                                                # the sounds' darkness per 20 px, the north's rows too
        rows = NORTH_H // MOOD_CELL
        nm_ = [int(round(v * 100)) for v in r[::MOOD_CELL // 2, ::MOOD_CELL // 2][:rows].ravel()]
        w['mood'] = nm_ + w['mood'][rows * w['mood_w']:]
    sd = os.path.join(OUT, 'sprites')
    for f in os.listdir(sd):                                         # the north's sprites of a former run
        if f.startswith('n') and f.endswith('.png'):
            os.remove(os.path.join(sd, f))
    new_sprites = []
    for i, sp in enumerate(n.sprites):
        name = 'n%04d' % i
        Image.fromarray(sp['rgba']).save(os.path.join(sd, name + '.png'))
        new_sprites.append(dict(name=name, x=int(sp['x']), y=int(sp['y']), w=int(sp['w']), h=int(sp['h']),
                                foot=int(sp['foot']), frames=int(sp['frames']), fps=int(sp.get('fps', w['fps']))))
    for c in n.copies:
        new_sprites.append(dict(name=c['name'], x=int(c['x']), y=int(c['y']), w=int(c['w']), h=int(c['h']),
                                foot=int(c['foot']), frames=int(c['frames']), fps=int(c.get('fps', w['fps']))))
    w['sprites'] += new_sprites
    w['lights'] += [dict(l, x=float(l['x']), y=float(l['y'])) for l in n.lights]
    w['north_h'] = NORTH_H
    with open(os.path.join(OUT, 'world.json'), 'w') as f:
        json.dump(w, f, indent=1)
    print('Norden: Welt', W, 'x', w['height'], '-', len(n.sprites), 'Figuren,', len(n.copies), 'Ostwaldbaeume,',
          len(n.drop), 'alte entfernt')


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--save-pre':
        save_pre()
    else:
        main()
