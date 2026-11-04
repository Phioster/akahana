"""Splitting the big generator images into chunks must lose nothing and leave no seams."""
import json
import os
import tempfile
import unittest

import numpy as np
from PIL import Image

from tools.world.split_chunks import keep_main, split


class Chunks(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(1)
        self.src = tempfile.mkdtemp()
        self.out = tempfile.mkdtemp()
        self.W, self.H = 360, 400
        self.ground = rng.integers(0, 255, (self.H, self.W, 3), np.uint8)
        self.flowers = rng.integers(0, 255, (self.H, self.W, 4), np.uint8)
        self.cells = rng.integers(0, 2, (self.H // 2, self.W // 2), np.uint8)
        self.mat = rng.integers(0, 6, (self.H // 2, self.W // 2), np.uint8)
        Image.fromarray(self.ground).save(os.path.join(self.src, 'ground.png'))
        Image.fromarray(self.flowers).save(os.path.join(self.src, 'flowers.png'))
        self.cells.tofile(os.path.join(self.src, 'walk_cells.bin'))
        self.mat.tofile(os.path.join(self.src, 'ground_mat.bin'))
        self.index = split(self.src, self.out, (180, 200), 8)

    def _png(self, cx, cy, kind):
        return np.array(Image.open(os.path.join(self.out, f'c_{cx}_{cy}_{kind}.png')))

    def _bin(self, cx, cy, kind):
        return np.fromfile(os.path.join(self.out, f'c_{cx}_{cy}_{kind}.bin'), np.uint8).reshape(100, 90)

    def test_index_counts_the_chunks(self):
        self.assertEqual(self.index['chunks'], [2, 2])
        self.assertEqual(self.index['chunk'], [180, 200])
        self.assertEqual(self.index['apron'], 8)

    def test_reassembled_chunks_equal_the_original(self):
        g = np.concatenate([np.concatenate([self._png(cx, cy, 'ground') for cx in range(2)], 1) for cy in range(2)], 0)
        self.assertTrue((g == self.ground).all())
        for kind, ref in (('cells', keep_main(self.cells)), ('mat', self.mat)):
            b = np.concatenate([np.concatenate([self._bin(cx, cy, kind) for cx in range(2)], 1) for cy in range(2)], 0)
            self.assertTrue((b == ref).all(), kind)

    def test_flower_apron_holds_the_neighbours_pixels(self):
        f00 = self._png(0, 0, 'flowers')
        self.assertEqual(f00.shape, (216, 196, 4))
        self.assertTrue((f00[8:208, 188:196] == self.flowers[0:200, 180:188]).all())   # right apron = neighbour
        self.assertTrue((f00[8:208, 8:188] == self.flowers[0:200, 0:180]).all())       # inner part unchanged
        self.assertTrue((f00[0:8, :, 3] == 0).all())                                    # outside the world: empty
        self.assertTrue((f00[8:208, 0:8, 3] == 0).all())

    def test_wall_and_path_lists_name_exactly_those_cells(self):
        # the game sets only these cells per tap; the rest comes from two native fills
        for cy in range(2):
            for cx in range(2):
                cells, mat = self._bin(cx, cy, 'cells').ravel(), self._bin(cx, cy, 'mat').ravel()
                walls = np.fromfile(os.path.join(self.out, f'c_{cx}_{cy}_walls.bin'), '<i4')
                paths = np.fromfile(os.path.join(self.out, f'c_{cx}_{cy}_paths.bin'), '<i4')
                self.assertTrue((walls == np.flatnonzero(cells == 0)).all())
                self.assertTrue((paths == np.flatnonzero((cells != 0) & (mat != 0) & (mat != 4))).all())


class KeepMain(unittest.TestCase):
    def test_keep_main_closes_lone_cells(self):
        c = np.ones((10, 10), np.uint8)
        c[4:7, 4:7] = 0
        c[5, 5] = 1                                   # walled in on all four sides
        k = keep_main(c)
        assert k[5, 5] == 0 and k[0, 0] == 1 and int(k.sum()) == 91
