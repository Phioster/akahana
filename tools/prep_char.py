#!/usr/bin/env python3
"""Turns the PixelLab monk (4 directions, 6-frame walk; source in ~/mohnweg-char-klein) into the game's sheet.

PixelLab draws a black outline and a purple habit; the world has no outlines and warm browns, so:
  - everything is repainted in the world's own muted palette, by brightness, in a few flat tones;
    the outline becomes the darkest tone, the upper-left edges catch the light
  - the stray red patch (it wanders between frames) disappears with it
  - the gap between the legs is closed: a habit, not trousers
  - a light wooden staff is drawn diagonally across the back, behind the body
Out: assets/char/wanderer.png, rows down/up/left/right, cols idle0, idle1, walk0..walk5; cell 24x28,
feet at (12, 27). The ground shadow is drawn by the game (scenes/player.gd).
"""
import colorsys
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.expanduser(os.environ.get('MOHNWEG_CHAR', '~/mohnweg-char-klein'))
CW, CH = 24, 28
# the world's own muted, slightly cool warm-greys (sampled from the cottage, bench and shrine sprites)
RAMP = np.array([[38, 34, 36], [54, 46, 46], [72, 62, 60], [96, 84, 82]], float)
RIM = np.array([112, 100, 94], float)           # light catching the upper left edges
SKIN = (np.array([196, 168, 146], float), np.array([150, 124, 108], float))
ROPE = (np.array([176, 160, 128], float), np.array([128, 114, 92], float))
STAFF = (np.array([156, 126, 94]), np.array([112, 90, 68]))


def recolour(img):
    """Repaint the PixelLab monk in the world's palette: few flat tones by brightness, no outline,
    a rim of light on the upper-left edges like every other object."""
    a = np.array(img.convert('RGBA')).astype(float)
    rgb, al = a[..., :3], a[..., 3] > 127
    out = np.zeros_like(rgb)
    h, w = al.shape
    for y in range(h):
        for x in range(w):
            if not al[y, x]:
                continue
            r, g, b = rgb[y, x] / 255.0
            hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
            if (hh < 0.12 or hh > 0.94) and ll > 0.55 and ss > 0.15:          # face, hands
                out[y, x] = SKIN[0] if ll > 0.68 else SKIN[1]
            elif 0.1 < hh < 0.3 and ss > 0.12 and ll > 0.35:                  # rope belt / strap
                out[y, x] = ROPE[0] if ll > 0.5 else ROPE[1]
            else:                                                             # habit, hood, outline
                k = 0 if ll < 0.09 else int(np.clip(ll * 1.4 * len(RAMP), 1, len(RAMP) - 1))
                out[y, x] = RAMP[k]
    for y in range(h):                                                        # rim light, upper left
        for x in range(w):
            if al[y, x] and (out[y, x] == RAMP).all(1).any() and 0 < y and 0 < x:
                if not al[y - 1, x] or not al[y, x - 1]:
                    if al[y + 1 if y + 1 < h else y, x] and al[y, x + 1 if x + 1 < w else x]:
                        out[y, x] = RIM
    a[..., :3] = out
    a[..., 3] = np.where(al, 255, 0)
    return a


def staff(cell, direction):
    """Slung across the back: diagonal from the front and back, hugging the back from the side.
    Drawn only where the cell is still empty, except from behind, where it lies over the back."""
    al = cell[..., 3] > 0
    ys, xs = np.where(al)
    top, bot, left, right = ys.min(), ys.max(), xs.min(), xs.max()
    if direction in ('down', 'up'):
        p0, p1 = ((right + 2, top), (left - 1, bot - 4)) if direction == 'down' else ((left - 2, top), (right + 1, bot - 4))
        over = direction == 'up'
        n = max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))
        for i in range(n + 1):
            x = round(p0[0] + (p1[0] - p0[0]) * i / n)
            y = round(p0[1] + (p1[1] - p0[1]) * i / n)
            if 0 <= x < cell.shape[1] and 0 <= y < cell.shape[0] and (over or cell[y, x, 3] == 0):
                cell[y, x, :3] = STAFF[0] if i < n * 0.45 else STAFF[1]
                cell[y, x, 3] = 255
        return cell
    back = -1 if direction == 'right' else 1
    for y in range(top - 3, bot - 7):
        row = np.where(al[min(max(y, top + 3), bot)])[0]
        edge = row.min() - 1 if back < 0 else row.max() + 1
        x = edge + (1 if back < 0 else -1) * (y - top) // 7
        if 0 <= x < cell.shape[1] and 0 <= y < cell.shape[0] and cell[y, x, 3] == 0:
            cell[y, x, :3] = STAFF[0] if y < top + 6 else STAFF[1]
            cell[y, x, 3] = 255
    return cell


def frames(direction):
    src = {'down': 'south', 'up': 'north', 'left': 'west', 'right': 'east'}[direction]
    # standing = the first walk frame (feet together): PixelLab's standing pose holds the staff in hand
    # and would not match the walk
    idle = close_habit(recolour(Image.open(os.path.join(SRC, f'walk_{src}', '0.png'))))
    walk = [close_habit(recolour(Image.open(os.path.join(SRC, f'walk_{src}', f'{i}.png')))) for i in range(6)]
    return [idle, idle] + walk


def close_habit(fr):
    """A habit, not trousers: below the belt the gap between the legs is filled with cloth, down to just
    above the feet, so a stride swings the hem instead of showing two legs."""
    al = fr[..., 3] > 0
    ys = np.where(al.any(axis=1))[0]
    top, bot = ys.min(), ys.max()
    start = top + int((bot - top) * 0.55)
    for y in range(start, bot - 2):
        xs = np.where(al[y])[0]
        if len(xs) < 2:
            continue
        for x in range(xs.min(), xs.max() + 1):
            if not al[y, x]:
                shade = 1 if (x - xs.min()) < (xs.max() - xs.min()) / 2 else 2   # lit side brighter
                fr[y, x, :3] = RAMP[shade]
                fr[y, x, 3] = 255
    return fr


def place(fr, feet_y, cx):
    cell = np.zeros((CH, CW, 4))
    h, w = fr.shape[:2]
    oy, ox = CH - 1 - feet_y, CW // 2 - cx
    for y in range(h):
        for x in range(w):
            ty, tx = y + oy, x + ox
            if fr[y, x, 3] > 0 and 0 <= ty < CH and 0 <= tx < CW:
                cell[ty, tx] = fr[y, x]
    return cell


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'assets', 'char', 'wanderer.png')
    sheet = np.zeros((CH * 4, CW * 8, 4))
    for r, d in enumerate(('down', 'up', 'left', 'right')):
        fs = frames(d)
        feet = max(int(np.where(f[..., 3] > 0)[0].max()) for f in fs)     # one ground line per direction
        cx = int(np.median([np.where(f[..., 3] > 0)[1].mean() for f in fs]).round())
        for c, f in enumerate(fs):
            cell = staff(place(f, feet, cx), d)
            sheet[r * CH:(r + 1) * CH, c * CW:(c + 1) * CW] = cell
    Image.fromarray(sheet.astype(np.uint8)).save(out)
    print('ok', out)
