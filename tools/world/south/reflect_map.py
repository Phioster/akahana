"""The reflections of everything that stands still by the water, baked once for the game (the approved
look of reflect_anim.py): each upright pixel mirrored at its foot onto open water, dimmed, its colour kept
in proportion. The water shader pulls the rows sideways with the ripples and breaks them further out.

Out: (H, W, 4) uint8; RGB = the mirrored colour (already dimmed), A = strength in the high nibble (0..15)
and distance below the foot / 6 in the low nibble (0..15). A = 0: nothing mirrored here."""
import numpy as np

import reflect_anim as ra


def bake(H, W, open_water, flowers, bend, low, ground, sprites):
    """open_water: (H, W) bool; flowers RGBA + bend: the swaying layer and its heights; low + ground: the flat
    things; sprites: [(rgba, x, y, foot)] standing things (frame 0)."""
    xs, ys, cols, feet = [], [], [], []
    m = (flowers[..., 3] > 0) & (bend > 0) & (bend < 255)
    y, x = np.nonzero(m)
    xs.append(x); ys.append(y); cols.append(flowers[y, x, :3]); feet.append(y + bend[y, x].astype(int))
    # a flat thing mirrors at its own lower edge (its waterline), column by column, plus its height over
    # the water: the bottom row shows first, the top row furthest down - turned over, not just moved
    from scipy import ndimage as ndi
    lab, _ = ndi.label(low > 0)
    y, x = np.nonzero(lab > 0)
    key = lab[y, x].astype(np.int64) * W + x
    bottom = np.zeros(key.max() + 1, np.int64)
    np.maximum.at(bottom, key, y)
    xs.append(x); ys.append(y); cols.append(ground[y, x, :3]); feet.append(bottom[key] + low[y, x].astype(int))
    for rgba, sx, sy, foot in sprites:
        y, x = np.nonzero(rgba[..., 3] > 0)
        xs.append(x + sx); ys.append(y + sy); cols.append(rgba[y, x, :3]); feet.append(np.full(len(y), foot))
    x = np.concatenate(xs); y = np.concatenate(ys); col = np.concatenate(cols).astype(float)
    foot = np.concatenate(feet)
    d = foot - y
    ry = foot + d + 1
    ok = (d >= 0) & (ry >= 0) & (ry < H) & (x >= 0) & (x < W)
    x, ry, d, col = x[ok], ry[ok], d[ok], col[ok]
    ok = open_water[ry, x]
    x, ry, d, col = x[ok], ry[ok], d[ok], col[ok]
    order = np.argsort(-d, kind='stable')                     # the nearest thing wins: written last
    x, ry, d, col = x[order], ry[order], d[order], col[order]
    fade = np.maximum(0.35, 1.0 - d / 90.0)
    k = np.clip(np.round(ra.KEEP * fade * 15), 1, 15).astype(np.uint8)
    out = np.zeros((H, W, 4), np.uint8)
    out[ry, x, :3] = np.clip(col * ra.DIM, 0, 255).astype(np.uint8)
    out[ry, x, 3] = (k << 4) | np.minimum(15, d // 6).astype(np.uint8)
    return out
