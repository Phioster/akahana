# Small life in the scene: footpaths with prints, a wall lantern, rocks, grass tufts, snowflakes, stars.
import numpy as np
from scipy import ndimage as ndi
from berg_objects import hx, pal, SNOWR, STONE, LOG

def curve(pts, n=600):
    P = np.array(pts, float)
    t = np.linspace(0, 1, n)
    out = []
    for tt in t:                                   # de Casteljau
        Q = P.copy()
        while len(Q) > 1: Q = Q[:-1] * (1 - tt) + Q[1:] * tt
        out.append(Q[0])
    return np.array(out)

def footpath(img, pts, G, width=1.5, bank=1.6, spacing=4.2, rng_seed=0, fade_from=None):
    """A trench trodden into the snow: packed, smoother floor, a shadow under its upper rim, snow pushed up
    into low banks on both sides, and prints alternating left/right along the floor."""
    H, W, _ = img.shape
    c = curve(pts)
    line = np.zeros((H, W), bool); tmap = np.zeros((H, W))
    for k, (x, y) in enumerate(c):
        i, j = int(round(x)), int(round(y))
        if 0 <= i < W and 0 <= j < H: line[j, i] = True; tmap[j, i] = k / (len(c) - 1)
    if not line.any(): return
    dist, (iy, ix) = ndi.distance_transform_edt(~line, return_indices=True)
    rng = np.random.default_rng(rng_seed)
    wob = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), 3) * 6         # width breathes a little along the way
    t = tmap[iy, ix]                                                     # how far along the path each pixel is
    A = np.ones((H, W)) if fade_from is None else np.clip(1 - (t - fade_from) / (1 - fade_from), 0, 1) ** 1.3
    hw = (width + 0.35 * wob) * (0.4 + 0.6 * A)                          # thins out as it fades
    keep = G < 0.15 + 0.85 * A                                           # and breaks up into patches
    orig = img.copy()
    yy = np.mgrid[0:H, 0:W][0]
    above = yy < iy                                                      # pixel lies on the upper side of the path
    floor = dist <= hw
    rim = (dist > hw) & (dist <= hw + bank) & (G < 0.92)
    smooth = ndi.uniform_filter(img, size=(5, 9, 1))
    img[floor] = smooth[floor] * np.array([0.82, 0.84, 0.90])            # packed snow, grain trodden flat
    sh = floor & ~above & (dist > hw - 1.0)                              # under the upper bank lies a thin shadow
    sh2 = floor & above & (dist > hw - 1.0)
    img[sh2] = img[sh2] * 0.84
    lit = rim & above                                                    # bank behind the path faces us: lit
    img[lit] = np.minimum(img[lit] * 1.28 + 8, 255)
    low = rim & ~above                                                   # bank in front: its top lit, the slope towards the path darker
    img[low] = np.minimum(img[low] * np.where(dist[low] > hw[low] + 0.8, 1.22, 1.05)[:, None], 255)
    seg = np.hypot(*np.diff(c, axis=0).T); s = np.concatenate([[0], np.cumsum(seg)])
    side = 1; d = spacing * 0.5
    while d < s[-1]:
        k = np.searchsorted(s, d); x, y = c[min(k, len(c) - 1)]
        tx, ty = c[min(k + 3, len(c) - 1)] - c[max(k - 3, 0)]; L = np.hypot(tx, ty) + 1e-6
        nx, ny = -ty / L, tx / L
        off = min(0.7, width * 0.45)
        i, j = int(round(x + nx * off * side)), int(round(y + ny * off * side))
        if 0 <= i < W and 1 <= j < H - 1 and (fade_from is None or rng.random() < A[j, i] * 1.2):
            img[j, i] = img[j, i] * 0.66                                 # the print
            img[j - 1, i] = np.minimum(img[j - 1, i] * 1.15, 255)
        side = -side; d += spacing
    if fade_from is not None:                                            # blend the whole trench out towards its end
        a = (A * keep)[..., None]
        img[:] = orig * (1 - a) + img * a

def rock(img, x, y, r, G, CL, seed):
    H, W, _ = img.shape
    rng = np.random.default_rng(seed)
    ph = rng.uniform(0, 6.28, 3)
    for j in range(y - r - 1, y + 2):
        for i in range(x - r - 1, x + r + 2):
            ang = np.arctan2(j - y, i - x)
            rr = r * (1 + 0.18 * np.sin(2 * ang + ph[0]) + 0.1 * np.sin(3 * ang + ph[1]))
            e = np.hypot((i - x), (j - y) * 1.5) / rr
            if e > 1 or not (0 <= i < W and 0 <= j < H): continue
            if j > y: continue                               # buried: only the top shows
            v = 0.55 - 0.3 * (i - x) / r + 0.15 * (CL[j, i] - .5)
            cap = (j < y - r * 0.35) and G[j, i] < 0.85
            P = SNOWR if cap else STONE
            if cap: v = 0.75 - 0.2 * (i - x) / r
            v = min(max(v, 0), .999) * (len(P) - 1); k = int(v)
            img[j, i] = P[min(len(P) - 1, k + (G[j, (i * 7) % W] < v - k))]
    for i in range(x - r, x + r + 1):                        # soft shadow on the snow at its foot, right side
        if 0 <= i < W and y + 1 < H and i > x - 1: img[y + 1, i] = img[y + 1, i] * 0.8

GRASS = pal(['#3d3424', '#5a4a30', '#7c6844', '#9c875b'])
def tuft(img, x, y, n, rng):
    H, W, _ = img.shape
    for b in range(n):
        lean = rng.choice([-1, 0, 0, 1]); hgt = rng.integers(2, 5)
        bx = x + rng.integers(-2, 3)
        for k in range(hgt):
            i, j = bx + (lean if k >= hgt - 1 else 0), y - k
            if 0 <= i < W and 0 <= j < H: img[j, i] = GRASS[min(3, 1 + (k == hgt - 1) + (lean < 0))]

def lantern(img, x, y, post=0):
    """Small iron lantern: cap, dark frame, warm glass; optionally on a wooden post. (x, y) = top of the glass."""
    H, W, _ = img.shape
    for k in range(post):                                # wooden post: lit left half, shaded right half
        j = y + 3 + k
        if 0 <= j < H:
            if 0 <= x < W: img[j, x] = LOG[3]
            if 0 <= x + 1 < W: img[j, x + 1] = LOG[1]
    if post:                                             # a little snow heaped at its foot
        for (u, v) in ((-1, 0), (0, 0), (1, 0), (2, 0), (0, -1), (1, -1)):
            j = y + 2 + post + v
            if 0 <= x + u < W and 0 <= j < H: img[j, x + u] = SNOWR[3] if v else SNOWR[2]
    IR = hx('#1a1a1c'); IR2 = hx('#2e2c2c')
    FL = [hx('#fde7a0'), hx('#f2b44a'), hx('#d9822e')]
    for (i, j, c) in ((x - 2, y - 2, IR2), (x - 1, y - 2, IR2), (x, y - 2, IR), (x, y - 3, IR), (x + 1, y - 2, IR2),
                      (x - 1, y - 1, IR), (x, y - 1, IR), (x + 1, y - 1, IR),
                      (x - 1, y, FL[1]), (x, y, FL[0]), (x + 1, y, FL[2]),
                      (x - 1, y + 1, FL[1]), (x, y + 1, FL[0]), (x + 1, y + 1, FL[2]),
                      (x - 1, y + 2, IR), (x, y + 2, IR), (x + 1, y + 2, IR),
                      (x - 1, y - 3, SNOWR[5]), (x + 1, y - 3, SNOWR[4]), (x, y - 4, SNOWR[5])):
        if 0 <= i < W and 0 <= j < H: img[j, i] = c

def snowflakes(img, rng, n, avoid=None):
    H, W, _ = img.shape
    for _ in range(n):
        x, y = rng.integers(0, W), rng.integers(0, H)
        if avoid is not None and avoid[y, x] and rng.random() < 0.8: continue   # only a few flakes against the sky
        lum = img[y, x].mean()
        b = rng.uniform(0.55, 1.0)
        col = np.array([222, 226, 234.]) * b
        if lum > 150: col = np.minimum(col * 1.05 + np.array([30, 15, 0]), 255)   # flakes in the warm light glow
        a = 0.85 if lum < 150 else 0.6
        img[y, x] = img[y, x] * (1 - a) + col * a
        if rng.random() < 0.12 and x + 1 < W: img[y, x + 1] = img[y, x + 1] * 0.6 + col * 0.4   # a few bigger ones

def stars(img, sky, rng, n, ymax):
    H, W, _ = img.shape
    for _ in range(n):
        x, y = rng.integers(0, W), rng.integers(0, ymax)
        if not sky[y, x] or img[y, x].mean() > 48: continue          # only dark, clear sky (no glow, no cloud)
        fade = 1 - y / ymax                                             # thin out towards the dusk glow
        if rng.random() > fade * 1.2: continue
        b = rng.uniform(0.35, 1.0) * (0.6 + 0.4 * fade)
        img[y, x] = np.array([200, 205, 225.]) * b + img[y, x] * (1 - b) * 0.5
