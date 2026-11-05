#!/usr/bin/env python3
"""The cave's inside for the game (Höhle, north): its picture, its walkable mask and cave.json - where its
mouth lies in the world, where he comes out, where he stands inside and where the way out ends."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'north'))
import cave_inside as C  # noqa: E402

OUT = os.path.join(HERE, '..', '..', 'assets', 'world', 'cave')
MOUTH = (150, 705)            # zone2_draft.CAVE: foot of the mouth, world coordinates


def main():
    walk, light = C.export(OUT)
    xs = np.nonzero(walk[C.H - 1])[0]
    mid = int(round(xs.mean()))
    meta = {
        'size': [C.W, C.H],
        'mouth': [MOUTH[0] - 5, MOUTH[1] - 13, 11, 13],       # x, y, w, h: the dark arch down to its threshold
        'out': [MOUTH[0], MOUTH[1] + 3],                       # where he steps out ...
        'out_to': [MOUTH[0], MOUTH[1] + 14],                   # ... and the few steps onto the snow
        'in': [mid, C.H - 3],
        'in_to': [mid, C.H - 30],
        'exit_y': C.H - 24,                                    # walking down past here (the snow blown in) takes him out
        'light': dict(light, kind='candle'),
    }
    json.dump(meta, open(os.path.join(OUT, 'cave.json'), 'w'), indent=1)
    print('Höhle:', meta)


if __name__ == '__main__':
    main()
