#!/usr/bin/env python3
"""The Japanese names in handwriting: Klee One (OFL, tools/fonts) as pixel pencil, the same 4x recipe as
tools/gen_hand_font.py but tidied (approved, 15 px): no graphite grain and no lone specks, so the dense
kanji stay readable; the stroke core one even grey, its edges a little lighter.
Characters: every kana plus the kanji used in docs/namen.md (add a name there, run this again).
Out: assets/ui/kanji.png (white, alpha = pencil) + assets/ui/kanji.json (same layout as hand.json)
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
S = 4
PX = 15                    # height of a kanji in art pixels
THR = 0.38
KANA = ''.join(chr(c) for c in range(0x3041, 0x3097)) + ''.join(chr(c) for c in range(0x30a1, 0x30fb)) + 'ー・'


def chars():
    with open(os.path.join(ROOT, 'docs', 'namen.md')) as f:
        used = {c for c in f.read() if '一' <= c <= '鿿'}
    return KANA + ''.join(sorted(used))


def build():
    path = os.path.join(ROOT, 'tools', 'fonts', 'KleeOne-Regular.ttf')
    size = 8
    while True:
        font = ImageFont.truetype(path, size * S)
        bb = font.getbbox('森')
        if bb[3] - bb[1] >= PX * S:
            break
        size += 1
    asc, desc = font.getmetrics()
    ascent, descent = int(np.ceil(asc / S)), int(np.ceil(desc / S))
    glyphs, cells = {}, []
    for ch in chars():
        adv = int(round(font.getlength(ch) / S))
        cw, chh = (adv + 8) * S, (ascent + descent + 4) * S
        im = Image.new('L', (cw, chh), 0)
        ImageDraw.Draw(im).text((4 * S, (ascent + 2) * S), ch, font=font, fill=255, anchor='ls')
        a = np.array(im, float).reshape(chh // S, S, cw // S, S).mean((1, 3)) / 255.0
        core = a > THR
        fuzz = (a > 0.18) & ~core
        lab, n = ndi.label(core | fuzz)                        # lone specks are noise at this size
        for k, v in enumerate(ndi.sum(np.ones_like(a), lab, range(1, n + 1)), 1):
            if v < 2:
                core[lab == k] = fuzz[lab == k] = False
        alpha = np.where(core, np.where(a < 0.6, 0.72, 0.92), np.where(fuzz, 0.16, 0.0))
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
    ascent = max(-g['oy'] for g in glyphs.values() if g['h'])
    descent = max(g['h'] + g['oy'] for g in glyphs.values() if g['h'])
    out = os.path.join(ROOT, 'assets', 'ui')
    Image.fromarray(atlas).save(os.path.join(out, 'kanji.png'))
    with open(os.path.join(out, 'kanji.json'), 'w') as f:
        json.dump(dict(size=PX, ascent=ascent, descent=descent,
                       glyphs={str(ord(k)): v for k, v in glyphs.items()}), f, ensure_ascii=False)
    return glyphs, ascent, descent


if __name__ == '__main__':
    g, a, d = build()
    print(len(g), 'glyphs, ascent', a, 'descent', d)
