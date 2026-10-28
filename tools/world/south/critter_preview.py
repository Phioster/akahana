"""Approval picture: the fish and ducks as they are drawn now against the new drawn sprites, on the lake's
water with the evening grade. python3 tools/world/south/critter_preview.py OUT.png"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import critter_art as ca  # noqa: E402
import fish_anim  # noqa: E402
import flight_video as fv  # noqa: E402
import mood_map  # noqa: E402
import water_anim  # noqa: E402
import zone2_draft as z2  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
F = os.path.join(ROOT, 'build', 'world_full')


def water_bg(x0, y0, w, h, t=1.0):
    G = np.array(Image.open(os.path.join(F, 'ground.png')).convert('RGB'))[y0:y0 + h, x0:x0 + w]
    W = np.array(Image.open(os.path.join(F, 'water.png')).convert('RGBA'))[y0:y0 + h, x0:x0 + w]
    return water_anim.animate(G, W, x0, y0, t), (W[..., 3] == 3)


def paste(img, sprite, cx, cy, flip=False):
    s = sprite[:, ::-1] if flip else sprite
    h, w = s.shape[:2]
    for j in range(h):
        for i in range(w):
            if s[j, i, 3]:
                y, x = cy - h // 2 + j, cx - w // 2 + i
                if 0 <= y < img.shape[0] and 0 <= x < img.shape[1]:
                    img[y, x] = s[j, i, :3]


def grade(img, w):
    return np.clip(mood_map.mood(np.clip(img, 0, 255), dict(w, lights=[], wisps=[]), 1.0,
                                 grass_mist=z2.GRASS_MIST), 0, 255).astype(np.uint8)


def main(out):
    with open(os.path.join(ROOT, 'assets', 'world', 'world.json')) as f:
        w = json.load(f)
    x0, y0, W, H = 330, 3040, 210, 150
    base, deep = water_bg(x0, y0, W, H)
    rng = np.random.default_rng(5)
    old, new = base.copy(), base.copy()
    # the fish: 8 headings, one row old, one row new; then the 3 shades of the new one
    for h in range(8):
        cx, cy = 18 + h * 24, 20
        ang = np.radians(h * 45)
        f = fish_anim.Fish((cx, cy), rng)
        f.len = 9
        f.hx, f.hy, f.ax, f.ay = cx, cy, 0.0001, 0.0001
        # the old drawing for a fixed heading: its own routine at one place, turned by hand
        L = 4.5
        for k in np.linspace(-L, L, 40):
            for s in np.linspace(-1.5, 1.5, 7):
                half = 1.5 * max(0.0, 1 - (k / L) ** 2) ** 0.5 + (0.6 if -L < k < -L + 1.5 else 0)
                if abs(s) <= half:
                    px = cx + k * np.cos(ang) - s * np.sin(ang)
                    py = cy + k * np.sin(ang) + s * np.cos(ang)
                    old[int(round(py)), int(round(px))] = fish_anim.DARK
        paste(new, ca.fish_cell(h * 45, 2), cx, cy)
    for sh in range(3):
        paste(new, ca.fish_cell(0, sh), 30 + sh * 24, 48)
        paste(old, ca.fish_cell(0, sh), 30 + sh * 24, 48)
    # the ducks: swimming (old, new), running, flying
    for k in range(2):
        fv.duck_swim(old, 120 + k * 36, 52, 1, wake=True)
        paste(new, ca.duck_frame('swim', k), 120 + k * 36 + 1, 52)
    for n, x in enumerate((24, 56, 88, 120)):
        fv.duck_new_flight(old, x, 100, n)
        paste(new, ca.duck_frame('fly', n), x, 100)
    for n, x in enumerate((152, 184)):
        paste(new, ca.duck_frame('run', n), x, 100)
    old, new = grade(old, w), grade(new, w)
    S = 5
    both = np.concatenate([old, np.full((6, W, 3), 20, np.uint8), new], 0)
    Image.fromarray(both).resize((W * S, both.shape[0] * S), Image.NEAREST).save(out)
    print('ok', both.shape)


if __name__ == '__main__':
    main(sys.argv[1])
