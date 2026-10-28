#!/usr/bin/env python3
"""Approval video: how animals take off, three panels side by side - the small birds as they are in the game
(scenes/bird.gd: two wing frames), the duck as it is (scenes/lake_life.gd Duck: body plus four wing pixels)
and a new duck with a takeoff run, splash, four wing positions and a shadow on the water.

    python3 tools/world/south/flight_video.py OUT_DIR
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
import water_anim  # noqa: E402
import zone2_draft as z2  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
F = os.path.join(ROOT, 'build', 'world_full')
FPS, SECONDS, SCALE = 24, 8, 4
PW, PH = 100, 72                                              # one panel in art pixels
BODY = [np.array(c, float) for c in ([59, 51, 44], [94, 82, 70], [138, 122, 104])]
HEAD, BILL = np.array([47, 74, 58.0]), np.array([201, 162, 78.0])
WAKE = [np.array([85, 112, 121.0]), np.array([127, 152, 156.0])]
SPLASH = np.array([150, 176, 182.0])
TIP = np.array([186, 170, 146.0])


def put(img, x, y, col):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
        img[y, x] = col


# ---------------------------------------------------------------- the small birds (as in the game)
def bird_sheet(kind):
    return np.array(Image.open(os.path.join(ROOT, 'assets', 'life', f'vogel_{kind}.png')).convert('RGBA'))


def draw_bird(img, sheet, frame, x, foot_y, flip):
    fr = sheet[:, frame * 8:frame * 8 + 8]
    if flip:
        fr = fr[:, ::-1]
    for j in range(8):
        for i in range(8):
            if fr[j, i, 3] > 0:
                put(img, x - 4 + i, foot_y - 8 + j, fr[j, i, :3].astype(float))


def birds_panel(img, t):
    spots = [('spatz', 28, 44, 0.0, 12.0), ('amsel', 48, 52, 0.25, -6.0), ('rotkehl', 20, 58, 0.5, 4.0)]
    for kind, x0, y0, delay, jit in spots:
        sheet = bird_sheet(kind)
        t0 = 3.0 + delay
        if t < t0 or t >= 6.5:
            if 6.5 <= t < 8 or t < t0:
                fr = 1 if (t * 1.0) % 0.9 < 0.25 else 0                # peck / stand, as in the game
                draw_bird(img, sheet, fr, x0, y0, False)
        elif t - t0 < 2.5:
            dt = t - t0
            vx, vy = 40.0 + jit, -48.0                                 # bird.gd: away, up, accelerating upward
            x = x0 + vx * dt
            y = y0 + vy * dt - 5.0 * dt * dt
            fr = 3 if (dt % 0.16) < 0.08 else 4
            draw_bird(img, sheet, fr, round(x), round(y), False)


# ---------------------------------------------------------------- ducks
def duck_swim(img, x, y, d, wake=True):
    """The duck as it paddles (lake_life.gd Duck._draw): pixel lists copied from there."""
    if wake:
        for t in range(3, 10):
            for side in (-1, 1):
                put(img, x - d * t, y + 1 + side * (t // 3), WAKE[0] if t < 6 else WAKE[1])
    duck_body(img, x, y, d)


def duck_body(img, x, y, d):
    for q in [[0, -1, 2], [-d, -1, 1], [0, 0, 1], [-d, 0, 1], [d, 0, 2], [-2 * d, 0, 1], [-3 * d, 0, 0],
              [0, 1, 0], [-d, 1, 0], [d, 1, 0], [-2 * d, 1, 0], [2 * d, 0, 1]]:
        put(img, x + q[0], y + q[1], BODY[q[2]])
    for q in [[2 * d, -1], [2 * d, -2], [3 * d, -2]]:
        put(img, x + q[0], y + q[1], HEAD)
    put(img, x + 4 * d, y - 2, BILL)


def duck_old_flight(img, x, y, t, d=1):
    up = int(t * 8.0) % 2 == 0
    for p in [(-1, -1), (-2, -2 if up else 0), (1, -1), (2, -2 if up else 0)]:
        put(img, x + p[0], y + p[1], BODY[2])
    duck_body(img, x, y, d)


# the new flying duck: body stretched, neck out, tail pointed; (dx, dy) from the body's middle, facing right
FLY_BODY = [
    "..........HH..",
    "..01111111HHb.",
    "...0111111....",
    "....0111......",
]
ANCHOR = (6, 1)                                               # the middle of the body in FLY_BODY
SHOULDER = (7 - ANCHOR[0], 0 - ANCHOR[1] + 1)                 # where the wing grows from (right of the middle)
WING_ELEV = [78, 30, -55, 30]                                 # up, half, down, half (degrees, up is positive)


def wing(img, x, y, elev, d, far=False, length=5.5):
    a = np.radians(elev)
    dx, dy = -np.cos(a) * d, -np.sin(a)                       # up and back (or down and back)
    px, py = -dy, dx
    sx, sy = x + SHOULDER[0] * d + (d if far else 0), y + SHOULDER[1] - (1 if far else 0)
    for k in range(int(length) + 1):
        th = max(1, int(round(2.4 * (1 - k / length) + 0.7)))
        cx, cy = sx + dx * k, sy + dy * k
        for s in range(th):
            o = (s - (th - 1) / 2.0)
            col = BODY[1] if far else (TIP if k > 3 or s == th - 1 else BODY[2])      # lighter: it must show on dark water
            put(img, cx + px * o, cy + py * o, col)


def duck_new_flight(img, x, y, phase, d=1, level=False):
    elev = WING_ELEV[phase % 4]
    if level:
        elev = max(-30, min(40, elev))                        # skimming the water: lower wing beats
    wing(img, x, y, elev, d, far=True)
    for j, row in enumerate(FLY_BODY):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            col = {'0': BODY[0], '1': BODY[1], 'H': HEAD, 'b': BILL}[ch]
            put(img, x + (i - ANCHOR[0]) * d, y + (j - ANCHOR[1]), col)
    wing(img, x, y, elev, d)


def shadow(img, x, y, h, water):
    w = max(1, int(round(4 * (1 - min(h, 40) / 50.0))))
    for i in range(-w, w + 1):
        xx, yy = int(round(x + i)), int(round(y))
        if 0 <= xx < img.shape[1] and 0 <= yy < img.shape[0] and water[yy, xx]:
            img[yy, xx] = img[yy, xx] * 0.62


def ducks_panel(img, t, water, new, rng_seed=3):
    rng = np.random.default_rng(rng_seed + int(t * FPS))
    for n, (x0, y0, delay) in enumerate([(24, 46, 0.0), (36, 56, 0.35)]):
        t0 = 3.0 + delay
        if t < t0:
            duck_swim(img, x0 + 0.6 * t, y0, 1)
            continue
        dt = t - t0
        if dt > 3.0 and t < 6.5:
            continue
        if t >= 6.5:
            duck_swim(img, x0 + 0.6 * 2.9, y0, 1)
            continue
        if not new:
            x = x0 + 0.6 * t0 + 40.0 * dt
            y = y0 - 20.0 * dt
            duck_old_flight(img, round(x), round(y), dt)
            continue
        run = 0.75
        if dt < run:                                          # running over the water, wings beating, splash
            v = 36.0 * (dt / run) ** 1.4
            x = x0 + 0.6 * t0 + 0.5 * v * dt
            y = y0
            for k in range(3):
                put(img, x - 4 - k * 2 - rng.integers(0, 2), y + 1 + rng.integers(-1, 2), SPLASH)
            for k in range(8, 14):
                put(img, x - k - 1, y + 1 + (k % 3 - 1), WAKE[1] if k % 2 else WAKE[0])
            duck_new_flight(img, round(x), round(y - 1), int(dt / 0.05), level=True)
        else:
            u = dt - run
            xr = x0 + 0.6 * t0 + 0.5 * 36.0 * run
            x = xr + 36.0 * u
            h = 14.0 * u + 3.0 * u * u
            shadow(img, round(x - 2), y0 + 1, h, water)
            duck_new_flight(img, round(x), round(y0 - 1 - h), int(dt / 0.075))


def main(out):
    with open(os.path.join(ROOT, 'assets', 'world', 'world.json')) as f:
        w = json.load(f)
    gx, gy = 300, 905                                         # the poppy meadow where the birds sit
    G1 = np.array(Image.open(os.path.join(F, 'ground.png')).convert('RGB'))[gy:gy + PH, gx:gx + PW].astype(float)
    F1 = np.array(Image.open(os.path.join(F, 'flowers.png')).convert('RGBA'))[gy:gy + PH, gx:gx + PW]
    lx, ly = 330, 3030                                        # open lake for the ducks
    G2 = np.array(Image.open(os.path.join(F, 'ground.png')).convert('RGB'))[ly:ly + PH, lx:lx + PW].astype(float)
    W2 = np.array(Image.open(os.path.join(F, 'water.png')).convert('RGBA'))[ly:ly + PH, lx:lx + PW]
    water = (W2[..., 3] == 3)
    frames = os.path.join(out, 'flug')
    os.makedirs(frames, exist_ok=True)
    for n in range(FPS * SECONDS):
        t = n / FPS
        a = G1.copy()
        m = F1[..., 3] > 0
        a[m] = F1[m][:, :3]
        birds_panel(a, t)
        panels = [a]
        for new in (False, True):
            b = water_anim.animate(G2, W2, lx, ly, t)
            ducks_panel(b, t, water, new)
            panels.append(b)
        res = []
        for p in panels:
            o = mood_map.mood(np.clip(p, 0, 255), dict(w, lights=[], wisps=[]), t, grass_mist=z2.GRASS_MIST)
            res.append(np.clip(o, 0, 255).astype(np.uint8))
        sheet = np.concatenate([np.concatenate([r, np.full((PH, 3, 3), 20, np.uint8)], 1) for r in res], 1)
        Image.fromarray(sheet).resize((sheet.shape[1] * SCALE, PH * SCALE), Image.NEAREST).save(
            os.path.join(frames, f'{n:03d}.png'))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(FPS), '-i',
                    os.path.join(frames, '%03d.png'), '-vf', 'pad=ceil(iw/2)*2:ceil(ih/2)*2', '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p', '-crf', '18', os.path.join(out, 'flug.mp4')], check=True)
    print('ok flug', flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
