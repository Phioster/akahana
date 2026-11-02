"""Zone 0-2 of the eastern wood: the poppy meadow runs out into the wood (no edge), the gate clearing with its two
stone lanterns, the first stretch of the moss path. World coordinates; draws the window X0..X1 x Y0..Y1.

    python3 zone0_draft.py OUT.png [scale]      (a graded preview, with the region's darkness)
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import field6  # noqa: E402
from field6 import ground_organic, patches, CMAP, DG as STEM  # noqa: E402
import layout as L  # noqa: E402
import mood_map  # noqa: E402
import objects_water as ow  # noqa: E402
import zone1_draft as z1  # noqa: E402
import zone2_draft as z2  # noqa: E402

ROOT = z1.ROOT
OLD = os.path.join(ROOT, 'build', 'world_old')
X0, Y0, X1, Y1 = 340, 660, 1000, 1060
W, H = X1 - X0, Y1 - Y0
GATE_Y = 820                                      # where the meadow meets the wood (the old Glenn spot, 496/820)
RAMP0, RAMP1 = 380, 760                           # the poppies run out between these two columns
FLOOR_TINT = np.array([0.80, 1.0, 0.96])
MOSS_PATH = np.array([[58, 62, 56], [76, 80, 70], [96, 98, 84]], float)


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def corridor():
    """How open the ground is (1 = meadow-like opening, 0 = wood): a tongue along the path, narrowing with depth."""
    yy, xx = np.mgrid[Y0:Y1, X0:X1]
    cy = GATE_Y + 40 * smooth((xx - 540) / 360.0) + 6 * np.sin(xx / 37.0)
    half = 70 - 30 * smooth((xx - 450) / 420.0)
    return np.clip(1 - (np.abs(yy - cy) / half) ** 2.2, 0, 1)


def render(seed=41):
    rng = np.random.default_rng(seed)
    w = json.load(open(os.path.join(OLD, 'world_old.json')))
    og = np.array(Image.open(os.path.join(OLD, 'ground.png')).convert('RGB')).astype(float)
    ofl = np.array(Image.open(os.path.join(OLD, 'flowers.png')).convert('RGBA'))
    yy, xx = np.mgrid[0:H, 0:W]
    gx = xx + X0
    open_ = corridor()
    # --- ground: the old meadow's own ground first, pixel by pixel giving way to the wood's dark floor
    floor = ground_organic(H, W, np.full((H, W), 0.55), np.zeros((H, W)), rng).astype(float) * 0.55 * FLOOR_TINT
    g = floor.copy()
    old_cols = min(W, 540 - X0)
    g[:, :old_cols] = og[Y0:Y1, X0:X0 + old_cols]
    ext = og[Y0:Y1, 500:540]                                    # the meadow's last columns carry on, shifted: no repeat
    for k in range(old_cols, W):
        g[:, k] = ext[:, (k - old_cols) % 40]
    keep_old = smooth((RAMP1 - gx) / (RAMP1 - 440.0))           # 1 = still meadow ground
    beside = smooth((gx - 500) / 90.0)                           # beside the tongue the wood turns dark sooner, but only inside the wood
    keep_old = np.clip(keep_old * (1 - beside * (1 - open_) * 0.75), 0, 1)
    take_old = rng.random((H, W)) < keep_old
    g = np.where(take_old[..., None], g, floor)
    # --- the old poppies thin out: whole blossoms leave with a probability that grows towards the wood
    heads = np.zeros((H, W, 4), np.uint8)
    fl = ofl[Y0:Y1, X0:X0 + old_cols]
    lab, n = ndi.label(fl[..., 3] > 0, structure=np.ones((3, 3)))
    cx = ndi.center_of_mass(np.ones_like(lab), lab, range(1, n + 1))
    drop = np.zeros(n + 1, bool)
    for i, (cy_, cx_) in enumerate(cx, 1):
        o_ = open_[min(int(cy_), H - 1), min(int(cx_), W - 1)]       # along the wood's rim more of them stay (Philip: lightly, no line)
        p_keep = 1 - smooth((cx_ + X0 - RAMP0) / (540 - RAMP0 + 60.0)) * (0.55 + 0.42 * o_)
        drop[i] = rng.random() > p_keep
    gone = drop[lab]
    sub = heads[:, :old_cols]
    sub[:] = np.where(((fl[..., 3] > 0) & ~gone)[..., None], fl, 0)
    # --- a few new blossoms inside the wood, rarer and rarer
    field6.HEADS[:] = field6.make_heads(np.random.default_rng(31))
    rim = np.clip(1 - np.abs(gx - 560) / 110.0, 0, 1) * (1 - open_)   # a loose band of blossoms along the rim, soft at both sides
    flow = 0.32 * np.clip(1 - (gx - 540) / 220.0, 0, 1) * open_ + 0.22 * rim * (0.6 + 0.4 * ndi.gaussian_filter(rng.random((H, W)), 6) / 0.25).clip(0, 1.4)
    for (x, y, kk, ph) in patches(H, W, flow, np.zeros((H, W), bool), rng, 20000):
        if x + X0 < 540:
            continue
        head = field6.HEADS[kk]
        for j, row in enumerate(head):
            for i, ch in enumerate(row):
                if ch != '.' and y + j < H and x + i < W:
                    heads[y + j, x + i, :3] = CMAP[ch]
                    heads[y + j, x + i, 3] = 255
    return g, heads, open_


def paint_path(g, rng):
    """The moss path from the meadow's edge to the gate and on to the junction; fades out in the poppies."""
    pa = L.paths()
    pts = np.vstack([pa['tor'], pa['moos'], pa['gabel']]).astype(float)
    m = np.zeros((H, W), bool)
    for x, y in pts:
        xi, yi = int(round(x)) - X0, int(round(y)) - Y0
        r = L.PATH_W // 2
        if 0 <= xi < W and 0 <= yi < H:
            m[max(0, yi - r):yi + r + 1, max(0, xi - r):xi + r + 1] = True
    # west of the old edge the trodden strip fades: random pixels only
    xx = np.mgrid[0:W][None, :] + X0
    m &= rng.random((H, W)) < np.clip((xx - 430) / 110.0, 0, 1)
    tone = rng.random((H, W))
    idx = np.digitize(ndi.gaussian_filter(tone, 0.8), [0.46, 0.56])
    g[m] = MOSS_PATH[idx][m]
    edge = m & ~ndi.binary_erosion(m, iterations=1)
    g[edge & (rng.random((H, W)) < 0.45)] *= 0.8
    return m


def things(open_, pmask, rng):
    """Everything standing: firs (none on the tongue or the path), the gate lanterns, young firs along the rim, ferns, rocks."""
    out = []
    gate = L.SPOTS['1']
    taken = np.zeros((H + 60, W + 20), bool)
    keep_free = ndi.binary_dilation(pmask, iterations=7) | (open_ > 0.12)
    gx0, gy0 = gate.x - X0, gate.y - Y0
    yy, xx = np.mgrid[0:H, 0:W]
    inside = np.hypot((xx - gx0) / 1.15, yy - gy0) < gate.r * 1.35
    keep_free |= inside
    for _ in range(int(H * W / 70)):
        x, y = int(rng.integers(-6, W + 6)), int(rng.integers(30, H + 30))
        if x + X0 < 520 or taken[y, x + 6]:
            continue
        xc, yc = min(max(x, 0), W - 1), min(y, H - 1)
        if keep_free[yc, xc]:
            continue
        depth = smooth((x + X0 - 520) / 140.0)
        if rng.random() > 0.15 + 0.85 * depth:
            continue
        taken[max(0, y - 6):y + 7, max(0, x + 6 - 8):x + 6 + 9] = True
        big = rng.random() < 0.35 + 0.5 * depth
        out.append(('fir', x, y, int(rng.integers(30, 50)) if big else int(rng.integers(14, 24)), int(rng.integers(0, 10 ** 6))))
    # young firs and ferns along the tongue's rim, thickening towards the gate
    for _ in range(260):
        x, y = int(rng.integers(30, W - 20)), int(rng.integers(40, H - 8))
        if x + X0 < 500 or keep_free[y, x] or not (0.0 < corridor_at(x, y) + 0.12):
            continue
        near = ndi.binary_dilation(open_ > 0.12, iterations=14)[y, x]
        if not near:
            continue
        if rng.random() < 0.5:
            out.append(('fern', x, y, int(rng.integers(5, 9)), int(rng.integers(0, 10 ** 6))))
        elif rng.random() < 0.6:
            out.append(('fir', x, y, int(rng.integers(12, 20)), int(rng.integers(0, 10 ** 6))))
    out.append(('lantern', int(gate.x - X0 - 22), int(gate.y - Y0 - 6), 0, 0))
    out.append(('lantern', int(gate.x - X0 + 24), int(gate.y - Y0 + 12), 0, 0))
    return sorted(out, key=lambda t: t[2])


_OPEN = None


def corridor_at(x, y):
    global _OPEN
    if _OPEN is None:
        _OPEN = corridor()
    return float(_OPEN[min(max(y, 0), H - 1), min(max(x, 0), W - 1)])


def draw_things(img, items, snow=0.0):
    lights = []
    for kind, x, y, h, sd in items:
        if kind == 'fir':
            a0, b0, a1, b1 = max(0, x - h), max(0, y - h - 4), min(W, x + h), min(H, y + h // 3 + 2)
            if a1 > a0 and b1 > b0:
                z1.Fir(x - a0, y - b0, h, sd, snow=snow).draw(img[b0:b1, a0:a1])
        elif kind == 'fern':
            ow.Farn(x, y, sd, h).draw(img, None)
        elif kind == 'lantern':
            t = z2.Steinlaterne(x, y)
            t.draw(img, None)
            lights += [dict(l, x=l['x'], y=l['y']) for l in t.lights()]
    return lights


def region_dark(gx):
    """The wood's darkness, 0 in the meadow, 1 deep in: what the game's region field does (task 7)."""
    return smooth((gx - 470) / 380.0)


def preview(out, scale=2):
    g, heads, open_ = render()
    rng = np.random.default_rng(5)
    pm = paint_path(g, rng)
    img = g.copy()
    m = heads[..., 3] > 0
    img[m] = heads[m][:, :3]
    items = things(open_, pm, rng)
    lights = draw_things(img, items)
    w = json.load(open(os.path.join(OLD, 'world_old.json')))
    # the old map's own sprites in the window (lanterns, banner): the edge firs go
    for s in w['sprites']:
        if s['name'].startswith('tanne') or not (X0 - 60 < s['x'] < 540 and Y0 - 60 < s['y'] < Y1):
            continue
        a = np.array(Image.open(os.path.join(ROOT, 'assets', 'world', 'sprites', s['name'] + '.png')))[:, :s['w']]
        x_, y_ = s['x'] - X0, s['y'] - Y0
        sub = img[max(0, y_):y_ + a.shape[0], max(0, x_):x_ + a.shape[1]]
        aa = a[max(0, -y_):max(0, -y_) + sub.shape[0], max(0, -x_):max(0, -x_) + sub.shape[1]]
        mm_ = aa[..., 3] > 0
        sub[mm_] = aa[..., :3][mm_]
    ww = dict(w, lights=[dict(l, x=l['x'], y=l['y']) for l in lights], wisps=[])
    out_img = mood_map.mood(np.clip(img, 0, 255), ww, 2.0, grass_mist=0.45).astype(float)
    d = region_dark(np.arange(W)[None, :] + X0)[..., None]
    out_img = out_img * (1 - 0.42 * d) * (1 + (np.array([0.92, 1.04, 1.02]) - 1) * d)
    Image.fromarray(np.clip(out_img, 0, 255).astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    preview(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2)
    print('ok')
