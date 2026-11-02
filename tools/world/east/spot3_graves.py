"""Place 3, the grave clearing: off to the side on a short spur of the moss path. Weathered gravestones leaning every which way,
two slender steles, cairns, little offering bowls, staffs with faded cloth pushed into the ground, a patch of moonlight.

    python3 spot3_graves.py OUT.png [scale]
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import forest as F  # noqa: E402
import layout as L  # noqa: E402
import mood_map  # noqa: E402
import objects_east as oe  # noqa: E402

S = L.SPOTS['3']
X0, Y0, X1, Y1 = int(S.x) - 150, int(S.y) - 125, int(S.x) + 150, int(S.y) + 140
W, H = X1 - X0, Y1 - Y0


def placement(masks, rng):
    """Positions of the things inside the clearing (window pixels), kept apart and off the path."""
    im = Image.new('L', (W, H), 0)
    ImageDraw.Draw(im).polygon([(x - X0, y - Y0) for x, y in L.blob(S, k=0.28)], fill=1)
    inside = ndi.binary_erosion(np.array(im) > 0, iterations=7)
    off = inside & ~ndi.binary_dilation(masks['path'], iterations=9)
    ys, xs = np.nonzero(off)
    taken, out = [], []
    wanted = [('stone', 8), ('stele', 2), ('cairn', 3), ('stab', 4), ('bowl', 3)]
    for kind, n in wanted:
        tries = 0
        while n and tries < 4000:
            tries += 1
            i = int(rng.integers(0, len(ys)))
            x, y = int(xs[i]), int(ys[i])
            gap = 15 if kind in ('stone', 'stele') else 9
            if any(abs(x - a) < gap and abs(y - b) < gap * 0.7 for a, b in taken):
                continue
            taken.append((x, y))
            out.append((kind, x, y, int(rng.integers(0, 10 ** 6))))
            n -= 1
    # a bowl belongs to a stone: put the bowls at the foot of the first three stones
    stones = [o for o in out if o[0] == 'stone'][:3]
    out = [o for o in out if o[0] != 'bowl'] + [('bowl', s[1] + int(rng.integers(-4, 5)), s[2] + 6, s[3]) for s in stones]
    return out


def render(seed=23):
    rng = np.random.default_rng(seed)
    img, masks = F.render_window(X0, Y0, X1, Y1, seed=31)
    items = placement(masks, rng)
    G = rng.random((H, W))
    for kind, x, y, sd in sorted(items, key=lambda t: t[2]):
        if kind in ('stone', 'stele', 'cairn'):                          # a soft shadow on the ground, lower right
            for j in range(-1, 3):
                for i in range(2, 11 if kind == 'stele' else 9):
                    xx, yy = x + i, y + j
                    if 0 <= yy < H and 0 <= xx < W and (i - 6) ** 2 / 20 + (j - 0.5) ** 2 / 2.4 < 1:
                        img[yy, xx] *= 0.62
        lean = int(rng.integers(-2, 3))
        if kind == 'stone':
            oe.Grabstein(x, y, sd, lean).draw(img, G)
        elif kind == 'stele':
            oe.Stele(x, y, sd).draw(img, G)
        elif kind == 'cairn':
            oe.Steinhaufen(x, y, sd, 6 if sd % 2 else 4).draw(img, G)
        elif kind == 'stab':
            oe.Stab(x, y, sd, lean or 1, int(rng.integers(15, 21))).draw(img, G)
        elif kind == 'bowl':
            oe.Opferschale(x, y, sd).draw(img, G)
    return img, masks


def preview(out, scale=3):
    img, masks = render()
    w = json.load(open(os.path.join(F.ROOT, 'build', 'world_old', 'world_old.json')))
    g = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=[], wisps=[]), 2.0, grass_mist=0.45).astype(float)
    g = g * (1 - 0.26) * np.array([0.94, 1.04, 1.04])
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy = S.x - X0 - 18, S.y - Y0 - 14                                   # the moon's light falls into the clearing, off centre
    beam = np.exp(-(((xx - cx) / 52.0) ** 2 + ((yy - cy) / 40.0) ** 2))
    g = g * (1 + 0.55 * beam[..., None] * np.array([0.75, 1.0, 1.0])) + 18 * beam[..., None] * np.array([0.3, 0.9, 0.9])
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    preview(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    print('ok')
