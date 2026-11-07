#!/usr/bin/env python3
"""Where the ground gets wet after the rain and where puddles stand (approved 2026-11-06, build/preview/regen/
wet.py round 3), baked once for the game.

assets/world/puddles.png (L, world size): 0 no wet ground (water, snow, bridges, the north); 1..127 meadow,
128..255 path (earth, stone), the rest of the value how early a puddle holds there (0 never .. 1 at the first
drizzle): a puddle stands where hold > 1 - wetness. Puddles lie in the hollows of the paths, in a few hollows of
the meadow and where one stands by a light; never on the stones of a fire pit, under a thing or in the water.
The chunks' refl.png get the things mirrored on the puddles too (south/reflect_map.bake, as on the water).
Reads the full images in build/world_full (make_world.sh moves them there) and the chunks."""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(HERE, 'south'))
import reflect_map  # noqa: E402

EARTH, STONE, WOOD, SNOW = 1, 2, 3, 4
DRY_ABOVE = 1290            # world y: above this the snow falls, no rain (Rain.reach is full from here)


def noise(h, w, cell, seed):
    """Smooth value noise, the preview's."""
    rng = np.random.default_rng(seed)
    g = rng.random((h // cell + 2, w // cell + 2)).astype(np.float32)
    y = np.arange(h, dtype=np.float32) / cell
    x = np.arange(w, dtype=np.float32) / cell
    yi, xi = y.astype(int), x.astype(int)
    fy, fx = (y - yi)[:, None], (x - xi)[None, :]
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a, b = g[yi][:, xi], g[yi][:, xi + 1]
    c, d = g[yi + 1][:, xi], g[yi + 1][:, xi + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def sprite_frames(world):
    cache, out = {}, []
    for s in world['sprites']:
        p = os.path.join(ROOT, 'assets/world/sprites', s['name'] + '.png')
        if not os.path.exists(p):
            continue
        if s['name'] not in cache:
            cache[s['name']] = np.array(Image.open(p).convert('RGBA'))[:, :s['w']]
        out.append((cache[s['name']], s['x'], s['y'], s['foot']))
    return out


def fields(H, W, mat, water, sprites, lights):
    """-> (hold 0..1 float, kind 0 none / 1 meadow / 2 path, can: where a puddle may ever stand)."""
    m = np.kron(mat, np.ones((2, 2), np.uint8))[:H, :W]
    kind = np.where((m == EARTH) | (m == STONE), 2, 1).astype(np.uint8)
    kind[m == WOOD] = 0             # the bridges; the pale SNOW patches of the south get wet too, they stood out white (0.17.5)
    wet_water = water[..., 3] > 0
    from scipy import ndimage as ndi
    kind[ndi.binary_dilation(wet_water, iterations=2)] = 0      # the water's own rim stays as it is
    kind[:DRY_ABOVE] = 0
    pud = noise(H, W, 7, 4) * 0.7 + noise(H, W, 3, 5) * 0.3
    pud2 = noise(H, W, 14, 6) * 0.75 + noise(H, W, 4, 7) * 0.25
    cover = np.zeros((H, W), bool)                           # under a thing no puddle
    for rgba, sx, sy, foot in sprites:
        h, w = rgba.shape[:2]
        rows = max(0, min(h, foot - sy))
        if rows == 0 or sx >= W or sy >= H or sx + w <= 0 or sy + rows <= 0:
            continue
        a = rgba[:rows, :, 3] > 0
        y0, x0 = max(0, sy), max(0, sx)
        y1, x1 = min(H, sy + rows), min(W, sx + w)
        cover[y0:y1, x0:x1] |= a[y0 - sy:y1 - sy, x0 - sx:x1 - sx]
    for l in lights:                                         # trodden hollows by the lights hold water
        lx, ly, fire = l['x'], l['y'], l['kind'] == 'fire'
        x0, x1 = int(max(0, lx - 40)), int(min(W, lx + 40))
        y0, y1 = int(max(0, ly - 20)), int(min(H, ly + 50))
        if x0 >= x1 or y0 >= y1:
            continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        k = np.exp(-(((xx - lx - (2 if fire else 0)) / (13.0 if fire else 9.0)) ** 2
                     + ((yy - ly - (24 if fire else 12)) / 6.0) ** 2))
        pud2[y0:y1, x0:x1] += (0.5 if fire else 0.35) * k
        pud[y0:y1, x0:x1] += (0.5 if fire else 0.3) * k
        if fire:                                              # the pit and its ring of stones stay dry (Philip)
            cover[y0:y1, x0:x1] |= ((xx - lx) / 18.0) ** 2 + ((yy - ly - 5) / 11.0) ** 2 < 1.0
    hold = np.where(kind == 2, (pud - 0.5) / 0.4, (pud2 - 0.77) / 0.2)
    hold = np.clip(hold, 0, 1)
    hold[(kind == 0) | cover | (m == STONE) | (m == SNOW)] = 0
    lab, n = ndi.label(hold > 0)                              # specks of a pixel or two read as noise, not water
    size = np.bincount(lab.ravel())
    hold[(size[lab] < 8) & (lab > 0)] = 0
    return hold, kind, hold > 0


def encode(hold, kind):
    v = np.zeros(hold.shape, np.uint8)
    g = kind == 1
    p = kind == 2
    v[g] = (1 + np.round(hold[g] * 126)).astype(np.uint8)
    v[p] = (128 + np.round(hold[p] * 127)).astype(np.uint8)
    return v


def main():
    full = os.path.join(ROOT, 'build/world_full')
    out = os.path.join(ROOT, 'assets/world')
    world = json.load(open(os.path.join(out, 'world.json')))
    W, H = world['width'], world['height']
    cw, ch = world['chunk']
    apron = world['apron']
    mat = np.fromfile(os.path.join(full, 'ground_mat.bin'), np.uint8).reshape(H // 2, W // 2)
    water = np.array(Image.open(os.path.join(full, 'water.png')).convert('RGBA'))
    sprites = sprite_frames(world)
    hold, kind, can = fields(H, W, mat, water, sprites, world['lights'])
    Image.fromarray(encode(hold, kind)).save(os.path.join(out, 'puddles.png'))
    # the things, the poppies and the flat things mirrored on the puddles, merged into the water's reflections
    flowers = np.array(Image.open(os.path.join(full, 'flowers.png')).convert('RGBA'))
    bend = np.array(Image.open(os.path.join(full, 'bend.png')).convert('L'))
    low = np.array(Image.open(os.path.join(full, 'low.png')).convert('L'))
    ground = np.array(Image.open(os.path.join(full, 'ground.png')).convert('RGB'))
    refl = np.array(Image.open(os.path.join(full, 'refl.png')).convert('RGBA'))
    pr = reflect_map.bake(H, W, can, flowers, bend, low, ground, sprites)
    m = (pr[..., 3] > 0) & (refl[..., 3] == 0)
    refl[m] = pr[m]
    pad = np.zeros((H + 2 * apron, W + 2 * apron, 4), np.uint8)
    pad[apron:apron + H, apron:apron + W] = refl
    for cy in range(H // ch):
        for cx in range(W // cw):
            x0, y0 = cx * cw, cy * ch
            Image.fromarray(pad[y0:y0 + ch + 2 * apron, x0:x0 + cw + 2 * apron]).save(
                os.path.join(out, 'chunks', f'c_{cx}_{cy}_refl.png'))
    print('Pfützen:', int(can.sum()), 'px möglich,', int((kind > 0).sum()), 'px werden nass')


if __name__ == '__main__':
    main()
