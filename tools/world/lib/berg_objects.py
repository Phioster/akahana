# Plateau objects for the lock-screen picture, drawn per pixel in the cherry-tree style (no outlines).
import numpy as np
from scipy import ndimage as ndi

def hx(c): c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0, 2, 4)], float)
def pal(l): return np.array([hx(c) for c in l])
LOG = pal(['#1a1410', '#271d16', '#36281c', '#4a3724', '#62492e', '#7a5c3a'])
SNOWR = pal(['#353d4e', '#465063', '#5d687c', '#7a8699', '#9ba6b8', '#c0c8d4', '#e2e5ea'])
FL = pal(['#5a2a14', '#9a4a1c', '#d9822e', '#f2b44a', '#fde7a0'])
STONE = pal(['#24252b', '#33343b', '#45464e', '#5a5b63', '#73747b'])
WARM = hx('#f0a050')

G_J = np.random.default_rng(77).random(64)

def drift(img, q, put, x_from, x_to, y_base, hump, wob, warm_of=None, up=4, down=4):
    """A lumpy snow bank along a base line: rises 1..up rows and spills 0..down rows forward, all soft."""
    H, W, _ = img.shape
    for i in range(x_from, x_to):
        u = (i - x_from) / max(x_to - x_from, 1)
        taper = np.sin(np.pi * u) ** 0.6                                   # the bank runs out to nothing at both ends
        # top and foot are both soft curves; near the ends the top sinks below the base line too,
        # so the bank frays out instead of leaving a flat strip
        hi = int(round(taper * (2.6 + 1.3 * hump[(i * 2) % 400]) - 1.2))
        lo = int(round(taper * (1.0 + 1.6 * (hump[(i * 2 + 150) % 400] + 0.8)) + (G_J[i % 64] - 0.5) * 1.4))
        lo = max(lo, 0)
        if taper < 0.12 or hi < -lo: continue
        for k in range(-min(lo, down), min(hi, up) + 1):
            j = (y_base(i) if callable(y_base) else y_base) - k
            v = 0.66 + 0.06 * k - 0.12 * u
            if k == -min(lo, down): v -= 0.22                              # its foot meets the ground in shadow
            c = q(SNOWR, v, j, i)
            if warm_of is not None:
                a = warm_of(i) * (0.55 + 0.1 * k)
                c = c * (1 - a) + WARM * a
            put(i, j, c)


class Cabin:
    """Log cabin seen from above at an angle: front wall of round logs, a pillowy snow roof with soft
    edges (nothing straight), warm windows whose light glows on the logs and spills onto the snow."""
    def __init__(s, x, y, w=56, wall=25, roof=23, seed=1, win=13, winh=12, doorw=10):
        s.x, s.y, s.w, s.wall, s.roof = x, y, w, wall, roof        # (x, y) = bottom-left of the front wall
        s.seed = seed
        s.win, s.winh, s.doorw = win, winh, doorw                   # the game's small cabin: windows of a few px

    def footprint(s, H, W):
        yy, xx = np.mgrid[0:H, 0:W]
        return (xx >= s.x - 7) & (xx <= s.x + s.w + 7) & (yy >= s.y - s.wall - s.roof - 12) & (yy <= s.y + 3)

    def draw(s, img, G, CL):
        H, W, _ = img.shape
        x0, y0, w = s.x, s.y, s.w
        rng = np.random.default_rng(s.seed)
        wob = ndi.gaussian_filter1d(rng.normal(0, 1, 400), 2.5); wob /= wob.std()      # soft wobble for edges
        def q(P, v, j, i):
            v = v + 0.22 * (CL[j % H, i % W] - 0.5) + 0.12 * (G[j % H, i % W] - 0.5)   # grainy, like the cherry tree
            v = min(max(v, 0), 0.999) * (len(P) - 1); k = int(v)
            return P[min(len(P) - 1, k + (G[j % H, (i * 7) % W] < v - k))]
        def put(i, j, c):
            if 0 <= i < W and 0 <= j < H: img[j, i] = c
        top = y0 - s.wall
        nw, nh, k = s.win, s.winh, s.win / 13.0
        wins = ((x0 + int(round(6 * k)), nw), (x0 + w - int(round(6 * k)) - nw, nw))
        door = (x0 + w // 2 - s.doorw // 2, s.doorw)
        # 1) warm light on the snow in front of windows and door (dithered, strongest near the wall)
        for j in range(y0 - 1, min(H, y0 + int(40 * k))):
            for i in range(x0 - int(20 * k), x0 + w + int(20 * k)):
                if not (0 <= i < W): continue
                best = 0
                for (cx, r) in ((wins[0][0] + nw // 2, 20 * k), (door[0] + door[1] // 2, 16 * k), (wins[1][0] + nw // 2, 20 * k)):
                    d = np.hypot((i - cx) / r, (j - y0 + 2) / (r * 0.8))
                    best = max(best, 1 - d if d < 1 else 0)
                a = min(best ** 1.1 * 0.85, 0.8)
                if a > 0.03 and G[j, i] < a * 1.5:
                    img[j, i] = img[j, i] * (1 - a) + WARM * a
        # 2) snow drift along the foot of the wall, lumpy
        # the window light falls down onto the drift first: its top catches the most warmth
        def warmth(i):
            return max(max(0, 1 - abs(i - (wx + ww / 2)) / (ww * 0.9)) for (wx, ww) in wins + ((door[0], door[1]),))
        hump = ndi.gaussian_filter1d(rng.normal(0, 1, 400), 4.0); hump /= hump.std()
        drift(img, q, put, x0 - 11, x0 + w + 11, y0 + 1, hump, wob, warm_of=lambda i: 0.75 * warmth(i))
        # 3) front wall: round logs (3 rows each: highlight, body, seam), warmed near the windows
        for j in range(top, y0 - 1):
            r = (j - top) % 3
            for i in range(x0, x0 + w):
                v = 0.5 - 0.22 * (i - x0) / w + (0.2 if r == 0 else -0.04 if r == 1 else -0.3)
                v += 0.1 * (CL[j, i] - 0.5) + 0.05 * np.sin(i * 0.9 + j * 3.1)
                c = q(LOG, v, j, i)
                glow = max(max(0, 1 - np.hypot(i - (wx + ww / 2), (j - top - 4 - nh * 0.5) * 1.3) / (14 * k)) for (wx, ww) in wins)
                put(i, j, c * (1 - 0.45 * glow) + WARM * 0.45 * glow)
        # log ends at both corners, round discs on every log
        for j in range(top, y0 - 2, 3):
            for (cx, lit, dx) in ((x0 - 1, 0.78, -1), (x0 + w, 0.45, 1)):
                for (u, v, k) in ((0, 0, 0), (0, 1, -0.22), (dx, 0, -0.12), (dx, 1, -0.3)):
                    put(cx + u, j + v, q(LOG, lit + k, j, cx))
        # 4) windows: bright warm panes with a cross of bars and a soft glow around them
        for (wx0, ww) in wins:
            for j in range(top + 4, top + 4 + nh):
                for i in range(wx0, wx0 + ww):
                    edge = i in (wx0, wx0 + ww - 1) or j in (top + 4, top + 3 + nh)
                    bar = (i == wx0 + ww // 2 or j == top + 4 + nh // 2 - 1) and nh >= 7
                    if edge: c = q(LOG, 0.22, j, i)
                    elif bar: c = FL[1]
                    else: c = FL[4] if (j - top) < 4 + (nh * 5) // 12 and CL[j, i] > 0.3 else FL[3] if CL[j, i] > 0.25 else FL[2]
                    put(i, j, c)
            for i in range(wx0 - 1, wx0 + ww + 1):                     # snow on the sill, lumpy
                put(i, top + 4 + nh, q(SNOWR, 0.8 + 0.1 * wob[i % 300], top + 4 + nh, i))
                if CL[(top + 5 + nh) % H, i % W] > 0.6: put(i, top + 5 + nh, q(SNOWR, 0.6, top + 5 + nh, i))
        dx, dw = door
        for j in range(top + 5, y0 - 1):
            for i in range(dx, dx + dw):
                plank = (i - dx) % 3 == 0
                v = 0.34 - 0.1 * (i - dx) / dw - (0.12 if plank else 0) + 0.06 * (CL[j, i] - .5)
                put(i, j, q(LOG, v, j, i))
        for j in range(top + 5, y0 - 1): put(dx + dw, j, FL[2] if CL[j, dx] > 0.4 else FL[1])   # light seam at the door
        put(dx + dw - 2, top + 15, FL[3])
        # 5) roof from above: front slope rising to a soft ridge, pillowy snow with rounded, uneven edges
        rt = top - s.roof
        left = lambda j: x0 - 4 - int(round(1.2 * wob[j % 300] + 0.8))
        right = lambda j: x0 + w + 4 + int(round(1.2 * wob[(j + 77) % 300] + 0.8))
        # the ridge under its snow is not a ruler line: soft humps and dips along it
        hump = ndi.gaussian_filter1d(rng.normal(0, 1, 400), 5.0); hump /= hump.std()   # broad, soft swells
        ridge = lambda i: rt - int(round(1.2 * hump[(i - x0 + 50) % 400] + 0.6))
        for j in range(rt - 5, top + 3):
            f = (j - rt) / s.roof
            for i in range(left(j), right(j) + 1):
                if j < ridge(i): continue
                # rounded corners: the snow pillow curves in at the ridge and sags over the eave
                ci = min(i - left(j), right(j) - i)
                if j < rt + 2 and ci < 3 - (j - rt + 2): continue
                eave = top + 1 + int(round(1.0 * wob[(i * 3) % 300] + 0.6 + 0.8 * np.sin(i * 0.45)))
                if j > eave: continue
                v = 0.6 + 0.22 * (1 - f) - 0.2 * (i - x0) / w + 0.08 * (CL[j, i] - .5)
                v += 0.06 * np.sin(i * 0.33 + j * 0.9 + 2 * wob[(i + j) % 300])            # wind ripples
                if j >= eave - 1: v -= 0.25                                              # the bulge's underside
                if ci < 2: v -= 0.12
                put(i, j, q(SNOWR, v, j, i))
            # shadow the snow lip casts on the logs right under it
        for i in range(x0, x0 + w):
            j = top + 2 + int(round(1.0 * wob[(i * 3) % 300] + 0.6 + 0.8 * np.sin(i * 0.45)))
            if j < y0 - 1: put(i, j, img[j, i] * 0.55)
            if G[j + 1, i % W] < 0.14: put(i, j + 1, q(SNOWR, 0.85, j + 1, i))           # a few icicles
        # back slope: a thin darker band above the ridge shows the roof falls away again
        for i in range(left(rt) + 2, right(rt) - 1):
            k = int(round(1.5 + 0.8 * wob[(i + 30) % 300]))
            for u in range(1, k + 1):
                put(i, ridge(i) - u, q(SNOWR, 0.38 - 0.08 * u + 0.05 * (CL[rt, i] - .5), rt - u, i))
        # 6) stone chimney, irregular, with a snow cap and a thin smoke trail
        cx = x0 + w - 17
        for j in range(rt - 7, rt + 5):
            wj = 5 + (1 if j > rt + 2 else 0)
            for i in range(cx - (1 if j > rt + 2 else 0), cx + wj):
                if (j - rt) % 3 == 0 and CL[j, i] < 0.3: continue
                put(i, j, q(STONE, 0.6 - 0.1 * (i - cx) + 0.15 * (CL[j, i] - .5), j, i))
        for i in range(cx - 1, cx + 6):
            put(i, rt - 8, q(SNOWR, 0.95, rt - 8, i))
            if 0 < i - cx < 5: put(i, rt - 9, q(SNOWR, 0.8, rt - 9, i))
        for k in range(16):
            sx = cx + 2 + int(round(k * 0.5 + 1.3 * np.sin(k * 0.55))); sy = rt - 10 - k
            a = 0.4 * (1 - k / 16)
            for (u, v) in ((0, 0), (1, 0), (0, -1), (1, -1)):
                if 0 <= sx + u < W and 0 <= sy + v < H and G[sy + v, sx + u] < 0.75:
                    img[sy + v, sx + u] = img[sy + v, sx + u] * (1 - a) + hx('#8c8a96') * a

CUT = pal(['#4a3826', '#644c33', '#826443', '#a07f57', '#bd9b6d', '#d6b788'])
IRON = pal(['#141414', '#28272a', '#403e3f', '#7d7f84', '#b8bcc3', '#5c3a28', '#66625d'])   # warm-ish iron reads against blue snow
METAL = pal(['#25272c', '#3a3d44', '#575b64', '#80858f', '#b0b5be'])


def _tools(img, G, CL, seed):
    H, W, _ = img.shape
    rng = np.random.default_rng(seed)
    wob = ndi.gaussian_filter1d(rng.normal(0, 1, 400), 2.5); wob /= wob.std()
    hump = ndi.gaussian_filter1d(rng.normal(0, 1, 400), 5.0); hump /= hump.std()
    def q(P, v, j, i):
        v = v + 0.22 * (CL[j % H, i % W] - 0.5) + 0.12 * (G[j % H, i % W] - 0.5)
        v = min(max(v, 0), 0.999) * (len(P) - 1); k = int(v)
        return P[min(len(P) - 1, k + (G[j % H, (i * 7) % W] < v - k))]
    def put(i, j, c):
        if 0 <= i < W and 0 <= j < H: img[j, i] = c
    return q, put, wob, hump


class WoodShed:
    """Lean-to on posts: snow-laden single-slope roof, firewood stacked underneath (cut ends facing us)."""
    def __init__(s, x, y, w=36, h=17, roof=12, seed=3):
        s.x, s.y, s.w, s.h, s.roof, s.seed = x, y, w, h, roof, seed       # (x, y) = bottom-left at the ground

    def draw(s, img, G, CL):
        q, put, wob, hump = _tools(img, G, CL, s.seed)
        x0, y0, w, h = s.x, s.y, s.w, s.h
        top = y0 - h
        # cast shadow on the snow behind/right (cool), then the dark back wall of rough planks
        for j in range(top - 3, y0 + 4):
            for i in range(x0 - 1, x0 + w + 7):
                e = ((i - x0 - w / 2 - 3) / (w / 2 + 4)) ** 2 + ((j - (top + y0) / 2 - 1) / (h / 2 + 3)) ** 2
                if e < 1 and G[j % img.shape[0], i % img.shape[1]] < 0.85 - 0.5 * e: img[j, i] = img[j, i] * 0.74
        for j in range(top, y0):
            for i in range(x0, x0 + w):
                v = 0.14 - 0.06 * ((i - x0) % 6 == 0) + 0.04 * np.sin(j * 1.3 + i)
                put(i, j, q(LOG, v, j, i))
        # stacked firewood: cut ends of different sizes, jittered, the pile domed in the middle
        rng = np.random.default_rng(s.seed + 9)
        logs = []
        for row in range(5):
            cy0 = y0 - 2 - row * 3.6
            cx = x0 + 2.5 + (1.8 if row % 2 else 0) + rng.uniform(-0.6, 0.6)
            while cx < x0 + w - 2:
                r = rng.choice([1.6, 2.0, 2.4, 2.8], p=[.2, .35, .3, .15])
                dome = (top + 2) + 4 * ((cx - x0 - w / 2) / (w / 2)) ** 2      # higher in the middle
                cy = cy0 + rng.uniform(-0.7, 0.7)
                if cy - r > dome and not (row == 4 and rng.random() < 0.35):
                    logs.append((cx, cy, r, rng.uniform(-0.12, 0.12)))
                cx += r * 1.9 + rng.uniform(0.0, 0.8)
        for (cx, cy, r, tone) in sorted(logs, key=lambda t: t[1]):
            for j in range(int(cy - r - 1), int(cy + r + 2)):
                for i in range(int(cx - r - 1), int(cx + r + 2)):
                    dd = np.hypot(i - cx, (j - cy) * 1.1) / r
                    if dd > 1.05: continue
                    if dd > 0.78: c = q(LOG, 0.32 + tone, j, i)                     # bark rim
                    else:
                        ring = 0.12 * (np.sin(dd * 9) > 0.4)                        # growth rings
                        c = q(CUT, 0.62 + tone - 0.15 * ((i - cx) + (j - cy)) / r - ring, j, i)
                    put(i, j, c)
            if G[int(cy - r) % img.shape[0], int(cx) % img.shape[1]] < 0.4:        # snow crumbs on the top logs
                put(int(cx), int(cy - r), q(SNOWR, 0.8, int(cy - r), int(cx)))
        # posts at the front corners
        for px in (x0, x0 + w - 1):
            for j in range(top - 1, y0):
                put(px, j, q(LOG, 0.5 if px == x0 else 0.3, j, px)); put(px + (1 if px == x0 else -1), j, q(LOG, 0.3, j, px))
        # lean-to roof from above, sloping down towards us, thick snow with soft swelling edges
        rt = top - s.roof
        lft = x0 - 3 - int(round(0.8 * wob[7] + 0.5)); rgt = x0 + w + 2 + int(round(0.8 * wob[19] + 0.5))
        for i in range(lft, rgt + 1):
            ci = min(i - lft, rgt - i)
            r0 = rt - int(round(1.0 * hump[(i - x0 + 20) % 400] + 0.5)) + max(0, 2 - ci)    # rounded corners
            e0 = top + int(round(0.9 * wob[(i * 3) % 300] + 0.8)) - max(0, 1 - ci)
            for j in range(r0, e0 + 1):
                f = (j - r0) / max(e0 - r0, 1)
                v = 0.6 + 0.2 * (1 - f) - 0.2 * (i - x0) / w
                if j >= e0 - 1: v -= 0.25
                if ci < 2: v -= 0.12
                put(i, j, q(SNOWR, v, j, i))
            put(i, r0, q(SNOWR, 0.95, r0, i))
            if G[(e0 + 1) % img.shape[0], i % img.shape[1]] < 0.12: put(i, e0 + 1, q(SNOWR, 0.85, e0 + 1, i))   # icicles
        # snow drifted against the base, lumpy, spilling a little forward
        drift(img, q, put, x0 - 9, x0 + w + 9, y0, hump, wob)


def rng_skip(cx, row):
    return (cx * 7 + row * 3) % 5 == 0          # a few gaps in the top row: wood has been taken


class ChoppingBlock:
    """Big stump with an axe stuck in it, seen so the head shows its side profile (narrow poll, flaring bit)."""
    def __init__(s, x, y, R=9, seed=5):
        s.x, s.y, s.R, s.seed = x, y, R, seed                # (x, y) = middle of the stump's foot

    # side profile of the head, bit pointing down; '.' empty, d/m/l/e = dark/mid/light/edge steel
    # side profiles, bit pointing down; '.' empty, d/m/l/e = dark/mid/light/edge iron; (rows, eye column, eye row)
    HEADS = {
        'spalt': (["dmmmmmd.",            # splitting axe: a heavy wedge, flat hammer poll
                   "dmmmlld.",
                   "dmmmlld.",
                   "dmmllld.",
                   "dmmllld.",
                   ".dmlll..",
                   ".deeee.."], 7, 1),
        'bart': ([".mmmm....",            # bearded axe: straight back, the bit hooks down towards the handle
                  ".dmld....",
                  ".dmld....",
                  ".dmlm....",
                  ".dmllm...",
                  ".dmlllm..",
                  ".dmllllmd",
                  ".deeeeeed"], 5, 1),
        'faell': (["...mmmmm...",       # felling axe, big enough for detail: poll
                   "..dmmhlmd..",
                   "..dmhllmd..",
                   "..dmmlmmd..",       # gentle waist, never thinner than 5 px
                   "..dmmllmr..",       # a speck of rust near the eye
                   ".dmmhllmmd.",       # cheeks curve out
                   ".dmlhmllmd.",       # highlight streak running down the cheek
                   "dmmlhmmlmmd",
                   "dbbbbbbbbbd",       # ground bevel, a lighter band above the edge
                   ".eeeeeeeee."], 9, 1),
        'wald': ([".mmmmm...",            # forest axe: square poll, short neck, fanned bit
                  ".dmmld...",
                  ".dmmld...",
                  "..dml....",
                  ".dmllm...",
                  "dmllllm..",
                  "dmllllmmd",
                  "deeeeeeed"], 6, 1),
    }

    def draw(s, img, G, CL):
        q, put, wob, hump = _tools(img, G, CL, s.seed)
        x, y, R = s.x, s.y, s.R
        rng = np.random.default_rng(s.seed)
        tf = y - 9                                            # centre row of the top face
        for k in range(26):                                   # chips around the stump
            a = rng.uniform(0, 2 * np.pi); r = rng.uniform(R + 1, R + 9)
            i, j = int(round(x + r * np.cos(a))), int(round(y + 1 + r * 0.5 * np.sin(a)))
            put(i, j, q(CUT, 0.55 + 0.3 * rng.random(), j, i))
        for j in range(y - 2, y + 4):                         # soft shadow
            for i in range(x - R, x + R + 6):
                if ((i - x - 2) / (R + 4)) ** 2 + ((j - y - 1) / 2.6) ** 2 < 1: img[j, i] = img[j, i] * 0.7
        for j in range(tf, y + 1):                            # bark sides, rounded at the bottom
            for i in range(x - R, x + R + 1):
                e = ((i - x) / (R + 0.2)) ** 2
                if e > 1 or (j > y - 1 and e > 0.8): continue
                v = 0.5 - 0.32 * (i - x) / R + 0.12 * (((i * 3 + j * 2) % 5) == 0) - 0.08 * (j > y - 2)
                put(i, j, q(LOG, v, j, i))
        drift(img, q, put, x - R - 4, x + R + 5, lambda i: y + 1 - (1 if ((i - x) / (R + 0.2)) ** 2 > 0.8 else 0),
              hump, wob, up=2, down=2)
        for j in range(tf - 4, tf + 4):                       # top face with growth rings
            for i in range(x - R, x + R + 1):
                e = ((i - x) / (R + 0.4)) ** 2 + ((j - tf) / 3.6) ** 2
                if e <= 1:
                    ring = 0.13 * (np.sin(np.sqrt(e) * 13) > 0.35)
                    put(i, j, q(CUT, 0.78 - ring - 0.12 * (i - x) / R, j, i))
        put(x + 4, tf + 1, q(CUT, 0.3, tf + 1, x + 4)); put(x + 5, tf + 2, q(CUT, 0.3, tf + 2, x + 5))   # an old split
        # head: its bit sits in the wood at the face's centre row, the rest stands above
        import os
        HEAD, ecol, erow = s.HEADS[os.environ.get('AXE', 'faell')]
        hx0, hy0 = x - len(HEAD[0]) // 2 - 1, tf - len(HEAD) + 1
        P = {'d': 0, 'm': 1, 'l': 2, 'b': 3, 'e': 4, 'r': 5, 'h': 6}                  # dark forged iron, only the ground bit is bright
        for v, row in enumerate(HEAD):
            for u, ch in enumerate(row):
                if ch in P: put(hx0 + u, hy0 + v, IRON[P[ch]])
        for u in (-1, len(HEAD[-1])):                       # wood bruised either side of the bit
            put(hx0 + u, tf, q(CUT, 0.4, tf, hx0 + u))
        # handle out of the eye to the right, rising a little; ash wood, darker underside, snow on top
        ex, ey = hx0 + ecol, hy0 + erow
        for k in range(20):
            i, j = ex + k, ey - int(round(k * 0.3))
            put(i, j, q(CUT, 0.62 - 0.01 * k, j, i)); put(i, j + 1, q(LOG, 0.42, j + 1, i))
            if 2 <= k <= 18 and G[(j - 1) % img.shape[0], (i * 3) % img.shape[1]] < 0.8:
                put(i, j - 1, q(SNOWR, 0.88 - 0.015 * k, j - 1, i))
        put(ex + 20, ey - 6, q(CUT, 0.45, ey - 6, ex + 20)); put(ex + 20, ey - 5, q(LOG, 0.4, ey - 5, ex + 20))


NEEDLE = pal(['#0b1416', '#111e21', '#18292c', '#213538', '#2c4446', '#3a5555'])


class Pine:
    """Snow-laden fir seen from above at an angle: ragged tiers, lit from the left, snow dithered onto the
    upper side of every tier, shadow cast onto the snow."""
    def __init__(s, x, y, h=36, seed=21):
        s.x, s.y, s.h, s.seed = x, y, h, seed      # (x, y) = foot of the trunk

    def draw(s, img, G, CL):
        q, put, wob, hump = _tools(img, G, CL, s.seed)
        H, W, _ = img.shape
        x, y, h = s.x, s.y, s.h
        rng = np.random.default_rng(s.seed)
        jag = rng.random(512)
        # shadow on the snow, lower right
        for j in range(y - 3, y + int(h * 0.22)):
            for i in range(x - 2, x + int(h * 0.55)):
                e = ((i - x - h * 0.24) / (h * 0.32)) ** 2 + ((j - y - h * 0.06) / (h * 0.14)) ** 2
                if e < 1 and 0 <= j < H and 0 <= i < W and G[j, i] < 0.9 - 0.4 * e:
                    img[j, i] = img[j, i] * 0.7
        # trunk stub
        for j in range(y - 3, y + 1):
            for i in range(x - 1, x + 1):
                put(i, j, q(LOG, 0.3 - 0.1 * (i - x + 1), j, i))
        # tiers from the bottom up; each a ragged fan, later tiers overlap the ones below
        n = max(4, int(h / 6.5))
        for t in range(n):
            f = t / (n - 1)
            ty = y - 2 - int(f * (h - 6))               # tier base row
            half = (1 - f) * h * 0.36 + 2.2              # half width
            th = 4 + (1 - f) * 3.5                       # tier height
            for j in range(int(ty - th - 2), ty + 2):
                for i in range(int(x - half - 2), int(x + half + 3)):
                    if not (0 <= i < W and 0 <= j < H): continue
                    u = (i - x) / half
                    vrel = (ty - j) / th                 # 0 at the tier's lower edge, 1 at its top
                    # fan shape: wide at the bottom edge, pulled in to the stem at the top, ragged tips
                    edge = max(1 - vrel, 0) ** 0.8 * (0.95 + 0.25 * (jag[(i * 7 + t * 31) % 512] - 0.5))
                    droop = 0.6 * u * u                  # branch tips hang lower at the sides
                    if abs(u) > edge or vrel < -droop - 0.15 * jag[(i * 13 + j) % 512] or vrel > 1: continue
                    lit = 0.55 - 0.35 * u + 0.25 * vrel - 0.15 * (1 - vrel) * (abs(u) < 0.25)
                    c = q(NEEDLE, lit, j, i)
                    # snow sits on the upper side of the tier, dithered: denser near the top, on the lit side
                    dens = np.clip(0.15 + 0.7 * vrel - 0.25 * u + 0.1 * (CL[j, i] - 0.5), 0, 0.95)
                    if G[j, (i * 5) % W] < dens * 0.8:
                        c = q(SNOWR, 0.55 + 0.35 * vrel - 0.2 * u, j, i)
                    put(i, j, c)
        # snow cap on the tip
        put(x, y - h + 3, q(SNOWR, 0.95, y - h + 3, x)); put(x, y - h + 4, q(SNOWR, 0.8, y - h + 4, x))
        put(x - 1, y - h + 5, q(SNOWR, 0.75, y - h + 5, x - 1))


class Stump:
    """Felled-tree stump: furrowed bark, flared roots, ringed cut face under a lumpy snow pillow,
    a splinter left standing at the back where the trunk broke off."""
    def __init__(s, x, y, r=6, seed=61):
        s.x, s.y, s.r, s.seed = x, y, r, seed                # (x, y) = middle of the foot

    def draw(s, img, G, CL):
        q, put, wob, hump = _tools(img, G, CL, s.seed)
        x, y, r = s.x, s.y, s.r
        h = r + 1                                             # side height
        tf = y - h                                            # centre row of the cut face
        for j in range(y - 2, y + 4):                         # soft shadow lower right
            for i in range(x - r - 2, x + r + 7):
                if ((i - x - 2) / (r + 5)) ** 2 + ((j - y - 1) / 2.6) ** 2 < 1: img[j, i] = img[j, i] * 0.72
        # flared roots: the foot widens, each root a short tapering ridge into the snow
        for (dx, ln, dy) in ((-1, 4, 0), (1, 4, 0), (-1, 2, 1), (1, 3, 1)):
            for k in range(ln):
                i = x + dx * (r + k); j = y - 1 + dy + (k // 2)
                put(i, j, q(LOG, 0.42 - 0.3 * dx * 0.4 - 0.05 * k, j, i))
                if k < ln - 1: put(i, j - 1, q(LOG, 0.5 - 0.3 * dx * 0.4, j - 1, i))
        # bark sides with vertical furrows, lit from the left
        for j in range(tf, y + 1):
            for i in range(x - r - 1, x + r + 2):
                wid = r + (1 if j > y - 3 else 0)             # slightly wider near the ground
                e = ((i - x) / (wid + 0.3)) ** 2
                if e > 1: continue
                fur = 0.14 * (((i - x + 40) * 5 + (j // 3)) % 4 == 0)
                put(i, j, q(LOG, 0.52 - 0.34 * (i - x) / r - fur, j, i))
        # cut face with rings, then a lumpy snow pillow on most of it
        for j in range(tf - 3, tf + 3):
            for i in range(x - r, x + r + 1):
                e = ((i - x) / (r + 0.4)) ** 2 + ((j - tf) / 2.8) ** 2
                if e > 1: continue
                ring = 0.13 * (np.sin(np.sqrt(e) * 11) > 0.35)
                c = q(CUT, 0.74 - ring - 0.12 * (i - x) / r, j, i)
                rim = e > 0.72                                # bark rim around the face
                if rim: c = q(LOG, 0.45 - 0.3 * (i - x) / r, j, i)
                snow = e < 0.62 + 0.18 * hump[(i * 4 + 30) % 400] * 0.5 and not (j > tf + 1 and i > x + 1)
                if snow: c = q(SNOWR, 0.86 - 0.15 * (i - x) / r - 0.1 * (j - tf + 3) / 6, j, i)
                put(i, j, c)
        for i in range(x - r + 2, x + r - 1):                 # the pillow bulges a pixel over the rim in places
            if hump[(i * 4 + 30) % 400] > 0.3: put(i, tf - 3, q(SNOWR, 0.9, tf - 3, i))
        # splinter at the back, growing out of the rim: ragged pale spikes where the trunk tore off
        for (u, hgt) in ((-2, 2), (-1, 3), (0, 4), (1, 3), (2, 1)):
            for k in range(hgt):
                put(x + u, tf - 2 - k, q(CUT, 0.68 - 0.07 * k - 0.1 * u, tf - 2 - k, x + u) if u < 1 else q(LOG, 0.4, tf - 2 - k, x + u))
        drift(img, q, put, x - r - 6, x + r + 7, lambda i: y + 1 - (1 if abs(i - x) > r else 0), hump, wob, up=2, down=2)


class FallenLog:
    """A felled trunk lying in the snow: bark sides, snow along its top, a pale cut end."""
    def __init__(s, x1, y1, x2, y2, r=3.2, seed=71):
        s.a = np.array([x1, y1], float); s.b = np.array([x2, y2], float); s.r, s.seed = r, seed

    def draw(s, img, G, CL):
        q, put, wob, hump = _tools(img, G, CL, s.seed)
        H, W, _ = img.shape
        a, b, r = s.a, s.b, s.r
        d = b - a; L = np.hypot(*d); t_ = d / L; n = np.array([-t_[1], t_[0]])
        if n[1] < 0: n = -n                                     # n points down (towards the viewer)
        x0, x1 = int(min(a[0], b[0]) - r - 4), int(max(a[0], b[0]) + r + 5)
        y0, y1 = int(min(a[1], b[1]) - r - 3), int(max(a[1], b[1]) + r + 5)
        def inside(i, j):
            p = np.array([i, j], float) - a; u = p @ t_
            return 0 <= u <= L and abs(p @ n) <= r * (0.92 + 0.08 * np.sin(u * 0.4))
        for j in range(y0, y1):                                 # shadow, offset down-right
            for i in range(x0, x1):
                p = np.array([i - 1.5, j - 2.0]) - a; u = np.clip(p @ t_, 0, L)
                if np.hypot(*(p - u * t_)) < r + 0.5 and 0 <= j < H and 0 <= i < W: img[j, i] = img[j, i] * 0.74
        for j in range(y0, y1):
            for i in range(x0, x1):
                p = np.array([i, j], float) - a; u = p @ t_
                if u < 0 or u > L: continue
                v = p @ n                                       # -r (top) .. +r (bottom)
                rr = r * (0.92 + 0.08 * np.sin(u * 0.4))         # trunk not perfectly even
                if abs(v) > rr: continue
                f = v / rr
                if f < -0.15 + 0.35 * (wob[int(u * 3) % 300] * 0.3) and G[j % H, i % W] < 0.9:
                    c = q(SNOWR, 0.8 - 0.25 * (f + 1), j, i)    # snow along the top
                else:
                    c = q(LOG, 0.5 - 0.35 * f + 0.08 * (int(u * 1.3 + f * 3) % 3 == 0), j, i)   # bark furrows
                put(i, j, c)
        # cut end at b: pale disc with rings and a bark rim
        for j in range(int(b[1] - r - 1), int(b[1] + r + 2)):
            for i in range(int(b[0] - 2), int(b[0] + 3)):
                p = np.array([i, j], float) - b
                e = (p @ t_ / 1.6) ** 2 + (p @ n / r) ** 2
                if e > 1 or p @ t_ < -0.5: continue
                put(i, j, q(LOG, 0.3, j, i) if e > 0.65 else q(CUT, 0.72 - 0.15 * (np.sin(np.sqrt(e) * 9) > 0.3), j, i))
        # the bank hugs the trunk: per column it starts at the log's own lower edge
        bottom = {}
        for i in range(x0, x1):
            js = [j for j in range(y0, y1) if 0 <= j < H and 0 <= i < W and inside(i, j)]
            if js: bottom[i] = max(js)
        if bottom:
            lo_i, hi_i = min(bottom), max(bottom)
            drift(img, q, put, lo_i - 2, hi_i + 3, lambda i: bottom.get(i, bottom[min(max(i, lo_i), hi_i)]) + 1,
                  hump, wob, up=2, down=2)
