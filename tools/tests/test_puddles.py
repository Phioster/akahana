"""The wet ground after the rain (tools/world/gen_wet.py): puddles where they belong, never where they must not be."""
import json
import os
import unittest

import numpy as np
from PIL import Image

D = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'world')


def hold(v):
    v = v.astype(int)
    return np.where(v == 0, 0.0, np.where(v < 128, (v - 1) / 126.0, (v - 128) / 127.0))


class Puddles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = json.load(open(os.path.join(D, 'world.json')))
        cls.v = np.array(Image.open(os.path.join(D, 'puddles.png')))
        cls.h = hold(cls.v)

    def test_covers_the_world(self):
        self.assertEqual(self.v.shape, (self.w['height'], self.w['width']))

    def test_the_north_stays_dry(self):
        self.assertEqual(int(self.v[:1230].max()), 0, 'wo Schnee fällt, regnet es nicht')

    def test_never_on_open_water(self):
        ow = np.array(Image.open(os.path.join(D, 'open_water.png'))) > 0
        self.assertEqual(int((self.h[ow] > 0).sum()), 0)

    def test_the_fire_pit_stays_dry_with_a_puddle_below(self):
        f = self.w['fire']
        x, y = int(f['x']), int(f['y'])
        yy, xx = np.mgrid[y - 12:y + 12, x - 18:x + 19]
        ring = ((xx - x) / 15.0) ** 2 + ((yy - y) / 9.0) ** 2 < 1.0          # the pit and its stones
        self.assertEqual(float(self.h[yy[ring], xx[ring]].max()), 0.0, 'nicht auf den Steinen (Philip)')
        self.assertGreater(int((self.h[y + 14:y + 36, x - 12:x + 16] > 0).sum()), 40, 'die Mulde darunter')

    def test_puddles_are_few_and_on_paths_most(self):
        wet = self.v > 0
        pud = self.h > 0
        self.assertLess(pud.sum() / wet.sum(), 0.08)
        path = self.v >= 128
        self.assertGreater((pud & path).sum() / max(1, path.sum()), (pud & ~path).sum() / max(1, (wet & ~path).sum()))

    def test_the_pale_patches_of_the_south_get_wet_too(self):
        # material 4 (SNOW) lies pale in the meadow too; left dry it stood out white after the rain (0.17.5)
        H, W = self.w['height'], self.w['width']
        full = os.path.join(D, '..', '..', 'build', 'world_full', 'ground_mat.bin')
        if not os.path.exists(full):
            self.skipTest('build/world_full fehlt')
        m = np.kron(np.fromfile(full, np.uint8).reshape(H // 2, W // 2), np.ones((2, 2), np.uint8))[:H, :W]
        south = np.zeros((H, W), bool)
        south[1400:] = True
        snow = (m == 4) & south
        self.assertGreater(float((self.v[snow] > 0).mean()), 0.9)


if __name__ == '__main__':
    unittest.main()
