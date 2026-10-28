import os
import sys
import unittest

import numpy as np

sys.path[:0] = [os.path.dirname(os.path.abspath(__file__)), os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')]
import reflect_map  # noqa: E402


class TestReflectMap(unittest.TestCase):
    def test_a_flat_thing_is_turned_over_not_moved(self):
        # phone 0.7.2: stones and lily pads showed moved down, not mirrored
        H, W = 20, 5
        low = np.zeros((H, W), np.uint8)
        ground = np.zeros((H, W, 3), np.uint8)
        low[4:7, 2] = 1                                         # a 3-px tall thing: rows 4 (top) .. 6 (bottom)
        ground[4, 2], ground[5, 2], ground[6, 2] = (200, 0, 0), (0, 200, 0), (0, 0, 200)
        water = np.ones((H, W), bool)
        water[low > 0] = False
        out = reflect_map.bake(H, W, water, np.zeros((H, W, 4), np.uint8), np.zeros((H, W), np.uint8),
                               low, ground, [])
        col = [tuple(out[y, 2, :3]) for y in range(H) if out[y, 2, 3] > 0]
        self.assertEqual(len(col), 3)
        self.assertGreater(col[0][2], 0, 'the bottom row (blue) comes first under it')
        self.assertGreater(col[2][0], 0, 'the top row (red) lies furthest down')
        first = min(y for y in range(H) if out[y, 2, 3] > 0)
        self.assertEqual(first, 7, 'lying in the water (stored 1 = height 0): right under its edge')


if __name__ == '__main__':
    unittest.main()
