#!/usr/bin/env python3
"""The wind in the grass for the approval page: the same pieces of the game's map as water_video, the
swaying layer moved by sway_anim in its two ways, A on the left, B on the right. One MP4 per spot.

    python3 tools/world/south/sway_video.py OUT_DIR [spot ...]
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import mood_map  # noqa: E402
import sway_anim  # noqa: E402
import water_anim  # noqa: E402
import zone2_draft as z2  # noqa: E402
from fireflies import Swarm  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
A = os.path.join(ROOT, 'assets', 'world')
F = os.path.join(ROOT, 'build', 'world_full')
SPOTS = {                                       # name: (x0, y0, x1, y1) in world pixels
    'gras': (90, 2040, 250, 2160),
    'schilf': (420, 2850, 580, 2970),
    'mohn': (300, 1100, 460, 1220),
}
FPS, SECONDS, SCALE = 12, 8, 3


def main(out):
    with open(os.path.join(A, 'world.json')) as f:
        w = json.load(f)
    ground = np.array(Image.open(os.path.join(F, 'ground.png')).convert('RGB'))
    flowers = np.array(Image.open(os.path.join(F, 'flowers.png')).convert('RGBA'))
    wmap = np.array(Image.open(os.path.join(F, 'water.png')).convert('RGBA'))
    bend = np.array(Image.open(os.path.join(F, 'bend.png')).convert('L'))
    fl = np.load(os.path.join(ROOT, 'build', 'mist_fields.npz'))
    only = sys.argv[2:]
    for name, (x0, y0, x1, y1) in SPOTS.items():
        if only and name not in only:
            continue
        sprites = [s for s in w['sprites'] if s['x'] < x1 and s['x'] + s['w'] > x0 and s['y'] < y1
                   and s['y'] + s['h'] > y0]
        pics = {s['name']: np.array(Image.open(os.path.join(A, 'sprites', s['name'] + '.png')).convert('RGBA'))
                for s in sprites}
        lights = [dict(l, x=l['x'] - x0, y=l['y'] - y0) for l in w['lights']]
        swarms = []
        for s in w.get('fireflies', []):
            if x0 - 40 < s['x'] < x1 + 40 and y0 - 40 < s['y'] < y1 + 40:
                sw = Swarm(s['x'] - x0, s['y'] - y0, 0)
                sw.flies = s['flies']
                swarms.append(sw)
        frames = os.path.join(out, name)
        os.makedirs(frames, exist_ok=True)
        for k in range(FPS * SECONDS):
            t = k / FPS
            halves = []
            for mode in ('A', 'B'):
                img = water_anim.animate(ground[y0:y1, x0:x1], wmap[y0:y1, x0:x1], x0, y0, t)
                f = sway_anim.sway(flowers[y0:y1, x0 - 4:x1], bend[y0:y1, x0 - 4:x1], x0 - 4, y0, t, mode)
                m = f[..., 3] > 0
                img[m] = f[m][:, :3]
                for s in sorted(sprites, key=lambda s: s['foot']):
                    fr = int(t * s['fps']) % s['frames']
                    a = pics[s['name']][:, fr * s['w']:(fr + 1) * s['w']]
                    sx, sy = s['x'] - x0, s['y'] - y0
                    for j in range(a.shape[0]):
                        yy = sy + j
                        if not 0 <= yy < img.shape[0]:
                            continue
                        i0, i1 = max(0, -sx), min(a.shape[1], img.shape[1] - sx)
                        if i1 <= i0:
                            continue
                        row = a[j, i0:i1]
                        k_ = row[:, 3] > 0
                        img[yy, sx + i0:sx + i1][k_] = row[k_, :3]
                ww = dict(w, lights=lights + [l for s in swarms for l in s.lights(t)], wisps=[])
                o = mood_map.mood(img, ww, t, grass_mist=z2.GRASS_MIST, water_band=fl['band'][y0:y1, x0:x1],
                                  calm=fl['calm'][y0:y1, x0:x1]).astype(float)
                for s in swarms:
                    s.draw(o, t)
                e = fl['edge'][y0:y1, x0:x1, None]
                halves.append(np.clip(o * (1 - e) + 214 * e, 0, 255).astype(np.uint8))
            gap = np.full((y1 - y0, 3, 3), 24, np.uint8)
            both = np.concatenate([halves[0], gap, halves[1]], 1)
            Image.fromarray(both).resize((both.shape[1] * SCALE, both.shape[0] * SCALE), Image.NEAREST).save(
                os.path.join(frames, f'{k:03d}.png'))
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i',
                        os.path.join(frames, '%03d.png'), '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18',
                        os.path.join(out, name + '.mp4')], check=True)
        print('ok', name, flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
