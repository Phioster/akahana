"""Reflections on the water: everything that stands upright by the water (trees, the jetty, reeds, lanterns,
the wanderer) shows mirrored at its foot, dimmed and taking on the water's colour, its rows pulled a pixel
or two sideways by the ripples and here and there broken, the further from the foot the more.
Upright pixels come as (x, y, rgb, foot_y): sprites from their foot, the swaying layer from its bend map,
the flat things in the ground from the generator's low map."""
import numpy as np

LOOP = 8.0
KEEP = 0.68                # how much of the thing's own colour shows (the rest is the water's)
DIM = 0.72


def upright_from_layer(layer, bend, x0, y0):
    """The swaying layer (reeds, grass, flowers): each pixel's foot from the bend map (height above foot)."""
    ys, xs = np.nonzero((layer[..., 3] > 0) & (bend > 0) & (bend < 255))
    return [(x0 + x, y0 + y, layer[y, x, :3].astype(float), y0 + y + int(bend[y, x])) for y, x in zip(ys, xs)]


def upright_from_low(ground, low, x0, y0):
    """Flat things drawn into the ground (jetty, boat, bridges, stones in the water): low holds how many
    pixels they stand above the water, so only their edges show mirrored, close under them."""
    from scipy import ndimage as ndi                   # mirrored at each thing's own lower edge, per column
    lab, _ = ndi.label(low > 0)
    ys, xs = np.nonzero(lab > 0)
    bottom = {}
    for y, x in zip(ys, xs):
        k = (lab[y, x], x)
        bottom[k] = max(bottom.get(k, y), y)
    return [(x0 + x, y0 + y, ground[y, x].astype(float), y0 + bottom[(lab[y, x], x)] + int(low[y, x]))
            for y, x in zip(ys, xs)]


def upright_from_sprite(pic, sx, sy, foot):
    ys, xs = np.nonzero(pic[..., 3] > 0)
    return [(sx + x, sy + y, pic[y, x, :3].astype(float), foot) for y, x in zip(ys, xs)]


def draw(img, x0, y0, water, ups, t, mode='B'):
    """img: picture cut at world (x0, y0); water: bool mask of the open water in the same cut.
    mode A: a clean mirror, only wobbling; B: also broken into ripple rows further out."""
    h, w = water.shape
    ph = 2 * np.pi * t / LOOP
    out = img.copy()
    for (x, y, col, foot) in ups:
        d = foot - y                                   # height above the foot = distance below it
        if d < 0:
            continue
        ry = foot + d + 1
        j = ry - y0
        if not 0 <= j < h:
            continue
        amp = min(2.0, 0.4 + d / 14.0)                 # rows sway more the further out they lie
        dx = int(np.round(amp * (0.65 * np.sin(ry * 0.85 - ph + 0.03 * x)        # two swells crossing at
                                 + 0.45 * np.sin(ry * 0.31 + 3 * ph + 0.05 * x + 1.7))))   # their own pace
        i = x - x0 + dx
        if not 0 <= i < w or not water[j, i]:
            continue
        if mode == 'B' and d > 6 and np.sin(ry * 1.7 + 2 * ph + np.sin(ry * 0.23 - ph) * 3) > 1 - min(4, d // 8) / 4.5:
            continue                                   # broken by a ripple row
        fade = max(0.35, 1.0 - d / 90.0)
        k = KEEP * fade
        out[j, i] = img[j, i] * (1 - k) + col * DIM * k
    img[:] = out
