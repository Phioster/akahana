"""Place 6, the old stone bridge with arches over the river, where the way to the ritual place crosses it.

    python3 spot6_bridge.py OUT.png [scale]
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

S = L.SPOTS['6']
X0, Y0, X1, Y1 = int(S.x) - 140, int(S.y) - 130, int(S.x) + 140, int(S.y) + 120
W, H = X1 - X0, Y1 - Y0


def render(seed=37):
    rng = np.random.default_rng(seed)
    river = np.array(L.river())
    k = int(np.argmin(np.hypot(river[:, 0] - S.x, river[:, 1] - S.y)))
    bx, by = int(river[k, 0]) - X0, int(river[k, 1]) - Y0               # where the river passes the spot's middle
    deck_y = int(S.y - Y0)
    front = deck_y + 6                                                   # the deck's front edge row; the wall's foot is FACE lower
    # the river, widened to the bridge's span for a short stretch, narrow elsewhere
    im = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(im)
    d.line([(x - X0, y - Y0) for x, y in river], fill=1, width=L.RIVER_W, joint='curve')
    span = np.zeros((H, W), bool)
    yy, xx = np.mgrid[0:H, 0:W]
    ctr = bx
    wide = np.abs(xx - ctr) < 14 * np.clip(1 - np.abs(yy - (front + 12)) / 40.0, 0, 1) ** 0.6 + 7
    span = wide & (np.abs(yy - (front + 12)) < 40)
    water = (np.array(im) > 0) | span
    masks = F.window_masks(X0, Y0, X1, Y1)
    land = ndi.binary_dilation(water, iterations=4)
    masks2 = {'path': masks['path'], 'clearing': masks['clearing'] | ndi.binary_dilation(span, iterations=14), 'river': water}
    img = F.floor(H, W, masks2, rng)
    shallow = water & (ndi.distance_transform_edt(water) < 4)
    ol.paint_lake(img, 0, water, shallow, rng)
    G = rng.random((H, W))
    items = F.scatter(H, W, masks2, rng)
    items = [t for t in items if t[0] != 'giant']
    # the way crosses the bridge: the pale paving of the deck is the path there; trees first, the bridge over them
    F.draw(img, items, G)
    ys, xs = np.nonzero(ndi.binary_dilation(water, iterations=3) & ~water & ~masks['path'])
    for _ in range(34):
        i = int(rng.integers(0, len(ys)))
        (ow.Schilf(int(xs[i]), int(ys[i]), int(rng.integers(4, 8)), int(rng.integers(0, 10 ** 6))) if rng.random() < 0.6 else ow.Farn(int(xs[i]), int(ys[i]), int(rng.integers(0, 10 ** 6)), int(rng.integers(5, 9)))).draw(img, G)
    oe.Steinbruecke(bx, front - oe.Steinbruecke.FACE - 6, 4).draw(img, G)
    return img, water


def preview(out, scale=3):
    img, water = render()
    w = json.load(open(os.path.join(F.ROOT, 'build', 'world_old', 'world_old.json')))
    g = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=[], wisps=[]), 2.0, grass_mist=0.45).astype(float)
    g = g * (1 - 0.26) * np.array([0.94, 1.04, 1.04])
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    preview(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    print('ok')
