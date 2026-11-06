#!/usr/bin/env python3
"""The journal page's sheet, for the page turn (shaders/page_turn.gdshader, approved 2026-11-06 from
build/preview/buch/turn.py). Out: assets/ui/buch_blatt.png, R = paper (the deckled edge's holes filled: the
sheet is one piece), G = the sheet including where it runs on under the stitched band (the turned page covers
the band), A = the page picture's own alpha."""
import os

import numpy as np
from PIL import Image
from scipy import ndimage as nd

UI = os.path.join(os.path.dirname(__file__), '..', 'assets', 'ui')
HINGE, PAPER_TOP = 3, 15

page = np.array(Image.open(os.path.join(UI, 'buch_seite.png')).convert('RGBA')).astype(int)
H, W = page.shape[:2]
paper = (page[..., 0] > 150) & (page[..., 1] > 120) & (page[..., 3] > 0)
paper = nd.binary_fill_holes(nd.binary_closing(paper, iterations=2)) & (page[..., 3] > 0)
sheet = paper.copy()
cols = paper.any(0) & (np.arange(W) > 8) & (np.arange(W) < 146)
sheet[HINGE:PAPER_TOP + 1, :] |= cols[None, :]
out = np.zeros((H, W, 4), np.uint8)
out[..., 0] = paper * 255
out[..., 1] = sheet * 255
out[..., 3] = 255
out[..., 2] = (page[..., 3] > 0) * 255
Image.fromarray(out).save(os.path.join(UI, 'buch_blatt.png'))
print('buch_blatt.png', W, H, int(paper.sum()), int(sheet.sum()))
