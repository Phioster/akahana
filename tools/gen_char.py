#!/usr/bin/env python3
"""The wanderer, a small monk: habit with a rope belt, staff slung across the back, pointed hood.
4 directions x (2 idle + 4 walk) frames, 14x20 cells, feet at (7, 19).

Rows: down, up, left, right.  Cols: idle0, idle1, walk0..walk3.
Lit from the upper left like the whole world; no outlines - the dark habit reads against the pale ground.
Usage: gen_char.py [kapuze] [out.png]   (default -> assets/char/wanderer.png)
"""
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def hx(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


PAL = {
    # dark habit with a light rim on the lit (upper left) edges: the silhouette must read on snow AND poppies
    'L': hx('#9c8068'),                                               # rim light
    'H': hx('#4a372c'), 'h': hx('#34261f'), 'd': hx('#1a1210'),       # hood: lit, mid, inner shadow
    'f': hx('#e8cba6'), 'g': hx('#b8916f'), 'e': hx('#1e1614'),       # face, face shade, eye
    'C': hx('#4a372c'), 'c': hx('#33261f'), 'k': hx('#1f1713'),       # habit: lit, mid, shade
    'y': hx('#dcbd84'), 'Y': hx('#a8895a'),                           # rope belt, its hanging end
    'p': hx('#d23c30'),                                               # a poppy pinned on
    'T': hx('#3c2c22'), 't': hx('#281d17'), 'w': hx('#8a6c50'), 'W': hx('#5a4434'),   # hat crown / brim
    's': hx('#c49a64'), 'S': hx('#8a6a44'),                           # staff, light wood
    'b': hx('#160f0d'), 'B': hx('#2a201c'),                           # sandals / feet
}

# 12 wide, 14 high; '.' is empty. Pointed hood, straight habit: a shape you know at a glance.
HOOD = {
    'down': [".....LH.....",
             "....LHHh....",
             "...LHHhhd...",
             "..LHdddddd..",
             "..Hdffffdd..",
             "..Hdfefedd..",
             "..hddffddd..",
             ".LCCcccpckk.",
             ".LCcccccckk.",
             ".Cyyyyyyykk.",
             "..CcccYcck..",
             "..Ccccccck..",
             "..Ccccccck..",
             "..LCccccck.."],
    'up': [".....LH.....",
           "....LHHh....",
           "...LHHhhd...",
           "..LHHhhhhd..",
           "..HHhhhhhd..",
           "..HHhhhhhd..",
           "..hhhhhhdd..",
           ".LCCcccckkk.",
           ".LCcccccckk.",
           ".Cyyyyyyykk.",
           "..Ccccccck..",
           "..Ccccccck..",
           "..Ccccccck..",
           "..LCccccck.."],
    'right': ["..LH........",
              "...LHh......",
              "...LHHhh....",
              "...HHhhdd...",
              "...HHhdfff..",
              "...Hhhdfef..",
              "...hhhddg...",
              "...LCCcckp..",
              "...LCcccck..",
              "...Cyyyyyk..",
              "...CcccYk...",
              "...Ccccck...",
              "...Ccccck...",
              "...LCcccck.."],
}
HAT = HOOD                                                # the hat variant was dropped (2026-10-26)
CW, CH = 14, 20                                           # cell; feet at (7, 19)


def body(rows, flip=False):
    a = np.zeros((len(rows), len(rows[0]), 4), np.uint8)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in PAL:
                a[j, i] = PAL[ch]
    return a[:, ::-1] if flip else a


def staff(c, direction, bob):
    """Slung diagonally across the back, long enough to show at both ends: the knob above one shoulder,
    the foot beside the habit on the other side. Behind the body from the front, over it from behind."""
    if direction in ('down', 'up'):
        x0, x1 = (12, 2) if direction == 'down' else (1, 11)
    else:
        x0, x1 = (2, 5) if direction == 'right' else (11, 8)
    y0, y1 = 1, 17
    n = max(abs(x1 - x0), y1 - y0)
    for i in range(n + 1):
        y = round(y0 + (y1 - y0) * i / n) + bob
        x = round(x0 + (x1 - x0) * i / n)
        if 0 <= y < CH and 0 <= x < CW:
            c[y, x] = PAL['s'] if i < n // 2 else PAL['S']
    if 0 <= y0 - 1 + bob < CH:                            # the knob
        c[y0 - 1 + bob, x0] = PAL['S']


def cell(direction, col, look):
    c = np.zeros((CH, CW, 4), np.uint8)
    walking = col >= 2
    step = (col - 2) % 4 if walking else 0
    bob = 1 if walking and step in (1, 3) else 0          # the body dips on each footfall
    breath = 1 if (not walking and col == 1) else 0
    # shadow under the feet: solid dark pixels (half transparency turns into a checkerboard when dithered)
    for i in range(5, 10):
        c[19, i] = (34, 28, 30, 255)
    # feet below the habit, alternating when walking
    if direction in ('down', 'up'):
        lf = 18 if step != 1 else 17
        rf = 18 if step != 3 else 17
        c[lf, 5:7] = PAL['b']
        c[rf, 8:10] = PAL['b']
    else:
        front = 1 if direction == 'right' else -1
        spread = {0: 0, 1: 1, 2: 0, 3: -1}[step] if walking else 0
        c[18, 6 + spread * front] = PAL['b']
        c[18, 8 - spread * front] = PAL['b']
    rows = (HOOD if look == 'kapuze' else HAT)[{'left': 'right'}.get(direction, direction)]
    b = body(rows, flip=(direction == 'left'))
    if direction != 'up':
        staff(c, direction, bob)                          # behind the body
    y0 = 4 + bob
    if breath:                                            # breathing: shoulders sink a pixel
        b = np.concatenate([b[:7], b[8:], b[-1:]], axis=0)
    x0 = 1
    m = b[..., 3] > 0
    sub = c[y0:y0 + b.shape[0], x0:x0 + b.shape[1]]
    hh = min(sub.shape[0], b.shape[0])
    sub[:hh][m[:hh]] = b[:hh][m[:hh]]
    if direction == 'up':
        staff(c, direction, bob)                          # seen from behind it lies over the back
    return c


def sheet(look):
    s = np.zeros((CH * 4, CW * 6, 4), np.uint8)
    for r, d in enumerate(('down', 'up', 'left', 'right')):
        for col in range(6):
            s[r * CH:(r + 1) * CH, col * CW:(col + 1) * CW] = cell(d, col, look)
    return s


if __name__ == '__main__':
    look = sys.argv[1] if len(sys.argv) > 1 else 'kapuze'
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'assets', 'char', 'wanderer.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    Image.fromarray(sheet(look)).save(out)
    print('ok', look)
