"""The generated world must be self-consistent: the game trusts these files blindly."""
import json
import os
import unittest

import numpy as np
from PIL import Image

from tools.tests.flood import reach

D = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'world')


def _cells(w, name):
    """Reassembles one per-cell layer from the chunks (the game never holds it whole)."""
    cw, ch = w['chunk']
    cols, rows = w['chunks']
    return np.concatenate([np.concatenate([
        np.fromfile(os.path.join(D, 'chunks', f'c_{cx}_{cy}_{name}.bin'), np.uint8).reshape(ch // 2, cw // 2)
        for cx in range(cols)], 1) for cy in range(rows)], 0)


def north(w):
    """How many rows the north added on top (0.11); tests written for the old frame add it."""
    return int(w.get('north_h', 0))


def west(w):
    """How many columns the west added on the left (0.18); tests written for the old frame add it."""
    return int(w.get('west_w', 0))


def pre_west(w):
    """world.json as it was before the west grew on the left: every x moved back, the west's own things gone."""
    k = west(w)
    w = dict(w)
    w['width'] -= k
    w['start'] = dict(w['start'], x=w['start']['x'] - k)
    w['sprites'] = [dict(s, x=s['x'] - k) for s in w['sprites'] if s['x'] >= k]
    w['lights'] = [dict(l, x=l['x'] - k) for l in w['lights'] if l['x'] >= k]
    return w


def pre_north(w):
    """world.json as it was before the north grew on top: every y moved back up."""
    n = north(w)
    w = dict(w)
    w['height'] -= n
    w['start'] = dict(w['start'], y=w['start']['y'] - n)
    w['sprites'] = [dict(s, y=s['y'] - n, foot=s['foot'] - n) for s in w['sprites'] if s['foot'] >= n]
    w['lights'] = [dict(l, y=l['y'] - n) for l in w['lights'] if l['y'] >= n]
    return w


class WorldAssets(unittest.TestCase):
    def setUp(self):
        self.w = json.load(open(os.path.join(D, 'world.json')))
        self.cells = _cells(self.w, 'cells')

    def test_the_whole_world_pictures_are_not_shipped(self):
        for f in ('ground.png', 'flowers.png', 'walk.bin', 'walk.png', 'walk_cells.bin', 'ground_mat.bin', 'water.png'):
            self.assertFalse(os.path.exists(os.path.join(D, f)), f)

    def test_sprites_lie_inside_the_world_and_match_their_files(self):
        for s in self.w['sprites']:
            self.assertGreaterEqual(s['x'], 0, s['name'])
            self.assertLessEqual(s['x'] + s['w'], self.w['width'], s['name'])
            with Image.open(os.path.join(D, 'sprites', s['name'] + '.png')) as img:
                cols = s.get('cols', s['frames'])                # long sheets in rows (0.18.2)
                self.assertEqual(img.size, (s['w'] * cols, s['h'] * -(-s['frames'] // cols)), s['name'])

    def test_start_is_walkable(self):
        st = self.w['start']
        self.assertEqual(self.cells[int(st['y']) // 2, int(st['x']) // 2], 1)

    def test_world_edges_are_closed(self):
        self.assertFalse(self.cells[:, :5].any())
        self.assertFalse(self.cells[:, -5:].any())
        self.assertFalse(self.cells[:15].any())
        self.assertFalse(self.cells[-5:].any())

    def test_lanterns_block_their_post_not_their_light(self):
        # gen_world blocked a lantern's whole box as a bar; one walks through the pool of light, round the post
        for s in self.w['sprites']:
            if 'laterne' not in s['name'] or s['w'] < 30:      # the stone ones with their wide pool of light
                continue
            cx, f = s['x'] + s['w'] // 2, s['foot']
            self.assertEqual(self.cells[f // 2, (cx - 12) // 2], 1, s['name'])
            self.assertEqual(self.cells[f // 2, (cx + 13) // 2], 1, s['name'])
            self.assertEqual(self.cells[(f - 1) // 2, cx // 2], 0, s['name'] + ' Pfosten')

    def test_water_moves_in_the_brooks_and_the_lake(self):
        kinds = set()
        cw, ch = self.w['chunk']
        cols, rows = self.w['chunks']
        for cy in range(rows):
            for cx in range(cols):
                with Image.open(os.path.join(D, 'chunks', f'c_{cx}_{cy}_water.png')) as wt:
                    kinds |= set(np.unique(np.array(wt)[..., 3]).tolist())
        self.assertTrue({1, 2, 3} <= kinds, 'alter Bach, neue Baeche, See')

    def test_the_world_is_fifteen_chunks_wide_and_twenty_four_tall(self):
        self.assertEqual((self.w['width'], self.w['height']), (2700, 4800))   # 0.11: the north on top, 0.18: the west
        self.assertEqual(self.w['chunks'], [15, 24])

    def _from_start(self):
        st = self.w['start']
        return reach(self.cells.astype(bool), [(int(st['y']) // 2, int(st['x']) // 2)], diagonal=True)

    def test_every_path_can_be_reached_from_the_start(self):
        # no dead ends: brooks may steer the way, never cut a path off (spec, anti-goal "labyrinth")
        mat = _cells(self.w, 'mat')
        paths = (mat == 1) & self.cells.astype(bool)
        got = self._from_start()
        self.assertGreater(got[paths].mean(), 0.99, 'Wegzellen vom Start erreichbar')

    def test_the_south_crossings_and_the_lake_rim_can_be_reached(self):
        mat = _cells(self.w, 'mat')
        got = self._from_start()
        south = np.zeros(mat.shape, bool)
        south[600 + north(self.w) // 2:] = True
        for kind, share, what in ((3, 0.97, 'Bruecken, Brett, Stege'), (2, 0.9, 'Trittsteine'),
                                  (5, 0.8, 'flacher Seerand und Pfuetzen')):
            sel = south & (mat == kind) & self.cells.astype(bool)
            self.assertTrue(sel.any(), what)
            self.assertGreater(got[sel].mean(), share, what)

    def test_ground_materials_cover_the_world_in_cells(self):
        mat = _cells(self.w, 'mat')
        self.assertEqual(mat.size, (self.w['height'] // 2) * (self.w['width'] // 2))
        self.assertTrue(set(np.unique(mat)) <= {0, 1, 2, 3, 4, 5})
        self.assertIn(5, mat, 'Trittsteine und Ufer sind nass')
        self.assertIn(3, mat, 'die Bruecke ist aus Holz')
        self.assertIn(4, mat, 'oben liegt Schnee')

    def test_birds_land_on_walkable_open_ground(self):
        self.assertGreaterEqual(len(self.w['birds']), 6)
        for b in self.w['birds']:
            self.assertEqual(self.cells[b['y'] // 2, b['x'] // 2], 1, b)

    def test_the_ford_over_the_stepping_stones_can_be_walked(self):
        # drawn as a crossing, but each stone was an island: water between them shut the ford
        n = north(self.w) // 2
        k = west(self.w) // 2
        part = self.cells[310 + n:370 + n, 45 + k:75 + k].astype(bool)     # old world y 620-740, x 90-150 round the stones
        got = reach(part, [(0, x) for x in range(part.shape[1])], diagonal=True)
        self.assertTrue(got[-1].any(), 'Nord- und Suedufer verbunden')

    def test_brook_and_wisps_lie_inside_the_world(self):
        self.assertGreaterEqual(len(self.w['brook']), 10)
        for p in self.w['brook'] + self.w['wisps']:
            self.assertTrue(0 <= p['x'] < self.w['width'] and 0 <= p['y'] < self.w['height'], p)


class ChunkAssets(unittest.TestCase):
    """The game streams these; every chunk needs all four files at the right size."""
    def test_every_chunk_is_complete(self):
        w = json.load(open(os.path.join(D, 'world.json')))
        cw, ch = w['chunk']
        cols, rows = w['chunks']
        self.assertEqual((cols * cw, rows * ch), (w['width'], w['height']))
        for cy in range(rows):
            for cx in range(cols):
                base = os.path.join(D, 'chunks', f'c_{cx}_{cy}_')
                with Image.open(base + 'ground.png') as g:
                    self.assertEqual(g.size, (cw, ch))
                with Image.open(base + 'water.png') as wt:
                    self.assertEqual(wt.size, (cw, ch))
                with Image.open(base + 'flowers.png') as f:
                    self.assertEqual(f.size, (cw + 2 * w['apron'], ch + 2 * w['apron']))
                for kind in ('cells', 'mat'):
                    self.assertEqual(os.path.getsize(base + kind + '.bin'), (cw // 2) * (ch // 2), base + kind)


if __name__ == '__main__':
    unittest.main()
