"""Place 5, the ritual place at the far end of the wood: a ring of standing stones around a low altar, stone lanterns, offering
bowls and staffs with cloth, and a tall turquoise shaft of light falling onto the altar. Two paths lead in (from the bridge, from the
Jizo way), the wood thins into fog behind.

    python3 spot5_ritual.py OUT.png [scale]
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import forest as F  # noqa: E402
import layout as L  # noqa: E402
import mood_map  # noqa: E402
import objects_east as oe  # noqa: E402
import zone2_draft as z2  # noqa: E402

S = L.SPOTS['5']
X0, Y0, X1, Y1 = int(S.x) - 120, int(S.y) - 190, int(S.x) + 270, int(S.y) + 110
W, H = X1 - X0, Y1 - Y0
SX, SY = int(S.x - X0), int(S.y - Y0)
CX, CY = SX + 92, SY - 2                                   # the ring stands to the right: the way runs past on its left
TURQ = np.array([0.80, 1.0, 0.90])                           # the shaft's colour: pale moon-white with a little green


def turquoise_flame(img, box):
    """The lanterns burn the wood's one cool colour: warm flame pixels become turquoise."""
    x0, y0, x1, y1 = box
    sub = img[y0:y1, x0:x1]
    m = (sub[..., 0] > 150) & (sub[..., 0] > sub[..., 2] + 40)
    lum = sub.max(-1)
    sub[m] = lum[m][:, None] * TURQ


def render(seed=61):
    rng = np.random.default_rng(seed)
    r2 = np.random.default_rng(43)
    masks = F.window_masks(X0, Y0, X1, Y1)
    yy, xx = np.mgrid[0:H, 0:W]
    own = (((xx - (CX + 56)) / 160.0) ** 2 + ((yy - (CY - 22)) / 92.0) ** 2) < 1       # the open ground of the ring and the hall
    own = ndi.binary_opening(own | ndi.binary_dilation(own, iterations=3), iterations=2)
    masks = dict(masks, clearing=masks['clearing'] | own)
    img = F.floor(H, W, masks, r2)
    F.draw(img, F.scatter(H, W, masks, r2), r2.random((H, W)))
    G = rng.random((H, W))
    lights = []
    # a ring of standing stones: an ellipse (we look from above at an angle), irregular angles and heights, open toward the two paths
    ang = np.sort(rng.uniform(0, 2 * np.pi, 0))
    ring = []
    for k in range(11):
        a = k / 11 * 2 * np.pi + rng.uniform(-0.18, 0.18)
        ring.append((CX + int(np.cos(a) * 68), CY + int(np.sin(a) * 38), a))
    pys, pxs = np.nonzero(masks['path'])
    things = []
    for x, y, a in ring:
        if masks['path'][max(y - 4, 0):y + 5, max(x - 8, 0):x + 9].any():
            continue                                                         # the ring is open where a way enters
        things.append(('stele', x, y, int(rng.integers(0, 10 ** 6)), float(rng.uniform(1.25, 1.9))))
    things += [('altar', CX, CY + 4, 5, 1.0)]
    for dx, dy in ((-26, -12), (-9, -14), (10, -13), (27, -11)):
        pass
    things += [('bowl', CX - 9, CY - 1, 11, 1), ('bowl', CX + 4, CY - 3, 12, 1), ('bowl', CX + 15, CY, 13, 1)]
    for dx, dy in ((-52, -56), (56, -58), (-30, 52)):                         # lanterns outside the ring, none on the way
        things.append(('lantern', CX + dx, CY + dy, 0, 1))
    things.append(('halle', CX + 112, CY - 74, 3, 1))
    things.append(('lantern', CX + 84, CY - 58, 0, 1)); things.append(('lantern', CX + 140, CY - 58, 0, 1))
    for dx, dy in ((-38, 32), (34, 36), (-62, -14), (68, -16), (4, 48)):      # staffs with faded cloth, bowls at the foot of the stones
        things.append(('stab', CX + dx, CY + dy, int(rng.integers(0, 10 ** 6)), 1))
    for x, y, a in ring[::3]:
        things.append(('bowl', x + 6, y + 6, int(rng.integers(0, 10 ** 6)), 1))
    things.append(('cairn', CX - 72, CY - 34, 41, 1)); things.append(('cairn', CX + 78, CY + 40, 42, 1))
    for kind, x, y, sd, size in sorted(things, key=lambda t: t[2]):
        if not (0 <= x < W and 0 <= y < H):
            continue
        if kind in ('stele', 'cairn'):                                       # shadow on the ground, lower right
            for j in range(-1, 3):
                for i in range(2, 11):
                    xx, yy = x + i, y + j
                    if 0 <= yy < H and 0 <= xx < W and (i - 6) ** 2 / 20 + (j - 0.5) ** 2 / 2.4 < 1:
                        img[yy, xx] *= 0.62
        if kind == 'stele':
            oe.Stele(x, y, sd, size).draw(img, G)
        elif kind == 'halle':
            oe.Halle(x, y, sd).draw(img, G)
        elif kind == 'altar':
            oe.Altar(x, y, sd).draw(img, G)
        elif kind == 'bowl':
            oe.Opferschale(x, y, sd).draw(img, G)
        elif kind == 'stab':
            oe.Stab(x, y, sd, 1, int(rng.integers(15, 21))).draw(img, G)
        elif kind == 'cairn':
            oe.Steinhaufen(x, y, sd, 6).draw(img, G)
        elif kind == 'lantern':
            t = z2.Steinlaterne(x, y)
            t.draw(img, None)
            lights.append(t.lights()[0])
    return img, masks, lights


def preview(out, scale=3):
    img, masks, lights = render()
    w = json.load(open(os.path.join(F.ROOT, 'build', 'world_old', 'world_old.json')))
    g = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=[], wisps=[]), 2.0, grass_mist=0.45).astype(float)
    g = g * (1 - 0.26) * np.array([0.94, 1.04, 1.04])
    yy, xx = np.mgrid[0:H, 0:W]
    for l in lights:                                                         # cool glow of the lanterns
        d = np.hypot(xx - l['x'], yy - l['y']) / 26.0
        g += (np.exp(-d * d * 2.2)[..., None] * 80 * np.array([1.0, 0.62, 0.22]))
    # the shaft of light: a tall, slightly widening column above the altar, brightest at the altar, with a pool on the ground
    top = 0
    t = np.clip((CY - 8 - yy) / max(CY - 8 - top, 1), 0, 1)
    half = 11 + 9 * t
    col = np.exp(-(((xx - CX) / half) ** 2) * 1.6) * (yy < CY - 4) * (1 - 0.82 * t) ** 1.2
    pool = np.exp(-(((xx - CX) / 46.0) ** 2 + ((yy - CY - 4) / 17.0) ** 2))
    g += col[..., None] * 48 * TURQ + pool[..., None] * 30 * TURQ
    g = np.clip(g, 0, 255)
    Image.fromarray(g.astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    preview(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 3)
    print('ok')
