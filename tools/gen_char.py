#!/usr/bin/env python3
"""The wanderer: a tiny monk, drawn pixel by pixel in the world's palette.

Small on purpose (about 13 px tall in a 12x16 cell, feet at (6, 15)): the world is the main thing.
Pointed hood, a face, sleeves, rope belt, a habit down to the ankles with two flat feet stepping under
the swinging hem, and the staff slung across the back. Rows: down, up, left, right. Cols: idle0, idle1, walk0..walk5.
Walk: two footfalls per cycle, on walk frames 1 and 4 (scenes/player.gd CONTACT): the feet move apart
and the hem swings wide; between the steps one foot is lifted and the body rises a pixel.
Out: assets/char/wanderer.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
CW, CH = 12, 16
STRIDE = 5                                    # px between the feet at full stride (FEET_SIDE contact)

PAL = {                                       # the world's muted warm-greys (cottage, bench, shrine)
    'L': (112, 100, 94),                      # light on the upper-left edges
    'H': (72, 62, 60), 'h': (54, 46, 46), 'd': (38, 34, 36),      # hood: lit, mid, inner shadow
    'f': (196, 168, 146), 'g': (150, 124, 108), 'e': (40, 32, 32),  # face, face shade, eye
    'C': (72, 62, 60), 'c': (54, 46, 46), 'k': (38, 34, 36),      # habit: lit, mid, shade
    'y': (176, 160, 128), 'Y': (128, 114, 92),                    # rope belt, its hanging end
    'l': (46, 40, 40), 'b': (30, 26, 28),                         # legs, feet
    's': (156, 126, 94), 'S': (112, 90, 68),                      # staff
}

UPPER = {                                     # 7 wide, rows 0..9 = cell rows 3..12
    'down': ["...L...",
             "..LHh..",
             ".LHhhd.",
             ".Hfefd.",
             ".hdgdd.",
             "LCCcckk",
             "CCyyyYk",
             ".Cccck.",
             ".Cccck.",
             ".Ccccc."],
    'up': ["...L...",
           "..LHh..",
           ".LHhhd.",
           ".HHhhd.",
           ".hhhhd.",
           "LCCcckk",
           "CCyyyyk",
           ".Cccck.",
           ".Cccck.",
           ".Ccccc."],
    'right': [".L.....",
              "..LHh..",
              "..HHhd.",
              "..Hhfe.",
              "..hhgf.",
              "..LCck.",
              "..CyyY.",
              "..Ccck.",
              "..Ccck.",
              "..Ccck."],                # front edge straight down: no belly, no hollow back
}


def put(c, x, y, key):
    if 0 <= x < CW and 0 <= y < CH:
        c[y, x] = (*PAL[key], 255)


def phase(i):
    """Walk frame i -> leg swing s in -1..1 (contact at frames 1 and 4) and its direction."""
    a = (i + 0.5) / 6 * 2 * math.pi
    return math.sin(a), math.cos(a)


def staff(c, direction, lift):
    if direction == 'down':
        line = [(9 - (y - 1) * 6 // 11, y) for y in range(1, 13)]
    elif direction == 'up':
        line = [(2 + (y - 1) * 6 // 11, y) for y in range(1, 13)]
    elif direction == 'right':
        line = [(3, y) for y in range(1, 12)]                 # hugging the back
    else:
        line = [(7, y) for y in range(1, 12)]
    for k, (x, y) in enumerate(line):
        put(c, x, y - lift, 's' if k < 5 else 'S')


# Below the habit only the feet show: two flat patches that move under the hem. Rows 13-15 of the cell,
# cols 2..8. 'C'/'c'/'k' the hem, 'b' the near foot, 'B' the far one (a touch darker).
FEET_SIDE = {                                  # facing right, cols 1..8; mirrored for left
    'stand': ["...Ccck.", "...Ccck.", "....bb.."],
    'pass': ["...Ccck.", "...Ccck.", "....bb.."],     # one foot under him, the other lifted out of sight
    'contact': ["...Ccck.", "..Ccccck", ".BB...bb"],  # stride: the hem opens at the bottom only
    'down': ["...Ccck.", "..Ccccc.", "..BB.bb."],     # feet come together again
}
FEET_FRONT = {
    'stand': [".Cccck.", ".Ccccc.", ".bb.bb."],
    'left_up': [".Cccck.", ".Ccccc.", "....bb."],
    'right_up': [".Cccck.", ".Ccccc.", ".bb...."],
    'both': [".Cccck.", "Cccccck", ".bb.bb."],
}
SIDE_CYCLE = ['pass', 'contact', 'down', 'pass', 'contact', 'down']     # contact on frames 1 and 4
FRONT_CYCLE = ['left_up', 'both', 'both', 'right_up', 'both', 'both']
PAL['B'] = (22, 20, 22)


def feet(c, rows, direction, swap, lift_body):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            if swap and ch in 'bB':
                ch = 'B' if ch == 'b' else 'b'
            if direction in ('left', 'right'):
                x = 1 + i if direction == 'right' else 9 - i
            else:
                x = 2 + i
            y = 13 + j                                        # hem and feet stay on the ground
            put(c, x, y, ch)


def cell(direction, col):
    c = np.zeros((CH, CW, 4), np.uint8)
    walking = col >= 2
    s, cs = phase(col - 2) if walking else (0.0, 0.0)
    lift = 1 if walking and abs(s) < 0.6 else 0         # between the steps the body rises a pixel
    breath = 1 if (not walking and col == 1) else 0
    side = direction in ('left', 'right')
    facing = 1 if direction == 'right' else -1
    if direction != 'up':
        staff(c, direction, lift)                       # behind the body
    i = col - 2
    if side:
        feet(c, FEET_SIDE[SIDE_CYCLE[i] if walking else 'stand'], direction, walking and i >= 3, lift)
    else:
        feet(c, FEET_FRONT[FRONT_CYCLE[i] if walking else 'stand'], direction, False, lift)
    rows = UPPER['right' if side else direction]
    if breath:
        rows = rows[:5] + rows[6:] + rows[-1:]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            x = 2 + i if direction != 'left' else 2 + (6 - i)
            put(c, x, 3 + j - lift, ch)
    if lift:                                            # body up a pixel: the habit grows, no gap opens
        last = rows[-1]
        for i, ch in enumerate(last):
            if ch != '.':
                x = 2 + i if direction != 'left' else 2 + (6 - i)
                put(c, x, 12, ch)
    if walking:                                         # sleeves swing against the legs
        if side:
            pass                                        # from the side a sleeve bump reads as a belly
        elif s > 0.35:
            put(c, 1, 9 - lift, 'c')
        elif s < -0.35:
            put(c, 9, 9 - lift, 'k')
    if direction == 'up':
        staff(c, direction, lift)                       # seen from behind it lies over the back
    return c


def sheet():
    out = np.zeros((CH * 4, CW * 8, 4), np.uint8)
    for r, d in enumerate(('down', 'up', 'left', 'right')):
        for col in range(8):
            out[r * CH:(r + 1) * CH, col * CW:(col + 1) * CW] = cell(d, col)
    return out


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'assets', 'char', 'wanderer.png')
    os.makedirs(os.path.dirname(out), exist_ok=True)
    Image.fromarray(sheet()).save(out)
    print('ok', out)
