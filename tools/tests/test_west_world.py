"""The west as the game gets it (gen_west, 0.18): its places and the greenhouse door can be reached from the start,
nothing stands out over the world's edge, its darkness has no little islands, the greenhouse's inside is whole."""
import json
import os
import unittest

import numpy as np

from tools.tests.flood import reach
from tools.tests.test_world_assets import D, _cells, west

PLACES = {'Dorfplatz': (536, 2344), 'Gewächshaus': (680, 2630), 'Mühle': (560, 3340), 'Westsee': (596, 4050),
          'Teehaus': (850, 4030), 'Einsiedelei': (362, 400)}          # core/test_travel.gd


class WestWorld(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = json.load(open(os.path.join(D, 'world.json')))
        cls.cells = _cells(cls.w, 'cells').astype(bool)
        st = cls.w['start']
        cls.got = reach(cls.cells, [(int(st['y']) // 2, int(st['x']) // 2)], diagonal=True)

    def test_the_west_is_there(self):
        self.assertEqual(west(self.w), 900)

    def test_every_west_place_can_be_reached(self):
        for name, (x, y) in PLACES.items():
            self.assertTrue(self.got[y // 2 - 15:y // 2 + 16, x // 2 - 15:x // 2 + 16].any(), name)

    def test_the_greenhouse_door_can_be_walked_into(self):
        m = json.load(open(os.path.join(D, 'glashaus', 'glashaus.json')))
        x, y, mw, mh = m['mouth']
        self.assertTrue(self.got[y // 2:(y + mh) // 2 + 1, x // 2:(x + mw) // 2 + 1].any(), 'bis in die Tür')
        ox, oy = m['out']
        self.assertTrue(self.cells[oy // 2, ox // 2], 'beim Hinausgehen steht er frei')

    def test_the_greenhouse_inside_is_one_piece_from_the_door(self):
        m = json.load(open(os.path.join(D, 'glashaus', 'glashaus.json')))
        W, H = m['size']
        walk = np.fromfile(os.path.join(D, 'glashaus', 'glashaus_walk.bin'), np.uint8).reshape(H, W).astype(bool)
        sx, sy = m['in']
        got = reach(walk, [(sy, sx)])
        self.assertTrue(got[m['in_to'][1], m['in_to'][0]])
        self.assertGreater(got.sum() / walk.sum(), 0.98, 'kein abgeschnittener Fleck')
        self.assertTrue(got[m['exit_y']:].any(), 'der Weg hinaus ist frei')

    def test_nothing_stands_out_over_the_edges(self):
        for s in self.w['sprites']:
            self.assertGreaterEqual(s['x'], 0, s['name'])

    def test_the_west_rim_is_closed(self):
        self.assertFalse(self.cells[:, :7].any())


if __name__ == '__main__':
    unittest.main()


class ExportFilter(unittest.TestCase):
    """0.18.0 on the phone: the greenhouse's json and walk grid were not exported (only .png get imported), so its
    door did nothing. Every raw data file the game reads with FileAccess must match the include filter."""
    def test_raw_world_data_is_exported(self):
        import fnmatch
        import glob
        root = os.path.join(os.path.dirname(__file__), '..', '..')
        line = [l for l in open(os.path.join(root, 'export_presets.cfg')) if l.startswith('include_filter=')][0]
        pats = [p.strip() for p in line.split('=', 1)[1].strip().strip('"').split(',')]
        for f in glob.glob(os.path.join(D, '**', '*.json'), recursive=True) + glob.glob(os.path.join(D, '*', '*.bin')):
            rel = os.path.relpath(f, root)
            self.assertTrue(any(fnmatch.fnmatch(rel, p) for p in pats), rel)


class SheetsAndEdges(unittest.TestCase):
    """Fable's review, 2026-11-08: what the game cannot draw or shows wrong, as tests."""
    @classmethod
    def setUpClass(cls):
        with open(os.path.join(D, 'world.json')) as f:
            cls.w = json.load(f)

    def test_every_sheet_fits_a_texture_and_matches_its_frames(self):
        from PIL import Image
        for s in self.w['sprites']:
            cols = s.get('cols', s['frames'])
            rows = -(-s['frames'] // cols)
            with Image.open(os.path.join(D, 'sprites', s['name'] + '.png')) as img:
                self.assertEqual(img.size, (s['w'] * cols, s['h'] * rows), s['name'])
                self.assertLessEqual(img.size[0], 8192, s['name'])
                self.assertLessEqual(img.size[1], 8192, s['name'])

    def test_every_foot_lies_on_its_picture(self):
        for s in self.w['sprites']:
            self.assertTrue(s['y'] <= s['foot'] <= s['y'] + s['h'], s)

    def test_the_mist_wall_closes_the_top_and_the_bottom_everywhere(self):
        from PIL import Image
        b = np.array(Image.open(os.path.join(D, 'mist_fields.png')).convert('RGB'))[..., 2].astype(int)
        self.assertGreaterEqual(int(b[0].min()), 200, 'oben')
        self.assertGreaterEqual(int(b[-1].min()), 200, 'unten')
        self.assertLessEqual(int(np.abs(np.diff(b[-1])).max()), 20, 'keine Stufe unten')

    def test_no_one_walks_on_moving_water_but_on_wet_ground_wood_or_stone(self):
        cells = _cells(self.w, 'cells').astype(bool)
        mat = _cells(self.w, 'mat')
        cw, ch = self.w['chunk']
        cols, rows = self.w['chunks']
        from PIL import Image
        kind = np.concatenate([np.concatenate([np.array(Image.open(os.path.join(D, 'chunks', f'c_{cx}_{cy}_water.png')))[..., 3]
                                               for cx in range(cols)], 1) for cy in range(rows)], 0)
        k = kind.reshape(kind.shape[0] // 2, 2, kind.shape[1] // 2, 2)
        moving = ((k == 1) | (k == 2)).all(axis=(1, 3))
        self.assertEqual(int((moving & cells & (mat == 0)).sum()), 0)
