#!/usr/bin/env python3
"""A short loop of one corner of zone 1 with its fireflies, torch and candles, in the game's mood."""
import os
import sys
import json

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import zone1_draft as z  # noqa: E402

out, (x0, y0, w_, h_) = sys.argv[1], (420, 520, 200, 170)
w = json.load(open(os.path.join(z.ROOT, 'assets', 'world', 'world.json')))
raw, fake = z.render('a', w, raw=True)
crop = raw[y0:y0 + h_, x0:x0 + w_]
static = [l for l in z.LIT]
frames = []
for k in range(32):
    t = 2.0 + k / 8.0
    ls = [dict(l, x=l['x'] - x0, y=l['y'] - y0) for l in fake['lights'] + static + [l for s in z.SWARMS for l in s.lights(t)]]
    img = z.mood_map.mood(crop.copy(), dict(fake, lights=ls), t).astype(float)
    for s in z.SWARMS:
        sw = z.Swarm.__new__(z.Swarm)
        sw.x, sw.y, sw.flies = s.x - x0, s.y - y0, s.flies
        sw.draw(img, t)
    Image.fromarray(img.astype(np.uint8)).resize((w_ * 4, h_ * 4), Image.NEAREST).save(f'{out}_{k:02d}.png')
    print(k, flush=True)
# a video, not a gif: a gif's 256 colours drop the few bright firefly pixels
os.system(f'ffmpeg -loglevel error -y -framerate 8 -i {out}_%02d.png -vf "loop=2:32:0" -c:v libx264 -pix_fmt yuv420p '
          f'-crf 16 {out}.mp4 && rm {out}_*.png')
