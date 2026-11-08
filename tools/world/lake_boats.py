"""Where the old boats lie in the two lakes (Philip's girlfriend, 2026-11-08: rafts and small old wooden boats, some
half sunk, some grown over at the shore): a raft on open water not far out, wrecks in the shallows, overgrown boats
on the bank. Chosen by rule from the finished maps (water, walk, paths, sprite feet) with fixed dice, so a rebuild
puts them in the same places. -> list of (kind, x, y, ang, seed) in world pixels."""
import numpy as np
from scipy import ndimage as ndi

LAKES = {'west': (399, 4061, 890, 4671), 'sued': (983, 4099, 1711, 4628)}
COUNT = {'floss': 2, 'wrack': 3, 'ufer': 2}


def place(kind_map, walk, mat, boxes, plants, seed=501):
    """kind_map: water kind (A of water.png); walk: bool; mat: per 2 px cell; boxes: [(x0, y0, x1, y1)] of standing
    things (whole pictures: a crown counts); plants: bool, where reeds and grass stand (flowers alpha)."""
    rng = np.random.default_rng(seed)
    out = []
    for name, (x0, y0, x1, y1) in LAKES.items():
        lake = kind_map[y0:y1, x0:x1] == 3
        lab, k = ndi.label(lake)
        big = np.argmax(np.bincount(lab.ravel())[1:]) + 1
        lake = lab == big
        din = ndi.distance_transform_edt(lake)                         # how far out on the water
        dout = ndi.distance_transform_edt(~lake)                       # how far up the bank
        path = np.kron(mat[y0 // 2:y1 // 2, x0 // 2:x1 // 2] == 1, np.ones((2, 2), bool))[:y1 - y0, :x1 - x0]
        busy = ndi.binary_dilation(path, iterations=8)
        for bx0, by0, bx1, by1 in boxes:
            if bx1 < x0 - 20 or bx0 > x1 + 20 or by1 < y0 - 20 or by0 > y1 + 20:
                continue
            busy[max(0, by0 - y0 - 10):max(0, by1 - y0 + 10), max(0, bx0 - x0 - 16):max(0, bx1 - x0 + 16)] = True
        reeds = ndi.binary_dilation(plants[y0:y1, x0:x1] & lake, iterations=6)   # the reed belt on the water
        taken = []

        def pick(ok, n, kind, spread=110):
            ys, xs = np.nonzero(ok)
            order = rng.permutation(len(ys))
            got = 0
            for i in order:
                x, y = int(xs[i]), int(ys[i])
                if any(np.hypot(x - a, y - b) < spread for a, b in taken):
                    continue
                taken.append((x, y))
                out.append((kind, x + x0, y + y0, float(rng.uniform(-0.6, 0.6)), int(rng.integers(1, 999))))
                got += 1
                if got >= n:
                    return
        pick((din > 18) & (din < 34) & ~busy, COUNT['floss'], 'floss')
        pick((din > 6) & (din < 16) & ~busy & ~reeds, COUNT['wrack'], 'wrack')   # in front of the reeds
        land = walk[y0:y1, x0:x1] & ~busy
        land = ndi.binary_erosion(land, iterations=7)                 # room all round it
        pick((dout > 20) & (dout < 28) & land, COUNT['ufer'], 'ufer')   # half a boat plus room from the water
    return out


def flatten(flowers, bend, kind_map, x, y, L, seed):
    """The grass round a beached boat lies flat, not cut out (Philip, 2026-11-08: the oval looked made): each blade
    is kept or laid down whole, by where its foot stands - near the boat most are down, further out fewer and fewer,
    the rim frayed by noise. Only on land: the reeds in the water stay. Changes flowers and bend in place."""
    import bendcode
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = x - L, y - 26, x + L + 1, y + 24
    fl, bd = flowers[y0:y1, x0:x1], bend[y0:y1, x0:x1]
    h, w = fl.shape[:2]
    noise = ndi.gaussian_filter(rng.random((h + 40, w)), 3)
    noise = (noise - noise.min()) / (np.ptp(noise) + 1e-6)
    keyr = rng.random((h + 40, w))                                     # one die per blade (its foot)
    jj, ii = np.nonzero(fl[..., 3] > 0)
    b = bd[jj, ii].astype(int)
    foot = jj + np.where(b >= 255, 0, bendcode.height(b))              # where each pixel's blade stands
    foot = np.clip(foot, 0, h + 39)
    e = ((ii - L) / (L / 2 + 9.0)) ** 2 + ((foot - 26 + 3) / 13.0) ** 2 + 0.55 * (noise[foot, ii] - 0.5)
    p = np.clip((1.0 - e) / 0.55, 0, 1) ** 0.8 * 0.92
    land = kind_map[np.clip(y0 + foot, 0, kind_map.shape[0] - 1), x0 + ii] == 0
    down = land & (keyr[foot, ii] < p)
    fl[jj[down], ii[down], 3] = 0
