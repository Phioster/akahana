#!/usr/bin/env python3
"""Composites the generated world the way the game does (ground, flowers, sprites sorted by foot) - for checking."""
import json, os, sys
import numpy as np
from PIL import Image
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
A = os.path.join(ROOT, 'assets', 'world')
D = os.path.join(ROOT, 'build', 'world_full')   # make_world.sh parks the whole pictures here
w = json.load(open(os.path.join(A, 'world.json')))
img = np.array(Image.open(os.path.join(D, 'ground.png')).convert('RGB')).astype(float)
fl = np.array(Image.open(os.path.join(D, 'flowers.png')))
m = fl[..., 3] > 0
img[m] = fl[m][:, :3]
for s in sorted(w['sprites'], key=lambda s: s['foot']):
    a = np.array(Image.open(os.path.join(A, 'sprites', s['name'] + '.png')))[:, :s['w']]
    x, y = s['x'], s['y']
    h_, w_ = a.shape[:2]
    sub = img[y:y + h_, x:x + w_]
    mm = a[:sub.shape[0], :sub.shape[1], 3] > 0
    sub[mm] = a[:sub.shape[0], :sub.shape[1], :3][mm]
if len(sys.argv) > 2 and sys.argv[2] == 'walk':
    wk = np.array(Image.open(os.path.join(D, 'walk.png'))) == 0
    img[wk] = img[wk] * 0.5 + np.array([255, 0, 0]) * 0.5
lum = img.mean(2, keepdims=True)
img = (img * 0.78 + lum * 0.22) * np.array([0.74, 0.76, 0.80])        # the game's grade, without mist
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1] if len(sys.argv) > 1 else 'preview.png')
