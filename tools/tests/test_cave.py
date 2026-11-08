"""The cave's screen (gen_cave): he can walk into its mouth from the snow, inside from the way in to the
candle and back off the bottom edge, and nowhere he could get stuck."""
import json
import os
import unittest

import numpy as np
from PIL import Image

from tools.tests.flood import reach
from tools.tests.test_world_assets import D, _cells

C = os.path.join(D, 'cave')


def cells(walk):
    """Pathing's rule: a 2-px cell is free only if all four pixels are."""
    h, w = walk.shape
    return walk[:h // 2 * 2, :w // 2 * 2].reshape(h // 2, 2, w // 2, 2).all(axis=(1, 3))


class Cave(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = json.load(open(os.path.join(C, 'cave.json')))
        cls.walk = np.array(Image.open(os.path.join(C, 'cave_walk.png'))) > 127
        cls.pic = Image.open(os.path.join(C, 'cave.png'))

    def test_picture_and_mask_have_the_cave_s_size(self):
        self.assertEqual(list(self.pic.size), self.m['size'])
        self.assertEqual(list(self.walk.shape[::-1]), self.m['size'])

    def test_the_game_s_raw_mask_is_the_picture_s(self):
        raw = np.fromfile(os.path.join(C, 'cave_walk.bin'), np.uint8).reshape(self.walk.shape)
        self.assertTrue(np.array_equal(raw > 0, self.walk))

    def test_the_way_in_is_never_a_crack(self):
        # 0.12.0 he got stuck in the way in: it narrowed to one cell; now at least three cells wide
        c = cells(self.walk)
        rows = c[150:self.m['exit_y'] // 2]
        self.assertGreaterEqual(int(rows.sum(1).min()), 3)

    def test_inside_the_way_in_reaches_the_candle_and_the_way_out(self):
        c = cells(self.walk)
        sx, sy = self.m['in']
        got = reach(c, [(sy // 2, sx // 2)])                  # 4-way: the game does not cut corners
        self.assertTrue(got[sy // 2, sx // 2], 'er steht beim Hereinkommen frei')
        tx, ty = self.m['in_to']
        self.assertTrue(got[ty // 2, tx // 2])
        lx, ly = int(self.m['light']['x']), int(self.m['light']['y'])
        near = got[ly // 2 - 6:ly // 2 + 10, lx // 2 - 10:lx // 2 + 10]
        self.assertTrue(near.any(), 'bis an die Kerze')
        self.assertTrue(got[self.m['exit_y'] // 2:].any(), 'der Weg hinaus ist frei')
        self.assertLess(self.m['in_to'][1], self.m['exit_y'], 'nach dem Hereinkommen steht er oberhalb')
        self.assertGreater(self.m['exit_y'], self.m['size'][1] - 30, 'hinaus geht es erst im letzten Stück')
        self.assertEqual(int((c & ~got).sum()), 0, 'kein abgeschnittener Fleck')

    def test_the_mouth_is_walked_into_from_the_snow(self):
        w = json.load(open(os.path.join(D, 'world.json')))
        free = _cells(w, 'cells').astype(bool)
        ox, oy = self.m['out_to']
        c0 = ox // 2 - 35                                       # the window round the mouth (moved with the west, 0.18)
        got = reach(free[300:420, c0:c0 + 80], [(oy // 2 - 300, ox // 2 - c0)], diagonal=True)
        x, y, mw, mh = self.m['mouth']
        mouth = got[y // 2 - 300:(y + mh) // 2 - 300, x // 2 - c0:(x + mw) // 2 - c0]
        self.assertTrue(mouth.any(), 'vom Schnee bis in den Höhleneingang')
        self.assertTrue(free[self.m['out'][1] // 2, self.m['out'][0] // 2], 'beim Hinausgehen steht er frei')
        mx, my = self.m['out']
        self.assertFalse(x <= mx < x + mw and y <= my < y + mh, 'hinaus ist nicht gleich wieder hinein')


if __name__ == '__main__':
    unittest.main()
