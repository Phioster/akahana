"""The eastern wood's skeleton: where the paths wind, where the clearings lie, where the river runs.
One source for the drafts, the generator and the tests (fixed seeds, nothing random at import).
Coordinates are WORLD pixels; the plan's picture (approval page, step 37) is relative to (540, 300)."""
from collections import deque

import numpy as np
from PIL import Image, ImageDraw

OX, OY = 540, 300                           # plan origin in the world
X0, Y0, X1, Y1 = 540, 300, 1740, 3100       # the window the masks cover
PATH_W = 8
RIVER_W = 14


class Spot:
    def __init__(self, x, y, r, seed, kind):
        self.x, self.y, self.r, self.seed, self.kind = x + OX, y + OY, r, seed, kind


SPOTS = {
    '1': Spot(110, 560, 38, 3, 'gate'), '3': Spot(420, 250, 88, 5, 'graves'), '4': Spot(430, 1050, 105, 6, 'pond'),
    '5': Spot(1090, 780, 120, 4, 'ritual'), '6': Spot(800, 320, 95, 7, 'bridge'), '7': Spot(850, 1150, 72, 8, 'jizo'),
    '9': Spot(700, 2050, 80, 9, 'glade'),
    'a': Spot(250, 620, 24, 11, 'small'), 'b': Spot(560, 420, 26, 12, 'small'), 'c': Spot(560, 1190, 22, 13, 'small'),
    'd': Spot(980, 950, 24, 14, 'small'), 'e': Spot(940, 840, 26, 15, 'small'), 'f': Spot(640, 2150, 22, 16, 'small'),
    'g': Spot(740, 1560, 26, 17, 'small'),
}
HUT = (252 + OX, 2600 + OY)                 # where the new branch leaves the south's east-shore path (792, 2900: on its EARTH ground)

# edge name -> (from, to, control points in plan coordinates); nodes: spot keys, 'W' (gate from the poppies),
# 'H' (hut), 'J1'/'J2' (junctions of the moss path)
_EDGES = {
    'tor': ('W', '1', [(0, 520), (110, 560)]),
    'moos': ('1', 'J1', [(110, 560), (200, 500), (270, 610), (360, 560)]),
    'gabel': ('J1', 'J2', [(360, 560), (430, 470)]),
    'gruft': ('J2', '3', [(430, 470), (370, 410), (460, 340), (420, 250)]),
    'wasser': ('J1', '4', [(360, 560), (290, 680), (420, 770), (310, 890), (440, 960), (430, 1050)]),
    'bruecke_w': ('J2', '6', [(430, 470), (480, 360), (540, 270), (610, 215), (680, 235), (730, 275), (766, 303), (800, 320)]),
    'bruecke_o': ('6', '5', [(800, 320), (834, 337), (880, 360), (930, 400), (960, 450), (985, 520), (960, 615), (1030, 700), (1090, 780)]),
    'jizo': ('4', '7', [(430, 1050), (520, 1130), (620, 1060), (700, 1170), (780, 1100), (850, 1150)]),
    'ritual_s': ('7', '5', [(850, 1150), (900, 1000), (1010, 950), (1060, 860), (1090, 780)]),
    'saum_h': ('H', '9', [(252, 2600), (340, 2570), (430, 2500), (520, 2400), (620, 2230), (700, 2050)]),
    'saum_n': ('9', '7', [(700, 2050), (760, 1850), (700, 1700), (790, 1500), (830, 1330), (850, 1150)]),
}
_RIVER = [(720, 0), (790, 120), (880, 225), (800, 320), (745, 420), (760, 560), (800, 720), (700, 900), (560, 1010), (430, 1050)]
_BACH = [(430, 1050), (470, 1300), (430, 1650), (380, 1950), (350, 2200)]       # ends at the east edge of the south's brook B (890, 2500)


def _spline(pts, seed, wig=26.0, n=40):
    """Catmull-Rom through the points plus a low-frequency sideways wobble that fades out at both ends."""
    P = np.array(pts, float)
    P = np.vstack([P[0] * 2 - P[1], P, P[-1] * 2 - P[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    out = np.array(out)
    tang = np.gradient(out, axis=0)
    nrm = np.stack([-tang[:, 1], tang[:, 0]], 1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True) + 1e-9
    ph = np.random.default_rng(seed).random() * 6.0
    s = np.arange(len(out))
    off = wig * (np.sin(s / 22 + ph) * 0.7 + np.sin(s / 9 + ph * 2) * 0.3) * np.clip(np.minimum(s, len(out) - 1 - s) / 30, 0, 1)
    return out + nrm * off[:, None] + np.array([OX, OY])


def paths():
    """edge name -> (N, 2) world polyline."""
    out = {}
    for i, (k, (_, _, c)) in enumerate(_EDGES.items()):
        a = _spline(c, 100 + i, wig=18.0 if len(c) < 3 else 36.0)
        if k.startswith('bruecke'):                                    # the wobble dies out toward the bridge: the way meets it straight
            b = _spline(c, 100 + i, wig=0.0)
            s = SPOTS['6']
            w = np.clip((np.hypot(b[:, 0] - s.x, b[:, 1] - s.y) - 40) / 80.0, 0, 1)[:, None]
            a = b + (a - b) * w + np.array([0.0, 15.0]) * (1 - w)    # the deck's middle lies a little below the spot's point
        out[k] = a
    return out


def river():
    """The river, bent by a soft bump so that it passes exactly through the bridge spot's middle (the way crosses there)."""
    r = _spline(_RIVER, 300, wig=30.0)
    s = SPOTS['6']
    k = int(np.argmin(np.hypot(r[:, 0] - s.x, r[:, 1] - s.y)))
    off = np.array([s.x, s.y]) - r[k]
    w = np.exp(-(((np.arange(len(r)) - k) / 38.0) ** 2))
    return r + off[None, :] * w[:, None]


def bach():
    return _spline(_BACH, 301, wig=34.0)


def blob(spot, k=0.28, n=48):
    """An irregular clearing outline, never a circle."""
    rr = np.random.default_rng(spot.seed)
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    f = 1 + k * (np.sin(a * 2 + rr.random() * 6) * 0.6 + np.sin(a * 3 + rr.random() * 6) * 0.4)
    sx = 1 + 0.25 * rr.random()
    return [(spot.x + np.cos(t) * spot.r * q * sx, spot.y + np.sin(t) * spot.r * q) for t, q in zip(a, f)]


class Masks:
    def __init__(self, path, clearing, river, bach):
        self.path, self.clearing, self.river, self.bach = path, clearing, river, bach

    @property
    def walk(self):
        """Walkable ground: paths and clearings; the river only on the bridge deck (spot '6')."""
        return self.path | self.clearing


def _draw(fn):
    im = Image.new('L', (X1 - X0, Y1 - Y0), 0)
    fn(ImageDraw.Draw(im))
    return np.array(im) > 0


def masks():
    def pts(a):
        return [(float(x) - X0, float(y) - Y0) for x, y in a]
    return Masks(
        _draw(lambda d: [d.line(pts(p), fill=1, width=PATH_W, joint='curve') for p in paths().values()]),
        _draw(lambda d: [d.polygon(pts(blob(s)), fill=1) for s in SPOTS.values()]),
        _draw(lambda d: d.line(pts(river()), fill=1, width=RIVER_W, joint='curve')),
        _draw(lambda d: d.line(pts(bach()), fill=1, width=9, joint='curve')))


def _graph():
    g = {}
    for a, b, _ in _EDGES.values():
        g.setdefault(a, set()).add(b)
        g.setdefault(b, set()).add(a)
    return g


def route_exists(a, b):
    seen, q = {a}, deque([a])
    g = _graph()
    while q:
        n = q.popleft()
        for m in g.get(n, ()):
            if m not in seen:
                seen.add(m)
                q.append(m)
    return b in seen


def disjoint_routes(a, b):
    """Edge-disjoint routes between two nodes (unit-capacity max flow on the small graph)."""
    cap = {}
    for u, v, _ in _EDGES.values():
        cap[(u, v)] = cap.get((u, v), 0) + 1
        cap[(v, u)] = cap.get((v, u), 0) + 1
    flow = 0
    while True:
        prev, q = {a: None}, deque([a])
        while q and b not in prev:
            n = q.popleft()
            for (u, v), c in cap.items():
                if u == n and c > 0 and v not in prev:
                    prev[v] = u
                    q.append(v)
        if b not in prev:
            return flow
        v = b
        while prev[v] is not None:
            u = prev[v]
            cap[(u, v)] -= 1
            cap[(v, u)] += 1
            v = u
        flow += 1
