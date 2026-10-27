#!/usr/bin/env python3
"""Approval video for the reflections: one spot of the lake shore, the wanderer standing in the shallows,
two strengths side by side (left gentle, right stronger), 8 s loop.

    python3 tools/world/south/reflect_video.py OUT_DIR
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
import reflect_anim as ra  # noqa: E402
import water_anim  # noqa: E402
import zone2_draft as z2  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
A = os.path.join(ROOT, 'assets', 'world')
F = os.path.join(ROOT, 'build', 'world_full')
SPOT = (470, 2880, 660, 3030)
FPS, SECONDS, SCALE = 12, 8, 3
STRENGTHS = (0.68,)
LAMP_H = 12                       # a lantern's light sits about this high above its foot


def main(out):
    x0, y0, x1, y1 = SPOT
    with open(os.path.join(A, 'world.json')) as f:
        w = json.load(f)
    G = np.array(Image.open(os.path.join(F, 'ground.png')).convert('RGB'))[y0:y1, x0:x1]
    FL = np.array(Image.open(os.path.join(F, 'flowers.png')).convert('RGBA'))[y0:y1, x0:x1]
    B = np.array(Image.open(os.path.join(F, 'bend.png')))[y0:y1, x0:x1]
    W = np.array(Image.open(os.path.join(F, 'water.png')))[y0:y1, x0:x1]
    LOW = np.array(Image.open(os.path.join(F, 'low.png')))[y0:y1, x0:x1]
    water = (W[..., 3] > 0) & (FL[..., 3] == 0)
    lake = water & (LOW == 0) & (W[..., 3] == 3)               # open lake water for the lantern's light
    sp = [s for s in w['sprites'] if s['x'] < x1 and s['x'] + s['w'] > x0 and s['y'] < y1 and s['y'] + s['h'] > y0]
    pics = {s['name']: np.array(Image.open(os.path.join(A, 'sprites', s['name'] + '.png')).convert('RGBA'))
            for s in sp}
    sheet = np.array(Image.open(os.path.join(ROOT, 'assets', 'char', 'wanderer.png')).convert('RGBA'))
    from scipy import ndimage as ndi                       # the wanderer ankle-deep, open water all round him
    open_ = ndi.binary_erosion(water, structure=np.ones((3, 9)))
    ys, xs = np.nonzero(open_ & (W[..., 1] > 2) & (W[..., 1] < 40))
    k = np.argmin(np.abs(xs - 70) + np.abs(ys - 112))
    mx, my = x0 + xs[k], y0 + ys[k]
    lights = [dict(l, x=l['x'] - x0, y=l['y'] - y0) for l in w['lights']]
    mirrored = []                                          # a lantern near the water: a broken path of
    for l in lights:                                       # its light on the surface below it
        i = int(l['x'])
        if not 0 <= i < W.shape[1]:
            continue
        col = lake[max(0, int(l['y'])):int(l['y']) + 70, i]
        if len(col) < 4:                                       # a light outside this cut
            continue
        run = np.convolve(col, np.ones(4), 'valid') == 4       # where the open water really begins: past
        if run.any():                                          # the jetty's end, not a wet pixel under it
            mirrored.append((i, int(l['y']) + int(np.argmax(run))))
    frames = os.path.join(out, 'spiegel')
    os.makedirs(frames, exist_ok=True)
    for n in range(FPS * SECONDS):
        t = n / FPS
        monk = sheet[0:16, (n // 6 % 2) * 12:(n // 6 % 2) * 12 + 12]           # idle breathing, frames 0-1
        ups = ra.upright_from_layer(FL, B, x0, y0) + ra.upright_from_low(G, LOW, x0, y0)
        for s in sp:
            fr = int(t * s['fps']) % s['frames']
            ups += ra.upright_from_sprite(pics[s['name']][:, fr * s['w']:(fr + 1) * s['w']], s['x'], s['y'], s['foot'])
        ups += ra.upright_from_sprite(monk, mx - 6, my - 15, my)
        side = []
        for keep in STRENGTHS:
            ra.KEEP = keep
            img = water_anim.animate(G, W, x0, y0, t)
            ra.draw(img, x0, y0, water, ups, t, 'B')
            m = FL[..., 3] > 0
            img[m] = FL[m][:, :3]
            for s in sorted(sp, key=lambda s: s['foot']):
                fr = int(t * s['fps']) % s['frames']
                a = pics[s['name']][:, fr * s['w']:(fr + 1) * s['w']]
                sx, sy = s['x'] - x0, s['y'] - y0
                for j in range(a.shape[0]):
                    yy = sy + j
                    if 0 <= yy < img.shape[0]:
                        i0, i1 = max(0, -sx), min(a.shape[1], img.shape[1] - sx)
                        if i1 > i0:
                            row = a[j, i0:i1]
                            kk = row[:, 3] > 0
                            img[yy, sx + i0:sx + i1][kk] = row[kk, :3]
            mm = monk[..., 3] > 0
            img[my - y0 - 15:my - y0 + 1, mx - x0 - 6:mx - x0 + 6][mm] = monk[mm][:, :3]
            o = mood_map.mood(img, dict(w, lights=lights, wisps=[]), t, grass_mist=z2.GRASS_MIST)
            ph = 2 * np.pi * t / 8.0
            for (lx, ly) in mirrored:                      # glints in rows, swaying, thinning out downwards
                for d in range(0, 26):
                    j = ly + d                     # lights are already in the cut's coordinates
                    if not 0 <= j < o.shape[0]:
                        continue
                    half = 1 + d // 9
                    off = int(np.round(1.0 * np.sin(j * 0.9 - ph) + 0.7 * np.sin(j * 0.37 + 3 * ph + 1.3)))
                    for i in range(lx - half + off, lx + half + off + 1):
                        hh = (np.sin(i * 12.9898 + j * 78.233) * 43758.5453) % 1.0   # every glint its own rhythm
                        cyc = 1 + int(hh * 5)                  # whole cycles per loop, so it still loops
                        if np.sin(cyc * ph + hh * 40.0) < 0.15:
                            continue
                        if 0 <= i < o.shape[1] and lake[j, i]:
                            a_ = keep * (1 - d / 30) * 0.9
                            o[j, i] = o[j, i] * (1 - a_) + np.array([236, 190, 110]) * a_
            side.append(np.clip(o, 0, 255).astype(np.uint8))
        im = side[0]
        Image.fromarray(im).resize((im.shape[1] * SCALE, im.shape[0] * SCALE), Image.NEAREST).save(
            os.path.join(frames, f'{n:03d}.png'))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i',
                    os.path.join(frames, '%03d.png'), '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-crf', '18', os.path.join(out, 'spiegel.mp4')], check=True)
    print('ok spiegel', len(mirrored), 'mirrored lights', flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
