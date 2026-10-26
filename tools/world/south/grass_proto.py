#!/usr/bin/env python3
"""Trial of the tall-grass field for the approval page: the wanderer walks through a patch of tall grass,
the blades lean in gusts, bend away from him, lie down under his feet and slowly rise again behind him.
Blades are drawn by depth, so the ones in front of him hide his legs.

    python3 tools/world/south/grass_proto.py OUT_BASENAME
"""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..'))
from field6 import HEADS, CMAP, make_heads  # noqa: E402
import field6  # noqa: E402
import mood_map  # noqa: E402
import ground as south_ground  # noqa: E402
from objects2 import hx  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
W, H = 180, 200
FPS = 15
SECONDS = 9
GREEN = [hx(c) for c in ['#283126', '#3a4635', '#4f5d43', '#677552', '#838d63', '#a3a676']]   # root .. tip
DRY = [hx(c) for c in ['#7c6c4a', '#9c8a62', '#b8a67c']]                                    # some tips gone straw
SPEED = 15.0                           # art px/s, as the game
LIFE = 3.0                             # seconds a pressed blade takes to rise again (as the poppies)


def meadow(rng):
    fog = np.full((H, W), 0.55)
    flow = np.full((H, W), 0.25)
    tone = south_ground.fresh_tone(H, W, fog, flow, rng) - 0.05
    g = south_ground.ground_from_tone(tone, fog, flow, rng)
    return g * np.array([0.9, 1.0, 0.88]) * 0.62            # dark between the blades, a little green


def blades(rng):
    out = []
    for _ in range(int(W * H / 8.5)):
        x, y = rng.uniform(0, W), rng.uniform(4, H + 8)
        h = rng.integers(6, 13)
        out.append(dict(x=x, y=y, h=h, lean=rng.normal(0.6, 0.5), stiff=rng.uniform(0.7, 1.3),
                        dry=rng.random() < 0.12, ph=rng.uniform(0, 6.3), shade=rng.uniform(-0.12, 0.12)))
    out.sort(key=lambda b: b['y'])
    return out


def gust(x, y, t):
    """Drifting patches of wind like the poppy shader: 0 calm .. 1 a full gust."""
    q = np.array([x / 70.0 - 0.0455 * t * 6, y / 45.0 - 0.078 * t * 6])
    n = np.sin(q[0] * 2.1 + np.sin(q[1] * 1.7)) * 0.5 + np.sin(q[1] * 2.6 + q[0] * 0.8 + 1.3) * 0.5
    return np.clip((n * 0.5 + 0.5 - 0.42) / 0.38, 0, 1)


def main(out):
    rng = np.random.default_rng(4)
    field6.HEADS[:] = make_heads(np.random.default_rng(31))
    ground = meadow(rng)
    bl = blades(rng)
    poppies = [(rng.integers(4, W - 6), rng.integers(4, H - 6), rng.integers(0, len(field6.HEADS))) for _ in range(30)]
    sheet = np.array(Image.open(os.path.join(ROOT, 'assets', 'char', 'wanderer.png')).convert('RGBA'))
    pressed = np.zeros(len(bl))                                # how far each blade is pushed down, 0..1
    side = np.zeros(len(bl))                                   # and to which side
    path = [(92, -12), (96, 60), (84, 120), (90, 215)]          # down through the patch, a slight bend
    seg = np.cumsum([0] + [np.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])])
    bx = np.array([b['x'] for b in bl])
    by = np.array([b['y'] for b in bl])
    frames = []
    for f in range(FPS * SECONDS):
        t = f / FPS
        s = min(t * SPEED, seg[-1])
        k = np.searchsorted(seg, s) - 1
        k = max(0, min(k, len(path) - 2))
        u = (s - seg[k]) / (seg[k + 1] - seg[k])
        mx = path[k][0] + (path[k + 1][0] - path[k][0]) * u
        my = path[k][1] + (path[k + 1][1] - path[k][1]) * u
        # blades near his feet are pushed aside and down; afterwards they rise again over LIFE seconds
        d = np.hypot((bx - mx) * 1.0, (by - my) * 1.6)
        hit = np.clip(1 - d / 7.5, 0, 1)
        side = np.where(hit > pressed, np.sign(bx - mx + 0.01), side)
        pressed = np.maximum(pressed - 1 / (LIFE * FPS), hit)
        img = ground.copy()
        for (px, py, hk) in poppies:                           # a few last poppies down in the grass
            for j, row in enumerate(field6.HEADS[hk]):
                for i, ch in enumerate(row):
                    if ch != '.' and 0 <= py + j < H and 0 <= px + i < W:
                        img[py + j, px + i] = CMAP[ch]
        drawn_monk = False
        for n, b in enumerate(bl):
            if not drawn_monk and b['y'] > my:                  # the wanderer stands among the blades
                drawn_monk = True
                frame = 2 + int(t * 9) % 6
                cell = sheet[0:16, frame * 12:(frame + 1) * 12]
                ox, oy = int(round(mx)) - 6, int(round(my)) - 15
                for j in range(16):
                    for i in range(12):
                        if cell[j, i, 3] > 0 and 0 <= oy + j < H and 0 <= ox + i < W:
                            img[oy + j, ox + i] = cell[j, i, :3]
            p = pressed[n]
            wind = 0.4 * np.sin(t * 2.2 + b['ph']) + 2.2 * gust(b['x'], b['y'], t)
            bend = (b['lean'] + wind) / b['stiff'] * (1 - p) + side[n] * p * b['h'] * 0.9   # pressed: laid sideways
            h = b['h'] * (1 - 0.75 * p)                                       # and low
            hh = max(1, int(round(h)))
            for kk in range(hh):
                v = kk / max(hh - 1, 1)
                x = int(round(b['x'] + bend * v ** 1.6))
                y = int(round(b['y'] - kk + p * v * 1.5))
                if not (0 <= x < W and 0 <= y < H):
                    continue
                if b['dry'] and v > 0.6:
                    c = DRY[min(2, int((v - 0.6) / 0.4 * 3))]
                else:
                    c = GREEN[min(5, max(0, int(v * 5.2 + b['shade'] * 6 + (0.6 if bend < 0 else 0) + 1.2 * p)))]   # laid blades catch light
                img[y, x] = c
        lights = [{'x': 40.5, 'y': 60.5, 'r': 7, 'k': 0.25 * (0.5 + 0.5 * np.sin(t * 1.3)), 'kind': 'firefly'},
                  {'x': 140.5, 'y': 150.5, 'r': 7, 'k': 0.25 * (0.5 + 0.5 * np.sin(t * 1.1 + 2)), 'kind': 'firefly'}]
        a = mood_map.mood(np.clip(img, 0, 255), {'lights': lights, 'wisps': []}, 2.0 + t).astype(np.uint8)
        Image.fromarray(a).resize((W * 4, H * 4), Image.NEAREST).save(f'{out}_{f:03d}.png')
        if f % 15 == 0:
            print(f, flush=True)
    os.system(f'ffmpeg -loglevel error -y -framerate {FPS} -i {out}_%03d.png -c:v libx264 -pix_fmt yuv420p -crf 16 '
              f'{out}.mp4 && cp {out}_060.png {out}_bild.png && rm {out}_[0-9]*.png')


if __name__ == '__main__':
    main(sys.argv[1])
