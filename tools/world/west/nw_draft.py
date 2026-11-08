#!/usr/bin/env python3
"""West zone 5 draft: the north-west corner above the village (x 0..WW, y 0..~1500), which the plan gives to the
snowy fir wood carrying on from Kogarashi and the north. Built from the north's own pieces (north/common,
objects_north): the ridge of angular rocks under mist at the top, the gorge of zone 2 running on west and petering
out, wind-swept rock below the ridge, and the needle wood thickening downwards into the village's forest.
Today's world (build/world_full) is drawn for real east of WW, as in dorf1_draft.

    python3 nw_draft.py OUT.png [scale]"""
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
NORTH = os.path.join(HERE, '..', 'north')
sys.path[:0] = [HERE, NORTH, os.path.join(HERE, '..', 'lib')]
from common import fbm, smooth, snow_ground, Firs, draw_things, noise_maps, footpath, through, HN  # noqa: E402
import objects_west as o  # noqa: E402
from objects_north import Gorge, facet_rock  # noqa: E402
import importlib.util  # noqa: E402
_sp = importlib.util.spec_from_file_location('north_zone2', os.path.join(NORTH, 'zone2_draft.py'))
nz2 = importlib.util.module_from_spec(_sp)                        # the north's zone 2 (the gorge's line): by path,
_sp.loader.exec_module(nz2)                                        # the south has a zone2_draft too

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
FULL = os.path.join(ROOT, 'build', 'world_full')
WW = 900
X0, X1, Y0, Y1 = 0, 1020, 0, 1520          # west coordinates; today's x 0 = WW
W, H = X1 - X0, Y1 - Y0
MIX = 60                                   # today's ground takes over in clumps over these columns east of WW
QUARRY = (360, 362)                         # the old quarry under the ridge (Philip, round 2)
BRUCH = [(885, 1444), (862, 1394), (868, 1340), (830, 1282), (792, 1236), (772, 1172), (716, 1120), (682, 1052),
         (618, 1002), (590, 934), (532, 882), (500, 812), (444, 762), (430, 692), (394, 642), (404, 582), (374, 532),
         (380, 472), (368, 420), (364, 388)]          # up from the orchard path, the sled's way
GORGE_END = 610                            # where the crack runs out under the slope


def gorge_line():
    """Today's gorge (north zone 2) at its west end, carried on west: the same rise, narrowing out to nothing."""
    xs0, cy0, hw0 = nz2.gorge_line(np.random.default_rng(52))
    c0, h0 = cy0[0] + nz2.NY0, hw0[0]
    xs = np.arange(GORGE_END - 20, WW + 1)
    d = xs - WW                                                    # <= 0
    r = np.random.default_rng(53)
    wob = ndi.gaussian_filter1d(r.normal(0, 1, len(xs)), 14) * 10
    wob -= wob[-1]
    cy = c0 + 0.12 * d + 10 * np.sin(d / 130.0) + wob * smooth(-d / 60.0)
    k = smooth((xs - GORGE_END) / (WW - GORGE_END))
    hw = (h0 + 3.5 * np.sin(-d / 41.0) * smooth(-d / 40.0)) * k ** 0.3   # stays open, then closes quickly
    return xs, cy, np.maximum(hw, 0)


def today():
    g = np.array(Image.open(os.path.join(FULL, 'ground.png')).convert('RGB'))[Y0:Y1, :W - WW].astype(float)
    fl = np.array(Image.open(os.path.join(FULL, 'flowers.png')).convert('RGBA'))[Y0:Y1, :W - WW]
    w = json.load(open(os.path.join(ROOT, 'assets', 'world', 'world.json')))
    return g, fl, w


def paste(img, s, root):
    p = os.path.join(root, s['name'] + '.png')
    if not os.path.exists(p):
        return
    a = np.array(Image.open(p).convert('RGBA'))[:, :s['w']].astype(float)
    y0, x0 = s['y'] - Y0, s['x'] + WW - X0
    h, w = a.shape[:2]
    ya, yb, xa, xb = max(0, y0), min(img.shape[0], y0 + h), max(0, x0), min(img.shape[1], x0 + w)
    if ya < yb and xa < xb:
        sub = a[ya - y0:yb - y0, xa - x0:xb - x0]
        al = sub[..., 3:] / 255.0
        img[ya:yb, xa:xb] = img[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al


def render():
    """-> img (H, W, 3) float, the parts for gen_west: dict(ground, things, keep, gorge, ridge, today_w)."""
    rng = np.random.default_rng(81)
    yy, xx = np.mgrid[0:H, 0:W]
    gx, gy = xx + X0, yy + Y0
    west = gx < WW

    # ---- the shape of the land
    n1, n2 = fbm(rng, 30, (H, W)), fbm(rng, 9, (H, W))
    reach = 236 + 34 * np.sin(gx / 90.0) + 40 * n1 + 14 * n2           # the north's peaks at x 0 reach down ~250
    ridge = (gy < reach) | (gy < 40 + 20 * n2)
    xs, cy, hw = gorge_line()
    G0 = Gorge(xs - X0, cy - Y0, hw, seed=37)
    gm = G0.mask(H, W)

    # ---- where the wood stands: none up on the ridge, thin on the rock below it, dense from the old map's top
    rise = smooth((gy - 480) / 560.0)
    wood = smooth(0.10 + 0.58 * rise + 0.30 * fbm(rng, 40, (H, W)))
    wood *= smooth((gy - 300) / 200.0)
    glades = fbm(rng, 26, (H, W)) + 0.4 * fbm(rng, 8, (H, W)) > 1.15         # open snow between the stands
    wood = np.where(glades, wood * 0.15, wood)
    wood *= 0.45 + 0.55 * smooth((WW - 30 - gx) / 220.0)                    # today's edge is open snow: thin out to it
    wood = np.minimum(wood, 0.72)
    qb = o.Steinbruch(*QUARRY)
    qfloor, qface = qb.masks(H, W)
    qzone = ndi.binary_dilation(qfloor | qface, iterations=14)
    from PIL import ImageDraw
    pim = Image.new('L', (W, H), 0)
    ImageDraw.Draw(pim).line([tuple(p) for p in through(BRUCH, 400)], fill=255, width=10)
    bpath = np.array(pim) > 0
    wood = np.where(ndi.binary_dilation(qzone, iterations=10), 0.0, wood)
    bare = n1 * 0.6 + fbm(rng, 10, (H, W)) + 0.5 * fbm(rng, 3, (H, W)) > 1.5 - 1.9 * smooth((560 - gy) / 360.0)
    qx_, qy_ = QUARRY                                                  # the quarry is cut into a knoll of rock
    outcrop = (((gx - qx_) / 128.0) ** 2 + ((gy - qy_ + 52) / 92.0) ** 2 + 0.35 * fbm(rng, 12, (H, W))) < 1
    bare |= outcrop & (fbm(rng, 5, (H, W)) > -0.6)
    g = snow_ground(rng, H, W, Y0, wood, bare=bare)                    # north rows are world rows here
    G, CL = noise_maps(rng, H, W)

    # ---- today's ground east of WW, taking over in clumps (paths and gorge switch exactly at WW)
    og, ofl, w = today()
    oimg = og.copy()
    m = ofl[..., 3] > 0
    oimg[m] = ofl[m][..., :3]
    clumps = 0.5 + 0.28 * fbm(rng, 14, (H, W)) + 0.12 * fbm(rng, 3, (H, W))
    tw = smooth((gx - WW) / float(MIX))
    take = (clumps < tw) & ~west
    t0 = nz2.gorge_line(np.random.default_rng(52))                    # today's gorge: its pixels stay today's
    tg = Gorge(t0[0] + WW - X0, t0[1] + nz2.NY0 - Y0, t0[2]).mask(H, W)
    take |= ndi.binary_dilation(tg, iterations=5) & ~west
    img = g.copy()
    sub = img[:, WW - X0:]
    tk = take[:, WW - X0:]
    sub[tk] = oimg[tk]

    # ---- flat things into the ground: the quarry and its way, the gorge, the ridge heaps, the top mist
    qb.draw(img, G)
    qd = ndi.distance_transform_edt(~(qface | qfloor))                 # bedded rock round the cut, fraying outward
    bed_reach = 30 + 14 * fbm(rng, 10, (H, W)) + 18 * smooth((QUARRY[1] - 60 - gy) / 40.0)   # reaching up the slope
    bed = (qd < bed_reach) & ~qface & ~qfloor & (gy < QUARRY[1] + 4) & (qd > 0)
    bed |= (qd < 0.6 * bed_reach) & ~qface & ~qfloor & (gy < QUARRY[1] + 16) & (np.abs(gx - QUARRY[0]) > 60)
    o.bedrock(img, G, bed, fade=smooth((qd / np.maximum(bed_reach, 1) - 0.45) / 0.55))
    footpath(img, BRUCH, G, width=2.0, bank=1.8, rng_seed=7)
    G0.draw(img, G, CL)
    flat_rock = np.zeros((H, W), bool)
    ry_, rx_ = np.nonzero(ridge & (gx < WW + 26) & (qd > 40) & (rng.random((H, W)) < 0.012))   # over the seam: today's edge had none
    for y, x in sorted(zip(ry_, rx_)):
        big = 1.0 + 0.8 * smooth((200 - (y + Y0)) / 200.0)
        ys, xs_ = facet_rock(img, int(x), int(y), rng.uniform(9, 17) * big, rng.uniform(7, 12) * big, False,
                             int(x * 3 + y * 7), True)
        ok = (ys >= 0) & (ys < H) & (xs_ >= 0) & (xs_ < W)
        flat_rock[ys[ok], xs_[ok]] = True
    # the knoll's own rocks: heaped over the face's top and flanks, so the cut sits in living rock
    rq = np.random.default_rng(143)
    oy, ox = np.nonzero(outcrop & (qd > bed_reach + 4) & (rq.random((H, W)) < 0.010))   # beyond the beds only
    for y, x in sorted(zip(oy, ox)):
        r_ = rq.uniform(6, 13) * min(1.0, (qd[y, x] - bed_reach[y, x]) / 14.0 + 0.4)   # small where they begin
        ys, xs_ = facet_rock(img, int(x), int(y), r_, r_ * 0.7, False, int(x * 5 + y * 3), True)
        ok = (ys >= 0) & (ys < H) & (xs_ >= 0) & (xs_ < W)
        keep_ = ok.copy()
        keep_[ok] = ~(qface | qfloor)[ys[ok], xs_[ok]]
        flat_rock[ys[keep_], xs_[keep_]] = True
    BAY = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0
    mist = np.clip((70 - gy + 12 * fbm(rng, 20, (H, W))) / 70.0, 0, 1)
    mine = west | flat_rock                                            # also my rocks reaching over the seam
    on = (mist > BAY[gy % 4, gx % 4]) & mine
    img[on] = img[on] * 0.25 + np.array([214.0, 214, 212]) * 0.75
    ground = img.copy()

    # ---- standing things: firs, loose rocks (more higher up), a few felled trunks and stumps in the wood
    keep = ndi.binary_dilation(gm, iterations=6) | ridge | (gy < 60) | ~west | qzone
    lane = ndi.binary_dilation(bpath, iterations=5)
    for d in range(2, 44, 2):                                         # a fir's top reaches ~45 px above its foot
        keep[d:] |= lane[:-d]
    keep |= lane
    occ = Firs()
    for s in w['sprites']:                                           # today's things at the edge keep their room
        cx = s['x'] + s['w'] // 2 + WW - X0
        if s['x'] < 80 and s['foot'] < Y1:
            occ.claim(cx, s['foot'] - Y0, 6 if s['h'] > 30 else 3)
    things = occ.place(rng, wood * west, keep, Y0, tries=90000)
    for _ in range(700):
        x, y = int(rng.integers(6, WW - 4)), int(rng.integers(60, H - 4))
        if keep[y, x] or rng.random() > 0.08 + 0.9 * smooth((700 - (y + Y0)) / 300.0):
            continue
        things.append((y, 'rock', (x, y, int(rng.integers(3, 9)))))
    n_log = 0
    for _ in range(400):
        x, y = int(rng.integers(20, WW - 40)), int(rng.integers(760, H - 20))
        if keep[y, x] or not 0.12 < wood[y, x] < 0.4 or n_log >= 14:          # in the glades, where one sees them
            continue
        L = rng.uniform(14, 22)
        a = rng.uniform(-0.5, 0.5)
        things.append((y + 3, 'log', (x, y, int(x + L * np.cos(a)), int(y + L * np.sin(a)))))
        things.append((y + 6, 'stump', (x - 4, y + 6)))
        n_log += 1
    qx, qy = QUARRY                                                  # what was left in the quarry
    for (dx, dy, bw, bh, bd) in ((-52, -8, 10, 6, 3), (-30, 6, 7, 5, 3), (8, -14, 12, 7, 4), (34, 4, 6, 4, 2),
                                 (54, -6, 8, 5, 3), (-12, 14, 5, 3, 2)):
        things.append((qy + dy, 'obj', o.QBlock(qx + dx, qy + dy, w=bw, h=bh, d=bd, seed=150 + dx)))
    sx_, sy_ = qx - 64, qy + 16                                       # a stack by the way out
    for k, (bw, bh) in enumerate(((14, 6), (12, 5), (9, 4))):
        things.append((sy_ + 0.1 * k, 'obj', o.QBlock(sx_ + k, sy_, w=bw, h=bh, d=3, seed=160 + k)))
        sy_ -= bh + 1
    things.append((qy + 22, 'obj', o.Schlitten(qx - 14, qy + 22)))
    tr = np.random.default_rng(144)
    for _ in range(34):                                               # talus fallen from the face, rubble at the rim
        x_ = int(tr.integers(qx - 70, qx + 71))
        if tr.random() < 0.6:
            y_ = qb.foot.get(x_, qy - 20) + int(tr.integers(2, 7))
        else:
            ang = tr.uniform(0, np.pi)
            x_, y_ = int(qx + np.cos(ang) * 74), int(qy + np.sin(ang) * 24 + tr.integers(-2, 3))
        things.append((y_, 'rock', (x_, y_, int(tr.integers(2, 5)))))
    hr = np.random.default_rng(142)                                  # the spoil heap east of the way out
    for _ in range(26):
        a_, r_ = hr.uniform(0, 2 * np.pi), hr.uniform(0, 1) ** 0.6
        x_, y_ = int(qx + 88 + np.cos(a_) * 22 * r_), int(qy + 18 + np.sin(a_) * 12 * r_)
        things.append((y_, 'rock', (x_, y_, int(hr.integers(2, 5)))))

    def extra(kind, a):
        a.draw(img, G)
    draw_things(img, [t for t in things if t[1] in ('pine', 'rock', 'log', 'stump', 'obj')], G, CL, extra)

    # ---- today's standing things east of WW, as the game shows them (frame 0)
    root = os.path.join(ROOT, 'assets', 'world', 'sprites')
    for s in sorted(w['sprites'], key=lambda s: s['foot']):
        if s['x'] < W - WW + X0 and s['y'] < Y1 and s['x'] > 2:
            paste(img, s, root)
    return img, dict(ground=ground, things=things, keep=keep, gorge=gm, ridge=ridge, flat_rock=flat_rock,
                     wood=wood, quarry_floor=qfloor, quarry_face=qface, path=bpath)


def main(out, scale=1):
    img, _ = render()
    yy, xx = np.mgrid[0:H, 0:W]                                       # preview only: the west edge's mist as the
    BAY = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16.0   # game's mist field draws it
    e = 1 - smooth((xx + X0) / 30.0)
    on = e > BAY[yy % 4, xx % 4]
    img[on] = img[on] * 0.3 + np.array([200.0, 200, 198]) * 0.7
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if scale != 1:
        im = im.resize((int(W * scale), int(H * scale)), Image.NEAREST if scale > 1 else Image.LANCZOS)
    im.save(out)


if __name__ == '__main__':
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 1)
