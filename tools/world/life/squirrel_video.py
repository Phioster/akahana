#!/usr/bin/env python3
"""Approval video: a squirrel nibbling in the grass by a broadleaf tree; the wanderer comes, it hops to the
trunk, climbs and is gone in the crown. Real map patch (build/world_full + sprites), graded like the game.
    python3 tools/world/life/squirrel_video.py OUT.mp4
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
import mood_map  # noqa: E402
import squirrel_art as sa  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
F = os.path.join(ROOT, 'build', 'world_full')
SP = os.path.join(ROOT, 'assets', 'world', 'sprites')
FPS, SECONDS, SCALE = 24, 11, 5
TREE = 'wt081'
_T = next(s for s in json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))['sprites'] if s['name'] == TREE)


def _trunk():
    a = np.array(Image.open(os.path.join(SP, TREE + '.png')).convert('RGBA'))[:, :_T['w'], 3] > 0
    y = a.shape[0] - 1
    while not a[y].any():
        y -= 1
    xs = np.nonzero(a[y])[0]
    base = y
    while a[y].sum() <= len(xs) + 3:            # up the trunk until the crown widens
        y -= 1
    return _T['x'] + int(xs.mean()), _T['y'] + y + 1, _T['y'] + base


TRUNK_X, CROWN_Y, BASE_Y = _trunk()               # trunk middle, crown's lower edge, trunk foot (world)
X0, Y0, W, H = TRUNK_X - 60, CROWN_Y - 60, 150, 116


def compose():
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    img = np.array(Image.open(os.path.join(F, 'ground.png')).convert('RGB'))[Y0:Y0 + H, X0:X0 + W].copy()
    fl = np.array(Image.open(os.path.join(F, 'flowers.png')))[Y0:Y0 + H, X0:X0 + W]
    m = fl[..., 3] > 0
    img[m] = fl[m][:, :3]
    back, front = img.copy(), np.zeros((H, W, 4), np.uint8)
    for s in sorted(w['sprites'], key=lambda s: s['foot']):
        a = np.array(Image.open(os.path.join(SP, s['name'] + '.png')).convert('RGBA'))[:, :s['w']]
        x, y = s['x'] - X0, s['y'] - Y0
        ya, yb, xa, xb = max(0, y), min(H, y + a.shape[0]), max(0, x), min(W, x + a.shape[1])
        if ya >= yb or xa >= xb:
            continue
        sub = a[ya - y:yb - y, xa - x:xb - x]
        mm = sub[..., 3] > 0
        back[ya:yb, xa:xb][mm] = sub[mm][:, :3]
        if s['name'] == TREE:                     # its crown is drawn again over a climbing squirrel
            crown = mm & (np.arange(ya, yb)[:, None] + Y0 < CROWN_Y)
            front[ya:yb, xa:xb][crown] = np.concatenate([sub[crown][:, :3], np.full((crown.sum(), 1), 255, np.uint8)], 1)
    return back, front


def paste(img, cell, x, y, flip=False):
    """cell's bottom middle at world (x, y)"""
    c = cell[:, ::-1] if flip else cell
    h, w = c.shape[:2]
    for yy in range(h):
        for xx in range(w):
            if c[yy, xx, 3]:
                px, py = int(x) - w // 2 + xx - X0, int(y) - h + yy - Y0
                if 0 <= px < W and 0 <= py < H:
                    img[py, px] = c[yy, xx, :3]


EAT = [('eat_dn', .18), ('eat_up', .25), ('eat_dn', .18), ('eat_up', .25), ('eat_dn', .18), ('eat_up', .6),
       ('eat_tw', .15), ('eat_up', .45)]
CLIMB = [(9, 0.05), (0.7, None), (40, 0.05)]       # px at a time and s per px; None: a pause on the bark


def squirrel(t):
    """(frame, x, y, flip) at time t: eats a nut, hops to the trunk, climbs in spurts, gone in the crown"""
    sx, sy = TRUNK_X + 32, BASE_Y + 9
    if t < 4.2:
        u = t % sum(d for _, d in EAT)
        for f, d in EAT:
            if u < d:
                return f, sx, sy, True
            u -= d
    if t < 4.6:
        return 'sit', sx, sy, True                # looks up
    hop_t = t - 4.6
    tx, ty = TRUNK_X + 4, BASE_Y + 2
    dist = np.hypot(sx - tx, sy - ty)
    n = int(hop_t / 0.11)
    if n * 5 < dist:
        k = n * 5 / dist
        return ('hop1' if n % 2 else 'hop2'), round(sx + (tx - sx) * k), round(sy + (ty - sy) * k), True
    ct, up = hop_t - dist / 5 * 0.11, 0
    for amount, per in CLIMB:
        if per is None:
            if ct < amount:
                return 'climb1', tx, ty - up, False
            ct -= amount
            continue
        if ct < amount * per:
            up += int(ct / per)
            break
        up += amount
        ct -= amount * per
    if ty - up < CROWN_Y - 14:
        return None
    return ('climb1' if int(ct / 0.1) % 2 else 'climb2'), tx, ty - up, False


def monk(t):
    sheet = np.array(Image.open(os.path.join(ROOT, 'assets', 'char', 'wanderer.png')).convert('RGBA'))
    walk = t > 2.0 and t < 6.0
    x = TRUNK_X + 97 - 15 * (min(max(t, 2.0), 6.0) - 2.0)
    col = 2 + int(t * 9) % 6 if walk else int(t * 1.5) % 2
    return sheet[2 * 16:3 * 16, col * 12:col * 12 + 12], x, BASE_Y + 21


def main(out):
    back, front = compose()
    tmp = tempfile.mkdtemp()
    for i in range(FPS * SECONDS):
        t = i / FPS
        img = back.copy()
        cell, mx, my = monk(t)
        sq = squirrel(t)
        things = [(my, lambda im: paste(im, cell, mx, my))]
        if sq:
            f, x, y, flip = sq
            things.append((y, lambda im: paste(im, sa.cell(f), x, y, flip)))
        for _, draw in sorted(things, key=lambda d: d[0]):
            draw(img)
        m = front[..., 3] > 0
        img[m] = front[m][:, :3]
        g = np.clip(mood_map.grade(img.astype(float)), 0, 255).astype(np.uint8)
        Image.fromarray(g).resize((W * SCALE, H * SCALE), Image.NEAREST).save(f'{tmp}/f{i:04d}.png')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i', f'{tmp}/f%04d.png',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '16', out], check=True)
    Image.open(f'{tmp}/f{int(FPS * 1.0):04d}.png').save(out.replace('.mp4', '_still.png'))


if __name__ == '__main__':
    main(sys.argv[1])
