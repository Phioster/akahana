"""The world grew to 1800 px wide (10 x 18 chunks), then 2700 (0.18, the west on the left): the old west part must
stay as it was, but for the strip the west's seam mends (today's x < 60)."""
import hashlib
import json
import os
import unittest

import numpy as np
from PIL import Image

D = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'world')
REF_WEST = '32476894134c63c97d1d63770a1e096c'     # 0.18.8: country things blanked too; 0.18.6: the new trees' places blanked (_trees); was ca2c6f54...     # 0.18: x 60..380 (x < 60 is the west's seam) moved 900 right; before: 314675e06f31a6aa6528d3d34aa51483     # ground x < 380, y 320..1200 of the old map (0.11: the north's overhang reaches the rows above;
                                                    # before the north, y < 1200 was ef6fbe12542ec42a75982570ee6e7813)
REF_SOUTH = ('13a6914e83554981216a9e219f473fa8', '8af83fd5fb911cfd727d38fd71622298')   # 0.18.8: country things blanked too; 0.18.6: trees blanked; was dea8c05e..., 417b22e5...   # 0.18.5: down to y 4040, below lie the lake's new boats   # 0.18: the first from x 80, the bottom shore's mending reaches x 64 (was db83c886...)   # ground y >= 1160, x < 400 and y >= 1260, x 460..640 (the poppies run into the wood from x 660 and the wood's mix takes y < 1230;
# 400..460 holds 85 pixels the south generator itself varies from run to run)


def _ground(cols):
    rows = [np.concatenate([np.array(Image.open(os.path.join(D, 'chunks', f'c_{cx}_{cy}_ground.png')).convert('RGB'))
                            for cx in cols], 1) for cy in range(24)]
    return np.concatenate(rows, 0)


def _trees(shape):
    """Where the new meadow trees (0.18.6) and country things (0.18.8) stand with their shade and petals: left out of the old world's check."""
    w = json.load(open(os.path.join(D, 'world.json')))
    m = np.zeros(shape, bool)
    for s in w['sprites']:
        if s['name'][:2] in ('wt', 'wl'):
            m[max(0, s['y'] - 4):s['foot'] + 40, max(0, s['x'] - 6):s['x'] + s['w'] + 34] = True
    return m


class WorldWidth(unittest.TestCase):
    def test_the_world_is_ten_chunks_wide(self):
        w = json.load(open(os.path.join(D, 'world.json')))
        self.assertEqual((w['width'], w['height'], w['chunks']), (2700, 4800, [15, 24]))
        for cx in (0, 14):
            self.assertTrue(os.path.exists(os.path.join(D, 'chunks', f'c_{cx}_23_cells.bin')))

    def test_the_old_west_and_the_south_are_pixel_identical(self):
        g = _ground(range(10))
        g[_trees(g.shape[:2])] = 0
        N, K = 1200, 900                           # the north on top (0.11), the west on the left (0.18)
        h = lambda a: hashlib.md5(np.ascontiguousarray(a).tobytes()).hexdigest()
        self.assertEqual(h(g[N + 320:N + 1200, K + 60:K + 380]), REF_WEST)
        self.assertEqual(h(g[N + 1160:4040, K + 80:K + 400]), REF_SOUTH[0])
        self.assertEqual(h(g[N + 1260:4040, K + 460:K + 640]), REF_SOUTH[1])


if __name__ == '__main__':
    unittest.main()
