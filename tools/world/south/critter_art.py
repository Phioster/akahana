"""Fish and ducks as drawn pixel sprites, like the small birds (assets/life/vogel_*.png): fixed frames
instead of shapes worked out afresh every frame (they jagged and flickered when turning).

  fisch.png   16 headings (22.5 deg steps from E, clockwise) x 3 shades x 4 tail phases x 4x4 quarter-pixel offsets (see fish_sheet_v2); 3 shades (faint, half, full: opaque colours stepping towards
              the water, no dissolving pixels), 11 x 11 each, the fish's middle at (5, 5)
  ente.png    swim (2 frames, the wake moves), run (2), fly (4 wing positions), facing right, 24 x 20 each,
              the duck's middle (waterline) at (12, 12); facing left = flipped
Source of truth for the game and the approval preview (critter_preview.py).
"""
import numpy as np
from PIL import Image

WATER = np.array([31, 42, 49])
FISH = [np.array(c) for c in ([48, 66, 76], [66, 90, 98], [96, 124, 132])]          # back, side, belly
WAKE = [np.array([85, 112, 121]), np.array([127, 152, 156])]
BODY = [np.array(c) for c in ([59, 51, 44], [94, 82, 70], [138, 122, 104])]
HEAD, BILL, TIP = np.array([47, 74, 58]), np.array([201, 162, 78]), np.array([186, 170, 146])
SPLASH = np.array([150, 176, 182])
CELL_F = 11
CELL_D = (24, 20)


def fish_cell(angle_deg, shade, bend=0.0, dx=0.0, dy=0.0):
    """One fish heading angle_deg (0 = right, 90 = down): a spindle with a forked tail, shaded back to belly,
    rasterised on a half-pixel-centred grid so mirrored headings give mirrored pictures."""
    out = np.zeros((CELL_F, CELL_F, 4), np.uint8)
    a = np.radians(angle_deg)
    c, s = np.cos(a), np.sin(a)
    ss = 4
    ys, xs = np.mgrid[0:CELL_F * ss, 0:CELL_F * ss]
    X = (xs + 0.5) / ss - CELL_F / 2 - dx                       # dx, dy: the fish's sub-pixel offset inside the cell
    Y = (ys + 0.5) / ss - CELL_F / 2 - dy
    u = X * c + Y * s                                           # along the fish
    v = -X * s + Y * c                                          # across it (positive: the belly side, "down")
    L = 4.6
    v = v - bend * np.clip((-u + 0.5) / (L + 1.5), 0.0, 1.0) ** 1.6 * 1.7    # tail swing: the rear bends sideways
    body = (u / L) ** 2 + (v / 1.55) ** 2 <= 1.0
    body &= u > -L + 0.4
    t = (-u - L + 0.4)                                          # the tail: two small flukes behind the body
    tail = (u <= -L + 1.0) & (u >= -L - 1.2) & (np.abs(v) <= 0.45 + 0.9 * (-u - L + 1.0 + 1.2) / 2.2) & ~body
    cover = (body | tail).reshape(CELL_F, ss, CELL_F, ss).mean(axis=(1, 3))
    vv = v.reshape(CELL_F, ss, CELL_F, ss).mean(axis=(1, 3))
    uu = u.reshape(CELL_F, ss, CELL_F, ss).mean(axis=(1, 3))
    mask = cover >= 0.5
    # shading by the screen's light from the upper left: back dark, side mid, belly light
    lx, ly = -0.6, -0.8
    for j, i in zip(*np.nonzero(mask)):
        k = (i - CELL_F / 2 + 0.5) * lx + (j - CELL_F / 2 + 0.5) * ly           # + toward the light side
        col = FISH[2] if k < -0.9 else (FISH[0] if k > 0.9 else FISH[1])
        if uu[j, i] < -L + 1.0:
            col = FISH[0]
        col = (WATER + (col - WATER) * (0.45, 0.75, 1.0)[shade]).astype(float)
        out[j, i, :3] = np.clip(col, 0, 255).astype(np.uint8)
        out[j, i, 3] = 255
    return out


WAG = [0.0, 1.0, 0.0, -1.0]                                     # tail swing, one swim cycle (v2)


SUB = [-0.5, -0.25, 0.0, 0.25]                                  # sub-pixel offsets (quarter pixel) per axis


def fish_sheet_v2():
    """16 headings across; rows = ((shade * 4 + tail phase) * 4 + sub-y) * 4 + sub-x."""
    return np.concatenate([np.concatenate([fish_cell(h * 22.5, sh, WAG[ph], SUB[ox], SUB[oy]) for h in range(16)], axis=1)
                           for sh in range(3) for ph in range(4) for oy in range(4) for ox in range(4)], axis=0)


def fish_sheet():
    return np.concatenate([np.concatenate([fish_cell(h * 45, sh) for h in range(8)], axis=1) for sh in range(3)], axis=0)


# ---------------------------------------------------------------- the duck (facing right)
# '.' nothing, '0' '1' '2' body dark..light, 'H' head, 'B' bill, 'T' wing tip
SWIM = [                                                        # facing right, body 7 wide like the old duck; head bobs on frame 2
    ["......HH...", "......HHBB.", "..01111H...", ".0111122...", "..011111...", "...0000...."],
    ["......HH...", "......HHBB.", "..01111H...", ".0111122...", "..011111...", "...0000...."],
    ["...........", "......HH...", "..0111HHBB.", ".0111122...", "..011111...", "...0000...."],
    ["......HH...", "......HHBB.", "..01111H...", ".0111122...", "..011111...", "...0000...."],
]
DUCK_FLY = [                                                    # stretched, neck out, pointed tail
    "...........HH.",
    "..01111111HHBB",
    "...0111111....",
    "....0111......",
]
FLY_MID = (6, 2)
WINGS = [                                                       # (dx, dy) from FLY_MID, shoulder at (1, -1); lighter tips
    [(1, -2), (1, -3), (0, -3), (0, -4), (-1, -4), (-1, -5), (-2, -5), (-2, -6)],                          # up
    [(1, -2), (0, -2), (0, -3), (-1, -3), (-2, -3), (-2, -4), (-3, -4)],                                   # half
    [(1, 0), (0, 1), (0, 2), (-1, 2), (-1, 3), (-2, 3), (-2, 4), (-3, 4)],                                 # down
    [(1, -2), (0, -2), (0, -3), (-1, -3), (-2, -3), (-2, -4), (-3, -4)],                                   # half again
]


def _put(img, x, y, col):
    if 0 <= x < img.shape[1] and 0 <= y < img.shape[0]:
        img[y, x, :3] = col
        img[y, x, 3] = 255


def _grid(img, rows, ox, oy):
    pal = {'0': BODY[0], '1': BODY[1], '2': BODY[2], 'H': HEAD, 'B': BILL}
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in pal:
                _put(img, ox + i, oy + j, pal[ch])


SWIM_WATERLINE = 5


def swim_frame(n):
    """Paddling duck, 28 x 16, the middle of its body at (14, 8): the head dips on every other beat and the
    two arms of the wake run on a pixel per beat, so the V seems to stream away behind it."""
    img = np.zeros((16, 28, 4), np.uint8)
    ox, oy = 14 - 5, 8 - SWIM_WATERLINE + 1
    pal = {'0': BODY[0], '1': BODY[1], '2': BODY[2], 'H': HEAD, 'B': BILL}
    for k in range(10):                                         # the wake first, the body over it
        for side in (-1, 1):
            if (k + n) % 4 == 3:                                # a gap that travels back along each arm
                continue
            x = ox + 1 - k
            y = oy + 5 + side * (1 + k // 3)
            if 0 <= x < 28 and 0 <= y < 16:
                _put(img, x, y, WAKE[0] if k < 5 else WAKE[1])
    _grid(img, SWIM[n % 4], ox, oy)
    for i in range(2, 7):                                       # a thin ripple line under the belly
        if (i + n) % 3:
            _put(img, ox + i, oy + 6, WAKE[0])
    return img


def duck_frame(kind, n):
    img = np.zeros((CELL_D[1], CELL_D[0], 4), np.uint8)
    cx, cy = 12, 12
    if kind == 'swim':
        _grid(img, DUCK_SWIM, cx - MID[0], cy - MID[1])
        sh = n % 2                                                # the wake: two lines, moving a pixel
        for k in range(2, 9):
            for side in (-1, 1):
                _put(img, cx - 5 - k, cy + 1 + side * ((k + sh) // 3), WAKE[0] if k < 5 else WAKE[1])
    elif kind in ('run', 'fly'):
        lift = 0 if kind == 'run' else 0
        _grid(img, DUCK_FLY, cx - FLY_MID[0], cy - FLY_MID[1] - lift)
        elev = n % 4 if kind == 'fly' else [1, 2][n % 2]
        for k, (dx, dy) in enumerate(WINGS[elev]):
            _put(img, cx + dx, cy - 1 + dy, TIP if k >= 4 else BODY[2])
        if kind == 'run':                                         # splash and a wake behind the running duck
            for k, (dx, dy) in enumerate([(-7, 2), (-9, 3), (-8, 1), (-11, 2)]):
                _put(img, cx + dx - n % 2, cy + dy, SPLASH)
            for k in range(8, 13):
                _put(img, cx - k - 2, cy + 3 + (k % 3 - 1), WAKE[k % 2])
    return img


def duck_sheet():
    frames = [swim_frame(i) for i in range(4)] + [duck_frame('run', 0), duck_frame('run', 1)]
    frames += [duck_frame('fly', i) for i in range(4)]
    frames = [np.pad(f, ((0, 20 - f.shape[0]), (0, 28 - f.shape[1]), (0, 0))) for f in frames]
    return np.concatenate(frames, axis=1)


if __name__ == '__main__':
    import os
    out = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets', 'life')
    Image.fromarray(fish_sheet_v2()).save(os.path.join(out, 'fisch.png'))
    Image.fromarray(duck_sheet()).save(os.path.join(out, 'ente.png'))
    print('ok')
