"""The bookmark on the book button (approved preview 2026-11-16): a golden ribbon comes out of a slit in the
light page block and hangs below the book. Drawn over buch_knopf at the same spot; 7 rows taller for the
hanging end. Outline only where the ribbon hangs over the ground."""
import os

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'assets', 'ui', 'buch_lesezeichen.png')
GOLD, GOLD_D = (214, 170, 70), (160, 118, 44)
SLIT = (110, 86, 58)
OUTLINE = (40, 26, 20)
X0 = 13                               # where it leaves the pages
PATH = [(0, 16), (0, 17), (0, 18), (0, 19), (0, 20), (0, 21), (1, 22), (1, 23), (1, 24), (2, 25)]


def build() -> Image.Image:
    w, h = 23, 29
    a = np.zeros((h, w, 4), np.uint8)
    for x in range(X0 - 2, X0 + 4):                            # the slit between the pages
        a[16, x] = SLIT + (255,)
    rib = np.zeros((h, w), bool)
    for dx, y in PATH:
        a[y, X0 + dx] = GOLD + (255,)
        a[y, X0 + dx + 1] = GOLD_D + (255,)
        rib[y, X0 + dx] = rib[y, X0 + dx + 1] = True
    a[26, X0 + 2] = GOLD + (255,)                              # the cut end, notched
    a[26, X0 + 4] = GOLD_D + (255,)
    rib[26, X0 + 2] = rib[26, X0 + 4] = True
    edge = np.zeros_like(rib)
    for dx, dy in [(-1, 0), (1, 0), (0, 1)]:
        edge |= np.roll(np.roll(rib, dy, 0), dx, 1)
    edge &= ~rib
    edge[:20] = False                                          # on the book itself no outline
    a[edge] = OUTLINE + (255,)
    return Image.fromarray(a)


if __name__ == '__main__':
    build().save(OUT)
    print('geschrieben', OUT)
