"""The eastern wood's skeleton: every place reachable, the ritual place far back and not by one road only."""
import unittest

import numpy as np

from tools.tests.flood import reach
from tools.world.east import layout as L


def _poly_len(p):
    return float(np.linalg.norm(np.diff(p, axis=0), axis=1).sum())


def _turns(p, deg=15):
    d = np.diff(p[::20], axis=0)
    a = np.degrees(np.arctan2(d[:, 1], d[:, 0]))
    t = np.abs((np.diff(a) + 180) % 360 - 180)
    return int((t > deg).sum())


class EastLayout(unittest.TestCase):
    def test_every_spot_is_reachable_from_the_gate(self):
        for s in ('3', '4', '5', '6', '7', '9'):
            self.assertTrue(L.route_exists('1', s), s)
        self.assertTrue(L.route_exists('H', '5'), 'the hut path leads on to the ritual place')

    def test_the_ritual_place_has_two_disjoint_routes_and_lies_farthest_back(self):
        self.assertGreaterEqual(L.disjoint_routes('J1', '5'), 2)
        far = {k: L.SPOTS[k].x for k in ('3', '4', '6', '7')}
        self.assertTrue(all(L.SPOTS['5'].x > x for x in far.values()), 'the ritual place is the easternmost')

    def test_paths_wind(self):
        for name, p in L.paths().items():
            chord = float(np.linalg.norm(p[-1] - p[0]))
            if chord < 150:                      # the gate and the junction links are short on purpose
                continue
            self.assertGreaterEqual(_poly_len(p), 1.05 * chord, name)
            self.assertGreaterEqual(_turns(p), 2, name)

    def test_clearings_are_not_circles(self):
        for k, s in L.SPOTS.items():
            pts = np.array(L.blob(s))
            area = 0.5 * abs(np.dot(pts[:, 0], np.roll(pts[:, 1], 1)) - np.dot(pts[:, 1], np.roll(pts[:, 0], 1)))
            per = _poly_len(np.vstack([pts, pts[:1]]))
            self.assertGreaterEqual(per * per / (4 * np.pi * area), 1.03, k)

    def test_the_masks_connect_the_whole_wood_from_the_gate(self):
        m = L.masks()
        gate = L.SPOTS['1']
        seed = (int(gate.y - L.Y0), int(gate.x - L.X0))
        bridge = L.SPOTS['6']
        deck = np.zeros_like(m.river)
        yy, xx = np.mgrid[0:m.river.shape[0], 0:m.river.shape[1]]
        deck[np.hypot(xx + L.X0 - bridge.x, yy + L.Y0 - bridge.y) < bridge.r] = True
        walk = m.walk & ~(m.river & ~deck)
        seen = reach(walk, [seed], diagonal=True)
        pond = L.SPOTS['4']                      # the pond itself is water: its rim is what must be reachable
        self.assertTrue(seen[int(pond.y - L.Y0), int(pond.x - L.X0 + pond.r * 0.8)] or seen[int(pond.y - L.Y0 + pond.r * 0.8), int(pond.x - L.X0)], 'pond rim')
        for k in ('3', '5', '6', '7', '9'):
            s = L.SPOTS[k]
            self.assertTrue(seen[int(s.y - L.Y0), int(s.x - L.X0)], k)

    def test_the_river_is_crossed_only_at_the_bridge(self):
        m = L.masks()
        bridge = L.SPOTS['6']
        yy, xx = np.mgrid[0:m.river.shape[0], 0:m.river.shape[1]]
        pond = L.SPOTS['4']
        away = (np.hypot(xx + L.X0 - bridge.x, yy + L.Y0 - bridge.y) >= bridge.r + 12) \
            & (np.hypot(xx + L.X0 - pond.x, yy + L.Y0 - pond.y) >= pond.r * 1.7)    # the river ends in the pond (its outline reaches 1.6 r)
        self.assertFalse((m.river & m.path & away).any(), 'no path crosses the river except at the bridge')
        self.assertFalse((m.river & m.clearing & away).any(), 'no clearing lies in the river')

    def test_the_branch_leaves_the_south_path_and_the_bach_meets_brook_b(self):
        import os
        from PIL import Image
        d = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'world', 'chunks')
        hx, hy = L.HUT
        mat = np.fromfile(os.path.join(d, f'c_{hx // 180}_{hy // 200}_mat.bin'), np.uint8).reshape(100, 90)
        near = mat[(hy % 200) // 2 - 2:(hy % 200) // 2 + 3, (hx % 180) // 2 - 3:(hx % 180) // 2 + 4]
        self.assertTrue((near == 1).any(), 'the branch starts on the south path (EARTH ground)')
        bx, by = (int(v) for v in L.bach()[-1])
        w = np.array(Image.open(os.path.join(d, f'c_{bx // 180}_{by // 200}_water.png')).convert('RGBA'))
        win = w[max(0, by % 200 - 12):by % 200 + 13, max(0, bx % 180 - 12):bx % 180 + 13, 3]
        self.assertTrue((win == 2).any(), 'the bach ends at brook B (water kind 2) of the south')


if __name__ == '__main__':
    unittest.main()
