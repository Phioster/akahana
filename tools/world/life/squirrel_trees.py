#!/usr/bin/env python3
"""Where the squirrels live: every broadleaf tree in world.json with its trunk (middle x, foot y) and the lower
edge of its crown, where a climbing squirrel vanishes. Found from the pictures: a narrow trunk under a much
wider crown that is not cherry pink. Fir trees ('tanne') and the camp's cherry ('baum') are left out.
Run after every world regen (it only reads):  python3 tools/world/life/squirrel_trees.py
Out: assets/world/squirrel_trees.json  [[trunk_x, foot_y, crown_y], ...]
"""
import json
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
A = os.path.join(ROOT, 'assets', 'world')


def trunk(a):
    """(x middle, foot row, crown row) of a tree picture's alpha, or None when it is not a trunk under a crown"""
    rows = np.nonzero(a.any(1))[0]
    if len(rows) == 0:
        return None
    y = rows[-1]
    xs = np.nonzero(a[y])[0]
    if xs.max() - xs.min() > 9:
        return None
    width, foot = xs.max() - xs.min() + 1, y
    while y > 0 and a[y].sum() <= width + 3:
        y -= 1
    if foot - y < 5 or a[:y + 1].any(0).sum() < width * 3:
        return None
    return int(xs.mean()), int(foot), int(y + 1)


def is_cherry(rgb):
    r, g, b = rgb.mean(0)
    return r > g + 25 and b > g


def find(world):
    out = []
    for s in world['sprites']:
        if s['h'] < 30 or s['name'].startswith('tanne') or s['name'] == 'baum':
            continue
        im = np.array(Image.open(os.path.join(A, 'sprites', s['name'] + '.png')).convert('RGBA'))[:, :s['w']]
        t = trunk(im[..., 3] > 0)
        if t is None:
            continue
        crown = im[:t[2]][im[:t[2], :, 3] > 0][:, :3].astype(float)
        if len(crown) < 300 or is_cherry(crown):
            continue
        out.append([s['x'] + t[0], s['y'] + t[1], s['y'] + t[2]])
    return sorted(out, key=lambda v: (v[1], v[0]))


if __name__ == '__main__':
    w = json.load(open(os.path.join(A, 'world.json')))
    trees = find(w)
    with open(os.path.join(A, 'squirrel_trees.json'), 'w') as f:
        json.dump(trees, f, separators=(',', ':'))
    print(len(trees), 'trees')
