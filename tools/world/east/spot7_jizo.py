"""Place 7, the Jizo way: small stone figures with red bibs along the path, ending in a tiny shrine in a clearing where the
way from the south joins in.

    python3 spot7_jizo.py OUT.png [scale]
"""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import forest as F  # noqa: E402
import layout as L  # noqa: E402
import mood_map  # noqa: E402
import objects_east as oe  # noqa: E402
import zone2_draft as z2  # noqa: E402

S = L.SPOTS['7']
X0, Y0, X1, Y1 = int(S.x) - 190, int(S.y) - 120, int(S.x) + 120, int(S.y) + 120
W, H = X1 - X0, Y1 - Y0


def along(path, rng):
    """Jizo positions along the last 150 px of the way before the clearing: irregular spacing, to either side of the path."""
    pts = np.array([(x - X0, y - Y0) for x, y in path])
    d = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
    out, t, side = [], d[-1] - 62, 1
    while t > d[-1] - 215:
        k = int(np.searchsorted(d, t))
        k = min(max(k, 1), len(pts) - 1)
        tang = pts[k] - pts[k - 1]
        nrm = np.array([-tang[1], tang[0]]) / (np.linalg.norm(tang) + 1e-9)
        p = pts[k] + nrm * side * rng.uniform(13, 19)
        out.append((int(p[0]), int(p[1]), int(rng.integers(0, 10 ** 6)), bool(rng.random() < 0.7)))
        t -= rng.uniform(26, 44)
        side = -side if rng.random() < 0.75 else side
    return out


def render(seed=51):
    rng = np.random.default_rng(seed)
    r2 = np.random.default_rng(41)
    masks = F.window_masks(X0, Y0, X1, Y1)
    img = F.floor(H, W, masks, r2)
    items = F.scatter(H, W, masks, r2)
    G = rng.random((H, W))
    cx, cy = int(S.x - X0), int(S.y - Y0)
    # the shrine stands beside the path, not on it: the nearest free spot to the clearing's middle
    from scipy import ndimage as ndi
    pth = ndi.binary_dilation(masks['path'], iterations=14)
    sy = cy - 22
    sx = next(cx + d for d in sorted(range(-60, 61), key=abs) if not pth[sy - 8:sy + 6, cx + d - 15:cx + d + 16].any())
    things = [('jizo',) + j for j in along(L.paths()['jizo'], rng)]
    things += [('schrein', sx, sy, 7, True), ('lantern', sx - 28, sy + 8, 0, True), ('lantern', sx + 28, sy + 8, 0, True),
               ('bowl', sx + 2, sy + 10, 5, True), ('stone', cx - 44, cy + 26, 9, True), ('jizo', cx + 50, cy + 18, 21, True),
               ('jizo', cx - 20, cy + 34, 22, False)]
    # no tree grows over a figure or the shrine: drop the trees whose crowns would reach them
    items = [t for t in items if not any(abs(t[1] - x) < 30 and y - 6 < t[2] < y + 78 for k, x, y, *_ in things if k in ('jizo', 'schrein'))]
    F.draw(img, items, rng.random((H, W)))
    jz = [i for i, t in enumerate(things) if t[0] == 'jizo']
    for n, i in enumerate(jz):                                              # only one figure keeps the red bib
        t = things[i]
        things[i] = (t[0], t[1], t[2], t[3], (t[4], n == 2))
    lights = []
    for kind, x, y, sd, flag in sorted(things, key=lambda t: t[2]):
        if kind == 'lantern':
            t = z2.Steinlaterne(x, y)
            t.draw(img, None)
            lights.extend(t.lights())
        elif kind == 'jizo':
            cap, bib = flag if isinstance(flag, tuple) else (flag, False)
            oe.Jizo(x, y, sd, cap=cap, bib=bib, lean=int(rng.integers(-1, 2))).draw(img, G)
        elif kind == 'schrein':
            oe.Schrein(x, y, sd).draw(img, G)
        elif kind == 'bowl':
            oe.Opferschale(x, y, sd).draw(img, G)
        elif kind == 'stone':
            oe.MoosStein(x, y, 6.0, sd).draw(img, G)
    return img, masks, lights


def preview(out, scale=3):
    img, masks, lights = render()
    w = json.load(open(os.path.join(F.ROOT, 'build', 'world_old', 'world_old.json')))
    g = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=lights, wisps=[]), 2.0, grass_mist=0.45).astype(float)
    g = g * (1 - 0.26) * np.array([0.94, 1.04, 1.04])
    Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    preview(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    print('ok')
