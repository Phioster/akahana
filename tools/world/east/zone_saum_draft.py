"""The wood's southern edge: from the lake's east shore the meadow runs on as a tongue along a new branch path through the
south's fir wall, and slowly becomes forest: first green broadleaf trees and firs, further north-east the dark twisted ones.
The glade (9) with its old bench, boulders and a ring of mushrooms lies in the middle of it.

    python3 zone_saum_draft.py OUT.png [scale]
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
import zone2_draft as z2  # noqa: E402

ROOT = F.ROOT
FULL = os.path.join(ROOT, 'build', 'world_full')
X0, Y0, X1, Y1 = 800, 2260, 1520, 3010
W, H = X1 - X0, Y1 - Y0
SEAM = 900
SRC_END = 880                    # the south's last 20 columns are its flat edge band: the extension starts before them


def meadow_window(w):
    """The south's picture (ground, blades, sprites) in x 800..899, then mirrored eastward, rolled each time."""
    g = np.array(Image.open(os.path.join(FULL, 'ground.png')).convert('RGB'))[Y0:Y1, X0:SRC_END].astype(float)
    fl = np.array(Image.open(os.path.join(FULL, 'flowers.png')).convert('RGBA'))[Y0:Y1, X0:SRC_END]
    m = fl[..., 3] > 0
    g[m] = fl[m][:, :3]
    return g


def edge_fir_free(w, g, path_y):
    """The south's edge firs are sprites; in the tongue's opening they must not stand. (Preview: just not pasted.)"""
    out = []
    for s in w['sprites']:
        if s['x'] + s['w'] < X0 or s['x'] > SEAM or s['y'] > Y1 or s['y'] + s['h'] < Y0:
            continue
        cy = s['foot']
        if s['x'] + s['w'] >= SEAM - 40 and abs(cy - path_y) < 95:
            continue
        out.append(s)
    return out


def smooth(t):
    return F.smooth(t)


def render(seed=19):
    rng = np.random.default_rng(seed)
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    west = meadow_window(w)
    cols = SRC_END - X0
    yy, xx = np.mgrid[0:H, 0:W]
    gx, gy = xx + X0, yy + Y0
    img = np.zeros((H, W, 3))
    img[:, :cols] = west
    for k in range(cols, W):                                    # the meadow runs on, mirrored: no jump at the seam
        j = k - cols
        t = j % 80
        img[:, k] = np.roll(west[:, cols - 1 - (t if t < 40 else 79 - t)], 17 * (j // 40), axis=0)
    # --- the branch path and the tongue around it
    pm = np.zeros((H, W), bool)
    im = Image.new('L', (W, H), 0)
    pts = [(float(x) - X0, float(y) - Y0) for x, y in L.paths()['saum_h']]
    ImageDraw.Draw(im).line(pts, fill=1, width=L.PATH_W, joint='curve')
    pm |= np.array(im) > 0
    pm_west = pm.copy()
    # west of the seam it joins the existing path: a short stretch of its ground on the meadow side
    d = ndi.distance_transform_edt(~pm)
    hw = 105 - 55 * smooth((gx - SEAM) / 420.0)
    open_ = np.clip(1 - (d / hw) ** 2.2, 0, 1)
    open_ = 1 - (1 - open_) * smooth((gx - 850) / 90.0)               # no straight line at the seam: the wood begins in a soft curve
    forest_f = F.floor(H, W, {'path': pm, 'clearing': np.zeros((H, W), bool), 'river': np.zeros((H, W), bool)}, rng)
    take = rng.random((H, W)) < np.clip(open_, 0, 1) ** 0.7
    g = np.where(take[..., None], img, forest_f)
    # --- glade 9: moss floor, bench, boulders, mushroom ring
    s9 = L.SPOTS['9']
    from PIL import ImageDraw as ID
    gim = Image.new('L', (W, H), 0)
    ID.Draw(gim).polygon([(x - X0, y - Y0) for x, y in L.blob(s9)], fill=1)
    glade = np.array(gim) > 0
    lush = ndi.gaussian_filter(glade.astype(float), 3) > 0.5
    moss = F.MOSS[np.clip((F.fbm(H, W, 3, rng) * 1.2 + 1).astype(int), 0, 2)] * 1.05
    lm = lush & (rng.random((H, W)) < 0.8)
    g[lm] = moss[lm]
    # path painting on the ground (pale, like the south's)
    pp = pm & (gx >= SEAM - 30)
    idx = np.digitize(ndi.gaussian_filter(rng.random((H, W)), 0.8), [0.46, 0.56])
    col = np.array([[104, 104, 90], [134, 132, 114], [164, 160, 138]], float)
    dark = smooth((gx - SEAM) / 450.0)[..., None]
    g[pp] = (col[idx] * (1 - 0.4 * dark))[pp]
    # --- trees: more and more twisted the further in, broadleaf green near the meadow
    green = np.clip(1 - smooth((gx - SEAM) / 520.0) * 1.1, 0, 1)
    masks = {'path': pm, 'clearing': glade | (open_ > 0.45), 'river': np.zeros((H, W), bool)}
    items = F.scatter(H, W, masks, rng, green=green)
    items = [t for t in items if not (t[1] + X0 < SEAM + 6 and t[1] + X0 > SEAM - 14 and open_[min(t[2], H - 1), min(max(t[1], 0), W - 1)] > 0.5)]
    for (dx, dy, size, sd) in ((20, 15, 5.2, 41), (-26, 11, 3.6, 42), (9, -13, 4.4, 43)):
        items.append(('stone', int(s9.x - X0 + dx), int(s9.y - Y0 + dy), size, sd))
    out = sorted(items, key=lambda t: t[2])
    G = rng.random((H, W))
    F.draw(g, out, G)
    z2.Bank(int(s9.x - X0 - 6), int(s9.y - Y0 + 6)).draw(g, G)
    oe.Pilzring(int(s9.x - X0 + 24), int(s9.y - Y0 + 14), 9, 5).draw(g, G)
    return g, green


def preview(out, scale=2):
    g, green = render()
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    out_img = mood_map.mood(np.clip(g, 0, 255), dict(w, lights=[], wisps=[]), 2.0, grass_mist=0.45).astype(float)
    d = (1 - green)[..., None]
    out_img = out_img * (1 - 0.26 * d) * (1 + (np.array([0.94, 1.04, 1.04]) - 1) * d)
    Image.fromarray(np.clip(out_img, 0, 255).astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    preview(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2)
    print('ok')
