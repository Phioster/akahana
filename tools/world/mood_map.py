#!/usr/bin/env python3
"""The whole world in the game's mood, as one big picture to look at (not used by the game).

Composites ground, poppies and sprites like preview.py, then runs shaders/post.gdshader's atmosphere
on every art pixel: grade, flickering lamp and fire light, the wisp's glow, bloom, drifting mist with
its softening, and the 4x4 Bayer raster where mist and light show. Frozen at one moment (t seconds).

    python3 tools/world/mood_map.py out.png [scale] [t]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
A = os.path.join(ROOT, 'assets', 'world')
D = os.path.join(ROOT, 'build', 'world_full')
LCOL = np.array([1.0, 0.62, 0.30])
WCOL = np.array([1.0, 0.58, 0.26])
MIST = np.array([214.0, 214.0, 212.0])
KIND = {'fire': 0, 'lantern': 1, 'wood': 2, 'candle': 3, 'wisp': 4, 'firefly': 3}
GLOW = {'fire': 40.0, 'lantern': 6.0, 'wood': 8.0, 'candle': 4.0, 'wisp': 4.0, 'firefly': 0.6}
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5
BAYER /= 16.0


def composite(w):
    img = np.array(Image.open(os.path.join(D, 'ground.png')).convert('RGB')).astype(float)
    fl = np.array(Image.open(os.path.join(D, 'flowers.png')))
    m = fl[..., 3] > 0
    img[m] = fl[m][:, :3]
    for s in sorted(w['sprites'], key=lambda s: s['foot']):
        a = np.array(Image.open(os.path.join(A, 'sprites', s['name'] + '.png')))[:, :s['w']]
        sub = img[s['y']:s['y'] + a.shape[0], s['x']:s['x'] + a.shape[1]]
        mm = a[:sub.shape[0], :sub.shape[1], 3] > 0
        sub[mm] = a[:sub.shape[0], :sub.shape[1], :3][mm]
    return img


def flick(kind, ph, s):
    if kind == 0:
        return 0.80 + 0.12 * np.sin(ph * 11) + 0.08 * np.sin(ph * 23 + 1.3)
    if kind == 1:
        return 0.9 + 0.06 * np.sin(ph * 13 + np.sin(ph * 7))
    if kind == 2:
        return 0.75 + 0.25 * (0.5 + 0.35 * np.sin(ph * 11 + s[0]) + 0.15 * np.sin(ph * 31 + s[1]))
    if kind == 3:
        return 0.8 + 0.2 * np.sin(ph * 13 + np.sin(ph * 7))
    return 1.0


def grade(c):
    return (c * 0.78 + c.mean(-1, keepdims=True) * 0.22) * np.array([0.74, 0.76, 0.80])


def bilinear(tex, u, v):
    """texture() with repeat + linear filtering, uv in texture units (0..1 per repeat)."""
    n = tex.shape[0]
    x, y = u * n - 0.5, v * n - 0.5
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - x0, y - y0
    t = lambda yy, xx: tex[yy % n, xx % n]
    return (t(y0, x0) * (1 - fx) * (1 - fy) + t(y0, x0 + 1) * fx * (1 - fy)
            + t(y0 + 1, x0) * (1 - fx) * fy + t(y0 + 1, x0 + 1) * fx * fy)


def mood(src, w, t):
    H, W = src.shape[:2]
    yy, xx = np.mgrid[0:H, 0:W]
    wx, wy = xx + 0.5, yy + 0.5
    em = (src[..., 0] > 190) & (src[..., 1] > 110) & (src[..., 2] < 140) & (src[..., 0] - src[..., 2] > 90)
    a = grade(src)
    ph = 2 * np.pi * t / 8.0
    L = np.zeros((H, W))
    Lw = np.zeros((H, W))
    bloom = np.zeros((H, W, 3))
    bloomw = np.zeros((H, W, 3))
    lights = [dict(l) for l in w['lights']]
    for wp in w['wisps']:                                    # the wisp at rest, mid-breath
        lights.append({'x': wp['x'] + 0.5, 'y': wp['y'] + 0.5, 'r': 34.0, 'k': 1.1, 'kind': 'wisp'})
    for l in lights:
        k = KIND.get(l['kind'], 3)
        f = flick(k, ph, (l['x'], l['y']))
        dx, dy = wx - l['x'], wy - l['y']
        d = np.hypot(dx, dy * 1.35) / l['r']
        li = l['k'] * f / (1 + 4 * d * d) * np.sqrt(np.clip(1 - d, 0, 1))
        r2 = dx * dx + dy * dy
        g = 0.0875 * np.exp(-r2 / 8) + 0.0221 * np.exp(-r2 / 72) + 0.00568 * np.exp(-r2 / 392)
        glow = GLOW.get(l['kind'], 4.0)
        if k == 4:
            Lw += li
            bloomw += np.array([240.0, 140.0, 60.0]) * glow * g[..., None]
        else:
            L += li
            bloom += np.array([250.0, 190.0, 90.0]) * glow * f * g[..., None]
    bloom *= np.array([1.0, 0.80, 0.55])
    a *= 1 + L[..., None] * LCOL * 1.4 + Lw[..., None] * WCOL * 1.2

    m1 = np.array(Image.open(os.path.join(A, 'mist1.png')).convert('L')) / 255.0
    m2 = np.array(Image.open(os.path.join(A, 'mist2.png')).convert('L')) / 255.0
    f = (0.55 * (bilinear(m1, (wx - 3.5 * t) / 256, wy / 256) - 0.5) * 6
         + 0.45 * (bilinear(m2, (wx - 6.0 * t) / 256, wy / 256) - 0.5) * 6)
    dens = np.clip((f - 0.2) * 0.36, 0, 0.32)[..., None]

    p = np.pad(src, ((1, 1), (1, 1), (0, 0)), mode='edge')         # softness only where the mist is thick
    nb = p[1:-1, 2:] + p[1:-1, :-2] + p[2:, 1:-1] + p[:-2, 1:-1]
    soft = grade(nb * 0.25 * 0.55 + src * 0.45) * (1 + L[..., None] * LCOL * 1.4)
    a = a + (soft - a) * np.clip(dens * 2.2, 0, 1)
    a = a * (1 - dens) + MIST * 0.8 * (1 + L[..., None] * LCOL * 1.6) * dens

    a += bloom + bloomw
    a[em] = np.maximum(a[em], src[em] * 1.05)

    eff = np.clip(dens[..., 0] * 7 + (L + Lw) * 2.5 + (bloom.sum(-1) + bloomw[..., 1]) / 90, 0, 1)
    eff[em] = 0
    bay = BAYER[yy % 4, xx % 4]
    on = eff > bay * 0.8 + 0.1                                     # raster only on mist and light
    l2 = a.mean(-1) + 0.001
    q = np.floor(l2 / 22 + bay) * 22
    a[on] = a[on] * (q / l2)[on][:, None]
    return np.clip(a, 0, 255).astype(np.uint8)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'karte.png'
    scale = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    t = float(sys.argv[3]) if len(sys.argv) > 3 else 2.0
    w = json.load(open(os.path.join(A, 'world.json')))
    img = Image.fromarray(mood(composite(w), w, t))
    img.resize((img.width * scale, img.height * scale), Image.NEAREST).save(out, optimize=True)
    print('ok', img.width * scale, img.height * scale)
