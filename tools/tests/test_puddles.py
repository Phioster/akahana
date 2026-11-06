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


if __name__ == '__main__':
    unittest.main()
