"""The wood's mood map: smooth from the poppy meadow into the wood, dark inside, the south untouched, a shaft at the altar."""
import json
import os
import unittest

import numpy as np
from PIL import Image

D = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'world')


# rows + 600: the north grew 1200 world rows on top (0.11); columns + 450: the west 900 on the left (0.18); half size
class GradeField(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f = np.array(Image.open(os.path.join(D, 'grade_field.png')).convert('RGB')).astype(float) / 255.0

    def test_grade_field_is_smooth_at_the_old_border(self):
        row = self.f[410 + 600, 150 + 450:330 + 450, 0]                      # world y 820: the gate, x 300..660
        self.assertLess(np.abs(np.diff(row)).max(), 0.05)
        self.assertLess(row[0], 0.01)
        self.assertGreater(row[-1], 0.4)

    def test_the_wood_is_dark_the_meadow_and_the_south_are_not(self):
        self.assertGreater(self.f[500 + 600, 600 + 450, 0], 0.95)      # world (1200, 1000): deep wood
        self.assertLess(self.f[300 + 600, 100 + 450, 0], 0.01)         # the poppy meadow
        self.assertLess(self.f[1500 + 600, 200 + 450, 0], 0.01)        # the south's ground
        self.assertLess(self.f[1450 + 600, 600 + 450, 0], 0.05)        # the warm meadow tongue at the south-east

    def test_the_shaft_stands_over_the_altar(self):
        self.assertGreater(self.f[..., 2].max(), 0.6)
        y, x = np.unravel_index(self.f[..., 2].argmax(), self.f[..., 2].shape)
        self.assertGreater(x * 2, 1500)                    # at the ritual place, far east
        self.assertLess(y * 2, 1200 + 1200)

    def test_the_wood_has_cool_swarms(self):
        w = json.load(open(os.path.join(D, 'world.json')))
        cool = [s for s in w['fireflies'] if s.get('cool')]
        self.assertGreaterEqual(len(cool), 8)
        for s in cool:
            self.assertGreater(s['x'], 540)


if __name__ == '__main__':
    unittest.main()
