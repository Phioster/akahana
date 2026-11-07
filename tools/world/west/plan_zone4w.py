#!/usr/bin/env python3
"""Layout sketch for west zone 4 (plan step 65): rice terraces, the mill on the brook that runs on into today's
south brook, the bamboo grove, the west lake that today's map hints at with its water strip at the edge
(x 0..12, y 4085..4662), the fisherman's hut with its zigzag jetty through the irises, the teahouse.
    python3 plan_zone4w.py OUT.png"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.interpolate import splprep, splev

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
WW, Y0, Y1, SHOW = 900, 2150, 4800, 520
S = 0.36

BROOK_A = [(250, 3110), (330, 3190), (430, 3270), (520, 3330), (640, 3390), (780, 3430), (924, 3444)]   # -> today's brook A
BROOK_C = [(640, 3690), (720, 3730), (830, 3758), (924, 3766)]                                         # a spring -> brook C
LAKE = [(924, 4085), (860, 4060), (760, 4050), (650, 4075), (540, 4120), (450, 4200), (400, 4320), (410, 4460),
        (470, 4580), (580, 4650), (720, 4672), (850, 4668), (924, 4662)]
TERRACES = (60, 2830, 430, 3110)
PATHS = {
    'sued': [(470, 2770), (380, 2830), (300, 2900), (260, 3000), (300, 3080), (400, 3200), (470, 3290)],
    'muehle': [(470, 3290), (560, 3390), (680, 3470), (800, 3540), (924, 3560)],
    'see': [(560, 3400), (600, 3560), (620, 3800), (600, 3960), (580, 4040)],
    'ufer': [(580, 4040), (700, 4020), (820, 4030), (880, 4120), (900, 4300), (924, 4330)],
    'bambus': [(250, 2520), (180, 2400), (130, 2280)],
}
PLACES = {8: (240, 2970, 'alte Reisfelder (Furuta)'), 9: (475, 3300, 'Wassermühle (Suisha-goya)'),
          10: (120, 2250, 'Bambushain (Takeyabu)'), 11: (575, 4060, 'Fischerhütte + Zickzack-Steg'),
          12: (880, 4400, 'Teehaus am Wasser'), 13: (640, 3690, 'Quelle')}


def P(x, y):
    return (x * S, (y - Y0) * S)


def curve(pts, n=200, closed=False):
    p = np.array(pts + ([pts[0]] if closed else []), float).T
    tck, _ = splprep(p, s=0, k=min(3, p.shape[1] - 1), per=closed)
    return [P(*q) for q in np.array(splev(np.linspace(0, 1, n), tck)).T]


def main(out):
    Wp, Hp = int((WW + SHOW) * S), int((Y1 - Y0) * S)
    img = Image.new('RGB', (Wp, Hp), (120, 132, 104))
    d = ImageDraw.Draw(img)
    for y in range(Hp):                                          # pale meadow up north, the tall green grass south
        t = np.clip(((y / S + Y0) - 2950) / 250, 0, 1)
        c = tuple(int(a * (1 - t) + b * t) for a, b in zip((176, 170, 166), (104, 120, 84)))
        d.line([(0, y), (WW * S, y)], fill=c)
    now = Image.open(os.path.join(ROOT, 'build/preview/world_now.png')).crop((0, Y0, SHOW, Y1))
    img.paste(now.resize((int(SHOW * S), Hp)), (int(WW * S), 0))
    d.line([(WW * S, 0), (WW * S, Hp)], fill=(200, 60, 50), width=2)
    x0, y0, x1, y1 = TERRACES                                    # terraces: bands stepping down
    for k, yy in enumerate(range(y0, y1, 28)):
        sh = 18 * np.sin(k * 1.3)
        d.rounded_rectangle([P(x0 + sh, yy), P(x1 - 20 + sh, yy + 22)], 4,
                            fill=(124, 138, 120) if k % 2 else (98, 116, 112), outline=(70, 66, 52))
    d.ellipse([P(40, 2170), P(230, 2340)], fill=(78, 112, 64))   # bamboo
    lake = [(min(x, WW * S), y) for x, y in curve(LAKE, 300, closed=True)]
    d.polygon(lake, fill=(44, 62, 74), outline=(150, 138, 90))
    irises = curve([(520, 4110), (580, 4150), (640, 4200), (700, 4220)], 40)
    for q in irises:
        d.ellipse([q[0] - 5, q[1] - 3, q[0] + 5, q[1] + 3], fill=(96, 92, 150))
    jet = [P(575, 4075), P(560, 4120), P(600, 4150), P(585, 4195), P(625, 4225)]   # the zigzag jetty
    d.line(jet, fill=(150, 120, 80), width=3)
    for pts, wd in ((BROOK_A, 4), (BROOK_C, 3)):
        d.line(curve(pts), fill=(50, 66, 80), width=wd)
    for name, pts in PATHS.items():
        d.line(curve(pts), fill=(206, 190, 150), width=2)
    try:
        font = ImageFont.truetype('/system/fonts/RobotoStatic-Regular.ttf', 13)
        bold = ImageFont.truetype('/system/fonts/RobotoStatic-Regular.ttf', 14)
    except OSError:
        font = bold = ImageFont.load_default()
    for n, (x, y, label) in PLACES.items():
        cx, cy = P(x, y)
        d.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], fill=(196, 52, 44), outline=(255, 240, 230))
        d.text((cx, cy), str(n), fill='white', font=bold, anchor='mm')
        d.text((cx + 14, cy), label, fill=(20, 20, 20), font=font, anchor='lm', stroke_width=2, stroke_fill=(240, 236, 228))
    for (hx_, hy_) in ((380, 2180), (560, 2150), (690, 2230), (300, 2320), (410, 2420), (720, 2400), (540, 2490),
                       (250, 2610), (430, 2640)):
        d.rectangle([P(hx_ - 22, hy_ - 30), P(hx_ + 22, hy_ - 8)], fill=(80, 70, 62))
    d.rectangle([P(613, 2560), P(747, 2603)], fill=(90, 120, 110))
    for name, (x, y) in {'Dorf': (470, 2330), 'Gewächshaus': (680, 2630), 'Westsee': (640, 4380)}.items():
        d.text(P(x, y), name, fill=(250, 250, 250), font=bold, anchor='mm', stroke_width=2, stroke_fill=(40, 40, 40))
    img.save(out)


if __name__ == '__main__':
    main(sys.argv[1])
