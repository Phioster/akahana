"""The journal pictures are drawn over the world: a see-through gap shows the game through the book."""
import os
import unittest

import numpy as np
from PIL import Image

from tools.tests.flood import holes

D = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'ui')


class UiAssets(unittest.TestCase):
    def test_the_book_button_has_no_see_through_holes(self):
        a = np.array(Image.open(os.path.join(D, 'buch_knopf.png')).convert('RGBA'))
        solid = a[..., 3] > 0
        gaps = holes(solid)
        self.assertEqual(int(gaps.sum()), 0, np.argwhere(gaps).tolist())
        self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255}, 'keine Halbtransparenz')


if __name__ == '__main__':
    unittest.main()
