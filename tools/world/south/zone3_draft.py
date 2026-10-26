#!/usr/bin/env python3
"""Draft of zone 3 for the approval page, drawn below zones 1 and 2 on one canvas: the tall grass goes on,
brooks wind through it towards the lake (the big one from the west, a short one from the east, one from a
spring in the middle, a little side brook), crossed by two bridges, a plank and stepping stones; willows,
reeds, bulrushes and ferns along the banks. The layout is plan_zone3's (approved plan, second draft).

    python3 tools/world/south/zone3_draft.py OUTDIR
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi
from scipy.interpolate import splprep, splev

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import extras  # noqa: E402
import mood_map  # noqa: E402
import zone2_draft as z2  # noqa: E402
from zone1_draft import Fir, W  # noqa: E402
from zone2_draft import Blade, fbm  # noqa: E402
from objects_south import Findling, Karren  # noqa: E402
import objects_water as o  # noqa: E402
import ground as south_ground  # noqa: E402
from fireflies import Swarm  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
Y3 = z2.Y0 + z2.NEW                         # first row of zone 3 on the shared canvas
NEW = 600                                   # three chunk rows


def curve(pts, n=300):
    tck, _ = splprep(np.array(pts, float).T, s=0, k=min(3, len(pts) - 1))
    return np.array(splev(np.linspace(0, 1, n), tck)).T


def meander(pts, amp, seed, n=300):
    """As plan_zone3: the base curve plus a slow sideways swing that grows and shrinks."""
    c = curve(pts, n)
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 1, n)
    sw = sum(rng.uniform(0.4, 1) * np.sin(t * f * 2 * np.pi + rng.uniform(0, 6)) for f in (2.3, 4.1, 7.7))
    sw *= amp * (0.4 + 0.6 * np.abs(np.sin(t * 3.1 + seed)))
    d = np.gradient(c, axis=0)
    d /= np.hypot(d[:, :1], d[:, 1:]) + 1e-9
    return c + np.stack([-d[:, 1], d[:, 0]], 1) * sw[:, None] * np.minimum(1, np.minimum(t, 1 - t) * 8)[:, None]


def layout():
    """Brooks (zone coordinates, fine samples) and trails, the same as the approved plan."""
    CA = meander([(14, 40), (90, 95), (150, 190), (140, 300), (220, 380), (330, 470), (410, 610)], 16, 3)
    CQ = meander([(566, 128), (540, 200), (500, 290), (440, 380), tuple(CA[205])], 10, 5)
    CB = meander([(886, 300), (800, 350), (720, 420), (640, 500), (560, 560), (520, 612)], 12, 8)
    CC = meander([(14, 360), (70, 390), tuple(CA[150])], 2.5, 9, 120)
    fine = lambda c: curve(c[::2] if len(c) > 200 else c, 900)
    brooks = {'A': (fine(CA), 12, 17), 'Q': (fine(CQ), 8, 11), 'B': (fine(CB), 9, 13), 'C': (fine(CC), 5, 7)}
    zone = lambda pts: [(x, y - Y3) for x, y in pts]
    trails = {'west': zone(z2.TRAIL_A), 'ost': zone(z2.TRAIL_B), 'mitte': zone(z2.TRAIL_S),
              'q1': [(255, 250), (330, 262), (420, 250), (520, 236), (614, 214)],
              'weide': [(268, 150), (200, 156), (130, 168), (62, 160)],
              'q3': [(250, 490), (330, 505), (400, 515), (476, 512)]}
    for k, (frm, to) in {'q1': ('west', 'mitte'), 'weide': ('west', None), 'q3': ('west', 'mitte')}.items():
        pts = trails[k]
        for end, tr in ((0, frm), (-1, to)):
            if tr:
                c = curve(trails[tr], 600)
                pts[end] = tuple(c[np.hypot(*(c - pts[end]).T).argmin()])
    return brooks, trails, CA, CB


CROSS = {('west', 'A'): o.Bruecke, ('ost', 'B'): o.Bruecke, ('q1', 'Q'): o.Brett,
         ('weide', 'A'): o.Trittsteine, ('q3', 'A'): o.Trittsteine}


def crossings(brooks, trails):
    """Where each trail meets a brook: (kind, x, y, angle of the trail, width of the water there)."""
    out = []
    for (tk, bk), kind in CROSS.items():
        t = curve(trails[tk], 600)
        c, w0, w1 = brooks[bk]
        d = np.hypot(t[:, None, 0] - c[None, :, 0], t[:, None, 1] - c[None, :, 1])
        i, j = np.unravel_index(d.argmin(), d.shape)
        tang = t[min(i + 3, len(t) - 1)] - t[max(i - 3, 0)]
        width = w0 + (w1 - w0) * j / len(c)
        out.append((kind, int(round(c[j, 0])), int(round(c[j, 1])), float(np.arctan2(tang[1], tang[0])), width))
    return out


def on_bank(c, i, off):
    x, y = c[i]
    dx, dy = c[min(i + 2, len(c) - 1)] - c[max(i - 2, 0)]
    n = np.hypot(dx, dy) + 1e-9
    return x - dy / n * off, y + dx / n * off


def render(w, seed=21):
    base, lights, swarms = z2.render(w, raw=True)
    rng = np.random.default_rng(seed)
    H = Y3 + NEW
    img = np.zeros((H, W, 3))
    img[:Y3] = base
    g2 = z2.STASH['ground']

    fog = np.clip(0.70 + 0.10 * fbm(NEW, W, 18, 304), 0, 1)
    flow = np.clip(0.22 + 0.10 * fbm(NEW, W, 10, 305), 0, 1)
    tone = south_ground.continued_tone(south_ground.tone_of(g2), south_ground.fresh_tone(NEW, W, fog, flow, rng))
    ground = south_ground.ground_from_tone(tone, fog, flow, rng)
    ground *= (1 - np.array([0.12, 0.0, 0.14])) * 0.62           # the grass field's floor, as zone 2 ends

    brooks, trails, CA, CB = layout()
    water = o.Brooks(list(brooks.values()), NEW, W, y0=0)
    near = ndi.distance_transform_edt(~water.mask)
    ground[near < 7] *= 0.85                                     # damp, darker soil along the water
    img[Y3:] = ground

    Y = lambda y: Y3 + int(round(y))
    path = np.zeros((H, W), bool)
    prng = np.random.default_rng(95)
    for k, pts in trails.items():
        pm, pc, pd_, pw_ = extras.path_mask(H, W, [(x, Y3 + y) for x, y in pts], prng)
        pm[:Y3 - 4] = False
        pc[:Y3 - 4] = False                                    # its middle too: zone 2 is finished up there
        extras.draw_path(img, pm, pc, pd_, pw_, prng)
        path |= pm
    water.y0 = Y3
    water.draw(img, rng)                                         # the water over the paths: they end at the banks

    cr = crossings(brooks, trails)
    things = [kind(x, Y(y), ang, wd) for kind, x, y, ang, wd in cr]
    QUELLE = o.Quelle(566, Y(128))
    things += [QUELLE, Holzlaterne(594, Y(112)), Karren(550, Y(268))]
    wa, wb = on_bank(brooks['A'][0], 180, -26), on_bank(brooks['B'][0], 600, -24)
    things += [o.Weide(int(wa[0]), Y(wa[1]), seed=4, size=1.45, lean=5), o.Weide(int(wb[0]), Y(wb[1]), seed=9, size=1.3, lean=-4)]
    things += [Findling(400, Y(90), 7, 31), Findling(80, Y(460), 8, 32), Findling(860, Y(470), 6, 33),
               Findling(700, Y(580), 7, 34)]

    # along the banks: reeds and bulrushes in clumps, never on a crossing or a path
    cross_pts = np.array([(x, y) for _, x, y, _, _ in cr], float)
    for bk, (c, w0, w1) in brooks.items():
        for i in range(10, len(c) - 4, int(rng.integers(14, 22))):
            for side in (-1, 1):
                if rng.random() < 0.35:
                    continue
                half = (w0 + (w1 - w0) * i / len(c)) / 2
                x, y = on_bank(c, i, side * (half + 1.5))
                if np.hypot(*(cross_pts - (x, y)).T).min() < 14 or not (16 < x < W - 16) or not (2 < y < NEW - 1):
                    continue
                if path[Y(y), int(x)]:
                    continue
                if rng.random() < 0.68:
                    things.append(o.Schilf(int(x), Y(y), int(rng.integers(6, 11)), int(rng.integers(0, 999))))
                else:
                    things.append(o.Rohrkolben(int(x), Y(y), int(rng.integers(3, 6)), int(rng.integers(0, 999))))
    for _ in range(26):                                          # ferns in the damp spots
        bk = ['A', 'B', 'Q'][int(rng.integers(0, 3))]
        c = brooks[bk][0]
        x, y = on_bank(c, int(rng.integers(20, len(c) - 20)), rng.choice([-1, 1]) * rng.uniform(7, 14))
        if 16 < x < W - 16 and 4 < y < NEW - 2 and not path[Y(y), int(x)] and not water.mask[int(y), int(x)]:
            things.append(o.Farn(int(x), Y(y), int(rng.integers(0, 999)), int(rng.integers(6, 9))))

    firs = []
    for y in range(Y3 + 4, H + 30, 13):
        for x in (int(rng.integers(-6, 12)), W - int(rng.integers(-6, 12))):
            firs.append(Fir(x, y + int(rng.integers(-3, 4)), int(rng.integers(36, 48)), int(rng.integers(0, 10 ** 6))))

    # the grass field, everywhere but on water, banks, paths and right round things
    keep_off = np.zeros((H, W), bool)
    wet = np.zeros((H, W), bool)
    wet[Y3:] = ndi.binary_dilation(water.mask, iterations=3)
    keep_off |= ndi.binary_dilation(path, iterations=2) | wet      # leaning stalks would cover a narrow path
    # a stalk stands on its foot and grows up to 13 px: none whose foot is just below water or a low thing
    low = wet.copy()
    for t_ in things:
        x0, y0, x1, y1 = t_.box()
        if isinstance(t_, (o.Weide,)):                           # under the willow the grass stays short:
            x0, y0 = t_.x - int(16 * t_.size), t_.y - 16           # its curtain reaches nearly to the ground
            x1, y1 = t_.x + int(20 * t_.size), t_.y + 3
        if isinstance(t_, (o.Schilf, o.Rohrkolben, o.Farn)):
            y0 = y1 - 2
        keep_off[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
        if isinstance(t_, o.Quelle):
            x0, y0, x1, y1 = x0 - 5, y0 - 3, x1 + 5, y1 + 3                  # a little clearing round the spring
            keep_off[max(0, y0):y1, max(0, x0):x1] = True
        if isinstance(t_, (o.Quelle, o.Bruecke, o.Brett, o.Trittsteine, Findling, o.Weide, Karren)):
            low[max(0, y0):max(0, y1), max(0, x0):max(0, x1)] = True
    shadow_of_low = low.copy()                                   # the 12 rows below each
    for k in range(1, 13):
        shadow_of_low[k:] |= low[:-k]
    keep_off |= shadow_of_low & ~path
    dens = np.clip(0.78 + 0.32 * fbm(H, W, 16, 306), 0.38, 1)   # thinner patches here and there, not one even carpet
    fade = np.clip((np.arange(H) - Y3) / 90.0, 0, 1)[:, None]    # closed like zone 2 at the seam, patchy further down
    dens = 1 - (1 - dens) * fade
    blades = []
    for _ in range(int(W * (NEW + 8) / 8.5)):
        x, y = rng.uniform(14, W - 14), rng.uniform(0, NEW + 8)
        yy = min(Y(y), H - 1)
        if keep_off[yy, int(x)] or rng.random() > dens[yy, int(x)]:
            continue
        blades.append(Blade(x, Y(y), rng))
    for _ in range(1400):                                        # wildflowers on long stems, as in zone 2
        x, y = int(rng.integers(16, W - 16)), int(rng.integers(2, NEW - 2))
        if keep_off[Y(y), x] or rng.random() > 1.2 - dens[Y(y), x]:
            continue
        things.append(z2.Wildflower(x, Y(y), int(rng.choice(3, p=[0.45, 0.33, 0.22])), rng, int(rng.integers(6, 10))))

    G = np.random.default_rng(3).random((H, W))
    for t_ in sorted(things + blades + firs,
                     key=lambda t_: t_.p.y if isinstance(t_, Fir) else (getattr(t_, 'order', None) or t_.box()[3])):
        if isinstance(t_, Fir):
            t_.draw(img)
        else:
            t_.draw(img, G)

    lit = lights + [l for t_ in things if hasattr(t_, 'lights') for l in t_.lights()]
    sw = swarms + SWARMS
    band = np.zeros((H, W))
    band[Y3:] = ndi.gaussian_filter(water.mask.astype(float), 3) * 1.6
    out = mood_map.mood(np.clip(img, 0, 255), dict(w, lights=lit + [l for s_ in sw for l in s_.lights(2.0)], wisps=[]),
                        2.0, grass_mist=z2.GRASS_MIST, water_band=np.clip(band, 0, 1)).astype(float)
    for s_ in sw:
        s_.draw(out, 2.0)
    return out.astype(np.uint8), water


class Holzlaterne:
    """The game's wooden post lantern (extras.WoodLantern, drawn on its own small canvas like gen_world)."""
    def __init__(s, x, y):
        s.x, s.y = x, y

    def box(s):
        return (s.x - 12, s.y - 22, s.x + 13, s.y + 8)

    def lights(s):
        return [{'x': s.x + 0.5, 'y': s.y - 10.5, 'r': 26.0, 'k': 0.6, 'kind': 'lantern'}]

    def draw(s, img, G):
        x0, y0, x1, y1 = s.box()
        extras.WoodLantern(s.x - x0, s.y - y0).draw(img[y0:y1, x0:x1], 0.0, 8.0)


# fireflies over the water and the quiet spots
SWARMS = [Swarm(110, Y3 + 200, 9, 21), Swarm(470, Y3 + 140, 8, 22), Swarm(330, Y3 + 420, 10, 23),
          Swarm(820, Y3 + 230, 8, 24), Swarm(620, Y3 + 400, 9, 25), Swarm(150, Y3 + 520, 8, 26)]


if __name__ == '__main__':
    out = sys.argv[1]
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    im, water = render(w)
    Image.fromarray(im).save(os.path.join(out, 'zone123.png'))
    np.save(os.path.join(out, 'water_flow.npy'), np.concatenate([water.flow, water.depth[..., None],
                                                                water.along[..., None]], -1).astype(np.float32))
    print('ok', im.shape, flush=True)
