"""Quick look at a window of the generated world: ground, flowers, sprites (frame 0), the walkable area outlined.
python3 look_world.py OUTDIR x0 y0 x1 y1 out.png [scale]"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def main(d, x0, y0, x1, y1, out, scale=2):
    g = np.array(Image.open(os.path.join(d, 'ground.png')).convert('RGB'))[y0:y1, x0:x1].astype(float)
    fl = np.array(Image.open(os.path.join(d, 'flowers.png')).convert('RGBA'))[y0:y1, x0:x1]
    m = fl[..., 3] > 0
    g[m] = fl[m][:, :3]
    w = json.load(open(os.path.join(d, 'world.json')))
    for s in sorted(w['sprites'], key=lambda s: s['foot']):
        if s['x'] + s['w'] < x0 or s['x'] > x1 or s['y'] + s['h'] < y0 or s['y'] > y1:
            continue
        p = os.path.join(d, 'sprites', s['name'] + '.png')
        if not os.path.exists(p):
            p = os.path.join(ROOT, 'assets', 'world', 'sprites', s['name'] + '.png')
        if not os.path.exists(p):
            continue
        a = np.array(Image.open(p).convert('RGBA'))[:, :s['w']]
        for j in range(a.shape[0]):
            yy = s['y'] + j - y0
            if not 0 <= yy < y1 - y0:
                continue
            row = a[j]
            xs = np.nonzero(row[:, 3] > 0)[0]
            xs = xs[(s['x'] + xs - x0 >= 0) & (s['x'] + xs - x0 < x1 - x0)]
            g[yy, s['x'] + xs - x0] = row[xs, :3]
    walk = np.array(Image.open(os.path.join(d, 'walk.png')).convert('L'))[y0:y1, x0:x1] > 0
    edge = walk & ~ndi.binary_erosion(walk)
    g[edge] = g[edge] * 0.5 + np.array([255, 60, 60]) * 0.5
    g = g * 0.8
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    a = sys.argv
    main(a[1], *map(int, a[2:6]), a[6], int(a[7]) if len(a) > 7 else 2)
