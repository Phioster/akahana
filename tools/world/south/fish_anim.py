"""Hints of fish in the lake: dark slim shapes drifting under the surface, now and then turning, and
once in a while one rising, a small ring spreading on the water where it touched. Only ever a hint: a calm,
slightly lighter shape in the restless water, (never drawn over land, the floor of the shallows, lilies or stones).
In the game: a few Fish nodes per lake chunk doing the same."""
import numpy as np

LOOP = 8.0
DARK = np.array([66.0, 90.0, 98.0])            # a fish just under the surface shows lighter: the dusk
                                               # grade sinks a dark one into the deep water's black
GLINT = np.array([127.0, 152.0, 156.0])
RIM = np.array([85.0, 112.0, 121.0])


class Fish:
    def __init__(s, home, rng, reach=16.0):
        s.hx, s.hy = home
        s.ax, s.ay = rng.uniform(0.6, 1.0) * reach, rng.uniform(0.35, 0.7) * reach
        s.w1, s.w2 = 2 * np.pi * rng.choice([1, 2]) / LOOP, 2 * np.pi * rng.choice([1, 2, 3]) / LOOP
        s.p1, s.p2 = rng.uniform(0, 6.3), rng.uniform(0, 6.3)
        s.len = int(rng.integers(7, 10))
        s.rise = rng.uniform(0, LOOP)                               # when in the loop it touches the surface
        s.rises = rng.random() < 0.5

    def at(s, t):
        x = s.hx + s.ax * np.sin(s.w1 * t + s.p1)
        y = s.hy + s.ay * np.sin(s.w2 * t + s.p2)
        dx = s.ax * s.w1 * np.cos(s.w1 * t + s.p1)
        dy = s.ay * s.w2 * np.cos(s.w2 * t + s.p2)
        return x, y, np.arctan2(dy, dx)


def draw(img, x0, y0, water, fishes, t):
    """img: picture cut at world (x0, y0); water: bool mask (deep lake water) of the same cut."""
    h, w = water.shape
    for f in fishes:
        x, y, ang = f.at(t)
        ca, sa = np.cos(ang), np.sin(ang)
        L = f.len / 2.0
        r = int(L) + 3
        body, rim = [], []
        for j in range(int(y) - r, int(y) + r + 1):                 # a calm spindle in the restless water:
            for i in range(int(x) - r, int(x) + r + 1):             # solid dark, a lighter rim where it lifts
                u = (i - x) * ca + (j - y) * sa                      # the water above it
                v = -(i - x) * sa + (j - y) * ca
                half = 1.5 * max(0.0, 1 - (u / L) ** 2) ** 0.5 + (0.6 if -L < u < -L + 1.5 else 0)   # tail fin
                if abs(u) <= L and abs(v) <= half:
                    body.append((i, j))
                elif u > L * 0.3 and abs(u) <= L + 1 and abs(v) <= half + 1 and (i * 7 + j * 3) % 3:
                    rim.append((i, j))                               # only at its head: a faint, broken bow wave
        for (i, j) in rim:
            if 0 <= i - x0 < w and 0 <= j - y0 < h and water[j - y0, i - x0]:
                img[j - y0, i - x0] = RIM
        for (i, j) in body:
            if 0 <= i - x0 < w and 0 <= j - y0 < h and water[j - y0, i - x0]:
                img[j - y0, i - x0] = DARK
        turn = abs(np.sin(f.w1 * t + f.p1)) < 0.12                   # turning, its flank catches the light
        i, j = int(round(x)) - x0, int(round(y)) - y0
        if turn and 0 <= i < w and 0 <= j < h and water[j, i]:
            img[j, i] = GLINT
        if f.rises:                                                  # a ring spreading where it rose
            age = (t - f.rise) % LOOP
            if age < 1.6:
                r = 1.5 + age * 3.0
                for a in np.linspace(0, 2 * np.pi, int(8 + r * 5), endpoint=False):
                    i = int(round(f.hx + f.ax * np.sin(f.w1 * f.rise + f.p1) + r * np.cos(a))) - x0
                    j = int(round(f.hy + f.ay * np.sin(f.w2 * f.rise + f.p2) + 0.6 * r * np.sin(a))) - y0
                    if 0 <= i < w and 0 <= j < h and water[j, i]:
                        img[j, i] = img[j, i] * 0.6 + np.array([127.0, 152.0, 156.0]) * 0.4 * (1 - age / 1.6) \
                            + img[j, i] * 0.4 * (age / 1.6)
