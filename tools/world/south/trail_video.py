#!/usr/bin/env python3
"""Approval video for the trail through tall grass: the wanderer walks down through it in the wind, the
blades part (as shaders/flowers.gdshader: the V of the wake, PUSH, R0/R1, life 3 s) and the pressed ones
show in one of two ways, side by side: A darker (in their own shadow), B laid flat with lying stalks.

    python3 tools/world/south/trail_video.py OUT_DIR
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
import sway_anim as sa  # noqa: E402
import zone2_draft as z2  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
F = os.path.join(ROOT, 'build', 'world_full')
A = os.path.join(ROOT, 'assets', 'world')
X0, Y0, W, H = 330, 2040, 110, 130
FPS, SECONDS, SCALE = 12, 8, 3
R0, R1, PUSH, LIFE, EVERY, LEAD = 5.0, 13.0, 4.0, 3.0, 0.13, 3.0
SPEED = 15.0


def hsh(a, b):
    return (np.sin(a * 12.9898 + b * 78.233) * 43758.5453) % 1.0


def walker(t):
    """Down the cut and back to the top in a gentle curve; 8 s loop."""
    u = (t % SECONDS) / SECONDS
    y = Y0 - 10 + u * (H + 20)
    x = X0 + 55 + 10 * np.sin(u * 2 * np.pi)
    return np.array([x, y])


def main(out):
    with open(os.path.join(A, 'world.json')) as f:
        w = json.load(f)
    G = np.array(Image.open(os.path.join(F, 'ground.png')).convert('RGB'))[Y0:Y0 + H, X0:X0 + W].astype(float)
    FLm = np.array(Image.open(os.path.join(F, 'flowers.png')).convert('RGBA'))[Y0:Y0 + H, X0 - 4:X0 + W]
    Bm = np.array(Image.open(os.path.join(F, 'bend.png')))[Y0:Y0 + H, X0 - 4:X0 + W]
    sheet = np.array(Image.open(os.path.join(ROOT, 'assets', 'char', 'wanderer.png')).convert('RGBA'))
    yy, xx = np.mgrid[0:H, 0:W]
    px, py = xx + X0 + 0.5, yy + Y0 + 0.5
    h = hsh(xx + X0, yy + Y0)
    frames = os.path.join(out, 'schneise')
    os.makedirs(frames, exist_ok=True)
    pts = []                                                    # [pos, dir, age], like core/trail.gd
    since = EVERY
    dt = 1.0 / FPS
    for n in range(-FPS * 4, FPS * SECONDS):                    # 4 s run-up so the loop starts with a wake
        t = n * dt
        pos = walker(t)
        d = walker(t + 0.05) - walker(t - 0.05)
        d = d / max(np.linalg.norm(d), 1e-6)
        for p in pts:
            p[2] += dt
        pts = [p for p in pts if p[2] < LIFE]
        since += dt
        if since >= EVERY:
            since = 0.0
            pts.insert(0, [pos + d * LEAD, d, 0.0])
            pts = pts[:24]
        if n < 0:
            continue
        best = np.zeros((H, W)); bo = np.zeros((H, W)); bk = np.zeros((H, W)); bn = np.zeros((H, W, 2))
        for p, dd, age in pts:
            k = max(0.0, 1 - age / LIFE)
            nrm = np.array([-dd[1], dd[0]])
            rx, ry = px - p[0], py - (p[1] - 2.0)
            s = k * np.clip(1 - np.abs(rx * dd[0] + ry * dd[1]) / 4.0, 0, 1)
            m = s > best
            best[m] = s[m]; bo[m] = (rx * nrm[0] + ry * nrm[1])[m]; bk[m] = k; bn[m] = nrm
        rw = R1 + (R0 - R1) * bk
        inside = (best > 0.3 * h) & (np.abs(bo) < rw)
        ease = bk * bk * (3 - 2 * bk)
        amt = PUSH * ease * np.clip(1 - np.abs(bo) / rw, 0, 1) * 1.6
        off = np.floor(np.clip(amt, 0, PUSH) + h * 0.6) * inside
        press = np.clip(np.sqrt(ease) * np.clip(1.2 - np.abs(bo) / (rw * 0.8), 0, 1), 0, 1) * (best > 0.05)
        swayed = sa.sway(FLm, Bm, X0 - 4, Y0, t, 'B')            # the wind first
        sx = np.clip(np.round(xx - bn[..., 0] * np.sign(bo) * off), 0, W - 1).astype(int)
        sy = np.clip(np.round(yy - bn[..., 1] * np.sign(bo) * off), 0, H - 1).astype(int)
        lay = swayed[sy, sx]                                     # then parted by the wake
        hgt = Bm[:, 4:][sy, sx]
        res = []
        for var in 'AB':
            img = G.copy()
            m = lay[..., 3] > 0
            img[m] = lay[m][:, :3]
            if var == 'A':
                img *= (1 - 0.5 * press)[..., None]
            else:
                lane = press > 0.15
                hid = lane & m & (hgt > 1) & (hgt < 255)
                img[hid] = G[hid] * (1 - 0.45 * press[hid])[:, None]
                dash = lane & (hsh(xx + X0, np.floor((yy + Y0) / 3)) < 0.18) & (press > 0.3)
                img[dash] = img[dash] * 0.5 + np.array([150.0, 150.0, 116.0]) * 0.5
            col = 2 + int(t * 3.0 / 2.0 * 6) % 6                  # his walk, facing down
            fr = sheet[0:16, col * 12:col * 12 + 12]
            fx, fy = int(round(pos[0])) - X0 - 6, int(round(pos[1])) - Y0 - 15
            for j in range(16):
                for i in range(12):
                    if fr[j, i, 3] > 0 and 0 <= fy + j < H and 0 <= fx + i < W:
                        img[fy + j, fx + i] = fr[j, i, :3]
            o = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=[], wisps=[]), t, grass_mist=z2.GRASS_MIST)
            res.append(np.clip(o, 0, 255).astype(np.uint8))
        im = np.concatenate([res[0], np.full((H, 4, 3), 20, np.uint8), res[1]], 1)
        Image.fromarray(im).resize((im.shape[1] * SCALE, H * SCALE), Image.NEAREST).save(
            os.path.join(frames, f'{n:03d}.png'))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i',
                    os.path.join(frames, '%03d.png'), '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-crf', '18', os.path.join(out, 'schneise.mp4')], check=True)
    print('ok schneise', flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
