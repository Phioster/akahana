#!/usr/bin/env python3
"""Approval video: butterflies over the poppies. They flutter about at a little height (a shadow pixel on the
ground shows how high), one settles on a flower and slowly opens and shuts; the wanderer comes through and
they rise and drift off. Real map patch, graded like the game.
    python3 tools/world/life/butterfly_video.py OUT.mp4
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..'), os.path.join(HERE, '..', 'lib')]
import butterfly_art as ba  # noqa: E402
import mood_map  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
F = os.path.join(ROOT, 'build', 'world_full')
SP = os.path.join(ROOT, 'assets', 'world', 'sprites')
X0, Y0, W, H = 1240, 3360, 120, 90
FPS, SECONDS, SCALE = 24, 12, 6


def compose():
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    img = np.array(Image.open(os.path.join(F, 'ground.png')).convert('RGB'))[Y0:Y0 + H, X0:X0 + W].copy()
    fl = np.array(Image.open(os.path.join(F, 'flowers.png')))[Y0:Y0 + H, X0:X0 + W]
    m = fl[..., 3] > 0
    img[m] = fl[m][:, :3]
    for s in sorted(w['sprites'], key=lambda s: s['foot']):
        a = np.array(Image.open(os.path.join(SP, s['name'] + '.png')).convert('RGBA'))[:, :s['w']]
        x, y = s['x'] - X0, s['y'] - Y0
        ya, yb, xa, xb = max(0, y), min(H, y + a.shape[0]), max(0, x), min(W, x + a.shape[1])
        if ya < yb and xa < xb:
            sub = a[ya - y:yb - y, xa - x:xb - x]
            mm = sub[..., 3] > 0
            img[ya:yb, xa:xb][mm] = sub[mm][:, :3]
    return img, fl[..., 3] > 0


class Flutter:
    """One butterfly: wanders with sudden turns, bobs up and down, flaps fast; may settle; flees the wanderer."""

    def __init__(self, kind, x, y, seed, settle_at=None):
        self.kind, self.p, self.rng = kind, np.array([x, y], float), np.random.default_rng(seed)
        self.v = self.rng.normal(size=2) * 6
        self.home = np.array([x, y], float)
        self.alt, self.ph, self.settle_at, self.sat, self.flee = 8.0, self.rng.random() * 6, settle_at, None, False

    def step(self, t, dt, monk):
        d = self.p - monk
        if np.hypot(*d) < 26 and not self.flee:
            self.flee, self.sat = True, None
            self.v = d / np.hypot(*d) * 18
        if self.sat is not None:                        # sitting on the flower
            self.alt = max(0.0, self.alt - 12 * dt)
            return
        if self.settle_at is not None and not self.flee and t > self.settle_at[0]:
            goal = np.array(self.settle_at[1], float)
            to = goal - self.p
            if np.hypot(*to) < 1:
                self.p, self.sat = goal, t
                return
            self.v = to / max(np.hypot(*to), 1) * 8
            self.alt = max(0.0, self.alt - 4 * dt)
        else:
            if self.rng.random() < dt * 2.5:              # a sudden turn now and then
                self.v = self.v * 0.4 + self.rng.normal(size=2) * 7
            if not self.flee:                             # stays over its patch of meadow
                self.v += (self.home - self.p) * 0.6 * dt
            sp = np.hypot(*self.v)
            top = 22 if self.flee else 11
            if sp > top:
                self.v *= top / sp
            self.alt = (14 if self.flee else 8) + 3 * np.sin(t * 5 + self.ph)
            if self.flee:
                self.v[1] -= 6 * dt
        self.p += self.v * dt

    def frame(self, t):
        if self.sat is not None:                        # slow open and shut on the flower
            u = (t - self.sat) % 2.4
            return 'open' if u < 1.1 else 'half' if u < 1.3 or u > 2.2 else 'shut'
        return ['open', 'half', 'shut', 'half'][int((t + self.ph) * 14) % 4]


def main(out):
    back, flower = compose()
    sheet = np.array(Image.open(os.path.join(ROOT, 'assets', 'char', 'wanderer.png')).convert('RGBA'))
    ys, xs = np.nonzero(flower[40:60, 30:60])
    fx, fy = X0 + 30 + xs[len(xs) // 2], Y0 + 40 + ys[len(ys) // 2]
    flies = [Flutter('fuchs', X0 + 40, Y0 + 35, 1, settle_at=(2.0, (fx, fy))), Flutter('weiss', X0 + 75, Y0 + 30, 2),
             Flutter('zitrone', X0 + 85, Y0 + 55, 3), Flutter('blau', X0 + 30, Y0 + 62, 4),
             Flutter('pfau', X0 + 95, Y0 + 20, 5), Flutter('aurora', X0 + 55, Y0 + 70, 6),
             Flutter('admiral', X0 + 20, Y0 + 20, 7)]
    tmp, dt = tempfile.mkdtemp(), 1 / FPS
    for i in range(FPS * SECONDS):
        t = i * dt
        walk = 5.5 < t < 11.5
        mx, my = X0 + W + 8 - 15 * (min(max(t, 5.5), 11.5) - 5.5), Y0 + 58
        col = 2 + int(t * 9) % 6 if walk else int(t * 1.5) % 2
        img = back.copy()
        for f in flies:
            f.step(t, dt, np.array([mx, my - 6]))
        c = sheet[2 * 16:3 * 16, col * 12:col * 12 + 12]
        mm = c[..., 3] > 0
        ox, oy = int(mx) - 6 - X0, int(my) - 16 - Y0
        for y, x in zip(*np.nonzero(mm)):
            if 0 <= ox + x < W and 0 <= oy + y < H:
                img[oy + y, ox + x] = c[y, x, :3]
        for f in flies:
            x, y = int(round(f.p[0])) - X0, int(round(f.p[1])) - Y0
            if f.alt > 1.5 and 0 <= x < W and 0 <= y < H:  # shadow on the ground, the butterfly up above it
                img[y, x] = (img[y, x] * 0.6).astype(np.uint8)
            cl = ba.cell(f.kind, f.frame(t))
            ay = y - int(round(f.alt)) - 3
            for yy, xx in zip(*np.nonzero(cl[..., 3])):
                if 0 <= x - 2 + xx < W and 0 <= ay + yy < H:
                    img[ay + yy, x - 2 + xx] = cl[yy, xx, :3]
        g = np.clip(mood_map.grade(img.astype(float)), 0, 255).astype(np.uint8)
        Image.fromarray(g).resize((W * SCALE, H * SCALE), Image.NEAREST).save(f'{tmp}/f{i:04d}.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{tmp}/f%04d.png',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', out], check=True)


if __name__ == '__main__':
    main(sys.argv[1])
