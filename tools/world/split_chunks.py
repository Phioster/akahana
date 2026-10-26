#!/usr/bin/env python3
"""Cuts the generator's big world images into chunks the game streams in around the camera.

Per chunk (cx, cy): c_<cx>_<cy>_ground.png (the chunk), c_<cx>_<cy>_flowers.png (the chunk plus an
apron of the neighbours' pixels, so the poppy shader can shift blossoms across the edge without a
seam), c_<cx>_<cy>_cells.bin and _mat.bin (walkable and ground material per 2-px cell), _walls.bin and
_paths.bin (int32 cell indices of the walls and of the cheap ground, for the per-tap path grid).
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
