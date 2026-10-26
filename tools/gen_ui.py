#!/usr/bin/env python3
"""The few hand-drawn UI pixels: the book button (an old closed notebook with a ribbon).
Out: assets/ui/buch.png (12x10)
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BOOK = ["............",
        ".cccccccccc.",
        ".cbbbbbbbbpp",
        ".cbbbbbbbbpp",
        ".cbbbbbbbbpp",
        ".cbbbbbbbbpp",
        ".cbbbbbbbbpp",
        ".cbbrbbbbbpp",
        ".ccccrcccccp",
        ".....r......"]
PAL = dict(c=(92, 70, 58), b=(126, 98, 80), p=(214, 206, 190), r=(184, 62, 52))

if __name__ == '__main__':
    a = np.zeros((len(BOOK), len(BOOK[0]), 4), np.uint8)
    for y, row in enumerate(BOOK):
        for x, ch in enumerate(row):
            if ch != '.':
                a[y, x] = (*PAL[ch], 255)
    out = os.path.join(ROOT, 'assets', 'ui')
    os.makedirs(out, exist_ok=True)
    Image.fromarray(a).save(os.path.join(out, 'buch.png'))
    print('ok')
