#!/usr/bin/env python3
"""The squirrel, drawn pixel by pixel like the small birds (tools/gen_birds.py): facing right, about 7 px tall in 12x12 cells.
Frames: sit, nibble, hop1 (stretched), hop2 (bunched), climb1, climb2 (on a trunk, seen from behind).
    python3 tools/world/life/squirrel_art.py OUT.png   # a sheet to look at
"""
import sys

import numpy as np
from PIL import Image

# . empty, b body, d back/shade, l belly, t tail, T tail shade, e ear tuft, k eye, f paws
FRAMES = {   # 0.21.1: kleiner neu gezeichnet (Philip: wirkte im Spiel zu groß), etwa 7 px hoch neben dem 16-px-Mönch
    'sit':    [".TT...e.",
               "TttT.dbk",
               "TttTdbbb",
               ".TTtdbll",
               "..Ttdbll",
               "..TTdbl.",
               "...ddf.f"],
    'eat_up': [".TT..e..",
               "TttTdbbk",
               "TttTdbfn",
               ".TTtdbl.",
               "..Ttdbll",
               "..TTdbl.",
               "...ddf.f"],
    'eat_dn': [".TT.....",
               "TttT..e.",
               "TttTdbbk",
               ".TTtdbfn",
               "..Ttdbll",
               "..TTdbl.",
               "...ddf.f"],
    'eat_tw': ["..TT.e..",
               ".TttTdbk",
               ".TttTdfn",
               "..TTtbl.",
               "..Ttdbll",
               "..TTdbl.",
               "...ddf.f"],
    'hop1':   ["TT.......",
               ".Tt...e..",
               "..TTddbbk",
               "...fbllb.",
               "..f....f."],
    'hop2':   [".TT......",
               "TttT..e..",
               "..TTdbbk.",
               "....dllf.",
               ".....f.f."],
    'climb1': ["..b...",
               "..kbe.",
               ".fbbd.",
               "..lbd.",
               ".flbd.",
               "..dTT.",
               "...TtT",
               "...TtT",
               "....T."],
    'climb2': ["......",
               "..b...",
               "..kbe.",
               ".fbbd.",
               "..lbdT",
               ".fbdtT",
               "...TtT",
               "....T.",
               "......"],
}
ORDER = ['sit', 'eat_up', 'eat_dn', 'eat_tw', 'hop1', 'hop2', 'climb1', 'climb2']
PAL = dict(b=(150, 86, 56), d=(108, 60, 42), l=(168, 128, 92), t=(140, 80, 52), T=(96, 54, 38),
           e=(108, 60, 42), k=(30, 24, 22), f=(86, 50, 36), D=(140, 80, 52), n=(186, 150, 96), B=(150, 86, 56))


def cell(name):
    rows = FRAMES[name]
    a = np.zeros((12, 12, 4), np.uint8)                # 12 tall, art at the bottom
    for y, row in enumerate(rows, 12 - len(rows)):
        for x, c in enumerate(row):
            if c != '.':
                a[y, x] = (*PAL[c], 255)
    return a


def sheet():
    return np.concatenate([cell(n) for n in ORDER], axis=1)


if __name__ == '__main__':
    s = sheet()
    bg = np.zeros((16, s.shape[1] + 4, 3), np.uint8) + np.array([88, 96, 78], np.uint8)
    m = s[..., 3] > 0
    bg[2:14, 2:-2][m] = s[m][:, :3]
    Image.fromarray(bg).resize((bg.shape[1] * 12, bg.shape[0] * 12), Image.NEAREST).save(sys.argv[1])
