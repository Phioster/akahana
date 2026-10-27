#!/usr/bin/env python3
"""The whole map from the game's data with its life in it at one moment: the birds on their spots, the
fireflies, fish under the lake's surface and a few ducks - as the game would show them, for looking at.

    python3 tools/world/south/life_map.py OUT_DIR
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import fish_anim  # noqa: E402
import mood_map  # noqa: E402
import objects_lake as ol  # noqa: E402
import preview_game as pg  # noqa: E402
import water_anim  # noqa: E402
import zone2_draft as z2  # noqa: E402
import zone4_draft as z4  # noqa: E402
from fireflies import Swarm  # noqa: E402

ROOT = pg.ROOT
A = pg.A


def main(out):
    with open(os.path.join(A, 'world.json')) as f:
        w = json.load(f)
    rng = np.random.default_rng(3)
    img, walk = pg.from_chunks(w)
    wmap = np.array(Image.open(os.path.join(ROOT, 'build', 'world_full', 'water.png')))
    img = water_anim.animate(img, wmap, 0, 0, 2.0)               # the water at a moment, as the shader moves it
    lake = (wmap[..., 3] == 3) & (wmap[..., 1] > 80)
    ys, xs = np.nonzero(lake)
    fishes = [fish_anim.Fish((xs[k], ys[k]), rng) for k in rng.integers(len(ys), size=9)]
    fish_anim.draw(img, 0, 0, (wmap[..., 3] == 3) & (wmap[..., 1] > 25), fishes, 2.0)
    G = np.random.default_rng(3).random(img.shape[:2])
    for k in rng.integers(len(ys), size=3):                     # three little groups of ducks
        ol.Enten(int(xs[k]), int(ys[k]), int(rng.integers(2, 4)), int(rng.integers(0, 99))).draw(img, G)
    for b in w['birds']:                                         # the birds on their spots, first frame
        kind = 'amsel' if b.get('snow') else ['spatz', 'spatz', 'amsel', 'rotkehl'][int(rng.integers(4))]
        sheet = np.array(Image.open(os.path.join(ROOT, 'assets', 'life', f'vogel_{kind}.png')).convert('RGBA'))
        for _ in range(int(rng.integers(1, 4))):
            fr = sheet[:, 8 * int(rng.integers(2)):8 * int(rng.integers(2)) + 8]
            x, y = int(b['x'] + rng.integers(-10, 11)) - 4, int(b['y'] + rng.integers(-6, 7)) - 7
            sub = img[y:y + 8, x:x + 8]
            m = fr[:sub.shape[0], :sub.shape[1], 3] > 0
            sub[m] = fr[:sub.shape[0], :sub.shape[1], :3][m]
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
    a = np.clip(a * (1 - e) + z4.MIST * e, 0, 255).astype(np.uint8)
    Image.fromarray(a).save(os.path.join(out, 'karte_leben_1x.png'))
    print('ok', a.shape, flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
