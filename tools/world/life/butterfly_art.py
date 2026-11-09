#!/usr/bin/env python3
"""Butterflies, seen from above at a slant: 5x3 cells. Wings open, half, shut (a flap is open-half-shut-half).
Three kinds, none red (red is the poppies'): cabbage white, brimstone, small blue.
    python3 tools/world/life/butterfly_art.py OUT.png
"""
import sys

import numpy as np
from PIL import Image

# . empty, W forewing, X its tip (the outer corners), s spot by the body, w hindwing and underside, b body
FRAMES = {
    'open': ["Xs.sX",
             "WwbwW",
             ".wbw."],
    'half': [".X.X.",
             ".wbw.",
             "..b.."],
    'shut': ["..X..",
             "..w..",
             "..b.."],
}
ORDER = ['open', 'half', 'shut']
WHITE, CREAM, DARK = (246, 244, 232), (206, 204, 192), (52, 46, 44)
KINDS = {                                       # one colour, or two: tips, eyes, bands
    'weiss':   dict(W=WHITE, X=(70, 68, 66), s=WHITE, w=CREAM, b=(60, 58, 56)),
    'aurora':  dict(W=WHITE, X=(236, 128, 52), s=WHITE, w=(196, 204, 176), b=(60, 58, 56)),
    'zitrone': dict(W=(246, 228, 120), X=(246, 228, 120), s=(214, 150, 64), w=(208, 190, 90), b=(80, 72, 50)),
    'blau':    dict(W=(160, 186, 236), X=(120, 140, 196), s=(160, 186, 236), w=(120, 140, 196), b=(60, 58, 70)),
    'fuchs':   dict(W=(226, 116, 52), X=DARK, s=(236, 206, 112), w=(146, 84, 50), b=DARK),
    'pfau':    dict(W=(182, 50, 44), X=(118, 150, 214), s=(222, 186, 96), w=(138, 40, 36), b=DARK),
    'admiral': dict(W=(196, 52, 40), X=(236, 232, 224), s=DARK, w=(56, 48, 46), b=DARK),
}


def cell(kind, name):
    a = np.zeros((3, 5, 4), np.uint8)
    for y, row in enumerate(FRAMES[name]):
        for x, c in enumerate(row):
            if c != '.':
                a[y, x] = (*KINDS[kind][c], 255)
    return a


if __name__ == '__main__':
    rows = [np.concatenate([np.pad(cell(k, n), ((1, 1), (1, 1), (0, 0))) for n in ORDER], 1) for k in KINDS]
    s = np.concatenate(rows, 0)
    bg = np.zeros(s.shape[:2] + (3,), np.uint8) + np.array([88, 96, 78], np.uint8)
    m = s[..., 3] > 0
    bg[m] = s[m][:, :3]
    Image.fromarray(bg).resize((bg.shape[1] * 16, bg.shape[0] * 16), Image.NEAREST).save(sys.argv[1])
