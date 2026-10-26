"""Fireflies: small swarms hovering low over the poppies, each fly drifting on its own slow loop and
glowing up and down in its own rhythm, each with its own small light."""
import numpy as np

GLOW = [np.array(c, float) for c in ([224, 178, 84], [248, 214, 120], [255, 242, 176])]   # dim .. bright


class Swarm:
    def __init__(s, x, y, n=7, seed=1, spread=12.0):
        rng = np.random.default_rng(seed)
        s.x, s.y = x, y
        s.flies = [dict(ax=rng.uniform(-spread, spread), ay=rng.uniform(-spread * 0.6, spread * 0.4) - 4,
                        rx=rng.uniform(2, 6), ry=rng.uniform(1.5, 4), sp=rng.uniform(0.25, 0.6),
                        ph=rng.uniform(0, 6.28), blink=rng.uniform(0.35, 0.8), bph=rng.uniform(0, 6.28))
                   for _ in range(n)]

    def state(s, t):
        """[(x, y, brightness 0..1)] at time t (seconds)."""
        out = []
        for f in s.flies:
            a = f['ph'] + t * f['sp']
            x = s.x + f['ax'] + f['rx'] * np.sin(a) + 0.6 * f['rx'] * np.sin(2.3 * a + 1)
            y = s.y + f['ay'] + f['ry'] * np.sin(1.7 * a + 2)
            b = 0.2 + 0.8 * max(0.0, np.sin(f['bph'] + t * f['blink'] * 2.4)) ** 1.2   # a faint glimmer, then a glow
            out.append((x, y, b))
        return out

    def lights(s, t):
        """Every fly its own small light, moving and glowing with it (in the game: its own little glow
        list in the post shader, so the lamps keep their 16 slots)."""
        return [{'x': x + 0.5, 'y': y + 0.5, 'r': 7.0, 'k': 0.22 * b, 'kind': 'firefly'}
                for x, y, b in s.state(t) if b > 0.05]

    def draw(s, img, t):
        """The flies themselves, drawn after the mood pass: a lit pixel, brighter ones with a small halo."""
        H, W = img.shape[:2]
        for x, y, b in s.state(t):
            if b < 0.12:
                continue
            i, j = int(round(x)), int(round(y))
            c = GLOW[min(2, int(b * 3))]
            if 0 <= i < W and 0 <= j < H:
                img[j, i] = c
            if b > 0.45:                                       # glowing up: a small cross of light round it
                for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    ii, jj = i + di, j + dj
                    if 0 <= ii < W and 0 <= jj < H:
                        img[jj, ii] = np.maximum(img[jj, ii], GLOW[1 if b > 0.8 else 0])
