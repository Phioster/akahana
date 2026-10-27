#!/usr/bin/env python3
"""Plan sketch of zone 4 (the lake in the reeds) for the approval page. Zone coordinates, 900 x 800.

The shore grows out of overlapping waves round a wide centre instead of a few hand-set points: bays and
spits of different sizes, a backwater, reed islands out in the water, a reed belt now thin, now deep.
The trails keep to the far edges; the human things sit half in the reeds."""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi
from scipy.interpolate import splprep, splev

W, H, S = 900, 800, 2
rng = np.random.default_rng(17)
yy, xx = np.mgrid[0:H, 0:W]


def curve(pts, n=400):
    p = np.array(pts, float).T
    tck, _ = splprep(p, s=0, k=min(3, p.shape[1] - 1))
    return np.array(splev(np.linspace(0, 1, n), tck)).T


# the lake as a field: inside where the wobbled distance from the centre is below 1
cx, cy, rx, ry = 458, 360, 340, 250
ang = np.arctan2((yy - cy) / ry, (xx - cx) / rx)
rad = np.hypot((xx - cx) / rx, (yy - cy) / ry)
wob = np.zeros_like(ang)
for k in range(2, 9):                                           # waves round the shore, smaller ones shorter
    wob += rng.uniform(0.02, 0.09) / (k ** 0.35) * np.sin(k * ang + rng.uniform(0, 6.3))
for (a0, depth, width) in [(2.5, 0.18, 0.22), (-0.6, 0.14, 0.3), (1.2, -0.12, 0.25), (-2.2, 0.1, 0.18)]:
    d = np.angle(np.exp(1j * (ang - a0)))
    wob -= depth * np.exp(-(d / width) ** 2)                    # deep bays (+) and spits (-)
fine = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 9)
fine /= fine.std()
lake = rad < 1 + wob + 0.025 * fine
back = ((xx - 140) / 55) ** 2 + ((yy - 610) / 32) ** 2 < 1 + 0.15 * fine   # a backwater to the south-west
lake |= back | ((np.abs(yy - 560 - 0.25 * (xx - 160)) < 7) & (xx > 140) & (xx < 230))   # joined by a channel
lake = ndi.binary_opening(lake, iterations=2)
belt_w = 7 + 14 * np.clip(0.5 + 0.5 * ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 20) * 3, 0, 1)
dist_out = ndi.distance_transform_edt(~lake)
dist_in = ndi.distance_transform_edt(lake)
reeds = (dist_out > 0) & (dist_out < belt_w)
island = ((xx - 470) / 34) ** 2 + ((yy - 380) / 22) ** 2 < 1 + 0.2 * fine
reed_isles = np.zeros_like(lake)
for (x0, y0, r0) in [(250, 300, 14), (650, 470, 11), (700, 250, 9), (330, 470, 10), (580, 200, 8)]:
    reed_isles |= ((xx - x0) / r0) ** 2 + ((yy - y0) / (r0 * 0.7)) ** 2 < 1 + 0.3 * fine
shallow = lake & (dist_in < 12)
puddles = np.zeros_like(lake)                                    # small pools scattered round the lake
tries = 0
while puddles.max() == 0 or (tries < 400 and ndi.label(puddles)[1] < 14):
    tries += 1
    x0, y0 = int(rng.integers(60, W - 60)), int(rng.integers(40, 690))
    near = dist_out[y0, x0]
    if not (22 < near < 90) or rng.random() > 1.2 - near / 90:
        continue
    r0 = rng.uniform(4, 11)
    blob = ((xx - x0) / r0) ** 2 + ((yy - y0) / (r0 * rng.uniform(0.5, 0.8))) ** 2 < 1 + 0.4 * fine
    if (ndi.binary_dilation(puddles, iterations=10) & blob).any():
        continue
    puddles |= blob

img = np.zeros((H, W, 3), np.uint8)
img[:] = (92, 112, 78)
img[reeds] = (70, 92, 60)
img[lake] = (96, 128, 150)
img[shallow] = (120, 160, 180)
img[lake & reed_isles] = (70, 92, 60)
img[ndi.binary_dilation(puddles, iterations=2) & ~puddles] = (70, 92, 60)
img[puddles] = (120, 160, 180)
img[island] = (92, 112, 78)
img[ndi.binary_dilation(island, iterations=5) & ~island & lake] = (70, 92, 60)
pil = Image.fromarray(img).resize((W * S, H * S), Image.NEAREST)
d = ImageDraw.Draw(pil)
f = ImageFont.truetype('/system/fonts/Roboto-Regular.ttf', 26)


def P(c, w, col):
    d.line([(x * S, y * S) for x, y in c], fill=col, width=int(w * S), joint='curve')


def M(x, y, r, c, n):
    d.ellipse([(x - r) * S, (y - r) * S, (x + r) * S, (y + r) * S], fill=c, outline=(30, 30, 30), width=2)
    if n:
        d.text((x * S - 8, y * S - 15), n, fill=(20, 20, 20), font=f)


for (x0, x1) in [(410, 418), (520, 505)]:                      # the brooks from zone 3 flow in
    P(curve([(x0, -5), ((x0 + x1) / 2 + 6, 50), (x1, 140)], 60), 9, (96, 128, 150))
trails = {'west': [(330, -5), (230, 40), (110, 90), (48, 200), (36, 360), (58, 520), (120, 690), (260, 735),
                   (450, 748)],
          'ost': [(730, -5), (800, 60), (858, 170), (866, 340), (850, 520), (790, 680), (640, 738), (450, 748)],
          'mitte': [(468, -5), (472, 50), (470, 92)],
          'zur_bank': [(120, 690), (190, 655)], 'zur_huette': [(850, 520), (800, 515)]}
trails['west'][-3:] = [(120, 660), (250, 690), (450, 700)]       # the round path keeps above the reeds
trails['ost'][-3:] = [(790, 640), (640, 690), (450, 700)]
wc = curve(trails['west'], 300)                                 # the bench path starts on the round path itself
trails['zur_bank'][0] = tuple(wc[np.hypot(*(wc - trails['zur_bank'][1]).T).argmin()])
for k, pts in trails.items():
    P(curve(pts, 300) if len(pts) > 2 else np.array(pts, float), 4, (205, 190, 160))
for (x, y) in [(330, 240), (352, 262), (600, 430), (585, 455), (410, 520), (620, 190), (180, 400), (760, 380)]:
    d.ellipse([(x - 13) * S, (y - 7) * S, (x + 13) * S, (y + 7) * S], outline=(150, 190, 140), width=4)
d.rectangle([465 * S, 92 * S, 477 * S, 150 * S], fill=(170, 130, 90), outline=(90, 60, 40), width=3)   # jetty, out of the reeds
d.ellipse([440 * S, 118 * S, 460 * S, 136 * S], fill=(140, 100, 70))                                   # boat in the reeds
M(458, 92, 8, (255, 210, 120), 'L')
M(470, 378, 12, (90, 150, 90), 'T')                                                              # the island's tree
d.rectangle([782 * S, 505 * S, 812 * S, 530 * S], fill=(200, 160, 120), outline=(90, 60, 40), width=3)   # hut, half in the reeds
d.text((788 * S, 500 * S), 'H', fill=(20, 20, 20), font=f)
d.rectangle([760 * S, 530 * S, 770 * S, 560 * S], fill=(170, 130, 90), outline=(90, 60, 40), width=2)   # its own little landing
M(195, 650, 9, (200, 200, 200), 'B')
for (x, y) in [(170, 640), (85, 250), (820, 120), (845, 620), (640, 700), (300, 690), (60, 640), (800, 420),
               (100, 420), (760, 200)]:
    if not (lake | reeds)[y, x]:                               # trees only on land
        M(x, y, 12, (90, 150, 90), 'T')
for (x, y) in [(330, 330), (600, 520), (140, 450), (720, 300), (450, 700), (780, 640)]:
    M(x, y, 7, (255, 240, 140), 'G')
for (x, y) in [(100, 160), (690, 610), (380, 600), (830, 300), (220, 580)]:
    M(x, y, 6, (110, 140, 90), 'F')
# the world's southern edge: no wall of firs but a sea of reeds turning into marsh and open water that fades
# into thick mist at the border - one can't go on, and one doesn't see where the world stops
edge = 700 + 14 * np.sin(np.arange(W) / 53.0) + 8 * np.sin(np.arange(W) / 17.0 + 1)
for i in range(W):
    e = int(edge[i])
    d.line([(i * S, (e + 22) * S), (i * S, H * S)], fill=(70, 92, 60), width=S)             # reeds, ever denser
    d.line([(i * S, (e + 62 + 6 * np.sin(i / 23.0)) * S), (i * S, H * S)], fill=(96, 128, 150), width=S)   # open water
fog = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
fd = ImageDraw.Draw(fog)
for y in range(720, H):
    a = int(np.clip((y - 720) / 80, 0, 1) ** 1.3 * 210)
    fd.rectangle([0, y * S, W * S, (y + 1) * S - 1], fill=(214, 214, 212, a))
pil.paste(fog, (0, 0), fog)
d = ImageDraw.Draw(pil)
d.text((330 * S, 735 * S), 'Schilfmeer, Sumpf, Nebel', fill=(30, 40, 30), font=f)
for x0 in (0, W - 14):
    d.rectangle([x0 * S, 0, (x0 + 14) * S, H * S], fill=(40, 60, 50))
d.text((300 * S, 380 * S), 'See', fill=(235, 240, 245), font=f)
pil.save(sys.argv[1])
