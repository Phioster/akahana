#!/usr/bin/env python3
"""The greenhouse's inside for the game (Garasu-muro, west), as gen_cave does the cave: its picture (what he walks
on and behind), its canopy (crowns and lianas over him), its walkable mask and glashaus.json - where its door lies
in the world, where he comes out, where he stands inside and where the way out ends."""
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, 'west')]
import glashaus_inside as GI  # noqa: E402
import dorf1_draft as D  # noqa: E402

OUT = os.path.join(HERE, '..', '..', 'assets', 'world', 'glashaus')


def main():
    os.makedirs(OUT, exist_ok=True)
    img, canopy, walk, light = GI.render()
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(OUT, 'glashaus.png'))
    can = np.zeros(canopy.shape, np.uint8)
    m = canopy[..., 3] > 0
    can[m, :3] = np.clip(canopy[m, :3], 0, 255).astype(np.uint8)
    can[m, 3] = 255
    Image.fromarray(can).save(os.path.join(OUT, 'glashaus_canopy.png'))
    Image.fromarray((walk * 255).astype(np.uint8)).save(os.path.join(OUT, 'glashaus_walk.png'))
    walk.astype(np.uint8).tofile(os.path.join(OUT, 'glashaus_walk.bin'))
    dx, dy = D.GLASHAUS[0], D.GLASHAUS[1] + 4                          # the door's foot in the world (west = world x)
    mid = (GI.DOOR[0] + GI.DOOR[1]) // 2
    meta = {
        'size': [GI.W, GI.H],
        'mouth': [dx - 4, dy - 12, 9, 10],                             # the doorway, up to its threshold
        'out': [dx, dy + 2],
        'out_to': [dx, dy + 14],
        'in': [mid, GI.H - 3],
        'in_to': [mid, GI.H - 28],
        'exit_y': GI.H - 10,
        'light': dict(light, kind='lantern'),
        'warm': True,                                                  # its own warm grade, not the evening outside
        'canopy': True,
    }
    json.dump(meta, open(os.path.join(OUT, 'glashaus.json'), 'w'), indent=1)
    print('Gewächshaus:', meta)


if __name__ == '__main__':
    main()
