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
    img, masks = F.render_window(X0, Y0, X1, Y1, seed=41)
    G = rng.random((H, W))
    cx, cy = int(S.x - X0), int(S.y - Y0)
    things = [('jizo',) + j for j in along(L.paths()['jizo'], rng)]
    things += [('schrein', cx + 6, cy - 22, 7, True), ('lantern', cx - 22, cy - 14, 0, True), ('lantern', cx + 36, cy - 14, 0, True),
               ('bowl', cx + 4, cy - 12, 5, True), ('stone', cx - 38, cy + 26, 9, True), ('jizo', cx + 44, cy + 14, 21, True),
               ('jizo', cx - 14, cy + 30, 22, False)]
    lights = []
    for kind, x, y, sd, flag in sorted(things, key=lambda t: t[2]):
        if kind == 'lantern':
            t = z2.Steinlaterne(x, y)
            t.draw(img, None)
            lights.extend(t.lights())
        elif kind == 'jizo':
            oe.Jizo(x, y, sd, cap=flag, lean=int(rng.integers(-1, 2))).draw(img, G)
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
