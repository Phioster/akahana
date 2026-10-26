#!/usr/bin/env python3
"""The sketchbook: a worn, hand-bound leather journal. One object behind the start screen, the settings
and (later) the memory pages.

Seen like the world, from above and a little from the front left, so three faces show: the cover on top,
the laced spine on the left and the thick deckle-edged page block at the front. Every surface has a height
map lit from the upper left; colours come in few shades (pixel art, no smooth gradients).
  buch_deckel.png   the closed journal: worn cover, flap, wrap strap with a brass stud, embossed poppies
  buch_seite.png    the opened journal: one deckle-edged page lying on the inside of the cover
  buch_knopf.png    the closed journal, small, as the button bottom right
  buch_schatten*.png  soft shadows it casts on the meadow
  mohn_knopf.png    a drawn poppy, the knob of the pencil sliders
  kritzel.png       small ink doodles: camera, house, footprints, back arrow (9x9 each)
Out: assets/ui/
"""
import os

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'assets', 'ui')
rng = np.random.default_rng(31)

LEATHER = np.array([74, 48, 34])
WORN = np.array([118, 82, 56])           # rubbed-off lighter leather
DARK = np.array([46, 30, 22])
CORD = np.array([132, 88, 56])           # the lacing on the spine
BRASS = np.array([176, 142, 76])
PAGE = np.array([214, 186, 132])         # old deckle-edged paper
PAGE_OLD = np.array([168, 128, 80])      # its browned edges
PAPER = np.array([226, 208, 168])
INK = np.array([62, 46, 38])
POPPY = np.array([150, 52, 40])          # faint pigment left in the embossing
STEM = np.array([88, 98, 64])
LIGHT = np.array([-0.55, -0.75, 1.1])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def noise(h, w, sig):
    n = ndi.gaussian_filter(rng.normal(0, 1, (h, w)), sig)
    return n / (np.abs(n).max() + 1e-9)


def rounded(h, w, r):
    yy, xx = np.mgrid[0:h, 0:w]
    m = np.ones((h, w), bool)
    for cy, cx in [(r, r), (r, w - 1 - r), (h - 1 - r, r), (h - 1 - r, w - 1 - r)]:
        corner = ((yy < r) if cy == r else (yy > h - 1 - r)) & ((xx < r) if cx == r else (xx > w - 1 - r))
        m &= ~(corner & ((yy - cy) ** 2 + (xx - cx) ** 2 > r * r))
    return m


def lit(albedo, height, amb=0.56, k=0.66, steps=8):
    gy, gx = np.gradient(height)
    n = np.dstack([-gx, -gy, np.ones_like(height)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    s = amb + k * np.clip((n * LIGHT).sum(2), 0, 1)
    s = np.round(s * steps) / steps
    return np.clip(albedo * s[..., None], 0, 255)


def bevel(mask, width):
    return np.clip(ndi.distance_transform_edt(mask) / width, 0, 1) ** 0.6


def put(out, y, x, rgb, mask=None):
    h, w = rgb.shape[:2]
    m = np.ones((h, w), bool) if mask is None else mask
    out[y:y + h, x:x + w, :3][m] = np.clip(rgb, 0, 255)[m]
    out[y:y + h, x:x + w, 3][m] = 255


def worn_leather(h, w, mask, scale=1.0):
    """Distressed leather: rubbed lighter patches, darker creases, fine crackle in the grain."""
    patches = noise(h, w, 6 * scale) + 0.5 * noise(h, w, 2 * scale)
    edge = 1 - bevel(mask, 7 * scale)                                  # edges get rubbed most
    rub = np.clip(0.45 * patches + 1.0 * edge ** 1.5 - 0.1, 0, 0.85)
    rub = np.round(rub * 5) / 5                                        # a few tones, like hand pixel art
    alb = LEATHER * (1 - rub[..., None]) + WORN * rub[..., None]
    crack = np.abs(noise(h, w, 1.1 * scale)) < 0.05
    height = 2.6 * bevel(mask, 4 * scale) + 0.35 * noise(h, w, 0.8) + 0.6 * noise(h, w, 3 * scale)
    height[crack] -= 0.5
    return alb, height


def emboss_poppies(alb, height, specs, pigment=0.4):
    """Poppies pressed into the cover (like the tree of life in the reference): a raised relief with an
    engraved outline, a little red pigment left in the petals."""
    h, w = height.shape
    yy, xx = np.mgrid[0:h, 0:w]
    for cx, cy, r, stem_to, bend in specs:
        ang = np.arctan2(yy - cy, xx - cx)
        d = np.hypot(yy - cy, xx - cx)
        edge = r * (0.8 + 0.2 * np.cos(4 * ang + 0.6))
        petal = d <= edge
        rim = petal & (d > edge - 1.2)
        vein = petal & (np.abs(np.sin(2 * (ang - 0.6 / 4 * 0 - 0.15))) < 0.12) & (d > r * 0.3)
        height[petal] += 1.6
        height[rim | vein] -= 1.2
        col = alb[petal] * (1 - pigment) + POPPY * pigment
        alb[petal] = col
        alb[d <= max(1.2, r * 0.22)] = DARK
        for y in range(cy + int(r * 0.8), stem_to):                     # stem: a pressed groove with a ridge
            t = (y - cy) / max(1, stem_to - cy)
            x = int(round(cx + bend * np.sin(t * 2.4)))
            height[y, x - 1:x + 3] += np.array([0.6, 1.4, 1.4, 0.6])
            height[y, x + 3] -= 0.8
            alb[y, x:x + 2] = alb[y, x:x + 2] * 0.7 + STEM * 0.3
    return alb, height


def page_block(h, w, deckle=True):
    """The front of the page block: many thin uneven sheets, browned towards the edges, deckled."""
    a = np.zeros((h, w, 3))
    for y in range(h):
        tone = 0.86 + 0.14 * rng.random()
        if y % 2:
            tone *= 0.9
        a[y] = PAGE * tone
    n = noise(h, w, 1.5)
    a *= (1 + 0.06 * n)[..., None]
    side = np.clip(1 - np.minimum(np.arange(w), w - 1 - np.arange(w)) / 8, 0, 1)
    a = a * (1 - 0.35 * side[None, :, None]) + PAGE_OLD * 0.35 * side[None, :, None]
    mask = np.ones((h, w), bool)
    if deckle:                                                         # ragged ends of the sheets
        for y in range(h):
            l, r = rng.integers(0, 3), rng.integers(0, 3)
            mask[y, :l] = False
            mask[y, w - r:] = False
    a[:, :] *= np.linspace(1.0, 0.82, h)[:, None, None]                 # deeper sheets in shade
    return a, mask


def journal(w=126, h=148, dx=13, dy=18, small=False):
    """The closed journal as one box seen from above, front and a little from the left. The book lies
    with its spine to the left: we see the cover on top, the rounded laced spine on the west face and the
    page block on the south face. Both side faces are sheared by the same depth vector (-dx, +dy), so
    they meet in one shared edge, like a real object. Returns RGBA."""
    W, H = w + dx + 2, h + dy + 2
    out = np.zeros((H, W, 4), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    # face masks in screen space (cover top-left corner at (dx, 0))
    top = np.zeros((H, W), bool)
    top[0:h, dx:dx + w] = rounded(h, w, 3 if small else 6)
    t_s = (yy - h) / dy                                                # 0..1 down the south face
    south = (yy >= h) & (yy < h + dy) & (xx >= dx - t_s * dx) & (xx < dx + w - t_s * dx - 1)
    t_w = (dx - xx) / dx                                               # 0..1 across the west face
    west = (xx < dx) & (xx >= 0) & (yy >= t_w * dy) & (yy < h + t_w * dy) & ~south
    # --- south face: leather lip of the front cover, the page block, the lip of the back cover
    sv = (yy - h - (0 if small else 0))
    lip = 1 if small else 2
    pb = np.zeros((H, W, 3))
    for y in range(h, h + dy):
        r = y - h
        if r < lip or r >= dy - lip:
            pb[y] = DARK * (1.2 if r < lip else 0.8)
        else:
            tone = (0.88 + 0.12 * rng.random()) * (0.95 if r % 2 else 1.0) * (1 - 0.12 * r / dy)
            pb[y] = PAGE * tone
    sx = xx - (dx - t_s * dx)                                          # position along the south face
    side = np.clip(1 - np.minimum(sx, (w - 1) - sx) / 8, 0, 1)
    pages = south & (yy >= h + lip) & (yy < h + dy - lip)
    pb[pages] = pb[pages] * (1 - 0.35 * side[pages][:, None]) + PAGE_OLD * 0.35 * side[pages][:, None]
    if not small:                                                      # deckle: ragged sheet ends
        for y in range(h + lip, h + dy - lip):
            row = south[y] & pages[y]
            xs_ = np.where(row)[0]
            if len(xs_):
                south[y, xs_[-rng.integers(0, 3):]] = False if rng.random() < 0.7 else south[y, xs_[-1]]
    put(out, 0, 0, pb, south)
    # --- one leather skin for top + west (spine) so the back really is part of the cover
    leather = top | west
    alb, hgt = worn_leather(H, W, leather, 0.35 if small else 1.0)
    # spine: rounded back. Light falls from the upper left, so the outer part of the round is lit
    u = np.clip((xx - (dx - dx)) / dx, 0, 1)                           # 0 outer edge .. 1 hinge
    roundness = np.sqrt(np.clip(1 - (1 - u) ** 2, 0, 1))
    hgt[west] += (6.0 * roundness - 6.0)[west]
    hinge = np.exp(-((xx - dx - 1.5) / 1.4) ** 2) * (yy < h)
    hgt -= 1.2 * hinge
    alb = alb * (1 - 0.15 * hinge[..., None])
    if not small:
        cyy, cxx = yy - 0, xx - dx
        # flap over the right part of the cover
        flap_x = w - 34 + 6 * np.sin(cyy / h * np.pi)
        fedge = top & (np.abs(cxx - flap_x) < 1.0)
        hgt[top & (cxx > flap_x)] += 1.2
        hgt[fedge] -= 0.6
        alb[fedge] = DARK
        sub_a, sub_h = alb[0:h, dx:dx + w].copy(), hgt[0:h, dx:dx + w].copy()
        sub_a, sub_h = emboss_poppies(sub_a, sub_h, [(40, 50, 15, 96, 6), (76, 38, 13, 96, -5), (60, 78, 11, 96, 3)])
        tm = top[0:h, dx:dx + w]
        alb[0:h, dx:dx + w][tm], hgt[0:h, dx:dx + w][tm] = sub_a[tm], sub_h[tm]
    else:
        pet = np.hypot(yy - 5, xx - (dx + 8)) <= 3.2
        alb[pet & top] = POPPY * 1.25
        hgt[pet & top] += 1.0
    # strap: hand-tied, a little sag and twist; it crosses the cover and continues down the spine
    sy = int(h * 0.66)
    xs = np.arange(W)
    centre = sy + (0 if small else 2.2) * np.sin((xs - dx) / w * np.pi * 1.2 + 0.5) + (0 if small else 0.8) * np.sin(xs / 9.0)
    centre = centre + np.where(xs < dx, (dx - xs) / dx * dy, 0)        # on the spine it follows the shear
    half = (1.2 if small else 5.0) + (0 if small else 0.9) * np.sin(xs / 17.0 + 1.0)
    dist = yy - centre[None, :]
    band = (np.abs(dist) <= half[None, :]) & leather
    alb[band] = np.array([60, 36, 26]) * (1 + 0.14 * noise(H, W, 1.2)[band][:, None])
    hgt[band] += (1.5 if small else 3.0) + (0 if small else 2.0) * np.clip((half[None, :] - np.abs(dist)) / 2, 0, 1)[band]
    if not small:
        edge_t = band & ~np.roll(band, 1, axis=0)
        edge_b = leather & ~band & np.roll(band, 1, axis=0)
        alb[edge_t] = WORN * 1.05
        alb[edge_b] = alb[edge_b] * 0.4
        stx = dx + w - 22
        scy = centre[stx]
        stud = np.hypot(yy - scy, xx - stx) <= 3.4
        alb[stud] = BRASS
        hgt[stud] += 2.0 + 2.5 * np.clip(1 - np.hypot(yy - scy, xx - stx) / 3.4, 0, 1)[stud]
    img = lit(alb, hgt, amb=0.6 if small else 0.56)
    # lacing on the spine: X-shaped cords, sheared with the face, entering holes at the hinge
    groups = [0.5] if small else [0.16, 0.44, 0.86]
    arm = 2 if small else 10
    def to_screen(u, v):                                               # spine-face coords -> screen
        return int(round(u)), int(round(v + (dx - u) / dx * dy))
    for f in groups:
        g = int(h * f)
        if abs(g - sy) < arm + 6:
            continue
        for (u0, v0, u1, v1) in [(1.5, g - arm, dx - 2.5, g + arm), (dx - 2.5, g - arm, 1.5, g + arm)]:
            for q in np.linspace(0, 1, 4 * (2 * arm + dx)):
                x, y = to_screen(u0 + (u1 - u0) * q, v0 + (v1 - v0) * q)
                if 0 < y < H - 1 and 0 <= x < W - 1 and west[y, x]:
                    if not small and west[y + 1, x]:
                        img[y + 1, x] = np.minimum(img[y + 1, x], DARK * 0.9)
                    img[y, x] = CORD * (1.2 if u1 > u0 else 0.95)
        if not small:
            for v in (g - arm, g + arm):                               # holes in the cover by the hinge
                img[v, dx + 2:dx + 4] = DARK * 0.55
    put(out, 0, 0, img, leather)
    return out


def deckel():
    return journal()


def knopf():
    """The same journal, small, as the button."""
    return journal(w=17, h=14, dx=4, dy=6, small=True)


def deckle_mask(h, w, amp=1.6):
    """A sheet with torn, uneven edges (Büttenrand)."""
    m = np.ones((h, w), bool)
    for y in range(h):
        m[y, :int(abs(noise(1, 1, 0)[0, 0]) * 0 + rng.integers(0, 3))] = False
        m[y, w - rng.integers(0, 3):] = False
    for x in range(w):
        m[:rng.integers(0, 3), x] = False
        m[h - rng.integers(0, 3):, x] = False
    return ndi.binary_opening(m, np.ones((2, 1))) & ndi.binary_opening(m, np.ones((1, 2))) | (ndi.binary_erosion(m, iterations=3))


def seite():
    """Opened: one deckle-edged page lying on the inside of the leather cover, laced at the top."""
    h, w = 236, 156
    out = np.zeros((h, w, 4), np.uint8)
    cm = rounded(h - 2, w - 2, 6)
    alb, hgt = worn_leather(h - 2, w - 2, cm)
    put(out, 2, 2, lit(alb * 0.9, hgt), cm)
    # page block under the page: thick, ragged at the bottom
    ph, pw, py, px = h - 26, w - 14, 14, 6
    pb, pm = page_block(7, pw - 2)
    put(out, py + ph - 1, px + 1, pb, pm)
    # the page: old paper, browned and deckled edges, slight curve up from the binding
    pmask = deckle_mask(ph, pw)
    yy, xx = np.mgrid[0:ph, 0:pw]
    d = ndi.distance_transform_edt(pmask)
    age = np.clip(1 - d / 7, 0, 1) ** 1.5
    palb = PAPER * (1 + 0.04 * noise(ph, pw, 4)[..., None])
    palb = palb * (1 - 0.5 * age[..., None]) + PAGE_OLD * 0.5 * age[..., None]
    spots = noise(ph, pw, 2.5) > 0.62                                 # foxing: small age spots
    palb[spots] = palb[spots] * 0.93
    phgt = 3.0 * (1 - np.exp(-yy / 18.0)) + 0.03 * noise(ph, pw, 2)
    put(out, py, px, lit(palb, phgt, amb=0.82, k=0.2, steps=24), pmask)
    # binding at the top: the cord lacing through the fold, X stitches
    for gx in (24, w // 2, w - 24):
        for t in range(-5, 6):
            for k in (-1, 1):
                y, x = 9 + int(round(k * t * 0.6)), gx + t
                out[y, x, :3] = CORD
                out[y, x, 3] = 255
    out[py:py + 2, px:px + pw, :3] = (out[py:py + 2, px:px + pw, :3] * 0.85).astype(np.uint8)
    return out


def schatten(w, h, blur=4.0, alpha=0.55):
    m = np.zeros((h + 16, w + 16))
    m[8:8 + h, 8:8 + w] = rounded(h, w, 8)
    m = ndi.gaussian_filter(m, blur)
    a = np.zeros(m.shape + (4,), np.uint8)
    a[..., :3] = (18, 14, 14)
    a[..., 3] = (np.round(m * alpha * 6) / 6 * 255).astype(np.uint8)
    return a


def mohn_knopf():
    img = np.zeros((7, 7, 4), np.uint8)
    yy, xx = np.mgrid[0:7, 0:7]
    ang = np.arctan2(yy - 3, xx - 3)
    d = np.hypot(yy - 3, xx - 3)
    petal = d <= 3.2 * (0.82 + 0.18 * np.cos(4 * ang + 0.6))
    alb = np.zeros((7, 7, 3))
    alb[petal] = np.array([196, 60, 48])
    alb[d <= 1] = INK * 0.8
    put(img, 0, 0, lit(alb, 1.5 * np.clip(1 - d / 3.2, 0, 1), amb=0.7, k=0.5), petal)
    return img


DOODLES = {
    'kamera': [".........", "...xxx...", ".xxxxxxx.", ".x..x..x.", ".x.x.x.x.", ".x..x..x.", ".xxxxxxx.", ".........", "........."],
    'haus': ["....x....", "...x.x...", "..x...x..", ".x.....x.", "..x...x..", "..x.x.x..", "..x.x.x..", "..xxxxx..", "........."],
    'schritte': [".........", ".xx......", ".xx......", "..x...xx.", "......xx.", ".xx....x.", ".xx......", "..x......", "........."],
    'zurueck': [".........", "...x.....", "..x......", ".xxxxxx..", "..x....x.", "...x...x.", ".......x.", "......x..", "........."],
}


def kritzel():
    names = list(DOODLES)
    img = np.zeros((9, 9 * len(names), 4), np.uint8)
    for i, n in enumerate(names):
        for y, row in enumerate(DOODLES[n]):
            for x, c in enumerate(row):
                if c == 'x':
                    img[y, i * 9 + x] = (*INK, 255)
    return img


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    parts = [('buch_knopf', knopf), ('buch_deckel', deckel), ('buch_seite', seite), ('mohn_knopf', mohn_knopf),
             ('kritzel', kritzel), ('buch_schatten', lambda: schatten(140, 170)),
             ('buch_schatten_offen', lambda: schatten(154, 234)), ('buch_knopf_schatten', lambda: schatten(16, 16, 1.2, 0.5))]
    for name, fn in parts:
        Image.fromarray(fn()).save(os.path.join(OUT, name + '.png'))
    print('ok')
