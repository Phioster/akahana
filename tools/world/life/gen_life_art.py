#!/usr/bin/env python3
"""The approved new animals (0.19) as sheets for the game:
  assets/life/eichhorn.png  12x12 cells in squirrel_art.ORDER (facing right)
  assets/life/falter.png    5x3 cells: a row per kind (butterfly_art.KINDS order), open | half | shut
  assets/life/sprung.png    11x11 fish cells: row 0 in the air heading right, nose -50..50 deg in 7 steps;
                            row 1 the same heading left; rows 2-3 the shape under water coming up (right,
                            dim | less dim) and rows 4-5 the same heading left, 4 tail phases each
"""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south')]
import butterfly_art as ba  # noqa: E402
import critter_art as ca  # noqa: E402
import fishjump_video as fj  # noqa: E402
import squirrel_art as sa  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
AIR_ANGLES = [-50, -33, -17, 0, 17, 33, 50]


def leap_sheet():
    C = ca.CELL_F
    out = np.zeros((6 * C, 7 * C, 4), np.uint8)
    for i, a in enumerate(AIR_ANGLES):
        out[0:C, i * C:(i + 1) * C] = fj.lit(ca.fish_cell(a, 2))
        out[C:2 * C, i * C:(i + 1) * C] = fj.lit(ca.fish_cell(180 - a, 2))
    for r, (ang, shade) in enumerate([(0, 0), (0, 1), (180, 0), (180, 1)]):
        for k, wag in enumerate(ca.WAG):
            out[(2 + r) * C:(3 + r) * C, k * C:(k + 1) * C] = ca.fish_cell(ang, shade, wag)
    return out


if __name__ == '__main__':
    d = os.path.join(ROOT, 'assets', 'life')
    Image.fromarray(sa.sheet()).save(os.path.join(d, 'eichhorn.png'))
    rows = [np.concatenate([ba.cell(k, n) for n in ba.ORDER], 1) for k in ba.KINDS]
    Image.fromarray(np.concatenate(rows, 0)).save(os.path.join(d, 'falter.png'))
    Image.fromarray(leap_sheet()).save(os.path.join(d, 'sprung.png'))
    print('ok', list(ba.KINDS), sa.ORDER)
