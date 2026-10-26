#!/usr/bin/env python3
"""Rasterises Pixel Operator 8 (CC0, tools/fonts) at its native 8 px into a glyph atlas the game builds a font from.

A bitmap made here keeps one font pixel = one art pixel; a TTF rendered by Godot would follow the
screen resolution instead and look smooth next to the pixel world.
Out: assets/ui/font.png (white on transparent) + assets/ui/font.json (per char: uv rect, offset, advance)
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SIZE = int(os.environ.get('FONT_SIZE', 8))
FONT = os.environ.get('FONT_FILE', 'PixelOperator8.ttf')
TIGHT = os.environ.get('FONT_TIGHT', '1') == '1'
CHARS = ''.join(chr(c) for c in range(32, 127)) + 'äöüÄÖÜß„“”‚‘’–—…·°éèàâ×'


def build():
    font = ImageFont.truetype(os.path.join(ROOT, 'tools', 'fonts', FONT), SIZE)
    ascent, descent = font.getmetrics()
    glyphs, cells = {}, []
    for ch in CHARS:
        im = Image.new('L', (SIZE * 3, SIZE * 2), 0)
        d = ImageDraw.Draw(im)
        d.fontmode = '1'                                   # hard pixels, no smoothing
        d.text((SIZE, 0), ch, font=font, fill=255)
        a = np.array(im) > 127
        adv = max(3, int(round(font.getlength(ch)))) if ch == ' ' else int(round(font.getlength(ch)))   # Tiny5's 2 px space runs words together
        if not a.any():
            glyphs[ch] = dict(x=0, y=0, w=0, h=0, ox=0, oy=0, adv=adv)
            continue
        ys, xs = np.where(a)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        cells.append((ch, a[y0:y1, x0:x1]))
        ox = int(x0 - SIZE)
        if TIGHT:                                          # proportional: glyph + 1 px gap, no side bearings
            ox, adv = 0, int(x1 - x0) + 1
        glyphs[ch] = dict(w=int(x1 - x0), h=int(y1 - y0), ox=ox, oy=int(y0 - ascent), adv=adv)
    cols = 16
    cw = max(c[1].shape[1] for c in cells) + 1
    ch_ = max(c[1].shape[0] for c in cells) + 1
    rows = (len(cells) + cols - 1) // cols
    atlas = np.zeros((rows * ch_, cols * cw, 4), np.uint8)
    for i, (c, bm) in enumerate(cells):
        x, y = (i % cols) * cw, (i // cols) * ch_
        h, w = bm.shape
        atlas[y:y + h, x:x + w][bm] = (255, 255, 255, 255)
        glyphs[c].update(x=x, y=y)
    out = os.environ.get('FONT_OUT', os.path.join(ROOT, 'assets', 'ui'))
    os.makedirs(out, exist_ok=True)
    Image.fromarray(atlas).save(os.path.join(out, 'font.png'))
    with open(os.path.join(out, 'font.json'), 'w') as f:
        json.dump(dict(size=SIZE, ascent=ascent, descent=descent,
                       glyphs={str(ord(k)): v for k, v in glyphs.items()}), f)
    return glyphs


if __name__ == '__main__':
    print(len(build()), 'glyphs')
