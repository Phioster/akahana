#!/usr/bin/env python3
"""Cuts the generator's big world images into chunks the game streams in around the camera.

Per chunk (cx, cy): c_<cx>_<cy>_ground.png (the chunk), c_<cx>_<cy>_flowers.png (the chunk plus an
apron of the neighbours' pixels, so the poppy shader can shift blossoms across the edge without a
seam), c_<cx>_<cy>_cells.bin and _mat.bin (walkable and ground material per 2-px cell), _walls.bin and
_paths.bin (int32 cell indices of the walls and of the cheap ground, for the per-tap path grid), and
c_<cx>_<cy>_water.png (where water moves and how, for the water shader; gen_south.water_map),
c_<cx>_<cy>_refl.png (the still things mirrored on the water, with the apron; south/reflect_map.py).
"""
import json
import os
import sys

import numpy as np
from PIL import Image

CELL = 2
GRASS, SNOW = 0, 4                   # GroundMat values that cost extra to walk on


def split(src_dir, out_dir, chunk=(180, 200), apron=8):
    cw, ch = chunk
    ground = np.array(Image.open(os.path.join(src_dir, 'ground.png')))
    flowers = np.array(Image.open(os.path.join(src_dir, 'flowers.png')).convert('RGBA'))
    wpath = os.path.join(src_dir, 'water.png')                   # where water moves, for the water shader
    water = np.array(Image.open(wpath).convert('RGBA')) if os.path.exists(wpath) else None
    bpath = os.path.join(src_dir, 'bend.png')                    # how high each swaying pixel stands
    bend = None
    if os.path.exists(bpath):
        fh, fw = flowers.shape[:2]
        bend = np.zeros((fh + 2 * apron, fw + 2 * apron), np.uint8)
        bend[apron:apron + fh, apron:apron + fw] = np.array(Image.open(bpath).convert('L'))
    rpath = os.path.join(src_dir, 'refl.png')                    # the still things mirrored on the water
    refl = None
    if os.path.exists(rpath):
        r = np.array(Image.open(rpath).convert('RGBA'))
        refl = np.zeros((r.shape[0] + 2 * apron, r.shape[1] + 2 * apron, 4), np.uint8)   # apron: the ripples
        refl[apron:apron + r.shape[0], apron:apron + r.shape[1]] = r                   # pull across the edge
    H, W = ground.shape[:2]
    assert W % cw == 0 and H % ch == 0, 'world size must be whole chunks'
    cells = np.fromfile(os.path.join(src_dir, 'walk_cells.bin'), np.uint8).reshape(H // CELL, W // CELL)
    mat = np.fromfile(os.path.join(src_dir, 'ground_mat.bin'), np.uint8).reshape(H // CELL, W // CELL)
    padded = np.zeros((H + 2 * apron, W + 2 * apron, 4), np.uint8)             # outside the world: empty
    padded[apron:apron + H, apron:apron + W] = flowers
    os.makedirs(out_dir, exist_ok=True)
    cols, rows = W // cw, H // ch
    for cy in range(rows):
        for cx in range(cols):
            x0, y0 = cx * cw, cy * ch
            name = os.path.join(out_dir, f'c_{cx}_{cy}_')
            Image.fromarray(ground[y0:y0 + ch, x0:x0 + cw]).save(name + 'ground.png')
            if water is not None:
                Image.fromarray(water[y0:y0 + ch, x0:x0 + cw]).save(name + 'water.png')
            if bend is not None:
                Image.fromarray(bend[y0:y0 + ch + 2 * apron, x0:x0 + cw + 2 * apron]).save(name + 'bend.png')
            if refl is not None:
                Image.fromarray(refl[y0:y0 + ch + 2 * apron, x0:x0 + cw + 2 * apron]).save(name + 'refl.png')
            Image.fromarray(padded[y0:y0 + ch + 2 * apron, x0:x0 + cw + 2 * apron]).save(name + 'flowers.png')
            sl = (slice(y0 // CELL, (y0 + ch) // CELL), slice(x0 // CELL, (x0 + cw) // CELL))
            np.ascontiguousarray(cells[sl]).tofile(name + 'cells.bin')
            np.ascontiguousarray(mat[sl]).tofile(name + 'mat.bin')
            # per tap the game only touches walls and paths (grass and snow are the bulk default)
            c, m = cells[sl].ravel(), mat[sl].ravel()
            np.flatnonzero(c == 0).astype('<i4').tofile(name + 'walls.bin')
            np.flatnonzero((c != 0) & (m != GRASS) & (m != SNOW)).astype('<i4').tofile(name + 'paths.bin')
    return {'chunk': [cw, ch], 'chunks': [cols, rows], 'apron': apron}


if __name__ == '__main__':
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, 'assets', 'world')
    world = os.path.join(root, 'assets', 'world')
    index = split(src, os.path.join(world, 'chunks'))
    p = os.path.join(world, 'world.json')
    w = json.load(open(p))
    w.update(index)
    json.dump(w, open(p, 'w'), indent=1)
    print('ok', index)
