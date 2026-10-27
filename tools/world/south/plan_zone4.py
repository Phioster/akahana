#!/usr/bin/env python3
"""Plan sketch of zone 4 (the lake in the reeds) for the approval page. Zone coordinates, 900 x 800."""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.interpolate import splprep, splev

W, H, S = 900, 800, 2
img = Image.new('RGB', (W * S, H * S), (92, 112, 78))
d = ImageDraw.Draw(img)
f = ImageFont.truetype('/system/fonts/Roboto-Regular.ttf', 26)


def curve(pts, n=400, closed=False):
    p = np.array(pts + ([pts[0]] if closed else []), float).T
    tck, _ = splprep(p, s=0, k=min(3, p.shape[1] - 1), per=closed)
    return np.array(splev(np.linspace(0, 1, n), tck)).T


def P(c, w, col):
    d.line([(x * S, y * S) for x, y in c], fill=col, width=int(w * S), joint='curve')


def poly(c, col):
    d.polygon([(x * S, y * S) for x, y in c], fill=col)


def M(x, y, r, c, n):
    d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=c, outline=(30, 30, 30), width=2)
    if n:
        d.text((x * S - 8, y * S - 15), n, fill=(20, 20, 20), font=f)


lake = curve([(390, 78), (470, 62), (545, 108), (640, 118), (705, 190), (690, 255), (752, 318), (770, 392),
              (715, 420), (668, 400), (628, 462), (560, 548), (448, 586), (360, 548), (300, 470), (262, 418),
              (215, 372), (232, 292), (290, 226), (322, 140)], closed=True)   # bays, a spit, nothing even
shore = np.array([(x + (x - 470) * 0.09, y + (y - 330) * 0.11) for x, y in lake])
poly(shore, (78, 98, 66))                                   # reed belt
poly(lake, (120, 160, 180))                                 # shallow rim (wading)
deep = np.array([(470 + (x - 470) * 0.86, 330 + (y - 330) * 0.84) for x, y in lake])
poly(deep, (96, 128, 150))
gap = lambda x, y, r: d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=(120, 160, 180))
for (x, y) in [(470, 66), (335, 565), (785, 400)]:            # where the paths reach the water: no reeds
    gap(x, y, 22)
for (x0, y0) in [(410, 0), (520, 0)]:                         # the brooks from zone 3 flow in
    P(curve([(x0, -5), (x0 + 8, 40), (x0 + 15, 90)]), 9, (96, 128, 150))
d.ellipse([470 * S, 330 * S, 530 * S, 380 * S], fill=(92, 112, 78), outline=(78, 98, 66), width=10)
for (x, y) in [(340, 250), (372, 276), (600, 440), (585, 470), (410, 480), (600, 170)]:
    d.ellipse([(x - 14) * S, (y - 8) * S, (x + 14) * S, (y + 8) * S], outline=(150, 190, 140), width=4)
trails = {'west': [(330, -5), (280, 110), (175, 220), (120, 350), (160, 500), (250, 610), (300, 650)],
          'sued': [(300, 650), (420, 668), (540, 652), (640, 600), (700, 520)],
          'ost': [(730, -5), (770, 110), (800, 220), (840, 340), (830, 440), (760, 480), (700, 520)],
          'mitte': [(468, -5), (468, 40), (470, 66)],
          'ufer_s': [(300, 650), (330, 575)], 'ufer_o': [(830, 440), (790, 405)]}
for k, pts in trails.items():
    P(curve(pts, 200) if len(pts) > 3 else np.array(pts, float), 4, (205, 190, 160))
d.rectangle([462 * S, 66 * S, 476 * S, 130 * S], fill=(170, 130, 90), outline=(90, 60, 40), width=3)   # jetty
d.ellipse([480 * S, 112 * S, 500 * S, 132 * S], fill=(140, 100, 70))                                   # boat
M(456, 70, 8, (255, 210, 120), 'L')
M(500, 352, 13, (90, 150, 90), 'T')                                                                # island tree
for (x, y) in [(150, 560), (250, 650), (690, 640), (840, 200), (110, 200), (820, 560)]:
    M(x, y, 13, (90, 150, 90), 'T')
M(520, 672, 9, (200, 200, 200), 'B')
M(712, 474, 12, (200, 160, 120), 'H')
for (x, y) in [(330, 300), (600, 480), (190, 430), (690, 300), (450, 700), (780, 650)]:
    M(x, y, 7, (255, 240, 140), 'G')
for (x, y) in [(260, 200), (650, 520), (380, 560), (720, 330)]:
    M(x, y, 6, (110, 140, 90), 'F')
for i in range(0, W, 14):                                   # the world's southern edge: a fir wood
    d.ellipse([(i - 8) * S, (760 + 8 * np.sin(i / 37)) * S, (i + 8) * S, 812 * S], fill=(40, 60, 50))
for x0 in (0, W - 14):
    d.rectangle([x0 * S, 0, (x0 + 14) * S, H * S], fill=(40, 60, 50))
d.text((440 * S, 300 * S), 'See', fill=(235, 240, 245), font=f)
img.save(sys.argv[1])
