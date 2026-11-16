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

    def test_the_bookmark_hangs_out_of_the_pages(self):
        # approved 2026-11-16: a golden ribbon comes out of a slit in the page block and hangs below the book;
        # a dark outline only where it hangs over the ground (rows below the book)
        k = np.array(Image.open(os.path.join(D, 'buch_knopf.png')).convert('RGBA'))
        m = np.array(Image.open(os.path.join(D, 'buch_lesezeichen.png')).convert('RGBA'))
        self.assertEqual(m.shape[1], k.shape[1])
        self.assertGreater(m.shape[0], k.shape[0] + 3, 'hängt unten heraus')
        ys = np.where(m[..., 3] > 0)[0]
        self.assertGreaterEqual(ys.min(), 15, 'beginnt im Seitenblock, nicht auf dem Deckel')
        self.assertGreater(ys.max(), 21, 'reicht unter das Buch')
        dark = (m[..., 3] > 0) & (m[..., :3].sum(-1) < 120)
        self.assertGreater(int(dark.sum()), 0, 'Umriss vorhanden')
        self.assertTrue((np.where(dark)[0] >= 20).all(), 'Umriss nur unterhalb des Buchs')


if __name__ == '__main__':
    unittest.main()
