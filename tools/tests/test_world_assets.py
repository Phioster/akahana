"""The generated world must be self-consistent: the game trusts these files blindly."""
import json
import os
import unittest

import numpy as np
from PIL import Image

D = os.path.join(os.path.dirname(__file__), '..', '..', 'assets', 'world')


def _cells(w, name):
    """Reassembles one per-cell layer from the chunks (the game never holds it whole)."""
    cw, ch = w['chunk']
    cols, rows = w['chunks']
    return np.concatenate([np.concatenate([
        np.fromfile(os.path.join(D, 'chunks', f'c_{cx}_{cy}_{name}.bin'), np.uint8).reshape(ch // 2, cw // 2)
        for cx in range(cols)], 1) for cy in range(rows)], 0)


class WorldAssets(unittest.TestCase):
    def setUp(self):
        self.w = json.load(open(os.path.join(D, 'world.json')))
        self.cells = _cells(self.w, 'cells')

    def test_the_whole_world_pictures_are_not_shipped(self):
        for f in ('ground.png', 'flowers.png', 'walk.bin', 'walk.png', 'walk_cells.bin', 'ground_mat.bin'):
            self.assertFalse(os.path.exists(os.path.join(D, f)), f)

    def test_sprites_lie_inside_the_world_and_match_their_files(self):
        for s in self.w['sprites']:
            self.assertGreaterEqual(s['x'], 0, s['name'])
            self.assertLessEqual(s['x'] + s['w'], self.w['width'], s['name'])
            with Image.open(os.path.join(D, 'sprites', s['name'] + '.png')) as img:
                self.assertEqual(img.size, (s['w'] * s['frames'], s['h']), s['name'])

    def test_start_is_walkable(self):
        st = self.w['start']
        self.assertEqual(self.cells[int(st['y']) // 2, int(st['x']) // 2], 1)

    def test_world_edges_are_closed(self):
        self.assertFalse(self.cells[:, :5].any())
        self.assertFalse(self.cells[:, -5:].any())
        self.assertFalse(self.cells[:15].any())

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
                with Image.open(base + 'flowers.png') as f:
                    self.assertEqual(f.size, (cw + 2 * w['apron'], ch + 2 * w['apron']))
                for kind in ('cells', 'mat'):
                    self.assertEqual(os.path.getsize(base + kind + '.bin'), (cw // 2) * (ch // 2), base + kind)


if __name__ == '__main__':
    unittest.main()
