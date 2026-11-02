"""Place 4, the pond: a still dark pond in the wood, a giant moss tree leaning over it from the west bank, a short jetty,
reeds and lilies, sitting stones, the river coming in from the north-east and the brook leaving to the south.

    python3 spot4_pond.py OUT.png [scale]
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
import objects_lake as ol  # noqa: E402
import objects_water as ow  # noqa: E402

S = L.SPOTS['4']
X0, Y0, X1, Y1 = int(S.x) - 135, int(S.y) - 125, int(S.x) + 135, int(S.y) + 125
W, H = X1 - X0, Y1 - Y0


def water_masks():
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    cx, cy = S.x, S.y
    pts = [(cx + (x - cx) * 0.62 - X0, cy + (y - cy) * 0.62 - Y0) for x, y in L.blob(S, k=0.22)]
    d.polygon(pts, fill=1)
    lake = np.array(im) > 0
    rv = Image.new('L', (W, H), 0)
    ImageDraw.Draw(rv).line([(x - X0, y - Y0) for x, y in L.river()], fill=1, width=L.RIVER_W, joint='curve')
    bv = Image.new('L', (W, H), 0)
    ImageDraw.Draw(bv).line([(x - X0, y - Y0) for x, y in L.bach()], fill=1, width=9, joint='curve')
    river, bach = np.array(rv) > 0, np.array(bv) > 0
    return lake, river, bach


def render(seed=29):
    rng = np.random.default_rng(seed)
    lake, river, bach = water_masks()
    water = lake | river | bach
    masks = F.window_masks(X0, Y0, X1, Y1)
    land_clear = ndi.binary_dilation(lake, iterations=18) & ~water
    masks2 = {'path': masks['path'], 'clearing': masks['clearing'] | land_clear, 'river': water}
    img = F.floor(H, W, masks2, rng)
    # the water, painted like the south's lake; shallow at the rim
    shallow = water & (ndi.distance_transform_edt(water) < 5)
    ol.paint_lake(img, 0, water, shallow, rng)
    items = F.scatter(H, W, masks2, rng)
    items = [t for t in items if t[0] not in ('giant',)]
    G = rng.random((H, W))
    F.draw(img, items, G)
    # the shore: reeds and cattails, lilies out on the water
    ring = ndi.binary_dilation(water, iterations=4) & ~ndi.binary_dilation(water, iterations=1) & ~masks['path']
    ys, xs = np.nonzero(ring)
    for _ in range(46):
        i = int(rng.integers(0, len(ys)))
        (ow.Schilf if rng.random() < 0.7 else ow.Rohrkolben)(int(xs[i]), int(ys[i]), int(rng.integers(4, 9)), int(rng.integers(0, 10 ** 6))).draw(img, G)
    inner = lake & (ndi.distance_transform_edt(lake) > 9)
    ys, xs = np.nonzero(inner)
    for _ in range(4):
        i = int(rng.integers(0, len(ys)))
        ol.Seerosen(int(xs[i]), int(ys[i]), int(rng.integers(4, 8)), int(rng.integers(0, 10 ** 6))).draw(img, G)
    # the giant tree first, then what stands in front of it: sitting stones, the jetty
    trow = int(S.y - Y0 - 6)
    tshore = int(np.nonzero(lake[trow])[0].min())
    tx, ty = tshore - 10, trow + 20
    oe.Riesenbaum(tx, ty, 11, 2.1, lean=14).draw(img, G)
    oe.MoosStein(tx + 14, ty + 6, 6.5, 5).draw(img, G)                      # sitting stones at the foot of the tree
    oe.MoosStein(tx + 25, ty + 10, 5.0, 6).draw(img, G)
    row = int(S.y - Y0 + 28)
    shore = int(np.nonzero(lake[row])[0].min())
    ol.Steg(row, shore - 10, shore + 34, 7, across=True, dry=shore + 1).draw(img, G)
    return img


def preview(out, scale=3):
    img = render()
    w = json.load(open(os.path.join(F.ROOT, 'build', 'world_old', 'world_old.json')))
    g = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=[], wisps=[]), 2.0, grass_mist=0.45).astype(float)
    g = g * (1 - 0.26) * np.array([0.94, 1.04, 1.04])
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    preview(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    print('ok')
