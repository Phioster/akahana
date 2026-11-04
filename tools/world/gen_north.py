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


class North:
    """What the north puts on top: full-size layers of NORTH_H rows (step 1: a closed snowfield)."""
    def __init__(s, W):
        rng = np.random.default_rng(61)
        H = NORTH_H
        s.W = W
        g = np.where((rng.random((H, W)) < 0.6)[..., None], np.array([232, 228, 220]), np.array([214, 212, 210]))
        s.ground = g.astype(np.uint8)
        s.walk = np.zeros((H, W), bool)
        s.mat = np.full((H // CELL, W // CELL), SNOW, np.uint8)
        s.sprites, s.lights = [], []
        s.mood = np.zeros((H // MOOD_CELL, W // MOOD_CELL), np.uint8)


def grow(a, top):
    return np.concatenate([top, a], 0)


def main():
    if not os.path.exists(os.path.join(PRE, 'world.json')):
        sys.exit('build/world_pre_north fehlt: erst gen_east laufen lassen (make_world.sh speichert sie)')
    w = json.load(open(os.path.join(PRE, 'world.json')))
    W, H = w['width'], w['height']
    n = North(W)
    for name in FULL:
        a = np.array(Image.open(os.path.join(PRE, name)))
        if name == 'ground.png':
            top = n.ground
        else:
            top = np.zeros((NORTH_H,) + a.shape[1:], a.dtype)
        if name == 'walk.png':
            top = (n.walk * 255).astype(np.uint8)
        Image.fromarray(grow(a, top)).save(os.path.join(OUT, name))
    for name in HALF:
        a = np.array(Image.open(os.path.join(PRE, name)))
        top = np.zeros((NORTH_H // 2,) + a.shape[1:], a.dtype)
        if name == 'mist_fields.png':
            top[:] = a[:1]                                       # the old top row's mist, carried up
        Image.fromarray(grow(a, top)).save(os.path.join(OUT, name))
    for name, cell in BINS.items():
        a = np.fromfile(os.path.join(PRE, name), np.uint8).reshape(H // cell, W // cell)
        if name == 'walk.bin':
            top = n.walk.astype(np.uint8)
        elif name == 'walk_cells.bin':
            top = n.walk.reshape(NORTH_H // CELL, CELL, W // CELL, CELL).all(axis=(1, 3)).astype(np.uint8)
        else:
            top = n.mat
        grow(a, top).tofile(os.path.join(OUT, name))
    w = shift_world(w, NORTH_H)
    if w.get('mood'):
        w['mood'] = [int(v) for v in n.mood.ravel()] + w['mood'][NORTH_H // MOOD_CELL * w['mood_w']:]
    w['sprites'] += n.sprites
    w['lights'] += n.lights
    w['north_h'] = NORTH_H
    with open(os.path.join(OUT, 'world.json'), 'w') as f:
        json.dump(w, f, indent=1)
    print('Norden: Welt', W, 'x', w['height'])


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--save-pre':
        save_pre()
    else:
        main()
