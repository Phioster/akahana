"""Ground for the south that grows out of the old world's ground instead of starting fresh: the light and
dark patches run on across the seam, then ease into new ones. Same look as field6.ground_organic."""
import os
import sys

import numpy as np
from scipy import ndimage as ndi

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'lib'))
from field6 import DG, MG, L1, WH, K  # noqa: E402

RAMP = np.array([DG, MG, L1, WH])
CUTS = [0.30, 0.48, 0.70]
CENTRE = np.array([0.22, 0.39, 0.59, 0.80])            # tone in the middle of each band


def tone_of(ground):
    """The smooth tone field behind a finished ground picture (which band each pixel is, blurred)."""
    d = ((ground[..., None, :] - RAMP[None, None]) ** 2).sum(-1)
    return ndi.gaussian_filter(CENTRE[d.argmin(-1)], 2.5)


def fresh_tone(H, W, fog, flow, rng):
    def fbm(scale, octs=4):
        out = np.zeros((H, W))
        a, t = 1, 0
        for _ in range(octs):
            n = ndi.gaussian_filter(rng.normal(0, 1, (H, W)), scale / (2 ** _))
            n /= n.std() + 1e-9
            out += a * n
            t += a
            a *= 0.5
        return out / t
    patch = fbm(10)
    return fog * 0.62 + 0.12 - 0.24 * np.clip(patch, -1.5, 1.5) / 1.5 - 0.15 * flow


def continued_tone(old_tone, new_tone, reach=44):
    """Below the seam: the old tone mirrored, handing over to the new one within `reach` rows."""
    out = new_tone.copy()
    n = min(reach, old_tone.shape[0], new_tone.shape[0])
    for d in range(n):
        a = (d / reach) ** 2 * (3 - 2 * d / reach)          # smoothstep
        out[d] = (1 - a) * old_tone[-1 - d] + a * new_tone[d]
    return out


def ground_from_tone(tone, fog, flow, rng):
    """field6.ground_organic, but from a given tone field."""
    H, W = tone.shape
    grain = ndi.gaussian_filter(rng.random((H, W)), 0.6)
    grain = (grain - grain.mean()) / grain.std()
    img = RAMP[np.digitize(tone + 0.10 * grain, CUTS)].astype(float)
    dens = 0.10 + 0.25 * (1 - fog) + 0.35 * flow
    for _ in range(int(H * W * 0.05)):                       # tufts: curved blades fanning from one root
        x, y = int(rng.integers(3, W - 3)), int(rng.integers(5, H - 1))
        if rng.random() > dens[y, x]:
            continue
        c = K if rng.random() < 0.35 else DG
        nb = int(rng.integers(3, 6))
        lean = rng.normal(0.4, 0.3)
        for b in range(nb):
            spread = (b - (nb - 1) / 2) * 0.55 + lean
            L = int(rng.integers(2, 5))
            for s in range(L):
                bx = x + int(round(spread * s * 0.7 + 0.15 * s * s * np.sign(spread)))
                by = y - s
                if 0 <= bx < W and 0 <= by < H:
                    img[by, bx] = c if s < L - 1 else (DG if c is K else MG)
    for _ in range(int(H * W * 0.0015)):                     # pebbles with a lit top-left pixel
        x, y = int(rng.integers(2, W - 3)), int(rng.integers(2, H - 3))
        if flow[y, x] > 0.3:
            continue
        w, h = int(rng.integers(2, 4)), int(rng.integers(1, 3))
        img[y:y + h, x:x + w] = MG
        img[y, x] = WH
        img[y + h - 1, x + w - 1] = DG
    return img
