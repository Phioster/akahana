#!/usr/bin/env python3
"""Draft of zone 1 for the approval page: the poppy field continued south of the camp, five chunks wide,
with the waymark stone, the wall remains and the scarecrow - in two variants, in the game's mood.

    python3 tools/world/south/zone1_draft.py OUTDIR
"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..'))
import field6  # noqa: E402
from field6 import ground_organic, patches, CMAP, DG  # noqa: E402
import extras  # noqa: E402
from berg_objects import Pine  # noqa: E402
import mood_map  # noqa: E402
from objects_south import Wegstein, Mauer, Vogelscheuche  # noqa: E402
import ground as south_ground  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
W, OLD_W, OLD_H = 900, 540, 1200
CTX = 160                                   # rows of the old world shown above the seam
NEW = 600                                   # zone 1: three chunk rows
BAND = 70                                   # old rows the new field may grow into (an uneven seam)


def old_layers(w):
    """The old world's last CTX rows as separate layers: ground, poppy heads (RGBA), and its sprites."""
    y0 = OLD_H - CTX
    g = np.array(Image.open(os.path.join(ROOT, 'build', 'world_full', 'ground.png')).convert('RGB')).astype(float)
    f = np.array(Image.open(os.path.join(ROOT, 'build', 'world_full', 'flowers.png')))
    sprites = [s_ for s_ in w['sprites'] if s_['y'] + s_['h'] > y0]
    return g[y0:], f[y0:], sprites


def draw_sprites(img, sprites, dy):
    for s_ in sorted(sprites, key=lambda s_: s_['foot']):
        a = np.array(Image.open(os.path.join(ROOT, 'assets', 'world', 'sprites', s_['name'] + '.png')))[:, :s_['w']]
        x, y = s_['x'], s_['y'] + dy
        for j in range(a.shape[0]):
            if 0 <= y + j < img.shape[0]:
                row = a[j, :max(0, min(a.shape[1], img.shape[1] - x))]
                m = row[:, 3] > 0
                img[y + j, x:x + len(row)][m] = row[m][:, :3]


class Fir:
    """A meadow fir as the old map's edges have it: little snow down here."""
    def __init__(s, x, y, h, seed, snow=0.25):
        s.p, s.seed, s.snow = Pine(x, y, h, seed), seed, snow

    def draw(s, img):
        hh, ww = img.shape[:2]
        G = np.random.default_rng(s.seed).random((hh, ww))
        G = np.where(G < s.snow, G, 1.0)
        CL = ndi.gaussian_filter(np.random.default_rng(s.seed + 1).random((hh, ww)), 0.65)
        CL = (CL - CL.min()) / (CL.max() - CL.min())
        s.p.draw(img, G, CL)


def forest_edge(x):
    """Southern edge of the placeholder wood (canvas row): long soft bows."""
    return CTX - 14 + 22 * np.sin(x / 41.0 + 0.7) + 7 * np.sin(x / 17.0 + 2)


def forest_west(y):
    """Western edge of the wood beside the old map, gently wavering."""
    return OLD_W + 6 + 7 * np.sin(y / 23.0) + 3 * np.sin(y / 9.0 + 1)


def in_forest(x, y):
    """How far inside the wood (px, < 0 outside). The two edges meet in a wide round corner, not an angle."""
    a = forest_edge(x) - y
    b = x - forest_west(y)
    k = 26.0
    return -k * np.logaddexp(-a / k, -b / k)


def forest_firs(rng):
    """East of the old map: a closed wood for now, its southern edge ragged, a few firs stepping out
    into the field (the eastern wood comes later)."""
    out = []
    for n, row in enumerate(range(-30, CTX + 12, 10)):
        for x in range(OLD_W - 8 + (n % 2) * 5, W + 10, 10):                  # staggered rows, no grid
            if in_forest(x, row) < -2 + 4 * rng.random() or rng.random() < 0.06:
                continue
            out.append(Fir(x + int(rng.integers(-3, 4)), row + int(rng.integers(-3, 4)), int(rng.integers(34, 46)),
                           int(rng.integers(0, 10 ** 6)), snow=0.08))
    for _ in range(9):                                         # lone ones out in the poppies
        x = int(rng.integers(OLD_W + 20, W - 20))
        out.append(Fir(x, CTX + int(rng.integers(14, 70)), int(rng.integers(30, 40)), int(rng.integers(0, 10 ** 6))))
    return out


def edge_firs(rng):
    """The west and east world edges keep their fir rows as the old map has them."""
    out = []
    for y in range(CTX + 22, CTX + NEW + 30, 13):
        for x in (int(rng.integers(-6, 12)), W - int(rng.integers(-6, 12))):
            out.append(Fir(x, y + int(rng.integers(-3, 4)), int(rng.integers(36, 48)), int(rng.integers(0, 10 ** 6))))
    return out


def blossoms(heads):
    """Each poppy head (a touching blob of head pixels) as (label image, centroids)."""
    lab, n = ndi.label(heads[..., 3] > 0, structure=np.ones((3, 3)))
    cy = ndi.mean(np.mgrid[0:lab.shape[0], 0:lab.shape[1]][0], lab, range(1, n + 1))
    cx = ndi.mean(np.mgrid[0:lab.shape[0], 0:lab.shape[1]][1], lab, range(1, n + 1))
    return lab, np.array(cy), np.array(cx)


def field(rng):
    H = NEW + BAND
    yy, xx = np.mgrid[0:H, 0:W]

    def fbm(s, seed):
        n = ndi.gaussian_filter(np.random.default_rng(seed).normal(0, 1, (H, W)), s)
        return n / n.std()
    fog = np.clip(0.70 + 0.10 * fbm(18, 104), 0, 1)
    flow = np.clip(0.20 + 0.10 * fbm(10, 105), 0, 1)
    return fog, flow


def render(kind, w, seed=7):
    rng = np.random.default_rng(seed)
    field6.HEADS[:] = field6.make_heads(np.random.default_rng(31))
    Hc = CTX + NEW
    G = np.random.default_rng(3).random((Hc, W))
    og, of, osprites = old_layers(w)
    top = CTX - BAND                                           # first row the new field reaches into

    # which world each spot belongs to: new below an uneven line through the band
    wav = ndi.gaussian_filter(np.random.default_rng(21).normal(0, 1, (Hc, W)), 7)
    wav /= wav.std()
    rows = np.arange(Hc)[:, None]
    M = np.clip((rows - top) / BAND, 0, 1) + 0.28 * wav * (rows >= top - 10)
    newer = (M > 0.5) | (rows >= CTX)                        # below the old map there is only the new field

    ground = np.zeros((Hc, W, 3))
    fog = np.full((CTX, W - OLD_W), 0.55)
    ground[:CTX, OLD_W:] = ground_organic(CTX, W - OLD_W, fog, np.zeros_like(fog), rng)
    ground[:CTX, :OLD_W] = og[:, :OLD_W]
    fog, flow = field(rng)
    # the ground below the seam grows out of the old one: its light and dark patches run on, then ease
    # into new ones (mixing two grounds grain by grain cut the patches off at the seam)
    tone = south_ground.continued_tone(south_ground.tone_of(ground[:CTX]),
                                       south_ground.fresh_tone(NEW, W, fog[BAND:], flow[BAND:], rng))
    ground[CTX:] = south_ground.ground_from_tone(tone, fog[BAND:], flow[BAND:], rng)

    # the trail starts at the camp, below the tent, and forks at the waymark
    camp_y = 1104 - (OLD_H - CTX)
    trail_a = [(252, camp_y), (256, camp_y + 40), (270, CTX + 60), (300, CTX + 150), (318, CTX + 260),
               (300, CTX + 380), (322, CTX + 520), (360, CTX + 600)]
    trail_b = [(300, CTX + 150), (380, CTX + 175), (480, CTX + 210), (600, CTX + 250), (700, CTX + 320),
               (760, CTX + 420), (790, CTX + 600)]
    prng = np.random.default_rng(91)
    path = np.zeros((Hc, W), bool)
    for pts in (trail_a, trail_b):
        pm, pc, pd_, pw_ = extras.path_mask(Hc, W, pts, prng)
        extras.draw_path(ground, pm, pc, pd_, pw_, prng)
        path |= pm

    things = [Wegstein(306, CTX + 146, kind), Vogelscheuche(612, CTX + 330, kind),
              Mauer([(110, CTX + 300), (140, CTX + 296), (172, CTX + 304), (205, CTX + 318), (226, CTX + 336)])]
    firs = forest_firs(rng) + edge_firs(rng)
    blocked = path.copy()
    for t in things:
        x0, y0, x1, y1 = t.box()
        blocked[max(0, y1 - 8):y1, max(0, x0):x1] = True
    for f_ in firs:
        blocked[max(0, f_.p.y - 6):max(0, f_.p.y + 2), max(0, f_.p.x - 8):max(0, f_.p.x + 9)] = True   # never a negative end
    xs_ = np.arange(W)[None, :]
    depth = in_forest(xs_, rows)
    blocked |= depth > 8                                         # under the firs: no poppies
    shade = ndi.gaussian_filter((depth > -2).astype(float), 4)
    dark = G < shade * 1.4                                       # the wood floor, darker towards it
    ground[dark & (xs_ >= OLD_W - 10)] *= 0.62

    fl = np.zeros((Hc, W))
    fl[top:] = flow
    fl[:top, OLD_W:] = flow[:1, OLD_W:].mean()             # the strip by the wood is meadow too
    F = patches(Hc, W, fl, blocked, rng, 700000)
    nh = np.zeros((Hc, W, 4), np.uint8)
    for (x, y, k, ph) in F:
        head = field6.HEADS[k]
        for s_ in range(len(head), len(head) + 2):             # stems in the ground layer, under new heads only
            for sx_ in (x + 1, x + 2):
                if y + s_ < Hc and newer[min(y + s_, Hc - 1), sx_] and (sx_ + y + s_) % 2 == 0 and not blocked[y + s_, sx_]:
                    ground[y + s_, sx_] = DG
        for j, row in enumerate(head):
            for i, ch in enumerate(row):
                if ch != '.' and y + j < Hc and x + i < W:
                    nh[y + j, x + i, :3] = CMAP[ch]
                    nh[y + j, x + i, 3] = 255
    oh = np.zeros((Hc, W, 4), np.uint8)
    oh[:CTX, :OLD_W] = of[:, :OLD_W]
    heads = np.zeros((Hc, W, 4), np.uint8)
    for src, mine in ((oh, lambda m: ~m), (nh, lambda m: m)):  # whole blossoms from one world or the other
        lab, cy, cx = blossoms(src)
        if len(cy) == 0:
            continue
        keep = mine(newer[np.clip(cy.round().astype(int), 0, Hc - 1), np.clip(cx.round().astype(int), 0, W - 1)])
        onpath = ndi.maximum(path.astype(int), lab, range(1, len(cy) + 1)) > 0
        keep &= ~np.asarray(onpath)
        sel = np.r_[False, keep][lab]
        heads[sel] = src[sel]
    img = ground.copy()
    m = heads[..., 3] > 0
    img[m] = heads[m][:, :3]

    # the old map cut its edge firs off at its own border (x 540, y 1200); now the world goes on there,
    # so those are drawn whole again, same foot and height
    cut = [s_ for s_ in osprites if s_['name'].startswith('tanne') and
           (s_['x'] + s_['w'] >= OLD_W or s_['y'] + s_['h'] >= OLD_H)]
    for s_ in cut:
        h = int(round((s_['h'] - 4) / 1.25))
        fx = s_['x'] + int(h * 0.45) + 3 if s_['x'] > 0 else s_['x'] + s_['w'] - int(h * 0.62) - 3   # left side cut too
        firs.append(Fir(fx, s_['foot'] - (OLD_H - CTX), max(h, 30),
                        int(rng.integers(0, 10 ** 6))))
    draw_sprites(img, [s_ for s_ in osprites if s_ not in cut], -(OLD_H - CTX))   # the camp, unchanged
    for t in sorted(things + firs, key=lambda t: t.box()[3] if hasattr(t, 'box') else t.p.y):
        if isinstance(t, Fir):
            t.draw(img)
        else:
            t.draw(img, G)

    lights = [dict(l, y=l['y'] - (OLD_H - CTX)) for l in w['lights']]
    fake = dict(w, lights=lights, wisps=[])
    return mood_map.mood(np.clip(img, 0, 255), fake, 2.0)


if __name__ == '__main__':
    out = sys.argv[1]
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    for kind in ('a', 'b'):
        im = Image.fromarray(render(kind, w))
        im.save(os.path.join(out, f'zone1_{kind}.png'))
        print('ok', kind, im.size, flush=True)
