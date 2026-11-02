"""The world grew to 1800 px wide (10 x 18 chunks): the old west part must stay as it was."""
import hashlib
import json
import os
import unittest

import numpy as np
from PIL import Image

D = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'world')
REF_WEST = 'ef6fbe12542ec42a75982570ee6e7813'     # ground x < 380, y < 1200 before the Ostwald (the poppy gate changes x >= 380)
REF_SOUTH = ('db83c886008044a18cbfe7631b5239cd', '38036b7ab865bcf7db851324b8d2fadd')   # ground y >= 1160, x < 400 and 460..800 (the fringe glade takes x >= 800;
# 400..460 holds 85 pixels the south generator itself varies from run to run)


def _ground(cols):
    rows = [np.concatenate([np.array(Image.open(os.path.join(D, 'chunks', f'c_{cx}_{cy}_ground.png')).convert('RGB'))
                            for cx in cols], 1) for cy in range(18)]
    return np.concatenate(rows, 0)


class WorldWidth(unittest.TestCase):
    def test_the_world_is_ten_chunks_wide(self):
        w = json.load(open(os.path.join(D, 'world.json')))
        self.assertEqual((w['width'], w['height'], w['chunks']), (1800, 3600, [10, 18]))
        for cx in (0, 9):
            self.assertTrue(os.path.exists(os.path.join(D, 'chunks', f'c_{cx}_17_cells.bin')))

    def test_the_old_west_and_the_south_are_pixel_identical(self):
        g = _ground(range(5))
        self.assertEqual(hashlib.md5(g[:1200, :380].tobytes()).hexdigest(), REF_WEST)
        self.assertEqual(hashlib.md5(g[1160:, :400].tobytes()).hexdigest(), REF_SOUTH[0])
        self.assertEqual(hashlib.md5(g[1160:, 460:800].tobytes()).hexdigest(), REF_SOUTH[1])


if __name__ == '__main__':
    unittest.main()
