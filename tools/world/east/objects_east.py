"""Trees and small things of the eastern wood, built on the south's broadleaf and the old fir: dark teal crowns
(no autumn), a giant moss tree with hanging strands, bare dead trees, mossy boulders.
Same interface as the south's things: box(), draw(img, G)."""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import objects_lake as ol  # noqa: E402
from objects_lake import hx, put  # noqa: E402

# dark crowns for the wood: blue-green, one cool light (the moon), a touch of moss yellow in the highlights
ol.AUTUMN['nacht'] = ([hx(c) * 0.9 for c in ['#101c1c', '#1a2c2a', '#26403a', '#355a4c', '#4a7662']], hx('#8fb8a0'))
ol.AUTUMN['moos'] = ([hx(c) * 0.92 for c in ['#131c14', '#202e1c', '#2f4426', '#455f33', '#637e45']], hx('#a8bb72'))
STRAND = [hx(c) for c in ['#2a3a2a', '#3e5538', '#587a48', '#83a468']]
RIM = hx('#7f9a96')
RIM2 = hx('#4c6561')
WOODC = [hx(c) for c in ['#2e2724', '#4a3f3a', '#76695f', '#a39689']]      # weathered grey wood, light enough to read in the dark
BARK = [hx(c) for c in ['#1b1917', '#322b29', '#4e4340', '#6d5f58']]      # grey with a little warmth (Philip: some brown again)


class Nachtbaum:
    """A broadleaf tree with a dark blue-green crown."""
    def __init__(s, x, y, seed=5, size=1.0, leaf='nacht'):
        s.t = ol.Laubbaum(x, y, seed, size, leaf)
        s.x, s.y = x, y

    def box(s):
        return s.t.box()

    def draw(s, img, G):
        s.t.draw(img, G)


class Riesenbaum:
    """A giant old tree: ONE trunk, thick at its roots and tapering into the crown (which sits on its top), roots arching
    over the ground, a broad crown of moss-green clumps and strands of hanging moss that grow from the crown's underside
    only (they stop well above the ground and keep clear of the trunk)."""
    def __init__(s, x, y, seed=3, size=2.1, lean=0, avoid=None):
        s.x, s.y, s.seed, s.size, s.lean, s.avoid = x, y, seed, size, lean, avoid      # avoid: a bool mask the moss must not touch (water)

    def box(s):
        r = int(22 * s.size) + abs(s.lean)
        return (s.x - r - 6, s.y - int(60 * s.size) - 4, s.x + r + 14, s.y + 8)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed + 7)
        sz = s.size
        h, w = img.shape[:2]
        # seen from above at an angle (like the cherry tree): a HUGE crown, a short, massive trunk with buttress roots
        th = int(10 * sz)                                                # the visible trunk, ground to the crown's underside
        topx = s.x + s.lean
        crown_base = s.y + int(6 * sz)                                   # the crown's own foot lies below the ground: it sits low
        tmp = img.copy()                                                  # the crown only: its own trunk and limbs are dropped,
        ol.Laubbaum(topx, crown_base, s.seed, sz, 'moos').draw(tmp, G)    # the one trunk below carries it
        changed = (np.abs(tmp - img).sum(-1) > 0)
        barkish = np.zeros(changed.shape, bool)
        for c in ol.BARK:
            barkish |= (np.abs(tmp - np.asarray(c, float)).sum(-1) < 1)
        take = changed & ~barkish
        img[take] = tmp[take]
        # hanging moss: from the crown's underside, short enough to stay clear of the ground, off the trunk
        under = crown_base - int(16 * sz)
        for _ in range(int(80 * sz)):
            x_ = int(topx + rng.normal(0, 13 * sz))
            if abs(x_ - topx) < 5:
                continue
            top = int(under + rng.uniform(-4, 5))
            ln = int(rng.uniform(7, 17) * sz ** 0.6)
            for k in range(ln):
                xx = x_ + int(np.round(np.sin(k * 0.55 + x_) * 0.7))
                if 0 <= top + k < h and 0 <= xx < w and top + k < s.y - 8 * sz and not (s.avoid is not None and s.avoid[top + k, xx]):
                    put(img, xx, top + k, STRAND[min(3, int(k / ln * 3.2))])
        # the trunk: a thick, gnarled column. Vertical bark furrows (lit ridges, dark gaps), swelling at the roots like buttresses,
        # a couple of knots, patches of moss on the north side, lit from the upper left. It tapers into the crown's limbs.
        seed = s.seed
        tr = th + int(2 * sz)                                              # a little into the crown, hidden by its leaves

        def centre(t):
            return s.x + s.lean * 0.25 * t ** 1.6 + 1.2 * np.sin(t * 3.4 + seed) * (1 - 0.5 * t)

        def half_w(k, t):
            return 3.0 * sz * (1 - 0.35 * t) + 4.2 * sz * (1 - t) ** 3.0 + 1.0 * np.sin(k * 0.31 + seed) * (1 - t) + 0.6

        knots = [(int(rng.uniform(0.25, 0.7) * tr), rng.uniform(-0.5, 0.5)) for _ in range(2)]
        for k in range(tr + 3):
            t = min(1.0, k / tr)
            cx, hw = centre(t), half_w(k, t)
            y = s.y - k
            for i in range(int(np.floor(cx - hw)), int(np.ceil(cx + hw)) + 1):
                if not (0 <= y < h and 0 <= i < w):
                    continue
                u = (i - cx) / max(hw, 1.0)
                if abs(u) > 1.0:
                    continue
                ridge = 0.5 + 0.5 * np.sin((i - cx) * 1.35 + 2.2 * np.sin(k * 0.12 + i * 0.4 + seed))
                lit = 0.95 - 0.6 * (u + 1) / 2 + 0.55 * (ridge - 0.5) + rng.normal(0, 0.07)
                if abs(u) > 0.86:
                    lit -= 0.35                                            # the edge is darker: it rounds
                c = BARK[int(np.clip(lit * 3.4, 0, 3))]
                if u < -0.72 and ridge > 0.5 and rng.random() < 0.6:
                    c = RIM2                                                # the moon's edge, broken up
                if u < 0.15 and np.sin(k * 0.19 + seed * 2.0 + u * 5) > 0.45 and rng.random() < 0.8 and k > 5:
                    c = MOSSC[int(np.clip(1 + (lit > 0.55), 0, 2))]        # moss on the shaded north-west side
                for kk, ku in knots:
                    if abs(k - kk) < 3 and abs(u - ku) < 0.28 * (4 - abs(k - kk)) / 3 + 0.05:
                        c = BARK[0]
                put(img, i, y, c)
        # roots running out over the ground, flat and broad at the foot
        for a_, ln_ in ((-1.0, 12), (1.0, 13), (0.45, 9), (-0.5, 8), (1.5, 7), (-1.6, 6)):
            for k in range(int(ln_ * sz * 0.6)):
                xx = int(s.x + a_ * (4 * sz * 0.7 + k * 1.1))
                yy = int(s.y + 1 + k * 0.18 * abs(a_) - max(0, 3 - k * 0.5))
                for d in range(max(1, 3 - k // 4)):
                    if 0 <= yy - d < h and 0 <= xx < w:
                        put(img, xx, yy - d, BARK[2 if d == 0 else 1] if k % 4 else BARK[0])
        # the limbs: three thick arms leaving the top of the trunk into the crown
        topc, topy = centre(1.0), s.y - tr
        for a_ in ():                                                      # the limbs are inside the crown now
            x_, y_ = topc, topy
            ang = -np.pi / 2 + a_
            for k in range(int(11 * sz)):
                ang += rng.normal(0, 0.1) * (1 if k > 3 else 0.2)
                x_, y_ = x_ + np.cos(ang), y_ + np.sin(ang) * 0.95
                r = max(0.9, 3.0 * sz * 0.55 * (1 - k / (11 * sz)))
                for j in range(int(y_ - r), int(y_ + r) + 1):
                    for i in range(int(x_ - r), int(x_ + r) + 1):
                        if (i - x_) ** 2 + (j - y_) ** 2 <= r * r and 0 <= j < h and 0 <= i < w:
                            v = ((i - x_) * 0.7 + (j - y_) * 0.7) / (r + 0.5)
                            put(img, i, j, BARK[int(np.clip(1.5 - 1.3 * v, 0, 3))])


class Kahlbaum:
    """A bare dead tree: a twisted trunk and a few forking limbs, dark against the mist."""
    def __init__(s, x, y, seed=2, size=1.0):
        s.x, s.y, s.seed, s.size = x, y, seed, size

    def box(s):
        r = int(16 * s.size)
        return (s.x - r, s.y - int(44 * s.size), s.x + r, s.y + 3)

    def draw(s, img, G):
        import tree as T
        rng = np.random.default_rng(s.seed)
        out = {'strokes': [], 'tips': []}
        T.grow(rng, np.array([s.x, s.y], float), -np.pi / 2 + rng.normal(0, 0.12), 16 * s.size, 2.4 * s.size, 4, out)
        h, w = img.shape[:2]
        for x, y, wd, depth in out['strokes']:
            r = max(0.5, wd * 0.5)
            for j in range(int(y - r), int(y + r) + 1):
                for i in range(int(x - r), int(x + r) + 1):
                    if (i - x) ** 2 + (j - y) ** 2 <= r * r + 0.3 and 0 <= j < h and 0 <= i < w:
                        put(img, i, j, BARK[min(3, max(0, int(1.4 - 1.2 * (i - x) / (r + 0.5) + 0.4 * (depth < 2))))])


class MoosStein:
    """A boulder with moss on its upper side."""
    def __init__(s, x, y, r=5.0, seed=1):
        s.x, s.y, s.r, s.seed = x, y, r, seed

    def box(s):
        r = int(s.r) + 3
        return (s.x - r, s.y - r, s.x + r + 2, s.y + 3)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        h, w = img.shape[:2]
        rx, ry = s.r * rng.uniform(1.0, 1.4), s.r * rng.uniform(0.6, 0.85)
        for j in range(int(s.y - ry - 2), int(s.y + 3)):
            for i in range(int(s.x - rx - 2), int(s.x + rx + 3)):
                e = ((i - s.x) / rx) ** 2 + ((j - (s.y - ry * 0.6)) / ry) ** 2
                if e > 1 or not (0 <= j < h and 0 <= i < w):
                    continue
                lit = 0.6 - 0.5 * ((i - s.x) / rx * 0.4 + (j - s.y) / ry * 0.6) + rng.normal(0, 0.08)
                grey = np.array([46, 52, 54]) * (0.6 + 0.9 * lit)
                moss = np.array([52, 74, 44]) * (0.7 + 0.7 * lit)
                top = (j - s.y) < -ry * 0.5 + rng.normal(0, 1.2)
                img[j, i] = moss if top and rng.random() < 0.8 else grey


class Knorrbaum:
    """A twisted, overgrown tree like the dark wood in the Hobbit: a thick trunk that winds, roots arching out of the
    ground, limbs that fork and curl back, a tangled crown wider than tall with only a few dark leaf clumps, and a
    thin web of twigs. Trees stand close, so their crowns grow into each other."""
    def __init__(s, x, y, seed=2, size=1.0, leaves=0.25):
        s.x, s.y, s.seed, s.size, s.leaves = x, y, seed, size, leaves

    def box(s):
        r = int(26 * s.size)
        return (s.x - r, s.y - int(58 * s.size), s.x + r, s.y + int(8 * s.size))

    def _stroke(s, img, x, y, r, rim):
        h, w = img.shape[:2]
        r = max(0.55, r)
        for j in range(int(y - r), int(y + r) + 1):
            for i in range(int(x - r), int(x + r) + 1):
                if (i - x) ** 2 + (j - y) ** 2 <= r * r + 0.2 and 0 <= j < h and 0 <= i < w:
                    v = ((i - x) * 0.7 + (j - y) * 0.7) / (r + 0.5)          # lit from the upper left
                    c = BARK[int(np.clip(1.5 - 1.4 * v + rim, 0, 3))]
                    if v < -0.55 and r >= 1.4:
                        c = RIM                                                  # the moon's cool light on the upper edge: it reads in the dark
                    put(img, i, j, c)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed + 11)
        sz = s.size
        h, w = img.shape[:2]
        tips = []

        def limb(p0, ang, length, width, depth):
            """One winding limb; it forks into two or three, one of them curling back."""
            if depth == 0 or length < 3:
                tips.append(p0)
                return
            cur, a = np.array(p0, float), ang
            n = max(3, int(length))
            wob = rng.normal(0, 0.55)
            for k in range(n):
                a += wob * 0.12 + rng.normal(0, 0.16)
                cur = cur + np.array([np.cos(a), np.sin(a)])
                s._stroke(img, cur[0], cur[1], width * (1 - 0.5 * k / n) * 0.5, 0.0 if depth > 3 else 0.4)
            kids = 2 if rng.random() < 0.65 else 3
            for i in range(kids):
                da = (i - (kids - 1) / 2) * 1.15 + rng.uniform(-0.45, 0.45)
                if rng.random() < 0.25:
                    da += np.pi * 0.35 * np.sign(da or 1)                      # a limb that curls back
                limb(cur, a + da * 0.75, length * rng.uniform(0.68, 0.88), width * 0.62, depth - 1)

        # roots: arcs out of the foot, over the ground, thick at the trunk
        for a in rng.uniform(-0.2, np.pi + 0.2, 7):
            ln = rng.uniform(7, 15) * sz
            for k in range(int(ln)):
                t = k / ln
                x_ = s.x + np.cos(a) * k * 1.1 + np.sin(k * 0.5 + a) * 0.8
                y_ = s.y + 1 + abs(np.sin(a)) * k * 0.35 - 2.2 * np.sin(t * np.pi) * 0.9 * sz
                s._stroke(img, x_, y_, (2.2 - 1.6 * t) * sz * 0.8, 0.2)
        # trunk: winding S-curve, thick
        pos = np.array([s.x, s.y - 1.0])
        top = int(20 * sz)
        for k in range(top):
            t = k / top
            pos = np.array([s.x + np.sin(t * 5.2 + s.seed) * 3.2 * sz + t * 3 * sz, s.y - k])
            s._stroke(img, pos[0], pos[1], (3.8 * (1 - 0.4 * t) + 1.6 * (1 - t) ** 4) * sz, 0.0)
        for a in (-1.1, 0.0, 1.15):                                      # the crown's limbs, sprawling wide
            limb(pos, -np.pi / 2 + a + rng.uniform(-0.25, 0.25), rng.uniform(11, 16) * sz, 4.6 * sz, 4)
        # a few dark leaf clumps at the tips
        for tp in tips:
            if rng.random() < s.leaves:
                r = rng.uniform(2.2, 3.4) * sz ** 0.5
                for j in range(int(tp[1] - r), int(tp[1] + r) + 1):
                    for i in range(int(tp[0] - r), int(tp[0] + r) + 1):
                        if (i - tp[0]) ** 2 + (j - tp[1]) ** 2 <= r * r and 0 <= j < h and 0 <= i < w and G[j % G.shape[0], i % G.shape[1]] < 0.75:
                            put(img, i, j, np.array(ol.AUTUMN['nacht'][0])[int(rng.integers(0, 3))])


class Pilzring:
    """A ring of small pale mushrooms in the moss."""
    def __init__(s, x, y, r=9, seed=3):
        s.x, s.y, s.r, s.seed = x, y, r, seed

    def box(s):
        return (s.x - s.r - 3, s.y - s.r - 4, s.x + s.r + 4, s.y + s.r + 3)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        h, w = img.shape[:2]
        for a in np.linspace(0, 2 * np.pi, 11, endpoint=False) + rng.uniform(0, 0.5):
            x = int(round(s.x + np.cos(a) * s.r * rng.uniform(0.85, 1.15)))
            y = int(round(s.y + np.sin(a) * s.r * 0.6 * rng.uniform(0.85, 1.15)))
            if 1 <= x < w - 2 and 3 <= y < h - 1:
                put(img, x, y, np.array([150, 150, 134]))
                put(img, x - 1, y - 1, np.array([196, 192, 170])); put(img, x, y - 1, np.array([214, 210, 188]))
                put(img, x + 1, y - 1, np.array([172, 170, 150]))


STONE = [hx(c) for c in ['#3b4547', '#5a676a', '#88989a', '#bccac6']]       # dark .. lit, cool grey
MOSSC = [hx(c) for c in ['#27382a', '#3d5a36', '#5d8048']]


def _rows(img, x, y, rows, pal_of):
    h, w = img.shape[:2]
    for j, (a, b, lean) in enumerate(rows):
        for i in range(a, b + 1):
            xx, yy = x + i + lean, y - len(rows) + 1 + j
            if 0 <= yy < h and 0 <= xx < w:
                put(img, xx, yy, pal_of(i - a, b - a, j, len(rows)))


class Grabstein:
    """A worn gravestone seen from the front and a little above: a rounded slab, lit from the upper left, moss on top and
    at the foot, a faint carved mark, leaning a little; a low moss mound before it."""
    def __init__(s, x, y, seed=1, lean=0, size=1.0):
        s.x, s.y, s.seed, s.lean, s.size = x, y, seed, lean, size

    def box(s):
        return (s.x - 9, s.y - 18, s.x + 10, s.y + 5)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        wd = int(7 * s.size) + rng.integers(0, 2)
        ht = int(12 * s.size) + rng.integers(0, 3)
        rows = []
        for j in range(ht):
            inset = 0 if j > 1 else (2 if j == 0 else 1)                  # rounded top
            lean = int(round(s.lean * (1 - j / ht)))
            rows.append((-wd // 2 + inset, wd // 2 - inset, lean))
        h, w = img.shape[:2]
        for j in range(-1, 3):                                            # the mound at its foot
            for i in range(-wd // 2 - 3, wd // 2 + 4):
                xx, yy = s.x + i, s.y + 1 + j
                if 0 <= yy < h and 0 <= xx < w and (i / (wd / 2 + 3.5)) ** 2 + (j / 2.2) ** 2 < 1:
                    put(img, xx, yy, MOSSC[1 if rng.random() < 0.7 else 0])

        def pal(i, span, j, n):
            lit = 0.95 - 0.5 * (i / max(span, 1)) - 0.2 * (j / n) + rng.normal(0, 0.1)
            if i == 0 and j > 1:
                return RIM                                                     # the moon's edge light on the left
            if j < 2 and rng.random() < 0.75 or j > n - 3 and rng.random() < 0.55:
                return MOSSC[int(np.clip(1 + (lit > 0.6), 0, 2))]
            return STONE[int(np.clip(lit * 3.2, 0, 3))]
        _rows(img, s.x, s.y, rows, pal)
        mk = int(rng.integers(0, 3))                                      # a carved mark, darker
        cx, cy = s.x + int(round(s.lean * 0.5)), s.y - ht // 2 - 1
        pts = [[(0, 0), (0, 1), (0, -1), (-1, 0), (1, 0)], [(0, 0), (-1, 1), (1, 1), (0, -1)], [(-1, -1), (-1, 0), (0, 1), (1, 0), (1, -1)]][mk]
        for dx, dy in pts:
            if 0 <= cy + dy < h and 0 <= cx + dx < w:
                put(img, cx + dx, cy + dy, STONE[0])


class Stele:
    """A tall slender carved slab."""
    def __init__(s, x, y, seed=2, size=1.0):
        s.x, s.y, s.seed, s.size = x, y, seed, size

    def box(s):
        return (s.x - 6, s.y - 28, s.x + 7, s.y + 4)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        ht = int(19 * s.size) + rng.integers(0, 4)
        rows = [(-2 + (j == 0), 2 - (j == 0), 0) for j in range(ht)]

        def pal(i, span, j, n):
            lit = 0.85 - 0.6 * (i / max(span, 1)) - 0.2 * (j / n) + rng.normal(0, 0.08)
            if j > n - 3 and rng.random() < 0.6:
                return MOSSC[1]
            if i == 2 and 3 < j < n - 4 and j % 3 == 0:                      # a column of carved marks
                return STONE[0]
            return STONE[int(np.clip(lit * 3.2, 0, 3))]
        _rows(img, s.x, s.y, rows, pal)


class Steinhaufen:
    """A little cairn of stacked flat stones."""
    def __init__(s, x, y, seed=3, n=6):
        s.x, s.y, s.seed, s.n = x, y, seed, n

    def box(s):
        return (s.x - 8, s.y - 10, s.x + 9, s.y + 3)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        h, w = img.shape[:2]
        levels = [(3, 0), (2, -2), (2, -4), (1, -6)] if s.n > 4 else [(2, 0), (1, -2)]
        for k, (half, dy) in enumerate(levels):
            for j in range(0, 2 + (k == 0)):
                for i in range(-half - 1, half + 2):
                    xx, yy = s.x + i + int(rng.integers(-1, 2)) * (k > 0), s.y + dy - j
                    if 0 <= yy < h and 0 <= xx < w:
                        lit = 0.9 - 0.2 * j - 0.5 * ((i + half) / (2 * half + 2)) + rng.normal(0, 0.1)
                        put(img, xx, yy, STONE[int(np.clip(lit * 3.2, 0, 3))])


class Opferschale:
    """A small bowl with an offering (a mound of pale rice)."""
    def __init__(s, x, y, seed=4):
        s.x, s.y, s.seed = x, y, seed

    def box(s):
        return (s.x - 5, s.y - 6, s.x + 6, s.y + 2)

    def draw(s, img, G):
        for i in range(-3, 4):
            put(img, s.x + i, s.y, STONE[0])
            put(img, s.x + i, s.y - 1, STONE[1] if abs(i) < 3 else STONE[0])
        for i in range(-2, 3):
            put(img, s.x + i, s.y - 2, np.array([196, 196, 182]) if i < 1 else np.array([150, 152, 140]))
        for i in range(-1, 2):
            put(img, s.x + i, s.y - 3, np.array([224, 222, 206]))
        put(img, s.x, s.y - 4, np.array([232, 230, 214]))


class Stab:
    """A thin staff pushed into the ground, a strip of faded cloth tied round it."""
    def __init__(s, x, y, seed=5, lean=1, height=17):
        s.x, s.y, s.seed, s.lean, s.height = x, y, seed, lean, height

    def box(s):
        return (s.x - 5, s.y - s.height - 3, s.x + 8, s.y + 3)

    def draw(s, img, G):
        h, w = img.shape[:2]
        for k in range(s.height):
            x = s.x + int(round(s.lean * k / s.height * 3))
            y = s.y - k
            if 0 <= y < h and 0 <= x < w:
                put(img, x, y, BARK[2] if k % 4 else BARK[3])
        x, y = s.x + int(round(s.lean * 0.7 * 3 * (s.height - 5) / s.height)), s.y - s.height + 5
        for i, c in enumerate([(120, 52, 48), (150, 66, 58)]):
            for j in (0, 1):
                if 0 <= y + j < h and 0 <= x + 1 + i < w:
                    put(img, x + 1 + i, y + j, np.array(c))


class Kreuz:
    """A worn cross, wooden (grey, split, one arm broken off) or stone (chipped), leaning, moss at the foot."""
    def __init__(s, x, y, seed=6, stone=False, lean=1):
        s.x, s.y, s.seed, s.stone, s.lean = x, y, seed, stone, lean

    def box(s):
        return (s.x - 8, s.y - 20, s.x + 9, s.y + 4)

    def draw(s, img, G):
        rng = np.random.default_rng(s.seed)
        h, w = img.shape[:2]
        ht = int(rng.integers(13, 17))
        pal = STONE if s.stone else WOODC
        broken = int(rng.integers(0, 2))                                  # which arm is gone
        for k in range(ht):
            x = s.x + int(round(s.lean * k / ht * 2))
            y = s.y - k
            for dx in (0, 1):
                if 0 <= y < h and 0 <= x + dx < w:
                    lit = 3 - 2 * dx - (1 if k % 5 == 0 else 0) - (1 if rng.random() < 0.15 else 0)
                    put(img, x + dx, y, pal[int(np.clip(lit, 0, 3))] if not (s.stone and dx == 0 and k > 2) else RIM)
        by = s.y - int(ht * 0.68)
        bx = s.x + int(round(s.lean * 0.68 * 2))
        for side in (-1, 1):
            reach = 3 if (side == (-1 if broken else 1)) else 5
            if side == (-1 if broken else 1):
                reach = 2                                                  # the broken one: a stub
            for i in range(1, reach + 1):
                xx = bx + side * i + (1 if side > 0 else 0)
                yy = by + (1 if i > 3 else 0)
                if 0 <= yy < h and 0 <= xx < w:
                    put(img, xx, yy, pal[2 if side < 0 else 1])
                    if 0 <= yy - 1 < h:
                        put(img, xx, yy - 1, pal[3 if side < 0 else 2] if i % 2 == 0 else pal[2])
        for i in range(-2, 4):                                            # moss at the foot
            xx = s.x + i
            if 0 <= s.y + 1 < h and 0 <= xx < w and rng.random() < 0.85:
                put(img, xx, s.y, MOSSC[1])
                if rng.random() < 0.6 and s.y - 1 >= 0:
                    put(img, xx, s.y - 1, MOSSC[0])


class Steinbruecke:
    """An old stone bridge with two round arches, seen from the south at an angle. x is the middle, y the middle row of the
    deck (the way crosses there). The deck's pale pavers on top with worn middle and moss in the joints, low parapets, below it
    the front wall of laid blocks (each its own cool/warm/green-grey tone, dithered light from the upper left, lichen,
    water stains, ivy hanging from the parapet), two arches with lit voussoirs and a pier, the arches' vaults dark with the
    mist-lit far side showing. About 74 px wide."""
    L = 74
    FACE = 25                                                     # front wall height, deck's front edge to the waterline
    DECK = 13

    def __init__(s, x, y, seed=4):
        s.x, s.y, s.seed = x, y, seed

    SLOPE = 0.5                                                   # the bridge runs from upper left to lower right, 2 : 1

    def box(s):
        r = s.L // 2 + 10
        return (s.x - r, s.y - int(r * s.SLOPE) - 16, s.x + r, s.y + int(r * s.SLOPE) + s.FACE + s.DECK + 12)

    def draw(s, img, G):
        """Drawn frontally on a copy, then every column moved down by SLOPE per pixel to the right (an oblique view like the
        world's other things): the courses of blocks run in 2-pixel steps, the vertical joints stay upright."""
        tmp = img.copy()
        s._front(tmp, G)
        ys, xs = np.nonzero((tmp != img).any(-1))
        dy = np.round((xs - s.x) * s.SLOPE).astype(int)
        yy = ys + dy
        ok = (yy >= 0) & (yy < img.shape[0])
        img[yy[ok], xs[ok]] = tmp[ys[ok], xs[ok]]

    def _front(s, img, G):
        rng = np.random.default_rng(s.seed)
        h, w = img.shape[:2]
        x0, x1 = s.x - s.L // 2, s.x + s.L // 2
        dtop = s.y - s.DECK // 2                                  # the deck's top row
        dfront = dtop + s.DECK                                    # its front edge
        yb = dfront + s.FACE                                      # waterline
        bay = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
        TINT = [np.array(t) for t in ((1.0, 1.0, 1.0), (1.06, 1.01, 0.94), (0.94, 1.02, 1.0), (0.97, 0.99, 1.05))]    # calm: nearly the same grey
        LICH = [np.array(c, float) for c in ((56, 76, 46), (82, 102, 58), (116, 132, 78))]

        def ok(i, j):
            return 0 <= j < h and 0 <= i < w

        def stone(lit, tint, i, j):
            v = np.clip(lit, 0, 0.999) * 3 + (bay[j % 4, i % 4] - 0.5)
            return np.clip(STONE[int(np.clip(round(v), 0, 3))].astype(float) * tint * 0.84, 0, 255)       # a step darker than the open-air stones: it stands in the wood's shade
        lich = np.zeros((h, w))
        for _ in range(15):                                       # lichen and moss patches: blobs, denser at the top and foot
            cx, cy = int(rng.integers(x0 - 4, x1 + 5)), int(rng.choice([dfront + int(rng.integers(0, 6)), yb - int(rng.integers(0, 6)), dtop + int(rng.integers(0, 6))]))
            r = rng.uniform(2.0, 4.5)
            for j in range(int(cy - r), int(cy + r) + 1):
                for i in range(int(cx - r), int(cx + r) + 1):
                    if ok(i, j) and (i - cx) ** 2 + (j - cy) ** 2 < r * r and rng.random() < 0.8:
                        lich[j, i] = 1
        arch = [(s.x - 19, 11.0), (s.x + 19, 11.0)]
        # --- the front wall
        for j in range(dfront, yb + 1):
            for i in range(x0, x1 + 1):
                if not ok(i, j):
                    continue
                inarch = False
                for (cx, r) in arch:
                    dx, dy = i - cx, yb - j
                    spring = r * 0.2 + 2
                    if abs(dx) <= r and (dy <= spring or dx * dx + (dy - spring) ** 2 <= r * r * 0.8) and dy < spring + r * 0.9:
                        inarch = True
                        edge = (abs(dx) > r - 1.8) or (dy > spring and dx * dx + (dy - spring) ** 2 > (r - 1.8) ** 2 * 0.8)
                        if edge:                                   # voussoirs: lit on the left, alternating tones
                            blk = (int(np.arctan2(dy - spring, dx) * 4) % 2)
                            put(img, i, j, stone(0.95 - 0.35 * (dx > 0) - 0.18 * blk, TINT[0], i, j))
                        elif dy < 3:
                            put(img, i, j, np.array([34, 58, 66]) + 6 * bay[j % 4, i % 4])   # the water in the arch
                        else:                                        # the vault: dark, the far side's misty light at the middle
                            far = np.clip(1 - (abs(dx) / r) ** 2 - (dy - 3) / (r + 3), 0, 1)
                            put(img, i, j, np.array([12, 20, 24]) + far * np.array([38, 58, 58]))
                if inarch:
                    continue
                row = (j - dfront) // 4
                col = (i + (row % 2) * 4) // 8
                rr = np.random.default_rng(s.seed * 7919 + row * 131 + col)
                tint = TINT[int(rr.integers(0, 4))] * (0.96 + 0.08 * rr.random())
                joint = ((i + (row % 2) * 4) % 8 == 0) or ((j - dfront) % 4 == 3)
                lit = 0.84 - 0.4 * ((i - x0) / s.L) - 0.12 * ((j - dfront) % 4) / 3 + 0.06 * rr.random() + rng.normal(0, 0.04)
                if (i + (row % 2) * 4) % 8 == 1 and not joint:
                    lit += 0.18                                    # the lit left edge of each block
                if joint:
                    lit = 0.06 + 0.1 * rng.random()
                c = stone(lit, tint, i, j)
                if lich[j, i] and not joint:
                    c = LICH[int(np.clip(rng.integers(0, 3) + (lit > 0.6), 0, 2))]
                put(img, i, j, c)
        for _ in range(9):                                         # dark water stains running down from the parapet
            i = int(rng.integers(x0 + 2, x1 - 2))
            ln = int(rng.integers(5, 12))
            for k in range(ln):
                if ok(i, dfront + 1 + k) and not any(abs(i - cx) < r + 1 and (yb - (dfront + 1 + k)) < r + 2 for cx, r in arch):
                    img[dfront + 1 + k, i] = img[dfront + 1 + k, i] * 0.72
        # --- the deck: pavers of different tones, a worn pale middle (people walk it), moss in the joints, cracks
        for j in range(dtop, dfront):
            for i in range(x0 - 3, x1 + 4):
                if not ok(i, j):
                    continue
                pj, pi = (j - dtop) // 4, (i + ((j - dtop) // 4 % 2) * 3) // 6
                rr = np.random.default_rng(s.seed * 104729 + pj * 977 + pi)
                tint = TINT[int(rr.integers(0, 4))] * (0.96 + 0.08 * rr.random())
                joint = ((i + ((j - dtop) // 4 % 2) * 3) % 6 == 0) or ((j - dtop) % 4 == 3)
                walk = 1 - abs((j - dtop) - s.DECK / 2) / (s.DECK / 2)
                lit = 0.78 - 0.3 * ((i - x0) / s.L) + 0.18 * walk + 0.1 * rr.random() + rng.normal(0, 0.05)
                c = stone(lit if not joint else 0.1, tint, i, j)
                if joint and rng.random() < 0.55:
                    c = LICH[int(rng.integers(0, 2))]
                elif lich[j, i] and not joint:
                    c = LICH[int(rng.integers(1, 3))]
                put(img, i, j, c)
        # --- parapets: back wall and front wall, a lit top face and dark undersides; moss crowns
        for (top, hgt) in ((dtop - 4, 5), (dfront - 4, 5)):
            for j in range(top, top + hgt):
                for i in range(x0 - 3, x1 + 4):
                    if ok(i, j):
                        lit = 0.95 - 0.42 * ((i - x0) / s.L) - 0.22 * ((j - top) / hgt) + rng.normal(0, 0.05)
                        c = stone(lit, TINT[(i // 9 + j) % 4], i, j) if j > top else np.clip(STONE[3] * 1.06, 0, 255)
                        if (i + 3 * (top % 3)) % 9 == 0 and j > top:
                            c = STONE[0]
                        if j == top and rng.random() < 0.25:
                            c = LICH[int(rng.integers(0, 3))]
                        put(img, i, j, c)
        # --- ivy hanging from the front parapet, bright leaves on dark stems
        for _ in range(7):
            i = int(rng.integers(x0 + 1, x1))
            ln = int(rng.integers(8, 18))
            for k in range(ln):
                j = dfront + 1 + k
                ii = i + int(round(np.sin(k * 0.6 + i) * 1.0))
                if ok(ii, j) and not any(abs(ii - cx) < r and (yb - j) < r + 2 for cx, r in arch):
                    put(img, ii, j, np.array([36, 56, 36]))
                    if k % 3 == 1:
                        put(img, ii + 1, j, LICH[2] if rng.random() < 0.5 else LICH[1])
        # --- the foot: a dark shadow and ripples on the water below the wall, ferns at both ends
        for j in range(yb + 1, yb + 4):
            for i in range(x0, x1 + 1):
                if ok(i, j) and not any(abs(i - cx) < r - 1 for cx, r in arch):
                    img[j, i] = img[j, i] * (0.62 + 0.1 * (j - yb))
        for dx in (-s.L // 2 - 3, s.L // 2 + 4):
            for k in range(9):
                a_ = -np.pi / 2 + (k - 4) * 0.4
                for r in range(6):
                    i, j = int(s.x + dx + np.cos(a_) * r), int(dfront + 8 + np.sin(a_) * r * 0.9)
                    if ok(i, j):
                        put(img, i, j, LICH[1 if r < 3 else 2] * (0.8 if k % 2 else 1.0))
