"""The north as the game gets it (gen_north): its ways are free to walk, and its darkness has no little islands
that make the wanderer put his lantern away and take it out again a few steps on (Philip 2026-11-04)."""
import json
import os
import unittest

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

from tools.tests.test_world_assets import D, _cells, north

DARK_ON, DARK_OFF = 0.55, 0.35             # scenes/lantern.gd
ISLAND = 2500                              # half-size px, gen_north.ISLAND: a clearing is larger


class NorthWorld(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = json.load(open(os.path.join(D, 'world.json')))
        cls.n = north(cls.w)
        cls.cells = _cells(cls.w, 'cells').astype(bool)
        cls.mat = _cells(cls.w, 'mat')
        cls.grade = np.array(Image.open(os.path.join(D, 'grade_field.png')).convert('RGB'))[..., 0] / 255.0

    def test_the_north_is_there(self):
        self.assertEqual(self.n, 1200)

    def test_nothing_stands_on_the_north_s_ways(self):
        rows = self.n // 2
        ways = self.mat[:rows] == 1                       # EARTH: the trodden paths
        self.assertGreater(ways.sum(), 2000)
        free = self.cells[:rows][ways].mean()
        self.assertGreater(free, 0.995, f'nur {free:.1%} der Wegzellen frei')

    def test_no_little_islands_in_the_north_s_darkness(self):
        f = self.grade[:self.n // 2]
        for name, m in (('helle Inseln im Wald', f <= DARK_OFF), ('dunkle Flecken im Freien', f >= DARK_ON)):
            lab, k = ndi.label(m)
            size = np.bincount(lab.ravel())
            edge = set(np.unique(np.r_[lab[0], lab[-1], lab[:, 0], lab[:, -1]]).tolist())
            small = [i for i in range(1, k + 1) if size[i] < ISLAND and i not in edge]
            self.assertEqual(small, [], name)

    def test_the_mist_wall_stands_at_the_world_s_edges_only(self):
        # 0.11.0: today's top row's wall was carried up the whole north: a grey wall through the hut's wood
        b = np.array(Image.open(os.path.join(D, 'mist_fields.png')).convert('RGB'))[..., 2]
        inner = b[40:self.n // 2 + 200, 40:1310]               # half size: under the top, off the west (its wall ~24 px in) and east edge (~45 px)
        self.assertEqual(int(inner.max()), 0)
        self.assertGreater(int(b[0, 900]), 200, 'oben am Weltrand steht die Nebelwand')


if __name__ == '__main__':
    unittest.main()
