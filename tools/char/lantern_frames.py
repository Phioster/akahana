"""Draws the wanderer hanging his lantern on the staff (Philip, 2026-11-04): 4 facings x 4 phases, 16x16 frames
(the 12x16 idle frame with 2 px room each side for the arm). Played 0..3 to hang it up, 3..0 to take it down."""
import sys
import numpy as np
from PIL import Image

PAD = 2
E = (38, 34, 36)          # sleeve (the robe's darkest)
F = (196, 168, 146)       # hand
WOOD = (156, 126, 94)
CAP = (52, 38, 34)
RED = (196, 62, 44)
HOT = (255, 186, 104)
DEEP = (120, 34, 30)


def lantern(px, cx, top):
    """The lantern with its cap row at y=top, middle column cx (same pixels as scenes/lantern.gd)."""
    for x in (cx - 1, cx, cx + 1):
        px(x, top, CAP)
    px(cx - 1, top + 1, RED); px(cx, top + 1, HOT); px(cx + 1, top + 1, RED)
    px(cx - 1, top + 2, DEEP); px(cx, top + 2, RED); px(cx + 1, top + 2, DEEP)
    px(cx, top + 3, CAP)


def hung(px, tx, cx, ty=1):
    for x in range(min(tx, cx), max(tx, cx) + 1):
        if x != tx:
            px(x, ty, WOOD)
    px(cx, ty + 1, CAP)
    lantern(px, cx, ty + 2)


def held(px, hand, sleeve):
    """Lantern dangling from the hand: string under it, then the lantern."""
    for s in sleeve:
        px(*s, E)
    hx, hy = hand
    px(hx, hy + 1, CAP)
    lantern(px, hx, hy + 2)
    px(hx, hy, F)


# per facing: staff tip x, lantern middle x, and the four phases (sleeve pixels, hand, hung?)
FRONT = dict(tx=9, cx=10, phases=[
    dict(sleeve=[(9, 9)], hand=(9, 10)),
    dict(sleeve=[(9, 8), (10, 7)], hand=(11, 6)),
    dict(sleeve=[(9, 8), (9, 7), (10, 6), (10, 5), (10, 4), (11, 3)], hand=(11, 2), hung=True),   # straight, behind the lantern
    dict(sleeve=[(9, 8)], hand=(10, 9), hung=True, free=True),
])
BACK = dict(tx=2, cx=1, phases=[
    dict(sleeve=[(2, 9)], hand=(2, 10)),
    dict(sleeve=[(2, 8), (1, 7)], hand=(0, 6)),
    dict(sleeve=[(2, 8), (2, 7), (1, 6), (1, 5), (1, 4), (0, 3)], hand=(0, 2), hung=True),
    dict(sleeve=[(2, 8)], hand=(1, 9), hung=True, free=True),
])
LEFT = dict(tx=7, cx=8, phases=[                # the lantern lies right against the staff (Philip: no gap);
    dict(sleeve=[(8, 9)], hand=(8, 10)),           # the arm stays close behind the body (across it read worse)
    dict(sleeve=[(8, 8), (8, 7)], hand=(9, 6)),
    dict(sleeve=[(8, 8), (8, 7), (8, 6), (9, 5), (9, 4), (9, 3)], hand=(9, 2), hung=True),
    dict(sleeve=[(8, 8)], hand=(8, 9), hung=True, free=True),
])


def mirrored(spec, k=10):
    m = lambda p: (k - p[0], p[1])
    return dict(spec, tx=k - spec['tx'], cx=k - spec['cx'], phases=[
        dict(ph, sleeve=[m(s) for s in ph['sleeve']], hand=m(ph['hand'])) for ph in spec['phases']])


SPECS = [FRONT, BACK, LEFT, mirrored(LEFT)]   # Player.Dir: DOWN, UP, LEFT, RIGHT


def build(sheet_path, out_path):
    sheet = np.array(Image.open(sheet_path).convert('RGBA'))
    out = np.zeros((64, 64, 4), np.uint8)
    for row, spec in enumerate(SPECS):
        base = sheet[row * 16:row * 16 + 16, 0:12]
        for k, ph in enumerate(spec['phases']):
            f = np.zeros((16, 16, 4), np.uint8)
            f[:, PAD:PAD + 12] = base

            def px(x, y, c):
                if 0 <= x + PAD < 16 and 0 <= y < 16:
                    f[y, x + PAD] = (*c, 255)
            if ph.get('hung'):                       # the arm reaches up behind the lantern: lantern over it
                for s in ph['sleeve']:
                    px(*s, E)
                hung(px, spec['tx'], spec['cx'])
                px(*ph['hand'], F)
            else:
                held(px, ph['hand'], ph['sleeve'])
            out[row * 16:row * 16 + 16, k * 16:k * 16 + 16] = f
    Image.fromarray(out).save(out_path)


if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'assets/char/wanderer.png',
          sys.argv[2] if len(sys.argv) > 2 else 'assets/char/wanderer_laterne.png')
