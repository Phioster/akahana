"""The world grew to 1800 px wide (10 x 18 chunks): the old west part must stay as it was."""
import hashlib
import json
import os
import unittest

import numpy as np
from PIL import Image

D = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'world')
REF_MD5 = '47cee5a72caf6043bc54e853c03957d4'      # ground of x < 900 (5 x 18 chunks) before the eastern wood, 0.9.2


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
        self.assertEqual(hashlib.md5(_ground(range(5)).tobytes()).hexdigest(), REF_MD5)

    def test_the_new_columns_are_closed_for_now(self):
        w = json.load(open(os.path.join(D, 'world.json')))
        cw, ch = w['chunk']
        for cx in range(5, 10):
            cells = np.fromfile(os.path.join(D, 'chunks', f'c_{cx}_9_cells.bin'), np.uint8)
            self.assertEqual(int(cells.sum()), 0, f'chunk {cx} must hold no walkable cell yet')


if __name__ == '__main__':
    unittest.main()
