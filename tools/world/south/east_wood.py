"""The placeholder wood east of the old map (columns 3-4, rows 0-5): closed, not to be entered, the eastern
wood with its ritual place comes later. Firs as the old map's edges have them, snowier the further north,
and across the top the old cliff of snow-capped boulders runs on. One baked picture: nobody can walk in
there, so nothing needs sorting against the wanderer.

    python3 east_wood.py OUT.png      (a mood preview beside the old map)
"""
import os
import sys

import numpy as np
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import field6  # noqa: E402
from field6 import ground_organic, patches, CMAP, DG as STEM  # noqa: E402
import zone1_draft as z1  # noqa: E402

H, X0, X1 = z1.OLD_H - z1.CTX, z1.OLD_W, z1.W      # down to where zone 1's canvas (and its wood) begins
WD = X1 - X0
DG, MG, L1, WH = [np.array(c, float) for c in ((92, 96, 104), (140, 144, 150), (186, 190, 196), (232, 234, 236))]


def snow_at(y):
    """Like the old map's pines up the slope; down at zone 1's wood it is the same thin dusting."""
    return 0.08 + 0.84 * float(np.clip((900 - y) / 700, 0, 1))


def render(seed=73):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:H, 0:WD]
    fog = np.full((H, WD), 0.55)
    alt = np.clip((900 - yy) / 700, 0, 1)                         # 1 up in the snow, 0 down by zone 1
    floor = ground_organic(H, WD, fog, np.zeros_like(fog), rng).astype(float)
    deep = 0.62 + 0.3 * alt
    k = 1 - (1 - deep) * np.clip(xx / 50.0, 0, 1)                # at the old map's edge as light as its ground
    g = floor * k[..., None]                                     # needle floor below, lighter snow ground above
    sn = ndi.gaussian_filter(rng.random((H, WD)), 1.2)
    lie = sn < 0.42 + 0.3 * alt - 0.3
    g[lie] = WH * (0.8 + 0.12 * alt[lie, None])                  # snow lying between the trunks
    # the seam: the old map's own ground carries on, pixel by pixel giving way to the wood's floor
    from PIL import Image
    old = np.array(Image.open(os.path.join(z1.ROOT, 'build', 'world_full', 'ground.png')).convert('RGB')).astype(float)
    src = old[np.clip(yy + 37, 0, old.shape[0] - 1), X0 - 45 + (xx % 45)]   # shifted, so nothing repeats beside itself
    take = rng.random((H, WD)) < np.clip(1 - xx / 60.0, 0, 1) ** 0.8
    g[take] = src[take]
    G = rng.random((H, WD))

    def boulder(x_, y_, rx, ry):                                 # as gen_world's cliff foot
        e = ((xx - x_) / rx) ** 2 + ((yy - y_) / ry) ** 2
        g[(e <= 1.6) & (yy > y_) & (xx > x_ - 1)] = DG
        m = e <= 1.0
        lit = (xx - x_) + (yy - y_) * 1.3 < -0.5
        g[m] = MG
        g[m & lit] = L1
        g[m & lit & (e < 0.3)] = WH
        g[m & (yy > y_ + ry * 0.4)] = DG
        g[m & (yy < y_ - ry * 0.3) & (G < 0.8)] = WH

    for x_ in range(-6, WD + 12, 13):                            # the cliff runs on across the top
        boulder(x_ + rng.integers(-3, 4), int(18 + rng.integers(-4, 6)), rng.uniform(9, 14), rng.uniform(8, 12))
        boulder(x_ + 6, int(36 + rng.integers(-3, 5)), rng.uniform(5, 8), rng.uniform(3.5, 5))
    for _ in range(40):                                          # boulders up the slope, fewer further down
        x_, y_ = int(rng.integers(6, WD - 6)), int(rng.integers(50, 700))
        if rng.random() < alt[y_, 0] * 1.1:
            boulder(x_, y_, rng.uniform(2.5, 6), rng.uniform(1.8, 3.6))

    # how thick the wood stands: thin at the old map's edge, glades here and there, denser further in
    glade = ndi.gaussian_filter(rng.normal(0, 1, (H, WD)), 22)
    glade /= glade.std()
    dens = np.clip(0.08 + xx / 150.0, 0, 1) * np.clip(0.8 - 0.6 * glade, 0, 1) * (0.7 + 0.3 * (1 - alt))
    taken = np.zeros((H + 60, WD + 20), bool)                    # one trunk per little patch of ground
    firs = []
    for _ in range(int(H * WD / 110)):                           # scattered, not in rows
        x, y = int(rng.integers(-6, WD + 6)), int(rng.integers(50, H + 40))
        if rng.random() > dens[min(y, H - 1), min(max(x, 0), WD - 1)] or taken[y, x + 6]:
            continue
        taken[max(0, y - 6):y + 7, max(0, x + 6 - 9):x + 6 + 10] = True
        firs.append((x, y, int(rng.integers(28, 50)), int(rng.integers(0, 10 ** 6))))
    before = g.copy()
    for (x, y, h, sd) in sorted(firs, key=lambda f: f[1]):       # each on its own small canvas: fast
        a0, b0 = max(0, x - h), max(0, y - h - 4)
        a1, b1 = min(WD, x + h), min(H, y + h // 3 + 2)
        if a1 <= a0 or b1 <= b0:
            continue
        sub = g[b0:b1, a0:a1]
        z1.Fir(x - a0, y - b0, h, sd, snow=snow_at(y)).draw(sub)
    trees = np.abs(g - before).sum(-1) > 0.5

    # the seam: a ragged fringe of single firs straddling it, as sprites (the old map's picture stays as it is)
    fringe = []
    for y in range(60, H + 30, 7):
        for _ in range(2):
            x = int(rng.normal(8, 13))
            if -22 <= x <= 40 and rng.random() < (0.35 + 0.5 * np.clip((x + 22) / 50, 0, 1)):
                fringe.append(z1.Fir(X0 + x, y + int(rng.integers(-3, 4)), int(rng.integers(30, 48)),
                                     int(rng.integers(0, 10 ** 6)), snow=snow_at(y)))

    # the poppies of the old meadow run a little way in under the first trees, thinning out
    field6.HEADS[:] = field6.make_heads(np.random.default_rng(31))
    flow = 0.45 * np.clip(1 - xx / 70.0, 0, 1) * np.clip((yy - 330) / 60.0, 0, 1)
    heads = np.zeros((H, WD, 4), np.uint8)
    for (x, y, kk, ph) in patches(H, WD, flow, ndi.binary_dilation(trees, iterations=2), rng, 60000):
        head = field6.HEADS[kk]
        for s_ in range(len(head), len(head) + 2):
            for sx_ in (x + 1, x + 2):
                if y + s_ < H and (sx_ + y + s_) % 2 == 0 and not trees[y + s_, sx_]:
                    g[y + s_, sx_] = STEM
        for j, row in enumerate(head):
            for i, ch in enumerate(row):
                if ch != '.' and y + j < H and x + i < WD:
                    heads[y + j, x + i, :3] = CMAP[ch]
                    heads[y + j, x + i, 3] = 255
    return np.clip(g, 0, 255), heads, fringe


def old_sprites_kept(sprites):
    """The old map's east edge firs go: the wood now runs on behind them, the meadow opens into it."""
    return [s for s in sprites if not (s['name'].startswith('tanne') and s['x'] + s['w'] / 2 > X0 - 25)]


if __name__ == '__main__':
    import json
    from PIL import Image
    import mood_map
    out = sys.argv[1]
    with open(os.path.join(z1.ROOT, 'build', 'world_full', 'world_old.json')) as f:
        w = json.load(f)
    w = dict(w, sprites=old_sprites_kept(w['sprites']))
    old = mood_map.composite(w)
    img = np.zeros((z1.OLD_H, z1.W, 3))
    img[:, :X0] = old
    eg, eh, fr = render()
    img[:H, X0:] = eg
    m = eh[..., 3] > 0
    img[:H, X0:][m] = eh[m][:, :3]
    for f_ in sorted(fr, key=lambda f_: f_.p.y):
        h = 50
        a0, b0 = f_.p.x - h, max(0, f_.p.y - h - 4)
        sub = img[b0:f_.p.y + 20, a0:f_.p.x + h]
        f_.p.x -= a0
        f_.p.y -= b0
        f_.draw(sub)
    img[H:, X0:] = img[H - 1, X0:]
    a = mood_map.mood(img, w, 2.0)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)[:H, 300:]).save(out)
    print('ok')
