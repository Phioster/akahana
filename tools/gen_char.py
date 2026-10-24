#!/usr/bin/env python3
"""The wanderer: 4 directions x (2 idle + 4 walk) frames, 12x16 cells, feet at (6, 15).

Rows: down, up, left, right.  Cols: idle0, idle1, walk0..walk3.
Lit from the upper left like the whole world; no outlines - the dark cloak reads against the pale ground.
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
def hx(c): return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)
PAL = {
    'H': hx('#6e6266'), 'h': hx('#4f454a'), 'd': hx('#2c2427'),       # hood: lit, mid, inner shadow
    'f': hx('#d2b394'), 'g': hx('#a3826c'), 'e': hx('#2a2020'),       # face, face shade, eye
    'r': hx('#c2382f'), 'R': hx('#7e1f22'),                           # scarf, like the poppies
    'C': hx('#5d5155'), 'c': hx('#41383c'), 'k': hx('#2a2326'),       # cloak: lit, mid, shade
    's': hx('#8a6f55'), 'S': hx('#5a4634'),                           # staff
    'b': hx('#241d1f'), 'B': hx('#3a3032'),                           # boots
}
DOWN = ["..hhhh..",
        ".Hhhhhd.",
        ".Hdffdd.",
        ".Hfefed.",
        ".rrrrRR.",
        "CCcccckk",
        "CCcccckk",
        ".Ccccck.",
        ".Ccccck.",
        "..cc.kk."]
UP = ["..hhhh..",
      ".Hhhhhd.",
      ".Hhhhhd.",
      ".Hhhhdd.",
      ".rrrrRR.",
      "CCcccckk",
      "CCccckkk",
      ".Ccccck.",
      ".Ccccck.",
      "..cc.kk."]
RIGHT = ["..hhh...",
         ".Hhhhh..",
         ".Hhhdff.",
         ".Hhhdfe.",
         ".rrrRR..",
         ".CCcck..",
         ".CCcckk.",
         ".Cccck..",
         ".Cccck..",
         "..cck..."]


def body(rows, flip=False):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in PAL:
                a[j, i] = PAL[ch]
    return a[:, ::-1] if flip else a


def cell(direction, col):
    c = np.zeros((16, 12, 4), np.uint8)
    walking = col >= 2
    step = (col - 2) % 4 if walking else 0
    bob = 1 if walking and step in (1, 3) else 0          # the body dips on each footfall
    breath = 1 if (not walking and col == 1) else 0
    # soft shadow under the feet (half transparent, the ground shows through)
    for i in range(3, 10):
        c[14, i] = (40, 34, 36, 110)
    for i in range(4, 9):
        c[15, i] = (40, 34, 36, 70)
    # legs / boots: rows 11..14, alternate when walking
    if direction in ('down', 'up'):
        lx, rx = 4, 7
        ll = 3 if step == 1 else 2 if step == 3 else 3
        rl = 2 if step == 1 else 3 if step == 3 else 3
        for k in range(ll):
            c[14 - k, lx] = PAL['B'] if k else PAL['b']
        for k in range(rl):
            c[14 - k, rx] = PAL['B'] if k else PAL['b']
    else:
        front = 1 if direction == 'right' else -1
        spread = {0: 0, 1: 1, 2: 0, 3: -1}[step] if walking else 0
        for k in range(3):
            c[14 - k, 5 + spread * front] = PAL['b'] if k == 0 else PAL['B']
            c[14 - k, 6 - spread * front] = PAL['b'] if k == 0 else PAL['B']
    rows = {'down': DOWN, 'up': UP, 'right': RIGHT, 'left': RIGHT}[direction]
    b = body(rows, flip=(direction == 'left'))
    y0 = 2 + bob
    if breath:                                             # breathing: shoulders and cloak sink a pixel
        b = np.concatenate([b[:5], b[6:], b[-1:]], axis=0)
    x0 = 2
    m = b[..., 3] > 0
    sub = c[y0:y0 + b.shape[0], x0:x0 + b.shape[1]]
    sub[m] = b[m]
    # staff: held on the far side, swings a little when walking
    sx = {'down': 10, 'up': 1, 'right': 10, 'left': 1}[direction]
    top = 3 + bob - (1 if walking and step in (0, 2) else 0)
    for y in range(top, 15):
        c[y, sx] = PAL['s'] if y < 8 else PAL['S']
    return c


sheet = np.zeros((16 * 4, 12 * 6, 4), np.uint8)
for r, d in enumerate(('down', 'up', 'left', 'right')):
    for col in range(6):
        sheet[r * 16:(r + 1) * 16, col * 12:(col + 1) * 12] = cell(d, col)
os.makedirs(os.path.join(ROOT, 'assets', 'char'), exist_ok=True)
Image.fromarray(sheet).save(os.path.join(ROOT, 'assets', 'char', 'wanderer.png'))
print('ok')
