"""Collects the west drafts the way south/layers.py collects the south (east/collect.py the Ostwald): the west's
thing classes are registered with the south's wrappers (standing things become sprites with their foot, flat ones
stay in the ground, swaying ones go to the sway layer). The mill splits into three sprites so the game can turn
its wheel and run its water: the house with the trough and posts (still), the wheel (WHEEL_FRAMES at WHEEL_FPS,
one whole turn) and the water (WATER_FRAMES at WATER_FPS: glints in the trough, the fall onto the paddles).

    c = collect_window(lambda: render_something(), width)
"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..')]
import layers  # noqa: E402
import objects_west as o  # noqa: E402

STAND = (o.Minka, o.Brunnen, o.Hortensie, o.Bambuszaun, o.Steinmauer, o.Obstbaum, o.Waescheleine, o.Korb,
         o.Gewaechshaus, o.Block, o.Steinmetz, o.Torii, o.Komainu, o.Yashiro, o.Shinboku, o.Kaki, o.Leiter,
         o.Bambus, o.Vogelscheuche, o.Teehaus, o.Netzgestell, o.Hasagi, o.SanfteBank, o.Holzstapel)
FLAT = (o.Beet, o.Platten, o.Treppe)
SWAY = (o.Iris,)

WHEEL_FRAMES, WHEEL_FPS = 288, 8          # 36 s: one turn (Muehle.TURN), the broken paddles come round again
WATER_FRAMES, WATER_FPS = 36, 10          # 3.6 s: the trough's glints (periods 9 and 18 px at 5 px/s)
FALL_SPEED = 4 / 0.6                      # the fall's glint (period 4 px) once in 0.6 s, so it loops with them


class MillHouse:
    """The mill's house with its trough and posts and the weir: all that stands still."""
    def __init__(s, m):
        s.m = m
        s.order = m.y

    def box(s):
        return s.m.box()

    def draw(s, img, G):
        s.m.house.draw(img, G)
        s.m.draw_boards(img)
        s.m.draw_posts(img)


class MillWheel:
    """The wheel, turning: frame k is k / WHEEL_FRAMES of a turn."""
    frames = WHEEL_FRAMES

    def __init__(s, m, G):
        s.m, s.G = m, G

    def box(s):
        return s.m.wheel.box()

    def draw(s, img, G):
        s.m.wheel.rot = 0.0
        s.m.wheel.draw(img, G)

    def draw_frame(s, img, k):
        s.m.wheel.rot = 2 * np.pi * k / s.frames
        s.m.wheel.draw(img, s.G)


class MillWater:
    """The water in the trough and the fall onto the paddles, over the wheel."""
    frames = WATER_FRAMES

    def __init__(s, m):
        s.m = m
        s.order = m.wheel.box()[3] + 1

    def box(s):
        wx, wy, r, x1, y1, xi, cyi, x0, y0, n, fall, rim = s.m._geom()
        return (x0 - 1, min(y0, y1) - 2, x1 + 4, max(y0, y1, rim) + 3)

    def draw(s, img, G):
        s.draw_frame(img, 0)

    def draw_frame(s, img, k):
        t = k / float(WATER_FPS)
        s.m.draw_water(img, t)
        s.m.draw_fall(img, t, FALL_SPEED)


class NwThing:
    """One standing thing of the north-west corner as north/common.draw_things draws it (pine, rock, log, stump):
    the item (foot, kind, args) with the canvas's own noise."""
    def __init__(s, item, G, CL):
        s.item, s.G, s.CL = item, G, CL
        s.order = int(round(item[0]))

    def box(s):
        _, kind, a = s.item
        if kind == 'pine':
            x, y, h = a[0], a[1], a[2]
            return (x - 16, y - h - 8, x + 17, y + 6)
        if kind == 'rock':
            x, y, r = a
            rr = max(2, int(r * 0.9))
            return (x - rr - 4, y - 2 * rr - 4, x + rr + 6, y + 6)
        if kind == 'log':
            return (min(a[0], a[2]) - 8, min(a[1], a[3]) - 10, max(a[0], a[2]) + 8, max(a[1], a[3]) + 8)
        x, y = a[0], a[1]                                              # stump
        return (x - 10, y - 12, x + 12, y + 6)

    def draw(s, img, G):
        from common import draw_things
        draw_things(img, [s.item], s.G, s.CL)


for cls in STAND + (MillHouse, MillWheel, MillWater, NwThing, o.Verschneit):
    if not hasattr(cls.draw, '_orig'):
        layers._wrap(cls, 'stand')
for cls in FLAT + (o.VerschneitFlat,):
    if not hasattr(cls.draw, '_orig'):
        layers._wrap(cls, 'flat')
for cls in SWAY:
    if not hasattr(cls.draw, '_orig'):
        layers._wrap(cls, 'sway')

_mill_draw = o.Muehle.draw


def _muehle_draw(m, img, G):
    """While collecting, the mill is three things; otherwise it draws as approved (frame t)."""
    if layers._active is None:
        return _mill_draw(m, img, G)
    if layers._active.pass_ == 'ground':
        return None
    MillHouse(m).draw(img, G)
    MillWheel(m, G).draw(img, G)
    MillWater(m).draw(img, G)


o.Muehle.draw = _muehle_draw
FPS = {'MillWheel': WHEEL_FPS, 'MillWater': WATER_FPS, 'Steinlaterne': 8}


def collect_window(render, width):
    """Two renders of the same window (same seeds), the ground pass first. Returns the Collected with .ground,
    .sway, .sway_h, .sprites (window pixels, each with its fps), .masks and .result (the full pass's return)."""
    c = layers.Collected()
    c.W = width
    layers._active = c
    try:
        c.pass_ = 'ground'
        res = render()
        c.ground = res[0].copy()
        c.pass_ = 'full'
        c.result = render()
        c.raw = c.result[0]
        c.finish(*c.raw.shape[:2])
    finally:
        layers._active = None
    for sp in c.sprites:
        sp['fps'] = FPS.get(type(sp['thing']).__name__, 8)
    return c
