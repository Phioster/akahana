"""The eastern wood's ground and trees: a dark moss floor, a mix of firs, dark broadleaf trees, bare dead trees and a
few giants, kept off paths and clearings (layout.py), thick everywhere else.

    python3 forest.py OUT.png X0 Y0 X1 Y1 [scale]      (a graded preview of that window, deep in the wood)
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
from field6 import ground_organic  # noqa: E402
import layout as L  # noqa: E402
import mood_map  # noqa: E402
import objects_east as oe  # noqa: E402
import objects_water as ow  # noqa: E402
import zone1_draft as z1  # noqa: E402

ROOT = z1.ROOT
TINT = np.array([0.74, 0.98, 0.92])
MOSS = np.array([[40, 56, 40], [58, 80, 54], [78, 104, 66]], float)
PATH = np.array([[72, 74, 66], [96, 98, 86], [124, 124, 108]], float)      # pale enough to read in the dark


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def fbm(h, w, scale, rng):
    n = ndi.gaussian_filter(rng.normal(0, 1, (h, w)), scale)
    return n / (n.std() + 1e-9)


def window_masks(x0, y0, x1, y1):
    m = L.masks()
    sl = (slice(max(0, y0 - L.Y0), y1 - L.Y0), slice(max(0, x0 - L.X0), x1 - L.X0))
    out = {}
    for k in ('path', 'clearing', 'river'):
        a = np.zeros((y1 - y0, x1 - x0), bool)
        src = getattr(m, k)[sl]
        a[max(0, L.Y0 - y0):max(0, L.Y0 - y0) + src.shape[0], max(0, L.X0 - x0):max(0, L.X0 - x0) + src.shape[1]] = src
        out[k] = a
    return out


def floor(h, w, masks, rng):
    """Dark needle-and-moss ground; lighter, greener inside the clearings; the path worn paler."""
    g = ground_organic(h, w, np.full((h, w), 0.55), np.zeros((h, w)), rng).astype(float) * 0.52 * TINT
    moss = fbm(h, w, 7, rng)
    mm = moss > 0.35                                           # moss carpets here and there
    g[mm] = MOSS[np.clip(((moss[mm] - 0.35) * 2.2).astype(int), 0, 2)] * (0.85 + 0.3 * rng.random(mm.sum()))[:, None]
    clr = masks['clearing']
    soft = ndi.gaussian_filter(clr.astype(float), 3) > 0.5
    lush = soft & (rng.random((h, w)) < 0.75)
    g[lush] = MOSS[np.clip((fbm(h, w, 3, rng)[lush] * 1.2 + 1).astype(int), 0, 2)] * 1.05
    p = ndi.binary_dilation(masks['path'], iterations=1)                  # painted a little wider than it is walked: it must read
    idx = np.digitize(ndi.gaussian_filter(rng.random((h, w)), 0.8), [0.46, 0.56])
    g[p] = PATH[idx][p]
    edge = p & ~ndi.binary_erosion(p)
    g[edge & (rng.random((h, w)) < 0.45)] *= 0.8
    return g


def scatter(h, w, masks, rng, density=1.0):
    """Trees as (kind, x, y, size, seed) in window pixels; none on paths/clearings, thick elsewhere, species in patches."""
    keep = ndi.binary_dilation(masks['path'] | masks['clearing'] | masks['river'], iterations=1)
    margin = {'fir': 9, 'dead': 12, 'leaf': 20, 'knorr': 23, 'giant': 30}       # a broad crown needs room: its trunk stands this far off
    free_by = {k: ndi.distance_transform_edt(~keep) < m for k, m in margin.items()}
    free = free_by['fir']
    near_clear = ndi.binary_dilation(masks['clearing'], iterations=34) & ~free_by['giant']
    kind_n = fbm(h, w, 38, rng)                                # which species rules here
    taken = np.zeros((h + 60, w + 20), bool)
    out = []
    for _ in range(int(h * w / 55 * density)):
        x, y = int(rng.integers(-6, w + 6)), int(rng.integers(20, h + 30))
        xc, yc = min(max(x, 0), w - 1), min(y, h - 1)
        r = rng.random()
        if near_clear[yc, xc] and r < 0.045:
            k, sz, hit = 'giant', rng.uniform(1.7, 2.1), 20
        elif kind_n[yc, xc] > 0.7 and r < 0.8:
            k, sz, hit = 'dead', rng.uniform(0.9, 1.3), 8
        elif kind_n[yc, xc] < -0.9 and r < 0.8:
            k, sz, hit = 'leaf', rng.uniform(0.7, 1.0), 12
        elif r < 0.55:                                          # the twisted, overgrown ones (Hobbit's dark wood) are the wood's face
            k, sz, hit = 'knorr', rng.uniform(0.9, 1.35), 17
        else:
            k, sz, hit = 'fir', int(rng.integers(26, 48)), 7
        if free_by[k][yc, xc] or taken[y, x + 6]:
            continue
        taken[max(0, y - hit):y + hit + 1, max(0, x + 6 - hit - 2):x + 6 + hit + 3] = True
        out.append((k, x, y, sz, int(rng.integers(0, 10 ** 6))))
    # stones with moss and ferns beside the paths
    rim = ndi.binary_dilation(masks['path'], iterations=14) & ~free
    ys, xs = np.nonzero(rim)
    for _ in range(int(len(ys) / 260)):
        i = int(rng.integers(0, len(ys)))
        k = 'stone' if rng.random() < 0.5 else 'fern'
        out.append((k, int(xs[i]), int(ys[i]), float(rng.uniform(3, 6)) if k == 'stone' else int(rng.integers(5, 9)), int(rng.integers(0, 10 ** 6))))
    return sorted(out, key=lambda t: t[2])


def draw(img, items, G):
    h, w = img.shape[:2]
    for k, x, y, sz, sd in items:
        if k == 'fir':
            a0, b0, a1, b1 = max(0, x - sz), max(0, y - sz - 4), min(w, x + sz), min(h, y + sz // 3 + 2)
            if a1 > a0 and b1 > b0:
                z1.Fir(x - a0, y - b0, sz, sd, snow=0.0).draw(img[b0:b1, a0:a1])
        elif k == 'leaf':
            oe.Nachtbaum(x, y, sd, sz).draw(img, G)
        elif k == 'giant':
            oe.Riesenbaum(x, y, sd, sz).draw(img, G)
        elif k == 'knorr':
            oe.Knorrbaum(x, y, sd, sz).draw(img, G)
        elif k == 'dead':
            oe.Kahlbaum(x, y, sd, sz).draw(img, G)
        elif k == 'stone':
            oe.MoosStein(x, y, sz, sd).draw(img, G)
        elif k == 'fern':
            ow.Farn(x, y, sd, sz).draw(img, G)


def render_window(x0, y0, x1, y1, seed=7):
    rng = np.random.default_rng(seed)
    h, w = y1 - y0, x1 - x0
    masks = window_masks(x0, y0, x1, y1)
    img = floor(h, w, masks, rng)
    items = scatter(h, w, masks, rng)
    draw(img, items, rng.random((h, w)))
    return img, masks


def preview(out, x0, y0, x1, y1, scale=2):
    img, _ = render_window(x0, y0, x1, y1)
    w = json.load(open(os.path.join(ROOT, 'build', 'world_old', 'world_old.json')))
    g = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=[], wisps=[]), 2.0, grass_mist=0.45).astype(float)
    g = g * (1 - 0.26) * np.array([0.94, 1.04, 1.04])                    # the wood's darkness (task 7 does this in the game)
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).resize(((x1 - x0) * scale, (y1 - y0) * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    a = sys.argv
    preview(a[1], int(a[2]), int(a[3]), int(a[4]), int(a[5]), int(a[6]) if len(a) > 6 else 2)
    print('ok')
