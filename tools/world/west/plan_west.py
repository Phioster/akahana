#!/usr/bin/env python3
"""Plan sketch of the west (the village) for the approval page: the new 900 px strip left of today's world
(west coordinates x 0..WW, today's x 0 = WW) with today's west edge rendered for real beside it.
python3 plan_west.py WORLD_NOW.png out.png   (WORLD_NOW: today's world composited, 1800 x 4800)"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.interpolate import splprep, splev

WW = 900                      # columns the world grows to the west
H = 4800
Y0, Y1 = 1200, 4800           # rows shown (the north band above is mountains, it only runs on)
SHOW = 520                    # columns of today's world shown beside the plan
S = 0.34

PLACES = {                    # number: (x, y in west coordinates, label)
    1: (820, 2300, 'Dorfeingang'),
    2: (520, 2330, 'Dorfplatz mit Brunnen'),
    3: (430, 2130, 'Häuser + Gärten'),
    4: (640, 2560, 'Gewächshaus'),
    5: (300, 2470, 'Steinmetz'),
    6: (420, 1880, 'Dorfschrein'),
    7: (600, 1700, 'Obstwiese'),
    8: (200, 2950, 'alte Reisfelder'),
    9: (480, 3300, 'Wassermühle'),
    10: (120, 2250, 'Bambushain'),
}
HOUSES = [(380, 2180), (560, 2150), (690, 2230), (300, 2320), (410, 2420), (720, 2400), (540, 2490),
          (250, 2610), (430, 2640)]
TRAILS = {
    'eingang': [(980, 2292), (900, 2300), (820, 2300), (700, 2315), (600, 2330), (520, 2330)],
    'nord': [(520, 2330), (500, 2240), (450, 2120), (430, 1990), (420, 1880)],
    'obst': [(450, 2050), (540, 1880), (600, 1700), (700, 1560), (860, 1450), (940, 1420)],
    'sued': [(520, 2330), (560, 2440), (630, 2540), (520, 2700), (380, 2820), (230, 2950), (300, 3150),
             (480, 3300), (700, 3420), (960, 3500)],
    'west': [(520, 2330), (380, 2360), (300, 2450), (200, 2330), (120, 2250)],
}


def curve(pts, n=300):
    p = np.array(pts, float).T
    tck, _ = splprep(p, s=0, k=min(3, len(pts) - 1))
    return np.array(splev(np.linspace(0, 1, n), tck)).T


def noise(h, w, scale, seed):
    r = np.random.default_rng(seed).random((h // 8 + 2, w // 8 + 2))
    n = ndi.zoom(ndi.gaussian_filter(r, scale / 8), 8, order=1)[:h, :w]
    return (n - n.mean()) / (n.std() + 1e-6)


def main(now, out):
    h = Y1 - Y0
    yy, xx = np.mgrid[Y0:Y1, 0:WW]
    n1, n2 = noise(h, WW, 50, 1), noise(h, WW, 18, 2)
    rng = np.random.default_rng(3)
    img = np.zeros((h, WW, 3))
    img[:] = [112, 122, 92]                                            # meadow
    snow = yy < 1560 + 60 * n1                                         # Kogarashi's snow runs on to the west
    img[snow] = [214, 216, 220]
    wood = (yy < 1900 + 80 * n1) & ((xx < 260 + 80 * n2) | (yy < 1650 + 60 * n2))   # fir wood north-west
    img[wood] = [56, 72, 62]
    img[snow & wood] = [150, 160, 158]                                 # snowy firs
    bamboo = ((xx - 120) / 130.0) ** 2 + ((yy - 2280) / 220.0) ** 2 < 1 + 0.3 * n2
    img[bamboo] = [96, 128, 78]
    orchard = ((xx - 610) / 190.0) ** 2 + ((yy - 1720) / 140.0) ** 2 < 1 + 0.25 * n1
    img[orchard & ~wood] = [104, 124, 80]
    pts = rng.random((60, 2)) * [380, 280] + [420, 1580]
    poppy = (xx > 700 + 80 * n1) & (yy > 1560) & (yy < 3150 + 50 * n1)  # the Mohnfeld reaches in from the east
    spk = rng.random((h, WW)) < 0.35
    img[poppy & spk] = [176, 48, 52]
    fields = (np.abs(xx - 240 - 40 * n2) < 170) & (yy > 2830) & (yy < 3120)
    terr = fields & (((yy - 2830) // 36) % 2 == 0)
    img[fields] = [120, 116, 86]
    img[terr] = [134, 140, 112]
    brook = np.zeros((h, WW), bool)
    im = Image.new('L', (WW, h), 0)
    ImageDraw.Draw(im).line([tuple(p - [0, Y0]) for p in curve([(60, 3000), (250, 3180), (470, 3290),
                                                                (700, 3380), (900, 3430)])], fill=255, width=14)
    brook = np.array(im) > 0
    img[brook] = [70, 104, 130]
    for (x, y) in pts:
        if orchard[int(y - Y0), int(x)] and not wood[int(y - Y0), int(x)]:
            img[int(y - Y0) - 5:int(y - Y0) + 5, int(x) - 5:int(x) + 5] = [78, 98, 60]
    for (x, y) in rng.random((70, 2)) * [860, 1250] + [20, 3520]:       # the south's meadow runs on: lone trees
        img[int(y - Y0) - 6:int(y - Y0) + 6, int(x) - 6:int(x) + 6] = [74, 96, 62]
    pim = Image.new('L', (WW, h), 0)
    d0 = ImageDraw.Draw(pim)
    for pts_ in TRAILS.values():
        d0.line([tuple(p - [0, Y0]) for p in curve(pts_)], fill=255, width=10)
    path = np.array(pim) > 0
    img[ndi.binary_dilation(path, iterations=1)] = [120, 96, 70]
    img[path] = [196, 178, 146]
    plan = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    d = ImageDraw.Draw(plan)
    for (x, y) in HOUSES:                                             # garden plot, house, mossy roof
        d.rectangle([x - 55, y - 50 - Y0, x + 55, y + 50 - Y0], fill=(120, 132, 88), outline=(150, 140, 120), width=3)
        d.rectangle([x - 28, y - 26 - Y0, x + 28, y + 26 - Y0], fill=(84, 66, 52))
        d.rectangle([x - 28, y - 26 - Y0, x + 28, y - 6 - Y0], fill=(70, 74, 62))
    gx, gy = 640, 2560
    d.rectangle([gx - 42, gy - 32 - Y0, gx + 42, gy + 32 - Y0], fill=(170, 196, 186), outline=(60, 50, 40), width=4)
    d.rectangle([300 - 34, 2470 - 22 - Y0, 300 + 34, 2470 + 22 - Y0], fill=(110, 104, 98), outline=(70, 56, 44), width=4)
    d.ellipse([520 - 14, 2330 - 14 - Y0, 520 + 14, 2330 + 14 - Y0], fill=(120, 120, 126), outline=(60, 60, 66), width=4)
    d.rectangle([420 - 30, 1880 - 24 - Y0, 420 + 30, 1880 + 24 - Y0], fill=(96, 70, 56))
    d.rectangle([480 - 22, 3300 - 20 - Y0, 480 + 22, 3300 + 20 - Y0], fill=(96, 76, 58))
    today = Image.open(now).convert('RGBA').crop((0, Y0, SHOW, Y1))
    full = Image.new('RGBA', (WW + SHOW, h))
    full.paste(plan, (0, 0))
    full.paste(today, (WW, 0))
    d = ImageDraw.Draw(full)
    d.line([(WW, 0), (WW, h)], fill=(196, 60, 52), width=6)
    f = ImageFont.truetype('/system/fonts/Roboto-Regular.ttf', 52)
    for n, (x, y, _) in PLACES.items():
        r = 40
        d.ellipse([x - r, y - Y0 - r, x + r, y - Y0 + r], fill=(196, 60, 52), outline=(30, 20, 20), width=4)
        tw = d.textlength(str(n), font=f)
        d.text((x - tw / 2, y - Y0 - 30), str(n), fill=(255, 255, 255), font=f)
    fx, fy = WW + 222, 2292 - Y0                                       # today's camp fire (the start)
    d.ellipse([fx - 30, fy - 30, fx + 30, fy + 30], outline=(255, 255, 255), width=6)
    full = full.resize((int((WW + SHOW) * S), int(h * S)), Image.LANCZOS)
    full.convert('RGB').save(out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
