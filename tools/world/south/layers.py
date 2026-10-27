"""Splits the approved zone drafts into what the game draws apart: the ground, the swaying layer (grass,
reeds, flowers, poppy heads) and the standing things as sprites with their foot.

The drafts stay the only source of the look. Nothing in them is rewritten: while collecting, the draw
methods of their thing classes are wrapped. A first pass renders with every swaying and standing thing
switched off (that is the ground); a second, normal pass records what each thing changes:

- swaying things: the pixels they change go into the RGBA sway layer;
- standing things are drawn once more onto a magenta sentinel, so every pixel they cover is known even
  where it happens to match what lay beneath; pixels that only darken the sentinel are shadows and go
  into the ground as a factor, the rest is the sprite.

    with layers.collect() as c:
        ...render the drafts...
    c.ground, c.sway, c.sprites, c.shadow
"""
import contextlib

import numpy as np

import objects_lake as ol
import objects_south as os_
import objects_water as ow
import zone1_draft as z1
import zone2_draft as z2
import zone3_draft as z3

SWAY = (z2.Blade, z2.Wildflower, ow.Schilf, ow.Rohrkolben, ow.Farn, os_.HohesGras)
FLAT = (ow.Bruecke, ow.Brett, ow.Trittsteine, ow.Quelle, ol.Steg, ol.Boot, ol.Seerosen, ol.WasserStein,
        ol.Treibholz)
STAND = (z1.Fir, z2.Bank, z2.Steinlaterne, z3.Holzlaterne, ow.Weide, ol.Laubbaum, ol.Huette, ol.Enten,
         os_.Wegstein, os_.Mauer, os_.Vogelscheuche, os_.Findling, os_.Steinhaufen, os_.Baumstumpf, os_.Stamm,
         os_.Zaun, os_.Voegel, os_.Kirschbaum, os_.Fackel, os_.Kerzen, os_.Karren)
SENTINEL = np.array([255.0, 0.0, 255.0])

_active = None                     # the Collected of the running pass, None when not collecting


class Collected:
    def __init__(s):
        s.ground = None            # (H, W, 3) float: the drafts with nothing swaying or standing
        s.raw = None               # (H, W, 3) float: the normal render, for checks
        s.sway = {}                # (y, x) -> rgb, last writer wins (turned into an array by finish)
        s.sprites = {}             # id(thing) -> dict(thing, rgba, x, y, foot): a later draw replaces
        s.shadow = {}              # (y, x) -> factor the ground is darkened by
        s.sway_h = {}              # (y, x) -> how high above its plant's foot a swaying pixel sits
        s.pass_ = 'ground'
        s.cut_sway = []            # masks of sway pixels a later zone lifted off again (zone 2: cut heads)
        s.scratch = None
        s.brooks = []              # the Brooks drawn (their centre lines give the stream sounds)
        s.masks = {}               # name -> (H, W) bool on the canvas: paths, brooks, lake, shallow, flat things

    def finish(s, H, W):
        sw = np.zeros((H, W, 4), np.uint8)
        for (y, x), c in s.sway.items():
            if 0 <= y < H and 0 <= x < W:
                sw[y, x, :3] = np.clip(c, 0, 255)
                sw[y, x, 3] = 255
        hh = np.zeros((H, W), np.uint8)              # poppy heads (not in sway_h) sway whole: 255
        hh[sw[..., 3] > 0] = 255
        for (y, x), h in s.sway_h.items():
            if 0 <= y < H and 0 <= x < W:
                hh[y, x] = min(254, h)
        for m in s.cut_sway:
            sw[:m.shape[0]][m] = 0
        hh[sw[..., 3] == 0] = 0
        s.sway = sw
        s.sway_h = hh
        s.shadow_px = list(s.shadow.keys())
        g = s.ground.copy()
        for (y, x), k in s.shadow.items():
            if 0 <= y < H and 0 <= x < W:
                g[y, x] *= k
        s.ground = g
        s.sprites = [v for v in s.sprites.values() if (v['rgba'][..., 3] > 0).any()]   # wholly off the canvas: none


def _box_of(t, img):
    """Generous region a thing may paint in: its box with a margin, else around its foot."""
    H, W = img.shape[:2]
    if hasattr(t, 'box'):
        x0, y0, x1, y1 = t.box()
    else:                                                      # Fir: a pine with its point
        x0, y0, x1, y1 = t.p.x - 40, t.p.y - 80, t.p.x + 40, t.p.y + 12
    m = 24
    return (max(0, int(x0) - m), max(0, int(y0) - m), min(W, int(x1) + m), min(H, int(y1) + m))


def _call(orig, t, img, rest):
    return orig(t, img, *rest)


def _wrap(cls, kind):
    orig = cls.draw

    def draw(t, img, *rest):
        c = _active
        if c is None:
            return orig(t, img, *rest)
        if c.pass_ == 'ground':
            return None if kind != 'flat' else orig(t, img, *rest)
        if img.shape[1] != z1.W:                               # a sideways jetty draws on the turned picture:
            return orig(t, img, *rest)                         # the outer call records it
        x0, y0, x1, y1 = _box_of(t, img)
        if kind == 'flat':                                     # where it lies, by kind: bridges, stones, the jetty
            before = img[y0:y1, x0:x1].copy()
            out = orig(t, img, *rest)
            ch = np.abs(img[y0:y1, x0:x1] - before).sum(-1) > 0.5
            _mark(c, type(t).__name__, img.shape, (y0, y1, x0, x1), ch)
            return out
        before = img[y0:y1, x0:x1].copy()
        out = orig(t, img, *rest)
        after = img[y0:y1, x0:x1]
        if kind == 'sway':
            ys, xs = np.nonzero(np.abs(after - before).sum(-1) > 0.5)
            foot = getattr(t, 'order', None) or t.box()[3]
            for j, i in zip(ys, xs):
                c.sway[(y0 + j, x0 + i)] = after[j, i].copy()
                c.sway_h[(y0 + j, x0 + i)] = max(0, foot - (y0 + j))
            return out
        if c.scratch is None or c.scratch.shape != img.shape:   # the sentinel run on a private canvas
            c.scratch = np.zeros(img.shape)
        probe = c.scratch
        probe[y0:y1, x0:x1] = SENTINEL
        orig(t, probe, *rest)
        p = probe[y0:y1, x0:x1]
        hit = np.abs(p - SENTINEL).sum(-1) > 0.5
        shade = hit & (p[..., 1] < 1.0) & (np.abs(p[..., 0] - p[..., 2]) < 2.0)   # only darkened: a shadow
        cover = hit & ~shade
        rgba = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        rgba[cover, :3] = np.clip(after[cover], 0, 255).astype(np.uint8)
        rgba[cover, 3] = 255
        for j, i in zip(*np.nonzero(shade)):
            c.shadow[(y0 + j, x0 + i)] = p[j, i, 0] / 255.0
        foot = t.p.y if isinstance(t, z1.Fir) else (getattr(t, 'order', None) or t.box()[3])
        frames = 1
        if hasattr(t, 'draw_frame'):                           # lanterns: a strip of frames, as gen_world cuts them
            frames = t.frames
            base = c.ground[y0:y1, x0:x1]
            strip = []
            for k in range(frames):
                im = c.scratch                                 # only the box is drawn into and read back
                im[y0:y1, x0:x1] = base
                t.draw_frame(im, k)
                f = im[y0:y1, x0:x1]
                a = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
                a[..., :3] = np.clip(f, 0, 255).astype(np.uint8)
                a[..., 3] = np.any(np.abs(f - base) > 0.5, axis=2) * 255
                strip.append(a)
            rgba = np.concatenate(strip, axis=1)
        c.sprites[id(t)] = dict(thing=t, rgba=rgba, x=x0, y=y0, foot=int(round(foot)), frames=frames,
                                w=x1 - x0, h=y1 - y0)
        return out

    draw._orig = orig
    cls.draw = draw


def _mark(c, name, shape, reg, m):
    full = c.masks.get(name)
    if full is None or full.shape != shape[:2]:
        grown = np.zeros(shape[:2], bool)
        if full is not None:                                   # zone canvases grow downwards: keep what is there
            grown[:full.shape[0]] = full[:shape[0]]
        full = c.masks[name] = grown
    y0, y1, x0, x1 = reg
    full[y0:y1, x0:x1] |= m


def _wrap_fn(mod, name, record):
    orig = getattr(mod, name)
    if hasattr(orig, '_orig'):
        return

    def fn(*a, **k):
        if _active is not None and _active.pass_ == 'full':
            record(_active, *a, **k)
        return orig(*a, **k)

    fn._orig = orig
    setattr(mod, name, fn)


def _rec_path(c, img, pm, *rest):
    _mark(c, 'path', img.shape, (0, pm.shape[0], 0, pm.shape[1]), pm)


def _rec_lake(c, img, y0, lake, shallow, *rest, **k):
    H = lake.shape[0]
    _mark(c, 'lake', img.shape, (y0, y0 + H, 0, lake.shape[1]), lake)
    _mark(c, 'shallow', img.shape, (y0, y0 + H, 0, lake.shape[1]), shallow & lake)


def _wrap_brooks():
    orig = ow.Brooks.draw
    if hasattr(orig, '_orig'):
        return

    def draw(b, img, rng):
        if _active is not None and _active.pass_ == 'full':
            _mark(_active, 'brook', img.shape, (b.y0, b.y0 + b.H, 0, b.W), b.mask)
            _active.brooks.append(b)
        return orig(b, img, rng)

    draw._orig = orig
    ow.Brooks.draw = draw


def _install():
    for k, group in (('sway', SWAY), ('flat', FLAT), ('stand', STAND)):
        for cls in group:
            if not hasattr(cls.draw, '_orig'):
                _wrap(cls, k)
    z1.HOOKS.update(heads=heads_shown, lift=lift_heads, old=old_sprites_shown)
    import extras
    _wrap_fn(extras, 'draw_path', _rec_path)
    _wrap_fn(ol, 'paint_lake', _rec_lake)
    _wrap_brooks()


def heads_shown(heads):
    """Zone 1 lays its poppy heads over the ground: in the ground pass they stay off, in the normal pass
    they go to the sway layer. Returns whether the draft should composite them into its picture."""
    c = _active
    if c is None:
        return True
    if c.pass_ == 'ground':
        return False
    ys, xs = np.nonzero(heads[..., 3] > 0)
    for j, i in zip(ys, xs):
        c.sway[(j, i)] = heads[j, i, :3].astype(float)
    return True


def lift_heads(mask):
    """Zone 2 lifts the cut blossoms on zone 1's last row off again: do the same in the sway layer."""
    if _active is not None and _active.pass_ == 'full':
        _active.cut_sway.append(mask.copy())


def old_sprites_shown():
    """Zone 1 paints the old world's sprites (the camp) for context; the game has them as sprites already."""
    return _active is None or _active.pass_ == 'full'


_install()


@contextlib.contextmanager
def collect():
    """Two renders of zone 4 (which renders zones 1-3 below it), the ground pass first."""
    global _active
    import zone4_draft as z4
    import json, os
    with open(os.path.join(z1.ROOT, 'build', 'world_old', 'world_old.json')) as f:
        w = json.load(f)
    c = Collected()
    _active = c
    try:
        c.pass_ = 'ground'
        c.ground = z4.render(w, raw=True)[0].copy()
        c.pass_ = 'full'
        res = z4.render(w, raw=True)
        c.raw, c.lights, c.swarms, c.band, c.edge_fog, c.calm = res
        c.finish(*c.raw.shape[:2])
    finally:
        _active = None
    yield c
