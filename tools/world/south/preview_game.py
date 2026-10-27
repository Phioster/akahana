#!/usr/bin/env python3
"""The map as the game has it: put back together from the chunks and the sprites in world.json (not from
the drafts), graded like the approved drafts. Also a picture of where one can walk.

    python3 tools/world/south/preview_game.py OUT_DIR
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import mood_map  # noqa: E402
import zone2_draft as z2  # noqa: E402
import zone4_draft as z4  # noqa: E402
from fireflies import Swarm  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
A = os.path.join(ROOT, 'assets', 'world')


def from_chunks(w):
    cw, ch = w['chunk']
    cols, rows = w['chunks']
    ap = w['apron']
    H, W = rows * ch, cols * cw
    img = np.zeros((H, W, 3))
    walk = np.zeros((H // 2, W // 2), bool)
    for cy in range(rows):
        for cx in range(cols):
            b = os.path.join(A, 'chunks', f'c_{cx}_{cy}_')
            g = np.array(Image.open(b + 'ground.png').convert('RGB')).astype(float)
            f = np.array(Image.open(b + 'flowers.png').convert('RGBA'))[ap:ap + ch, ap:ap + cw]
            m = f[..., 3] > 0
            g[m] = f[m][:, :3]
            img[cy * ch:(cy + 1) * ch, cx * cw:(cx + 1) * cw] = g
            walk[cy * ch // 2:(cy + 1) * ch // 2, cx * cw // 2:(cx + 1) * cw // 2] = np.fromfile(
                b + 'cells.bin', np.uint8).reshape(ch // 2, cw // 2)
    for s in sorted(w['sprites'], key=lambda s: s['foot']):
        a = np.array(Image.open(os.path.join(A, 'sprites', s['name'] + '.png')).convert('RGBA'))[:, :s['w']]
        sub = img[s['y']:s['y'] + a.shape[0], s['x']:s['x'] + a.shape[1]]
        k = a[:sub.shape[0], :sub.shape[1], 3] > 0
        sub[k] = a[:sub.shape[0], :sub.shape[1], :3][k]
    return img, walk


def main(out):
    with open(os.path.join(A, 'world.json')) as f:
        w = json.load(f)
    img, walk = from_chunks(w)
    fl = np.load(os.path.join(ROOT, 'build', 'mist_fields.npz'))
    swarms = []
    for s in w.get('fireflies', []):
        sw = Swarm(s['x'], s['y'], 0)
        sw.flies = s['flies']
        swarms.append(sw)
    lit = dict(w, lights=w['lights'] + [l for s in swarms for l in s.lights(2.0)])
    a = mood_map.mood(img, lit, 2.0, grass_mist=z2.GRASS_MIST, water_band=fl['band'], calm=fl['calm']).astype(float)
    for s in swarms:
        s.draw(a, 2.0)
    e = fl['edge'][..., None]
    a = a * (1 - e) + z4.MIST * e
    a = np.clip(a, 0, 255).astype(np.uint8)
    Image.fromarray(a).save(os.path.join(out, 'spiel_1x.png'))
    wf = np.repeat(np.repeat(walk, 2, 0), 2, 1)
    v = a.astype(float) * 0.55
    v[~wf] = v[~wf] * 0.45 + np.array([150, 40, 40]) * 0.55
    Image.fromarray(v.astype(np.uint8)).save(os.path.join(out, 'begehbar_1x.png'))
    print('ok', a.shape, flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
