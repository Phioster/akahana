"""The lake of zone 4 (zone coordinates, 900 x 800), shared by the plan sketch and the drawing: the water,
its shallow rim, the reed belt (now thin, now deep), reed islands, the island, the backwater and the small
pools round the lake. Grown from overlapping waves round a wide centre, seed 17 (the approved plan)."""
import numpy as np
from scipy import ndimage as ndi
from scipy.interpolate import splprep, splev

W, H = 900, 800


def curve(pts, n=400):
    p = np.array(pts, float).T
    tck, _ = splprep(p, s=0, k=min(3, p.shape[1] - 1))
    return np.array(splev(np.linspace(0, 1, n), tck)).T


def masks():
    yy, xx = np.mgrid[0:H, 0:W]
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
    ch = curve([(150, 606), (172, 600), (190, 584), (204, 586), (222, 572), (246, 560), (272, 546)], 200)   # a winding ditch,
    ch[:, 1] += 2.5 * np.sin(np.linspace(0, 9, len(ch)))                                    # not a ruled line
    from scipy.spatial import cKDTree
    dch = cKDTree(ch).query(np.stack([xx.ravel(), yy.ravel()], 1))[0].reshape(H, W)
    lake |= back | (dch < 3.2 + 0.8 * fine)
    lake = ndi.binary_opening(lake, iterations=2)
    belt_w = 7 + 14 * np.clip(0.5 + 0.5 * ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 20) * 3, 0, 1)
    dist_out = ndi.distance_transform_edt(~lake)
    dist_in = ndi.distance_transform_edt(lake)
    reeds = (dist_out > 0) & (dist_out < belt_w)
    island = ((xx - 470) / 34) ** 2 + ((yy - 380) / 22) ** 2 < 1 + 0.2 * fine
    reed_isles = np.zeros_like(lake)
    for (x0, y0, r0) in [(250, 300, 14), (650, 470, 11), (700, 250, 9), (330, 470, 10), (580, 200, 8),
                         (420, 250, 7), (520, 520, 9), (180, 480, 6)]:
        reed_isles |= ((xx - x0) / r0) ** 2 + ((yy - y0) / (r0 * 0.7)) ** 2 < 1 + 0.3 * fine
    shallow = lake & (dist_in < 12)
    puddles = np.zeros_like(lake)                                    # small pools scattered round the lake
    tries = 0
    while puddles.max() == 0 or (tries < 1500 and ndi.label(puddles)[1] < 20):
        tries += 1
        x0, y0 = int(rng.integers(60, W - 60)), int(rng.integers(40, 690))
        near = dist_out[y0, x0]
        if not (20 < near < 200) or rng.random() > 1.25 - near / 200 or y0 > edge(x0) - 20:
            continue
        blob = organic_pool(x0, y0, rng.uniform(6, 12), rng)
        lb, nb = ndi.label(blob)                                 # keep only its main body, no 1-px crumbs
        if nb == 0:
            continue
        blob = lb == 1 + int(np.argmax(ndi.sum(blob, lb, range(1, nb + 1))))
        if blob.sum() < 40:
            continue
        if (ndi.binary_dilation(puddles, iterations=10) & blob).any():
            continue
        puddles |= blob
    return dict(lake=lake, back=back, reeds=reeds, island=island, reed_isles=reed_isles, shallow=shallow,
                puddles=puddles, dist_out=dist_out, dist_in=dist_in, fine=fine, rng=rng)


# trails (zone coordinates): far out round the lake, meeting below it as a round path
TRAILS = {'west': [(330, -5), (230, 40), (110, 90), (48, 200), (36, 360), (58, 520), (120, 660), (250, 690),
                   (450, 700)],
          'ost': [(730, -5), (800, 60), (858, 170), (866, 340), (850, 520), (790, 640), (640, 690), (450, 700)],
          'mitte': [(468, -5), (472, 50), (470, 92)],
          'zur_bank': [None, (190, 655)], 'zur_huette': [(850, 520), (800, 515)]}
wc = curve(TRAILS['west'], 300)                                 # the bench path starts on the round path itself
TRAILS['zur_bank'][0] = tuple(wc[np.hypot(*(wc - TRAILS['zur_bank'][1]).T).argmin()])


def edge(x):
    """Row where the reed sea at the world's southern edge begins (the plan's edge + 22)."""
    return 722 + 14 * np.sin(np.asarray(x) / 53.0) + 8 * np.sin(np.asarray(x) / 17.0 + 1)


def organic_pool(x0, y0, r0, rng, shape=(H, W)):
    """A pool in a hollow: a few overlapping lobes of different size, stretched and turned each its own way,
    the rim frayed by fine noise, so no two are alike and none is an ellipse."""
    h, w = shape
    R = int(r0 * 2.2) + 4
    ys, xs = slice(max(0, y0 - R), min(h, y0 + R)), slice(max(0, x0 - R), min(w, x0 + R))
    yy, xx = np.mgrid[ys, xs]
    f = np.zeros(yy.shape)
    for _ in range(int(rng.integers(2, 5))):
        cx, cy = x0 + rng.normal(0, r0 * 0.55), y0 + rng.normal(0, r0 * 0.3)
        a, b, t = r0 * rng.uniform(0.45, 0.9), r0 * rng.uniform(0.25, 0.5), rng.uniform(-0.6, 0.6)
        u, v = (xx - cx) * np.cos(t) + (yy - cy) * np.sin(t), -(xx - cx) * np.sin(t) + (yy - cy) * np.cos(t)
        f = np.maximum(f, np.exp(-((u / a) ** 2 + (v / b) ** 2)))
    n = ndi.gaussian_filter(rng.normal(0, 1, yy.shape), 1.3)
    out = np.zeros(shape, bool)
    out[ys, xs] = f + 0.12 * n / (n.std() + 1e-9) > 0.42
    return out


def natural_trails():
    """The two paths round the lake as trodden ways rather than a frame: the west one wanders, now near the
    reeds, now away, round the pools; the east one runs straighter, then bends towards the hut; they meet
    below the lake off-centre. Sideways wobble like a meandering brook, then pushed out of reeds and pools.
    Returns zone-coordinate control points, one about every 30 px."""
    m = masks()
    yy, xx = np.mgrid[0:H, 0:W]
    keep = ndi.binary_dilation(m['lake'] | m['reeds'], iterations=7)   # puddles keep off the paths, not the other way | (yy > edge(xx) - 14)
    free = ndi.distance_transform_edt(~keep)
    gy, gx = np.gradient(ndi.gaussian_filter(ndi.distance_transform_edt(keep), 3))
    out = {}
    for name, base, amp, seed in (
            ('west', [(330, -5), (270, 40), (185, 70), (120, 118), (70, 178), (42, 258), (34, 340), (46, 420),
                      (38, 500), (46, 570), (62, 636), (128, 674), (220, 680), (300, 668), (380, 678), (452, 684),
                      (530, 680)], 9, 1),
            ('ost', [(730, -5), (764, 58), (792, 112), (842, 160), (858, 250), (846, 330), (858, 412), (842, 468),
                     (826, 522), (806, 580), (752, 626), (688, 652), (610, 670), (530, 680)], 5, 2)):
        c = curve(base, 800)
        rng = np.random.default_rng(seed)
        t = np.linspace(0, 1, len(c))
        sw = sum(rng.uniform(0.4, 1) * np.sin(t * f * 2 * np.pi + rng.uniform(0, 6)) for f in (3.1, 5.3, 9.7))
        d = np.gradient(c, axis=0)
        d /= np.hypot(d[:, :1], d[:, 1:]) + 1e-9
        c = c + np.stack([-d[:, 1], d[:, 0]], 1) * (amp * sw * np.minimum(1, np.minimum(t, 1 - t) * 10))[:, None]
        for rnd in range(3):                                     # out of the reeds and pools, then smooth; again
            for _ in range(40):
                xi = np.clip(c[:, 0].round().astype(int), 0, W - 1)
                yi = np.clip(c[:, 1].round().astype(int), 0, H - 1)
                bad = keep[yi, xi] & (c[:, 1] > 0)
                if not bad.any():
                    break
                c[bad, 0] += 2 * np.sign(gx[yi, xi][bad])
                c[bad, 1] += 2 * np.sign(gy[yi, xi][bad])
            if rnd < 2:
                c[:, 0] = ndi.gaussian_filter1d(c[:, 0], 5, mode='nearest')
                c[:, 1] = ndi.gaussian_filter1d(c[:, 1], 5, mode='nearest')
        arc = np.r_[0, np.cumsum(np.hypot(*np.diff(c, axis=0).T))]
        idx = [int(np.argmin(np.abs(arc - a))) for a in np.arange(0, arc[-1], 30)] + [len(c) - 1]
        pts = [(float(c[i, 0]), float(c[i, 1])) for i in idx]
        pts[0], pts[-1] = base[0], base[-1]
        out[name] = [p for k, p in enumerate(pts) if k == 0 or np.hypot(p[0] - pts[k - 1][0], p[1] - pts[k - 1][1]) > 8]
    return out
