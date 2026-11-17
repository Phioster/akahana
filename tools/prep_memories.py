"""Brings the approved sketch pages (book filter already applied) into the game: 800 px wide, so they stay
fine on the phone (the page shows them 130 art px wide, about 780 screen px) but keep the APK small.
Usage: python3 tools/prep_memories.py <folder with the filtered pages>"""
import os
import sys

from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'assets', 'erinnerungen')
WIDTH = 800
COLOURS = 48          # ink on paper needs few tones; a palette keeps each page well under 600 kB


def whiten(im: Image.Image) -> Image.Image:
    """Paper to white: the page is drawn multiplied onto the book, a tinted paper would darken it into a box."""
    paper = max(im.getcolors(1 << 24), key=lambda c: c[0])[1]
    lut = []
    for ch in paper:
        lut += [min(255, round(v * 255 / max(ch, 1))) for v in range(256)]
    return im.point(lut)


def prep(src: str) -> list:
    os.makedirs(OUT, exist_ok=True)
    done = []
    for f in sorted(os.listdir(src)):
        if not f.endswith('.png'):
            continue
        im = Image.open(os.path.join(src, f)).convert('RGB')
        im = whiten(im)
        im = im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)
        im = im.quantize(COLOURS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        im.save(os.path.join(OUT, f), optimize=True)
        done.append(f[:-4])
    return done


if __name__ == '__main__':
    print(len(prep(sys.argv[1])), 'Seiten')
