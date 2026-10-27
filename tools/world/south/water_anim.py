"""Moving water, as the game's water shader draws it (shaders/water.gdshader is a port of this): the
brooks' streaks drift downstream, the lake ripples calmly, each in the palette and the formula the
generator painted it with. Input is the ground and the water map (gen_south.water_map)."""
import numpy as np

import objects_water as ow

WATER = np.array(ow.WATER, float)
OLD_WAT = np.array([(0x3c, 0x46, 0x50), (0x4e, 0x5a, 0x65), (0x64, 0x71, 0x7c), (0x7f, 0x8c, 0x96),
                    (0xa3, 0xae, 0xb6), (0xd6, 0xdd, 0xe1)], float)
K_NEW = 2 * np.pi * 22 / 256        # streaks along the new brooks (whole periods in 256 px: no seam)
LOOP = 8.0                          # seconds, as the wallpaper and the lights: everything comes round together
W_NEW = 2 * np.pi * 5 / LOOP        # streak phase speed: 5 whole turns a loop = about 7.3 px/s downstream
W_LAKE = 2 * np.pi / LOOP


def hash2(x, y, s=0.0):
    x, y = np.mod(x, 289.0), np.mod(y, 289.0)                  # as the shader: small arguments for 32-bit sin
    return (np.sin(x * 12.9898 + y * 78.233 + s) * 43758.5453) % 1.0


def animate(ground, wmap, x0, y0, t):
    """ground (h, w, 3) and its water map (h, w, 4) cut at world (x0, y0); returns the ground at time t."""
    out = ground.astype(float).copy()
    h, w = ground.shape[:2]
    yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w].astype(float)
    kind = wmap[..., 3]
    ang = wmap[..., 0] / 256.0 * 2 * np.pi
    dep = wmap[..., 1] / 255.0
    along = wmap[..., 2].astype(float)
    fx, fy = np.cos(ang), np.sin(ang)
    n = hash2(xx, yy) * 2 - 1
    h2 = hash2(xx, yy, 1.7)

    m = kind == 2                                                # the new brooks
    across = xx * fy - yy * fx
    streak = np.sin(along * K_NEW - t * W_NEW + 2.2 * np.sin(across * 0.9) + 0.8 * n)
    v = 0.62 - 0.38 * dep + 0.06 * n
    v = np.where(streak > 0.82, v + 0.28, v)
    v = np.where((streak > 0.97) & (h2 < 0.5), 0.97, v)
    out[m] = WATER[np.clip(np.round(v * 4), 0, 4).astype(int)][m]

    m = kind == 1                                                # the old brook, in gen_world's look
    rip = np.sin(along * K_NEW - t * W_NEW + 2.2 * np.sin(across * 0.9) + 0.8 * n)   # the new brooks' streaks:
                                                                # wavering across the stream, not straight bars
    base = np.clip(((0.52 - 0.22 * dep + 0.06 * (h2 - 0.5)) * 6).astype(int), 0, 3)
    wi = np.where(rip > 0.82, np.minimum(base + 1, 3), base)    # a streak lifts one step, never to the near-white
                                                                # ones: in the snow they glittered
    wi = np.where((rip > 0.97) & (h2 < 0.06), 4, wi)          # now and then a glint
    wi = np.where((dep < 0.25) & (h2 < 0.15), 4, wi)          # light catching on the bank, still
    out[m] = OLD_WAT[wi][m]

    m = kind == 3                                                # the lake and the pools: calm ripples
    v = 0.6 - 0.45 * dep + 0.05 * n
    idx = np.clip(np.round(v * 4), 0, 4).astype(int)
    ripple = np.sin(xx * 0.45 + 3.0 * np.sin(yy * 0.35 + t * W_LAKE) + n + t * 2 * W_LAKE) > 0.93
    ripple &= (yy % 3 == 0) & (h2 < 0.6)
    idx = np.where(ripple, 4, idx)
    out[m] = WATER[idx][m]
    return out
