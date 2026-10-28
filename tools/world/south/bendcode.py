"""How the bend map stores a swaying pixel: its height above the plant's foot (0..127), plus 128 for reeds
and bulrushes (they only step aside on the trail, they are not pressed flat); 255 = a poppy head that sways
whole. shaders/flowers.gdshader reads it the same way."""
import numpy as np

REED = 128
WHOLE = 255


def height(b):
    b = np.asarray(b).astype(int)
    return np.where(b >= WHOLE, WHOLE, b % REED)


def is_reed(b):
    b = np.asarray(b).astype(int)
    return (b >= REED) & (b < WHOLE)


def encode(h, reed):
    return min(REED - 1, h) | (REED if reed else 0)
