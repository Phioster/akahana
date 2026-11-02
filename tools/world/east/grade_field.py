"""The wood's mood as a map for the post shader (half the world's size, like mist_fields.png):
R darkness (0 meadow .. 1 deep wood), G moonlight in the clearings, B the pale shaft above the ritual altar.
Smooth everywhere: the poppy meadow darkens slowly into the wood, no edge."""
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE]
import layout as L  # noqa: E402
import spot5_ritual as s5  # noqa: E402

H, W = 3600, 1800
TOP = 1040


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def build():
    gy, gx = np.mgrid[0:H // 2, 0:W // 2] * 2.0 + 1.0
    dark = smooth((gx - 470) / 380.0)                                   # the poppies run out into the wood
    yb = 1.0 - smooth((gy - (TOP - 40)) / 110.0)
    south = np.where(gx >= 900, 1.0, np.maximum(yb, smooth((gx - 660) / 240.0)))    # like the wood's own mix: no edge at x=900 or y=TOP
    along = (900 + 600 - gx) / 600.0 * 0.45 + (gy - 2350) / 650.0 * 0.75          # warm and green near the meadow's tongue
    warm = smooth(along + 0.25) * smooth((gy - 2250) / 80.0)
    r = dark * south * (1 - warm)
    clr = np.zeros((H, W), bool)
    clr[L.Y0:L.Y1, L.X0:L.X1] = L.masks().clearing
    g = ndi.gaussian_filter(clr[::2, ::2].astype(float), 4) * 0.7 * r      # moonlight lies in the clearings
    cx, cy = s5.X0 + s5.CX - 18, s5.Y0 + s5.CY - 14                     # the shaft falls a little off the altar's centre
    top = cy - 150
    t = np.clip((cy - 8 - gy) / (cy - 8 - top), 0, 1)
    half = 11 + 9 * t
    col = np.exp(-(((gx - cx) / half) ** 2) * 1.6) * (gy < cy - 4) * (gy > top) * (1 - 0.82 * t) ** 1.2
    pool = np.exp(-(((gx - cx) / 46.0) ** 2 + ((gy - cy - 4) / 17.0) ** 2))
    b = np.clip(col * 0.8 + pool * 0.5, 0, 1)
    return np.stack([r, g, b], 2)


def write(out):
    f = build()
    Image.fromarray(np.round(np.clip(f, 0, 1) * 255).astype(np.uint8)).save(os.path.join(out, 'grade_field.png'))


if __name__ == '__main__':
    write(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, '..', '..', '..', 'assets', 'world'))
