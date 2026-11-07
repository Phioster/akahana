#!/usr/bin/env python3
"""West zone 1 draft (plan step 61): the way in from the camp fire, the village square with its well and the nine
empty houses in their overgrown gardens. West coordinates: the world grows by WW columns to the left, today's x 0
is WW here. Today's world (build/world_full) is drawn for real east of WW, its fir wall at the edge removed.

    python3 dorf1_draft.py OUT.png [scale]   (not zone1_draft: the south has one, z2 imports it)"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import field6  # noqa: E402
from field6 import patches, CMAP  # noqa: E402
import extras  # noqa: E402
import mood_map  # noqa: E402
import objects_west as o  # noqa: E402
import zone2_draft as z2  # noqa: E402   (the south's: Blade, Wildflower, Bank, Steinlaterne)
from objects_south import Fackel, Kerzen  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
FULL = os.path.join(ROOT, 'build', 'world_full')
WW = 900                                   # columns the world grows to the west
X0, Y0, X1, Y1 = 230, 1990, 1180, 2770     # the window drawn (west coordinates)
W, H = X1 - X0, Y1 - Y0
EDGE = 24                                  # today's columns 0..EDGE are the fir wall: they go
SQUARE = (520, 2330)
GLASHAUS = (680, 2600)                     # zone 2: the greenhouse's foot (front wall middle)
STEINMETZ = (330, 2500)                    # zone 2: the stonemason's house, its workshop on the east
FIRE = (222 + WW, 2292)
# (garden centre, house seed, roof kind, how fallen in); the house stands at the back of its plot, facing south
HOUSES = [((380, 2180), 1, 'kawara', 0.5), ((560, 2150), 2, 'kaya', 0.8), ((690, 2230), 3, 'kawara', 0.35),
          ((300, 2320), 4, 'kaya', 0.6), ((410, 2420), 5, 'kawara', 0.7), ((720, 2400), 6, 'kaya', 0.45),
          ((540, 2490), 7, 'kawara', 0.9), ((250, 2610), 8, 'kawara', 0.55), ((430, 2640), 9, 'kaya', 0.65)]
PATHS = {
    'eingang': [(FIRE[0] - 14, FIRE[1] + 10), (1040, 2312), (930, 2300), (820, 2306), (700, 2322), (600, 2334),
                (SQUARE[0] + 16, SQUARE[1] + 2)],
    'nord': [(SQUARE[0] - 6, SQUARE[1] - 14), (500, 2250), (470, 2150), (446, 2060), (430, 1990)],
    'sued': [(SQUARE[0] + 8, SQUARE[1] + 14), (560, 2420), (620, 2520), (600, 2620), (540, 2700), (470, 2770)],
    'glas': [(603, 2600), (626, 2619), (656, 2623), (680, 2611)],              # zone 2: below the beds to the door
    'west': [(SQUARE[0] - 16, SQUARE[1] + 4), (420, 2360), (350, 2440), (300, 2470), (250, 2520)],
}


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def fbm(h, w, s, seed):
    n = ndi.gaussian_filter(np.random.default_rng(seed).normal(0, 1, (h, w)), s)
    return n / n.std()


def today():
    g = np.array(Image.open(os.path.join(FULL, 'ground.png')).convert('RGB')).astype(float)
    fl = np.array(Image.open(os.path.join(FULL, 'flowers.png')).convert('RGBA'))
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    return g, fl, w


def ground(og, rng):
    """Today's ground is kept east of the fir wall; west of it the light and dark patches of today's meadow run on
    into fresh ones (the south's way of growing ground: south/ground.py), so there is no seam and no stripes."""
    import ground as sg
    n = WW + EDGE - X0                                   # new columns, counted from the seam leftwards
    old_t = sg.tone_of(og[Y0:Y1, EDGE:EDGE + 80])        # (H, 80): column d = d px east of the seam
    fog = np.clip(0.70 + 0.10 * fbm(H, n, 18, 11), 0, 1)
    flow = np.clip(0.20 + 0.10 * fbm(H, n, 10, 12), 0, 1)
    new_t = sg.fresh_tone(H, n, fog, flow, rng)          # column d = d px west of the seam
    t = sg.continued_tone(old_t[:, ::-1].T, new_t.T, reach=70).T     # mirrored at the seam, then fresh
    newg = sg.ground_from_tone(t, fog, flow, rng)[:, ::-1]
    g = np.zeros((H, W, 3))
    g[:, :n] = newg
    g[:, n:] = og[Y0:Y1, EDGE:EDGE + W - n]
    return g


def path_masks(rng):
    mask = np.zeros((H, W), bool)
    for name, pts in PATHS.items():
        local = [(x - X0, y - Y0) for x, y in pts]
        m, core, d, width = extras.path_mask(H, W, local, rng)
        mask |= m
        yield name, m, core, d, width


def main(out, scale=2):
    rng = np.random.default_rng(61)
    og, ofl, w = today()
    img = ground(og, rng)
    yy, xx = np.mgrid[0:H, 0:W]
    gx, gy = xx + X0, yy + Y0
    G = np.random.default_rng(3).random((H, W))

    # ---- the square: trodden gravel round the well
    sq = extras.forecourt(H, W, SQUARE[0] - X0, SQUARE[1] - Y0, 46, 26, rng)
    extras.draw_gravel(img, sq, rng)
    # ---- paths (earth, like the old ones)
    pathm = np.zeros((H, W), bool)
    for name, m, core, d, width in path_masks(rng):
        extras.draw_path(img, m, core, d, width, rng)
        pathm |= m
    pathm |= sq
    LAWN = np.array([0.60, 0.74, 0.56])

    # ---- houses and their gardens
    things, lights = [], []
    blocked = pathm.copy()                       # no grass, no poppies here
    plots = np.zeros((H, W))                     # 1 inside a garden plot
    for (cx, cy), seed, kind, ruin in HOUSES:
        r = np.random.default_rng(seed * 11)
        hx_, hy_ = cx - X0 + int(r.integers(-6, 7)), cy - Y0 - 10
        hw = int(r.integers(40, 50))
        house = o.Minka(hx_, hy_, w=hw, seed=seed, kind=kind, ruin=ruin,
                        roof=17 if kind == 'kawara' else 19, pal=seed // 2 + seed % 2)
        things.append(house)
        blocked[hy_ - 34:hy_ + 4, hx_ - hw // 2 - 6:hx_ + hw // 2 + 8] = True
        left, right, top, bot = cx - 55 - X0, cx + 55 - X0, cy - 48 - Y0, cy + 50 - Y0
        e = ((xx - (left + right) / 2) / 56.0) ** 2 + ((yy - (top + bot) / 2) / 50.0) ** 2 + 0.15 * fbm(H, W, 6, seed)
        plots = np.maximum(plots, smooth((1.05 - e) / 0.25))
        # the plot's rim: a fence or a dry-stone wall all along the front, a gap where the stones lead out, the
        # sides half fallen
        gate = hx_ + int(r.integers(-8, 9))
        Fence = (lambda pts, k: o.Bambuszaun(pts, seed=seed + k, ruin=ruin)) if r.random() < 0.65 else \
            (lambda pts, k: o.Steinmauer(pts, seed=seed + k))
        things.append(Fence([(left, bot), (gate - 6, bot + 1)], 0))
        things.append(Fence([(gate + 6, bot + 1), (right, bot)], 1))
        for side, k in ((left, 2), (right, 3)):
            if r.random() < 0.75:
                y_a = top + int(r.integers(30, 50))
                things.append(o.Bambuszaun([(side, y_a), (side + int(r.integers(-1, 2)), bot - 3)], seed=seed + k,
                                           ruin=min(1, ruin + 0.3)))
        things.append(o.Platten((hx_ + int(r.integers(-4, 5)), hy_ + 5), (gate, bot + 4), seed=seed))
        blocked[hy_ + 3:bot + 6, gate - 4:gate + 5] = True
        # the garden: hydrangeas along the house, a bed, a fruit tree, things left behind
        for k in range(int(r.integers(4, 7))):
            things.append(o.Hortensie(hx_ + int(r.choice([-1, 1])) * int(r.integers(hw // 2 + 4, hw // 2 + 14)),
                                      hy_ + int(r.integers(2, 30)), int(r.integers(5, 8)),
                                      str(r.choice(['blau', 'lila', 'rosa'])), seed * 7 + k))
        bx = int(r.integers(left + 6, right - 30))
        things.append(o.Beet(bx, hy_ + int(r.integers(24, 40)), w=int(r.integers(14, 22)), rows=int(r.integers(3, 5)),
                             seed=seed))
        blocked[hy_ + 10:hy_ + 42, bx - 1:bx + 24] = True
        if r.random() < 0.8:
            things.append(o.Obstbaum(int(r.choice([left + 14, right - 14])), hy_ + int(r.integers(28, 44)), seed=seed))
        if seed in (1, 4, 6, 8):                     # candles left on the veranda of a few houses (Philip, round 2)
            side = -1                                # left of the door, on the veranda (Philip)
            cx_ = hx_ + side * int(r.integers(8, hw // 2 - 4))
            pts = [(cx_, hy_ + 1), (cx_ + 3, hy_ + 2), (cx_ - 3, hy_ + 2)]
            k = Kerzen(pts[:int(r.integers(2, 4))], seed=seed, on=house)   # the south's candles, two or three, drawn after the house
            things.append(k)
            lights += k.lights()
        prop = r.random()
        if prop < 0.35:
            things.append(z2.Bank(hx_ + int(r.choice([-1, 1])) * (hw // 2 - 8), hy_ + 7))   # beside the stones, not on them
        elif prop < 0.65:
            things.append(o.Waescheleine(hx_ + hw // 2 + 2, hy_ + 18, seed=seed))
        else:
            things.append(o.Korb(hx_ + int(r.integers(-hw // 2, hw // 2)), hy_ + 5))

    lawn = plots[..., None] * ~pathm[..., None]
    img = img * (1 - lawn) + img * LAWN * lawn                   # short garden grass: greener, a little darker
    # ---- zone 2: the greenhouse and the stonemason
    gh = o.Gewaechshaus(GLASHAUS[0] - X0, GLASHAUS[1] - Y0)
    things.append(gh)
    lights += gh.lights()
    x0b, y0b, x1b, y1b = gh.box()
    blocked[max(0, y0b):y1b, max(0, x0b):x1b] = True
    st = o.Steinmetz(STEINMETZ[0] - X0, STEINMETZ[1] - Y0)
    things.append(st)
    x0b, y0b, x1b, y1b = st.box()
    blocked[max(0, y0b):y1b, max(0, x0b):x1b] = True
    for k, (bx_, by_, bw, bh) in enumerate([(376, 2512, 7, 4), (388, 2508, 5, 6), (352, 2514, 9, 3), (392, 2518, 6, 3)]):
        things.append(o.Block(bx_ - X0, by_ - Y0, w=bw, h=bh, seed=50 + k))
        blocked[by_ - Y0 - 10:by_ - Y0 + 3, bx_ - X0 - 2:bx_ - X0 + bw + 6] = True
    # ---- the well, lanterns at the square and the way in, a torch by the first house
    things.append(o.Brunnen(SQUARE[0] - X0, SQUARE[1] - Y0 + 4))
    for (x, y) in ((SQUARE[0] - 34, SQUARE[1] - 10), (SQUARE[0] + 40, SQUARE[1] + 12), (860, 2290)):
        t = z2.Steinlaterne(x - X0, y - Y0)
        things.append(t)
        lights += t.lights()
        blocked[y - Y0 - 14:y - Y0 + 4, x - X0 - 5:x - X0 + 6] = True
    f = Fackel(660 - X0, 2318 - Y0)
    things.append(f)
    lights += f.lights()

    # ---- the meadow: today's poppies stay, the new ones thin out westward; the grass rises in the village
    heads = np.zeros((H, W, 4), np.uint8)
    fl = ofl[Y0:Y1, :X1 - WW]
    heads[:, WW - X0:] = fl
    heads[:, WW - X0:WW - X0 + EDGE] = 0
    field6.HEADS[:] = field6.make_heads(np.random.default_rng(31))
    keep = 0.79 * (1 - smooth((WW + 40 - gx) / 260.0)) + 0.05 + 0.08 * smooth(-fbm(H, W, 30, 5))
    for (x, y, kk, ph) in patches(H, W, np.full((H, W), 0.5), ndi.binary_dilation(blocked, iterations=2), rng, 60000):
        if x + X0 >= WW + EDGE or rng.random() > keep[min(y + 2, H - 1), min(x + 2, W - 1)]:
            continue
        for j, row in enumerate(field6.HEADS[kk]):
            for i, ch in enumerate(row):
                if ch != '.' and y + j < H and x + i < W:
                    heads[y + j, x + i, :3] = CMAP[ch]
                    heads[y + j, x + i, 3] = 255
    m = heads[..., 3] > 0
    img[m] = heads[m][:, :3]
    # tall grass only in loose drifts between the gardens; inside the plots it is short and full of flowers
    dens = smooth((WW - 40 - gx + 30 * fbm(H, W, 20, 7)) / 220.0) * np.clip(0.18 + 0.32 * fbm(H, W, 14, 8), 0, 1)
    dens = np.clip(dens * (1 - 0.85 * plots), 0, 1)
    grass_free = ndi.binary_dilation(blocked, iterations=2)
    for _ in range(int(W * H / 3)):                         # short garden grass: dark tufts close together
        x, y = int(rng.integers(2, W - 2)), int(rng.integers(4, H))
        if rng.random() > plots[y, x] ** 1.5 or grass_free[y, x]:
            continue
        for d in range(int(rng.integers(1, 3))):
            img[y - d, x + (d and rng.random() < 0.3)] = o.MOSS[1 + d] * 0.9
    for _ in range(int(W * H / 7)):
        x, y = rng.uniform(2, W - 2), rng.uniform(14, H)
        xi, yi = int(x), min(int(y), H - 1)
        if rng.random() > dens[yi, xi] or grass_free[yi, xi]:
            continue
        things.append(z2.Blade(x, yi, rng))
    for _ in range(16000):
        x, y = int(rng.integers(4, W - 4)), int(rng.integers(6, H - 2))
        if rng.random() > 0.05 + 0.4 * dens[y, x] + 0.9 * plots[y, x] ** 2 or grass_free[y, x]:
            continue
        things.append(z2.Wildflower(x, y, int(rng.choice(3, p=[0.45, 0.33, 0.22])), rng, int(dens[y, x] * 6)))

    # ---- today's standing things in the window, without the fir wall at the edge
    sprites = [s for s in w['sprites'] if s['x'] + WW < X1 + 40 and s['x'] + WW + s['w'] > X0
               and Y0 - 160 < s['y'] < Y1 and s['x'] > 2]           # the edge wall: every fir standing at x 0

    class Old:
        def __init__(s, sp):
            s.sp = sp

        def box(s):
            return (0, 0, 0, s.sp['foot'] - Y0)

        def draw(s, img, G):
            sp = s.sp
            a = np.array(Image.open(os.path.join(ROOT, 'assets', 'world', 'sprites', sp['name'] + '.png'))
                         .convert('RGBA'))[:, :sp['w']].astype(float)
            x_, y_ = sp['x'] + WW - X0, sp['y'] - Y0
            ya, yb = max(0, y_), min(H, y_ + a.shape[0])
            xa, xb = max(0, x_), min(W, x_ + a.shape[1])
            if ya >= yb or xa >= xb:
                return
            sub = a[ya - y_:yb - y_, xa - x_:xb - x_]
            al = sub[..., 3:] / 255.0
            img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al
    things += [Old(s) for s in sprites]
    for l in w['lights']:
        if X0 <= l['x'] + WW < X1 and Y0 <= l['y'] < Y1:
            lights.append(dict(l, x=l['x'] + WW - X0, y=l['y'] - Y0))
    for t in sorted(things, key=lambda t: getattr(t, 'order', None) or t.box()[3]):
        t.draw(img, G)
    ww = dict(w, lights=lights, wisps=[])
    out_img = mood_map.mood(np.clip(img, 0, 255), ww, 2.0, grass_mist=0.45)
    Image.fromarray(np.clip(out_img, 0, 255).astype(np.uint8)).resize((W * scale, H * scale), Image.NEAREST).save(out)


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2)
    print('ok')
