"""The split into ground / sway / sprites must not change the approved picture and must put it back
together. Local only (scipy, minutes of rendering):

    cd tools/world/south && nice python3 -m unittest test_layers
"""
import hashlib
import json
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import layers  # noqa: E402
import objects_lake as ol  # noqa: E402
import zone1_draft as z1  # noqa: E402
import zone4_draft as z4  # noqa: E402

RAW_MD5 = '895531ecd162f1e4a4ceb9c18b71751f'   # zone4_draft.render(raw=True)[0] before the split existed


def recompose(c):
    out = c.ground.copy()
    m = c.sway[..., 3] > 0
    out[m] = c.sway[m][:, :3]
    for s in sorted(c.sprites, key=lambda s: s['foot']):
        a = s['rgba'][:, :s['w']]                              # first frame of a strip
        h, w = a.shape[:2]
        reg = out[s['y']:s['y'] + h, s['x']:s['x'] + w]
        k = a[..., 3] > 0
        reg[k] = a[k][:, :3]
    return out


class TestLayers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with layers.collect() as c:
            cls.c = c

    def test_paint_without_collector_is_unchanged(self):
        w = json.load(open(os.path.join(z1.ROOT, 'build', 'world_old', 'world_old.json')))
        r = z4.render(w, raw=True)[0]
        self.assertEqual(hashlib.md5(np.ascontiguousarray(r).tobytes()).hexdigest(), RAW_MD5)

    def test_collecting_does_not_change_the_picture(self):
        self.assertEqual(hashlib.md5(np.ascontiguousarray(self.c.raw).tobytes()).hexdigest(), RAW_MD5)

    def test_layers_recompose_the_draft(self):
        same = (np.abs(recompose(self.c) - self.c.raw).sum(-1) < 1.5).mean()
        self.assertGreater(same, 0.97, same)

    def test_ground_is_the_draft_where_nothing_stands_or_sways(self):
        free = self.c.sway[..., 3] == 0
        for s in self.c.sprites:
            a = s['rgba'][:, :s['w']]
            h, w = a.shape[:2]
            free[s['y']:s['y'] + h, s['x']:s['x'] + w] &= a[..., 3] == 0
        for (y, x) in self.c.shadow_px:
            free[y, x] = False
        diff = np.abs(self.c.ground - self.c.raw).sum(-1)[free]
        self.assertGreater((diff < 1.5).mean(), 0.995)

    def test_shadows_land_in_ground(self):
        trees = [s for s in self.c.sprites if isinstance(s['thing'], ol.Laubbaum)]
        self.assertTrue(trees)
        self.assertTrue(self.c.shadow_px)
        t = trees[0]
        ys = [y for (y, x) in self.c.shadow_px if t['x'] <= x < t['x'] + t['rgba'].shape[1]
              and t['y'] <= y < t['y'] + t['rgba'].shape[0]]
        self.assertTrue(ys, 'the tree casts no shadow into the ground')

    def test_lanterns_become_64_frame_strips(self):
        lan = [s for s in self.c.sprites if s['frames'] > 1]
        self.assertGreaterEqual(len(lan), 3)
        for s in lan:
            self.assertEqual(s['rgba'].shape[1], 64 * s['w'])
            f = [s['rgba'][:, k * s['w']:(k + 1) * s['w']] for k in (0, 5, 17)]
            self.assertFalse(all((f[0] == g).all() for g in f[1:]), 'the flame does not move')

    def test_every_standing_thing_has_a_sprite(self):
        self.assertGreater(len(self.c.sprites), 100)
        for s in self.c.sprites:
            self.assertTrue((s['rgba'][..., 3] > 0).any(), type(s['thing']).__name__)


if __name__ == '__main__':
    unittest.main()
