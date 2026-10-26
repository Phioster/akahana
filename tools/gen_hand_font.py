#!/usr/bin/env python3
"""Turns the handwriting Caveat (OFL, tools/fonts) into pixel pencil: each glyph is drawn 4x larger,
averaged down to art pixels and kept where the stroke covers enough. The stroke core is solid, its edges
lighter, with a little graphite grain, all baked into the alpha so the game can tint it (graphite on paper,
chalk outside the book).
Out: assets/ui/hand.png (white, alpha = pencil) + assets/ui/hand.json (same layout as font.json)
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
S = 4                      # supersampling
XH = 6                     # x-height in art pixels
THR = 0.38                 # coverage that counts as a stroke
CHARS = ''.join(chr(c) for c in range(32, 127)) + 'äöüÄÖÜß„“”‚‘’–—…·°éèàâ×'


def font_for_xheight(path):
    size = 8
    while ImageFont.truetype(path, size * S).getmask('x').size[1] < XH * S:
        size += 1
    return ImageFont.truetype(path, size * S), size


def build():
    font, size = font_for_xheight(os.path.join(ROOT, 'tools', 'fonts', 'Caveat.ttf'))
    asc, desc = font.getmetrics()
    ascent, descent = int(np.ceil(asc / S)), int(np.ceil(desc / S))
    rng = np.random.default_rng(7)
    glyphs, cells = {}, []
    for ch in CHARS:
        adv = int(round(font.getlength(ch) / S))
        cw, chh = (adv + 8) * S, (ascent + descent + 4) * S
        im = Image.new('L', (cw, chh), 0)
        ImageDraw.Draw(im).text((4 * S, (ascent + 2) * S), ch, font=font, fill=255, anchor='ls')
        a = np.array(im, float).reshape(chh // S, S, cw // S, S).mean((1, 3)) / 255.0
        core = a > THR
        fuzz = (a > 0.18) & ~core
        if not (core | fuzz).any():
            glyphs[ch] = dict(x=0, y=0, w=0, h=0, ox=0, oy=0, adv=max(adv, 3))
            continue
        grain = ndi.gaussian_filter(rng.normal(0, 1, a.shape), 0.6) > 0.6
        tone = np.clip(0.08 + 0.22 * (a < 0.6) + 0.12 * grain, 0, 0.5)
        alpha = np.where(core, 1 - tone, np.where(fuzz, 0.14, 0.0))
        ys, xs = np.where(alpha > 0)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        cells.append((ch, alpha[y0:y1, x0:x1]))
        glyphs[ch] = dict(w=int(x1 - x0), h=int(y1 - y0), ox=int(x0 - 4), oy=int(y0 - (ascent + 2)), adv=adv)
    cols = 16
    cwid = max(c[1].shape[1] for c in cells) + 1
    chgt = max(c[1].shape[0] for c in cells) + 1
    rows = (len(cells) + cols - 1) // cols
    atlas = np.zeros((rows * chgt, cols * cwid, 4), np.uint8)
    for i, (c, al) in enumerate(cells):
        x, y = (i % cols) * cwid, (i // cols) * chgt
        h, w = al.shape
        atlas[y:y + h, x:x + w, :3] = 255
        atlas[y:y + h, x:x + w, 3] = (al * 255).astype(np.uint8)
        glyphs[c].update(x=x, y=y)
    # line metrics from the drawn glyphs, not the font's generous ascent: tighter, like handwriting
    ascent = max(-g['oy'] for g in glyphs.values() if g['h'])
    descent = max(g['h'] + g['oy'] for g in glyphs.values() if g['h'])
    out = os.path.join(ROOT, 'assets', 'ui')
    Image.fromarray(atlas).save(os.path.join(out, 'hand.png'))
    with open(os.path.join(out, 'hand.json'), 'w') as f:
        json.dump(dict(size=16, ascent=ascent, descent=descent,
                       glyphs={str(ord(k)): v for k, v in glyphs.items()}), f)
    return glyphs, ascent, descent


if __name__ == '__main__':
    g, a, d = build()
    print(len(g), 'glyphs, ascent', a, 'descent', d)
