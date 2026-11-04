"""The Ostwald as generated world data: every path walkable and reachable, the bridge crossable, trees block
only their trunk, the old west and the south left alone, the water moving."""
import json
import os
import unittest

import numpy as np
from PIL import Image

from tools.tests.flood import reach
from tools.tests.test_world_assets import D, _cells
from tools.world.east import layout as L

TOP = 1040                                      # zone 1's top row: the south below it keeps its ground


class EastWorld(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = json.load(open(os.path.join(D, 'world.json')))
        cls.cells = _cells(cls.w, 'cells').astype(bool)
        cls.mat = _cells(cls.w, 'mat')
        st = cls.w['start']
        cls.got = reach(cls.cells, [(int(st['y']) // 2, int(st['x']) // 2)], diagonal=True)

    def _cell(self, x, y):
        return int(y) // 2, int(x) // 2

    def test_every_path_pixel_is_walkable_and_reachable(self):
        for name, p in L.paths().items():
            pond = L.SPOTS['4']
            pts = p[::2][np.hypot(p[::2, 0] - pond.x, p[::2, 1] - pond.y) > 70]       # the pond's middle is water
            cs = [self._cell(x, y) for x, y in pts]
            walk = np.mean([self.cells[c] for c in cs])
            seen = np.mean([self.got[c] for c in cs])
            self.assertGreater(walk, 0.97, f'{name} walkable')
            self.assertGreater(seen, 0.97, f'{name} reachable from the start')

    def test_every_spot_and_the_ritual_place_can_be_reached(self):
        for key, s in L.SPOTS.items():
            if key == '4' or s.kind == 'small':                  # the pond: its shore, not its middle; the small clearings lie off every way
                continue
            y, x = self._cell(s.x, s.y)
            self.assertTrue(self.got[y - 5:y + 6, x - 5:x + 6].any(), f'spot {key}')

    def test_the_way_crosses_the_bridge_without_a_gap(self):
        s = L.SPOTS['6']
        for name in ('bruecke_w', 'bruecke_o'):
            p = L.paths()[name]
            near = p[np.hypot(p[:, 0] - s.x, p[:, 1] - s.y) < 40]
            self.assertGreater(len(near), 10, name)
            for x, y in near[::2]:
                self.assertTrue(self.got[self._cell(x, y)], f'{name} {x:.0f},{y:.0f}')

    def test_the_river_cannot_be_walked_away_from_the_bridge(self):
        s = L.SPOTS['6']
        r = L.river()
        far = r[np.hypot(r[:, 0] - s.x, r[:, 1] - s.y) > 60][::6]
        bad = [self._cell(x, y) for x, y in far if self.cells[self._cell(x, y)]]
        self.assertLess(len(bad) / max(len(far), 1), 0.05)

    def test_no_sprite_bottom_pixel_blocks(self):
        # a tree hangs over the way: only its trunk's foot is solid, never the crown above
        pm = L.masks().path
        checked = bad = 0
        for s in self.w['sprites']:
            if not s['name'].startswith('e') or s['h'] < 44:
                continue
            y0, y1 = s['y'], s['foot'] - 18
            for y in range(max(y0, L.Y0), min(y1, L.Y1), 3):
                for x in range(max(s['x'], L.X0), min(s['x'] + s['w'], L.X1), 3):
                    if pm[y - L.Y0, x - L.X0]:
                        checked += 1
                        bad += not self.cells[self._cell(x, y)]
        self.assertGreater(checked, 200)
        self.assertLess(bad / checked, 0.03)

    def test_the_wood_opens_only_along_its_paths_and_clearings(self):
        lm = L.masks()
        ok = np.zeros((self.cells.shape[0] * 2, self.cells.shape[1] * 2), bool)
        try:
            from scipy import ndimage as ndi
        except ImportError:
            self.skipTest('scipy fehlt (CI)')
        ok[L.Y0:L.Y1, L.X0:L.X1] = ndi.binary_dilation(lm.path | lm.clearing, iterations=6)
        east = np.zeros_like(self.cells)
        east[:, 450:] = self.cells[:, 450:]                      # x >= 900
        ys, xs = np.nonzero(east)
        self.assertGreater(len(ys), 20000, 'the wood is open')
        meadow = (ys * 2 >= 2260) & (xs * 2 < 1520)              # the fringe's open meadow tongue
        stray = ~ok[ys * 2, xs * 2] & ~meadow
        self.assertLess(stray.mean(), 0.02)

    def test_the_wood_is_closed_outside_its_frame(self):
        self.assertFalse(self.cells[:150, 450:].any())           # y < 300
        self.assertFalse(self.cells[1560:, 450:].any())          # y >= 3120: below the wood

    def test_ground_materials_mark_paths_and_the_deck(self):
        east = self.mat[150:1550, 270:]
        self.assertIn(1, east)                                   # earth on the paths
        self.assertIn(3, east)                                   # the pond's jetty is wood

    def test_water_moves_in_the_river_and_the_pond(self):
        kinds = set()
        for cy in range(2, 17):
            for cx in range(5, 10):
                with Image.open(os.path.join(D, 'chunks', f'c_{cx}_{cy}_water.png')) as wt:
                    kinds |= set(np.unique(np.array(wt)[..., 3]).tolist())
        self.assertTrue({2, 3} <= kinds)

    def test_lights_of_the_wood_lie_in_the_wood(self):
        east = [l for l in self.w['lights'] if l['x'] > 900]
        self.assertGreaterEqual(len(east), 6)
        for l in east:
            self.assertTrue(L.X0 <= l["x"] < 1800 and L.Y0 <= l["y"] <= L.Y1, l)


if __name__ == '__main__':
    unittest.main()


class EastWorldLocal(unittest.TestCase):
    """2026-11-04: the pond's meadow fell into three parts (no crossing over its river and brook); every path was
    still reachable the long way round, so the global test above did not see it."""
    @classmethod
    def setUpClass(cls):
        cls.w = json.load(open(os.path.join(D, 'world.json')))
        cls.cells = _cells(cls.w, 'cells').astype(bool)

    def test_the_paths_meeting_at_a_spot_join_near_it(self):
        for key, s in L.SPOTS.items():
            ends = [pts[1] if a == key else pts[-2] for a, b, pts in L._EDGES.values() if key in (a, b)]
            if len(ends) < 2:
                continue
            R = s.r + 50
            y0, x0 = max(0, int(s.y - R) // 2), max(0, int(s.x - R) // 2)
            sub = self.cells[y0:int(s.y + R) // 2, x0:int(s.x + R) // 2]
            starts = []
            for p in ends:
                q = np.array(p, float) + (L.OX, L.OY)
                v = q - (s.x, s.y)
                q = np.array((s.x, s.y)) + v / np.hypot(*v) * min(np.hypot(*v), s.r + 20)
                ys, xs = np.nonzero(sub)
                k = np.argmin((xs - (q[0] // 2 - x0)) ** 2 + (ys - (q[1] // 2 - y0)) ** 2)
                starts.append((ys[k], xs[k]))
            got = reach(sub, starts[:1], diagonal=False)
            for st in starts[1:]:
                self.assertTrue(got[st], f'spot {key} ({s.kind}): its paths do not meet near it')

    def test_no_poppy_heads_deep_in_the_wood(self):
        x0, x1, y0, y1 = 800, 900, 1100, 2200          # wood share above 0.4 here (gen_east.POPPY_GONE)
        red = 0
        for cy in range(y0 // 200, y1 // 200):
            for cx in range(x0 // 180, (x1 - 1) // 180 + 1):
                f = np.array(Image.open(os.path.join(D, 'chunks', f'c_{cx}_{cy}_flowers.png')).convert('RGBA'))[8:208, 8:188].astype(int)
                gx = np.arange(cx * 180, cx * 180 + 180)[None, :]
                inside = (gx >= x0) & (gx < x1)
                head = (f[..., 3] > 0) & (f[..., 0] > 70) & (f[..., 0] - f[..., 1] > 30) & (f[..., 0] - f[..., 2] > 20)
                red += int((head & inside).sum())
        self.assertEqual(red, 0)
