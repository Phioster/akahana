#!/usr/bin/env python3
"""The whole map so far in the game's mood, as one picture: the old world and below it the south (zones
1-3), graded in one pass so the mist runs on across the seam. The empty strip east of the old world
(the eastern wood comes later) is left out: plain dark there.

    python3 tools/world/south/full_map.py OUT.png [scale]
"""
import copy
import json
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, HERE)
import mood_map  # noqa: E402
import zone1_draft as z1  # noqa: E402
import zone2_draft as z2  # noqa: E402
import zone3_draft as z3  # noqa: E402
import zone4_draft as z4  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
EMPTY = np.array([29.0, 28.0, 32.0])         # the page background: nothing drawn there yet


def main(out, scale=2):
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    south, lights, swarms, band, edge_fog, calm = z4.render(w, raw=True)
    top = z1.OLD_H - z1.CTX                    # the south canvas starts at this old-world row
    old = mood_map.composite(w)
    H = top + south.shape[0]
    img = np.zeros((H, z1.W, 3))
    img[:top] = EMPTY
    img[:top, :z1.OLD_W] = old[:top, :z1.OLD_W]
    img[top:] = south
    lit = [l for l in w['lights']] + [dict(l, y=l['y'] + top) for l in lights[len(w['lights']):]]
    sw = []
    for s_ in swarms:
        s2 = copy.deepcopy(s_)
        s2.y += top
        sw.append(s2)
    wb = np.zeros((H, z1.W))
    wb[top:] = band
    cm = np.zeros((H, z1.W))
    cm[top:] = calm
    ef = np.zeros((H, z1.W))
    ef[top:] = edge_fog
    a = mood_map.mood(img, dict(w, lights=lit + [l for s_ in sw for l in s_.lights(2.0)]), 2.0,
                      grass_mist=z2.GRASS_MIST, water_band=wb, calm=cm).astype(float)
    for s_ in sw:
        s_.draw(a, 2.0)
    a = a * (1 - ef[..., None]) + z4.MIST * ef[..., None]   # the world fades into mist in the south
    a[:top, z1.OLD_W:] = EMPTY                 # keep the empty strip plain, no mist over nothing
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    im.save(out.replace('.png', '_1x.png'))
    im.resize((im.width * scale, im.height * scale), Image.NEAREST).save(out, optimize=True)
    print('ok', im.size, flush=True)


if __name__ == '__main__':
    main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 2)
