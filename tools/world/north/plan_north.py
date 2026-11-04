#!/usr/bin/env python3
"""Plan sketch of the north (Yukimine-toge) for the approval page: the new band above today's world (north
coordinates y 0..HN, today's y 0 = HN) with today's top edge rendered for real underneath.
python3 plan_north.py WORLD_DIR out.png"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.interpolate import splprep, splev

HN = 1200                     # rows the world grows upward
W = 1800
SHOW = 600                    # rows of today's world shown under the plan
S = 0.6                       # output scale

PLACES = {                    # number: (x, y in north coordinates, label)
    1: (275, 1170, 'Felstor'),
    2: (620, 980, 'Nadelwald'),
    3: (330, 860, 'Holzfällerhütte'),
    4: (130, 640, 'Höhle'),
    5: (560, 560, 'Schlucht mit Steg'),
    6: (520, 330, 'Serpentinen'),
    7: (800, 400, 'Aussicht'),
    8: (470, 110, 'Pass'),
    9: (1250, 650, 'Bergsee + Wasserfall'),
    10: (1320, 1050, 'Flussweg'),
}
TRAILS = {
    'kogarashi': [(275, 1200), (282, 1150), (262, 1060), (300, 960), (330, 900)],
    'hoehle': [(300, 830), (240, 760), (170, 700), (140, 660)],
    'schlucht': [(360, 820), (430, 740), (470, 660), (540, 600), (560, 560)],
    'serpentine': [(560, 540), (640, 500), (560, 450), (450, 420), (540, 360), (640, 320), (560, 260),
                   (460, 230), (520, 170), (470, 110)],
    'aussicht': [(640, 500), (720, 470), (800, 420)],
    'see': [(800, 420), (900, 470), (1010, 560), (1120, 640), (1190, 700)],
    'fluss': [(1290, 760), (1330, 900), (1310, 1050), (1350, 1200), (1340, 1500), (1340, 1820)],
}


def curve(pts, n=200):
    p = np.array(pts, float).T
    tck, _ = splprep(p, s=0, k=min(3, len(pts) - 1))
    return np.array(splev(np.linspace(0, 1, n), tck)).T


def noise(h, w, scale, seed):
    r = np.random.default_rng(seed).random((h // 8 + 2, w // 8 + 2))
    n = ndi.zoom(ndi.gaussian_filter(r, scale / 8), 8, order=1)[:h, :w]
    return (n - n.mean()) / (n.std() + 1e-6)


def blob(cx, cy, rx, ry, wob, seed):
    yy, xx = np.mgrid[0:HN, 0:W]
    n = noise(HN, W, 40, seed)
    return ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 < 1 + wob * n


def today(d):
    """Today's top rows as they look in the game: ground, flowers, every standing thing (frame 0)."""
    import json
    g = np.array(Image.open(os.path.join(d, 'ground.png')).convert('RGB'))[:SHOW, :W]
    fl = np.array(Image.open(os.path.join(d, 'flowers.png')).convert('RGBA'))[:SHOW, :W]
    m = fl[..., 3] > 0
    g[m] = fl[m][:, :3]
    pil = Image.fromarray(g)
    w = json.load(open(os.path.join(d, 'world.json')))
    root = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'assets', 'world', 'sprites')
    for s in sorted(w['sprites'], key=lambda s: s['foot']):
        if s['y'] > SHOW:
            continue
        p = os.path.join(root, s['name'] + '.png')
        if os.path.exists(p):
            a = Image.open(p).convert('RGBA').crop((0, 0, s['w'], s['h']))
            pil.alpha_composite(a, (s['x'], s['y'])) if pil.mode == 'RGBA' else None
            if pil.mode != 'RGBA':
                pil = pil.convert('RGBA')
                pil.alpha_composite(a, (s['x'], s['y']))
    return np.array(pil.convert('RGB'))


def main(world, out):
    yy, xx = np.mgrid[0:HN, 0:W]
    up = 1 - yy / HN                                                  # 0 at today's edge .. 1 at the top
    img = np.zeros((HN, W, 3))
    snow_lo, snow_hi = np.array([176, 178, 184]), np.array([236, 239, 244])
    img[:] = snow_lo + (snow_hi - snow_lo) * np.clip(up * 1.3, 0, 1)[..., None]
    n1, n2 = noise(HN, W, 60, 1), noise(HN, W, 25, 2)
    rock = n1 + 0.6 * n2 + 5 * (up - 0.62) > 0.3                     # bare rock grows in up the slopes
    peaks = (yy < 250 + 70 * n1) & (np.abs(xx - 480) > 170 + 50 * n2)   # the ridge, open only at the pass
    east = 1 / (1 + np.exp(-(xx - 900) / 90.0))                       # above the dark east wood the needle wood reaches higher
    wood = n1 + 0.5 * n2 > -0.9 + 3.2 * (up - 0.15 - 0.2 * east)      # single firs below thicken into the needle wood
    clearing = blob(330, 860, 120, 85, 0.25, 3)
    lake = blob(1250, 680, 150, 95, 0.18, 4)
    ice = lake & (xx + 0.6 * (yy - 680) < 1220 + 30 * n2)              # half frozen: the west half
    gorge = np.zeros((HN, W), bool)
    gx = np.arange(0, 980)
    gy = 590 + 40 * np.sin(gx / 160.0) - 0.04 * gx + 8 * noise(1, 980 + 16, 8, 5)[0, :980]
    for x, y in zip(gx, gy):
        half = (13 + 6 * np.sin(x / 47.0)) * min(1.0, x / 60.0 + 0.4, (980 - x) / 120.0)   # runs out at its east end
        gorge[int(y - half):int(y + half), x] = True
    path = np.zeros((HN, W), bool)
    im = Image.new('L', (W, HN), 0)
    d0 = ImageDraw.Draw(im)
    for k, pts in TRAILS.items():
        c = curve(pts, 400)
        d0.line([tuple(p) for p in c], fill=255, width=9)
    path = np.array(im) > 0
    img[wood & ~clearing] = [52, 70, 62]
    img[rock & ~wood] = [118, 120, 128]
    img[peaks] = [92, 94, 104]
    img[peaks & (n2 > 0.4)] = [222, 226, 232]
    img[gorge] = [34, 36, 46]
    img[gorge & (np.abs(yy - np.interp(xx, gx, gy)) < 3)] = [150, 176, 196]   # frozen brook down in it
    img[lake] = [70, 110, 140]
    img[ice] = [186, 210, 226]
    fall = (np.abs(xx - 1250) < 10) & (yy > 520) & (yy < 590)
    img[fall] = [214, 232, 244]
    riv = Image.new('L', (W, HN + SHOW), 0)
    ImageDraw.Draw(riv).line([tuple(p) for p in curve([(1250, 770), (1270, 900), (1230, 1050), (1265, 1200),
                                                        (1260, 1500)], 300)], fill=255, width=16)
    riv = np.array(riv) > 0
    img[riv[:HN] & ~lake] = [70, 110, 140]
    img[ndi.binary_dilation(path, iterations=1)] = [120, 96, 70]
    img[path] = [206, 186, 150]
    plan = np.clip(img, 0, 255).astype(np.uint8)

    b = today(world)
    full = np.concatenate([plan, b], 0)
    pil = Image.fromarray(full)
    d = ImageDraw.Draw(pil)
    d.line([(0, HN), (W, HN)], fill=(196, 60, 52), width=4)
    f = ImageFont.truetype('/system/fonts/Roboto-Regular.ttf', 34)
    fb = ImageFont.truetype('/system/fonts/Roboto-Regular.ttf', 32)
    tw = d.textlength('heutiger Rand der Welt', font=f)
    d.rectangle([8, HN + 8, 24 + tw, HN + 52], fill=(30, 28, 32))
    d.text((16, HN + 10), 'heutiger Rand der Welt', fill=(255, 220, 210), font=f)
    for n, (x, y, label) in PLACES.items():
        d.ellipse([x - 24, y - 24, x + 24, y + 24], fill=(196, 60, 52), outline=(30, 20, 20), width=3)
        tw = d.textlength(str(n), font=fb)
        d.text((x - tw / 2, y - 18), str(n), fill=(255, 255, 255), font=fb)
    # the Steinbruecke of the east wood the river path ends at
    bx, by = 1340, HN + 620
    if by < HN + SHOW:
        d.ellipse([bx - 18, by - 18, bx + 18, by + 18], outline=(255, 255, 255), width=4)
    pil = pil.resize((int(W * S), int((HN + SHOW) * S)), Image.LANCZOS)
    pil.save(out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
