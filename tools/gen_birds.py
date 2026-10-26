#!/usr/bin/env python3
"""Draws the three small birds pixel by pixel: sparrow, blackbird, robin (its breast matches the poppies).

One strip per species, 8x8 frames facing right: stand, peck, hop, wings up, wings down.
Out: assets/life/vogel_<art>.png
"""
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# . empty, b body, d dark (wing, cap), l light (belly), k beak/eye, r breast, f feet
FRAMES = {
    'stand': ["........",
              "....dd..",
              "...dbbk.",
              "...bbb..",
              ".ddbbr..",
              "dddbbr..",
              "..lll...",
              "...f.f.."],
    'peck':  ["........",
              "........",
              "........",
              "....dd..",
              ".ddbbbd.",
              "dddbbbbk",
              "..lllr..",
              "...f.f.."],
    'hop':   ["....dd..",
              "...dbbk.",
              "...bbb..",
              ".ddbbr..",
              "dddbbr..",
              "..lll...",
              "...f.f..",
              "........"],
    'up':    ["..d.....",
              "..dd....",
              "..ddd...",
              "..ddbd..",
              ".dbbbbk.",
              "dd.lr...",
              "........",
              "........"],
    'down':  ["........",
              "........",
              "....bd..",
              ".dbbbbk.",
              "dddlr...",
              "..ddd...",
              "..dd....",
              "...d...."],
}
ORDER = ['stand', 'peck', 'hop', 'up', 'down']
ARTS = {
    'spatz':  dict(b=(118, 102, 88), d=(74, 62, 54), l=(168, 158, 146), k=(46, 40, 36), r=(118, 102, 88), f=(90, 74, 62)),
    'amsel':  dict(b=(44, 42, 46), d=(30, 28, 32), l=(52, 50, 54), k=(206, 146, 62), r=(44, 42, 46), f=(60, 52, 48)),
    'rotkehl': dict(b=(112, 100, 86), d=(80, 70, 60), l=(176, 168, 156), k=(40, 36, 34), r=(176, 70, 52), f=(90, 74, 62)),
}

if __name__ == '__main__':
    out = os.path.join(ROOT, 'assets', 'life')
    os.makedirs(out, exist_ok=True)
    for art, pal in ARTS.items():
        strip = np.zeros((8, 8 * len(ORDER), 4), np.uint8)
        for i, name in enumerate(ORDER):
            for y, row in enumerate(FRAMES[name]):
                for x, c in enumerate(row):
                    if c != '.':
                        strip[y, i * 8 + x] = (*pal[c], 255)
        Image.fromarray(strip).save(os.path.join(out, f'vogel_{art}.png'))
    print('ok')
