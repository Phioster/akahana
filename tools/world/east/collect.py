"""Collects one east window (a forest band, a spot) the way south/layers.py collects the south: a ground pass
without the standing and swaying things, then a normal pass recording them. The east things are registered with
the south's wrappers here; their foot is their y.

    c = collect_window(lambda: render_something(), width)   # render returns (img, ...) in window pixels
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, '..', 'south'), os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..'), HERE]
import layers  # noqa: E402
import objects_east as oe  # noqa: E402

STAND = (oe.Riesenbaum, oe.Kahlbaum, oe.Knorrbaum, oe.MoosStein, oe.Grabstein, oe.Stele, oe.Steinhaufen,
         oe.Opferschale, oe.Stab, oe.Kreuz, oe.Jizo, oe.Schrein, oe.Altar, oe.Halle)
FLAT = (oe.Steinbruecke, oe.Pilzring)

for cls in STAND + FLAT:
    cls.order = property(lambda s: s.y)                        # the foot: where it stands, not its box's lower edge
for cls in STAND:
    if not hasattr(cls.draw, '_orig'):
        layers._wrap(cls, 'stand')
for cls in FLAT:
    if not hasattr(cls.draw, '_orig'):
        layers._wrap(cls, 'flat')


def collect_window(render, width):
    """Two renders of the same window (same seeds), the ground pass first. Returns the Collected with .ground
    (shadows applied), .sway, .sway_h, .sprites (window pixels), .masks and .result (the full pass's return value)."""
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
    return c
