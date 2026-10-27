"""The wind in the swaying layer, as shaders/flowers.gdshader moves it (gusts as drifting noise patches),
in two ways for the approval page:

  A  every plant moves as a whole by the gust's few pixels (what the poppies do today)
  B  a plant bends: its foot stays, the higher a pixel sits above the foot the further it goes
     (the generator's bend map holds each pixel's height; poppy heads are 255 and move whole as in A)
"""
import numpy as np

BEND_H = 10.0                         # px above the foot from where a blade goes the whole way
CALM_B = 1.1                          # the gentle sway between gusts: at 0.5 it rounded to 0, reeds stood still


def _h(ix, iy):
    return (np.sin(ix * 127.1 + iy * 311.7) * 43758.5453) % 1.0


def vnoise(qx, qy):
    ix, iy = np.floor(qx), np.floor(qy)
    fx, fy = qx - ix, qy - iy
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b, c, d = _h(ix, iy), _h(ix + 1, iy), _h(ix, iy + 1), _h(ix + 1, iy + 1)
    return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy


def wind_dx(px, py, t, calm=0.5):
    """Whole-pixel shift of the gust at world pixel (px, py), time t: the flower shader's formula."""
    ph = 2 * np.pi * t / 8.0
    qx, qy = px / 70.0 - 0.0455 * t, py / 45.0 - 0.078 * t
    n = vnoise(qx, qy) * 0.65 + vnoise(qx * 2.3 + 17.0, qy * 2.3 + 5.0) * 0.35
    g = np.clip((n - 0.42) / (0.8 - 0.42), 0, 1)
    g = g * g * (3 - 2 * g)
    w = 2.6 * g + calm * np.sin(3 * ph + 2 * np.pi * vnoise(px / 23.0 + 3.1, py / 23.0 + 8.7))
    return np.floor(w + 0.5)


def sway(layer, bend, x0, y0, t, mode):
    """layer (h, w, 4) and bend (h, w) cut at world (x0, y0) with a margin of 4 px on the left; returns the
    visible part (margin dropped) at time t."""
    h, w = layer.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    dx = wind_dx(xx + x0, yy + y0, t).astype(int)
    dx_b = wind_dx(xx + x0, yy + y0, t, CALM_B).astype(int)   # blades also stir between the gusts
    out = np.zeros_like(layer)
    if mode == 'A':
        src = np.clip(xx - dx, 0, w - 1)
        out = layer[yy, src]
    else:
        best = np.full((h, w), -1)
        for k in range(-2, 4):                                 # which source pixel lands here after bending (either way)
            sx = np.clip(xx - k, 0, w - 1)
            hs = bend[yy, sx].astype(float)
            d = np.round(dx_b[yy, sx] * np.minimum(hs / BEND_H, 1.0)).astype(int)
            d = np.where(hs >= 255, dx[yy, sx], d)
            hit = (d == k) & (layer[yy, sx, 3] > 0) & (hs > best)
            out[hit] = layer[yy, sx][hit]
            best = np.where(hit, hs, best)
    return out[:, 4:]
