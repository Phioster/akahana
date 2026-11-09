#!/usr/bin/env python3
"""Approval video: now and then a fish leaps out of the lake. A dark shape swims up under the surface, the
fish breaks out with a little splash, arcs through the air (lit, silvery), dives back in with a bigger
splash, and two rings spread and fade. Real lake patch with the moving water, graded like the game.
    python3 tools/world/life/fishjump_video.py OUT.mp4
"""
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SOUTH = os.path.join(HERE, '..', 'south')
sys.path[:0] = [HERE, SOUTH, os.path.join(HERE, '..'), os.path.join(HERE, '..', 'lib')]
import critter_art as ca  # noqa: E402
import mood_map  # noqa: E402
import water_anim  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
F = os.path.join(ROOT, 'build', 'world_full')
X0, Y0, W, H = 1250, 4300, 120, 90
FPS, SECONDS, SCALE = 24, 10, 6
AIR = 0.6                                           # seconds in the air
JUMPS = [(1.4, 60, 50, 1), (4.6, 30, 30, -1), (7.4, 88, 66, 1)]   # (leaves the water at, x, y, direction)


def put(img, x, y, col):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        img[y, x] = col


SILVER, BACK, BELLY = (150, 168, 174), (84, 104, 114), (196, 208, 208)


def lit(cell):
    """the fish out of the water in three calm tones: dark back on top, silver side, light belly underneath
    (the water fish's shading bands read as a check pattern in the air)"""
    c = cell.copy()
    m = c[..., 3] > 0
    c[m, :3] = SILVER
    for i in range(c.shape[1]):
        ys = np.nonzero(m[:, i])[0]
        if len(ys) >= 3:                                  # thin diagonal columns stay plain silver
            c[ys[0], i, :3] = BACK
            c[ys[-1], i, :3] = BELLY
    return c


def stamp(img, cell, cx, cy):
    for j, i in zip(*np.nonzero(cell[..., 3])):
        put(img, cx - ca.CELL_F // 2 + i, cy - ca.CELL_F // 2 + j, cell[j, i, :3])


def splash(img, x, y, u, big):
    """water thrown up for 0.3 s: single drops flying out and falling, no closed shape"""
    if u < 0 or u > 0.3:
        return
    k = u / 0.3
    drops = [(-1.0, 1.0), (1.0, 1.1), (-0.4, 1.6), (0.5, 1.5)] + ([(-1.6, 0.8), (1.7, 0.7)] if big else [])
    for dx, up in drops:
        reach = 3.5 if big else 2.5
        put(img, x + dx * reach * k, y - up * (3 if big else 2) * np.sin(k * np.pi), ca.SPLASH)


def ring(img, x, y, u):
    """a ring spreading over 1.6 s, flat like everything on the water"""
    if u < 0 or u > 1.6:
        return
    r = 3 + u * 5
    col = ca.WAKE[1] if u < 0.7 else ca.WAKE[0]
    for a in np.linspace(0, 2 * np.pi, int(8 + r * 6), endpoint=False):
        if u > 1.1 and int(a * 5) % 2:              # breaking up as it fades
            continue
        put(img, x + np.cos(a) * r, y + np.sin(a) * r * 0.5, col)


def main(out):
    G = np.array(Image.open(os.path.join(F, 'ground.png')).convert('RGB'))[Y0:Y0 + H, X0:X0 + W]
    Wt = np.array(Image.open(os.path.join(F, 'water.png')).convert('RGBA'))[Y0:Y0 + H, X0:X0 + W]
    tmp = tempfile.mkdtemp()
    span = 12                                          # px travelled in the air
    for i in range(FPS * SECONDS):
        t = i / FPS
        img = water_anim.animate(G, Wt, X0, Y0, t).astype(np.uint8)
        for t0, x, y, d in JUMPS:
            u = t - t0
            ex, ey = x + d * span, y                     # where it goes back in
            if -1.2 < u < 0:                             # the shape under the water, coming up
                k = (u + 1.2) / 1.2
                stamp(img, ca.fish_cell(0 if d > 0 else 180, 0 if k < 0.5 else 1, ca.WAG[int(t * 8) % 4]),
                      x - d * (1 - k) * 14, y)
            if 0 <= u < AIR:                             # in the air: an arc, nose up, flat, nose down
                k = u / AIR
                ang = (-50 + 100 * k) * (1 if d > 0 else -1) + (0 if d > 0 else 180)
                stamp(img, lit(ca.fish_cell(ang, 2)), x + d * span * k, y - 9 * np.sin(k * np.pi))
            splash(img, x, y, u, False)
            splash(img, ex, ey, u - AIR, True)
            ring(img, x, y, u - 0.2)                     # after the drops, never under them
            ring(img, ex, ey, u - AIR - 0.2)
            ring(img, ex, ey, u - AIR - 0.55)
        g = np.clip(mood_map.grade(img.astype(float)), 0, 255).astype(np.uint8)
        Image.fromarray(g).resize((W * SCALE, H * SCALE), Image.NEAREST).save(f'{tmp}/f{i:04d}.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{tmp}/f%04d.png',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', out], check=True)


if __name__ == '__main__':
    main(sys.argv[1])
