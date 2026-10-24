"""The generated world must be self-consistent: the game trusts these files blindly."""
import json
import os
import unittest

import numpy as np
from PIL import Image

D = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'world')


class WorldAssets(unittest.TestCase):
    def setUp(self):
        self.w = json.load(open(os.path.join(D, 'world.json')))
        self.walk = np.fromfile(os.path.join(D, 'walk.bin'), np.uint8).reshape(self.w['height'], self.w['width'])

    def test_sprites_lie_inside_the_world_and_match_their_files(self):
        for s in self.w['sprites']:
            self.assertGreaterEqual(s['x'], 0, s['name'])
            self.assertLessEqual(s['x'] + s['w'], self.w['width'], s['name'])
            with Image.open(os.path.join(D, 'sprites', s['name'] + '.png')) as img:
                self.assertEqual(img.size, (s['w'] * s['frames'], s['h']), s['name'])

    def test_start_is_walkable(self):
        st = self.w['start']
        self.assertEqual(self.walk[int(st['y']), int(st['x'])], 1)

    def test_world_edges_are_closed(self):
        self.assertFalse(self.walk[:, :10].any())
        self.assertFalse(self.walk[:, -10:].any())
        self.assertFalse(self.walk[:30].any())

    def test_cells_are_the_2x2_all_of_the_mask(self):
        cells = np.fromfile(os.path.join(D, 'walk_cells.bin'), np.uint8)
        h, w = self.w['height'] // 2, self.w['width'] // 2
        self.assertEqual(cells.size, h * w)
        expect = self.walk.reshape(h, 2, w, 2).all(axis=(1, 3)).astype(np.uint8).ravel()
        self.assertTrue((cells == expect).all())


if __name__ == '__main__':
    unittest.main()
