#!/usr/bin/env python3
"""The world grows south and east: the approved zone drafts and the placeholder east wood are put
together with the old map (whose picture stays as it is) into the generator's whole-world images, which
split_chunks.py then cuts as before. Run after gen_world.py (make_world.sh does).

In:  build/world_old/{ground,flowers}.png, walk.bin, ground_mat.bin  (gen_world's old map, moved there by
     make_world.sh) and build/world_old/world_old.json (its world.json)
Out: assets/world/{ground,flowers}.png, walk.bin, walk_cells.bin, ground_mat.bin, sprites/s*.png,
     world.json (grown, merged)
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [os.path.join(HERE, 'south'), os.path.join(HERE, 'lib'), HERE]
import east_wood  # noqa: E402
import layers  # noqa: E402
import zone1_draft as z1  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
FULL = os.path.join(ROOT, 'build', 'world_old')
OUT = os.path.join(ROOT, 'assets', 'world')
W, H = 900, 3600
OW, OH = z1.OLD_W, z1.OLD_H
TOP = OH - z1.CTX                     # the south canvas starts at this world row
SEAM = 1190                           # from here down the old map's closed bottom edge gives way
CELL = 2
GRASS, EARTH, STONE, WOOD, SNOW, WET = range(6)   # GroundMat
FRAMES, FPS = 64, 8


def old_world():
    with open(os.path.join(FULL, 'world_old.json')) as f:
        w = json.load(f)
    g = np.array(Image.open(os.path.join(FULL, 'ground.png')).convert('RGB'))
    fl = np.array(Image.open(os.path.join(FULL, 'flowers.png')).convert('RGBA'))
    walk = np.fromfile(os.path.join(FULL, 'walk.bin'), np.uint8).reshape(OH, OW).astype(bool)
    mat = np.fromfile(os.path.join(FULL, 'ground_mat.bin'), np.uint8).reshape(OH // CELL, OW // CELL)
    return w, g, fl, walk, mat


def kept_old_sprites(sprites):
    """The old edge firs at its east and south border go: zone 1 draws the southern ones whole again,
    the east wood's fringe stands where the eastern ones were."""
    return [s for s in sprites if not (s['name'].startswith('tanne') and
                                       (s['x'] + s['w'] >= OW or s['y'] + s['h'] >= OH))]


def fringe_sprites(fringe, ground):
    """The east wood's seam firs, cut out like gen_world cuts its sprites (drawn on the ground they stand on)."""
    out = []
    for f in fringe:
        h = f.p.h
        x0, y0 = max(0, f.p.x - h), max(0, f.p.y - h - 4)
        x1, y1 = min(W, f.p.x + h), min(H, f.p.y + h // 3 + 2)
        base = ground[y0:y1, x0:x1].astype(float)
        im = base.copy()
        z1.Fir(f.p.x - x0, f.p.y - y0, h, f.p.seed, snow=f.snow).draw(im)
        a = np.zeros((y1 - y0, x1 - x0, 4), np.uint8)
        a[..., :3] = np.clip(im, 0, 255).astype(np.uint8)
        a[..., 3] = (np.abs(im - base).sum(-1) > 0.5) * 255
        out.append(dict(rgba=a, x=x0, y=y0, foot=f.p.y, frames=1, w=x1 - x0, h=y1 - y0))
    return out


def footprint(s):
    """What a standing thing covers on the ground: its pixels in the last rows above its foot."""
    a = s['rgba'][:, :s['w']]
    m = np.zeros((H, W), bool)
    fy = s['foot'] - s['y']
    lo, hi = max(0, fy - 4), min(a.shape[0], fy + 1)
    if hi <= lo:
        return m
    sub = a[lo:hi, :, 3] > 0
    ys, xs = np.nonzero(sub)
    m[np.clip(s['y'] + lo + ys, 0, H - 1), np.clip(s['x'] + xs, 0, W - 1)] = True
    return m


def main():
    w, og, ofl, owalk, omat = old_world()
    with layers.collect() as c:
        pass
    eg, eh, fringe = east_wood.render()
    EH = east_wood.H

    ground = np.zeros((H, W, 3), np.uint8)
    ground[:TOP, :OW] = og[:TOP]
    ground[:EH, OW:] = np.clip(eg, 0, 255).astype(np.uint8)
    ground[TOP:] = np.clip(c.ground, 0, 255).astype(np.uint8)
    flowers = np.zeros((H, W, 4), np.uint8)
    flowers[:TOP, :OW] = ofl[:TOP]
    flowers[:EH, OW:] = eh
    flowers[TOP:] = c.sway

    # ---------------------------------------------------------------- sprites
    for f in glob.glob(os.path.join(OUT, 'sprites', 's[0-9]*.png')):
        os.remove(f)                                           # last run's south sprites
    sprites = kept_old_sprites(w['sprites'])
    new = [dict(s, y=s['y'] + TOP, foot=s['foot'] + TOP) for s in c.sprites]
    new += fringe_sprites(fringe, ground)
    blocked = np.zeros((H, W), bool)
    for n, s in enumerate(sorted(new, key=lambda s: (s['foot'], s['x']))):
        name = f's{n}'
        Image.fromarray(s['rgba']).save(os.path.join(OUT, 'sprites', name + '.png'))
        sprites.append(dict(name=name, x=int(s['x']), y=int(s['y']), w=int(s['w']), h=int(s['rgba'].shape[0]),
                            foot=int(s['foot']), frames=int(s['frames']), fps=FPS))
        blocked |= footprint(s)

    # ---------------------------------------------------------------- where one can walk, and on what
    m = {k: np.zeros((H, W), bool) for k in ('path', 'brook', 'lake', 'shallow', 'Bruecke', 'Brett', 'Steg',
                                             'Trittsteine', 'Quelle')}
    for k, v in c.masks.items():
        if k in m:
            m[k][TOP:TOP + v.shape[0]] = v[:H - TOP]
    stones = m['Trittsteine']
    ford = ndi.binary_dilation(stones, iterations=3) & m['brook']   # between the stones: wade, as the old ford
    wood = m['Bruecke'] | m['Brett'] | m['Steg']
    deep = m['lake'] & ~m['shallow']
    fog = np.zeros((H, W))
    fog[TOP:] = c.edge_fog
    walk = np.ones((H, W), bool)
    walk &= ~(m['brook'] | deep | m['Quelle'] | blocked)
    walk |= wood | stones | ford
    walk &= fog < 0.3                                          # into the mist at the edges: no further
    walk[:, :10] = walk[:, W - 10:] = False
    yy, xx = np.mgrid[TOP:TOP + z1.CTX + 60, 0:W]               # zone 1's wood beside the camp: closed, too
    walk[TOP:TOP + z1.CTX + 60] &= z1.in_forest(xx, yy - TOP) < -2
    walk[H - 10:] = False
    walk[:EH, OW - 10:] = False                                # the east wood, as the old map's edge was
    walk[:SEAM, :OW] = owalk[:SEAM]                            # the old map as it was, its bottom edge opened
    walk[:SEAM, OW - 10:OW] = False

    lab, _ = ndi.label(walk, structure=np.ones((3, 3)))        # islands nobody can reach are not ground to
    st = w['start']                                            # walk on: a tap there would find no way
    walk &= lab == lab[int(st['y']), int(st['x'])]

    mat = np.full((H, W), GRASS, np.uint8)
    mat[m['path']] = EARTH
    mat[m['shallow'] | ford] = WET
    mat[stones] = STONE
    mat[wood] = WOOD
    cells_mat = mat[::CELL, ::CELL].copy()
    cells_mat[:SEAM // CELL, :OW // CELL] = omat[:SEAM // CELL]

    # ---------------------------------------------------------------- the index
    lights = list(w['lights']) + [dict(l, y=l['y'] + TOP) for l in c.lights[len(w['lights']):]]
    brook = list(w.get('brook', []))
    for b in c.brooks:                                         # points along the new water, for its sound
        ys, xs = np.nonzero(b.depth > 0.85)
        for k in range(0, len(ys), 45):
            brook.append({'x': float(xs[k]), 'y': float(ys[k] + b.y0 + TOP)})
    flies = [dict(x=float(s.x), y=float(s.y + TOP), flies=[{k: round(float(v), 4) for k, v in f.items()}
                                                          for f in s.flies]) for s in c.swarms]
    birds = list(w.get('birds', []))
    rng = np.random.default_rng(5)
    open_ = walk & (mat == GRASS)
    open_[:TOP] = False
    for _ in range(4000):
        x, y = int(rng.integers(30, W - 30)), int(rng.integers(TOP + 40, H - 120))
        if open_[y - 6:y + 7, x - 6:x + 7].all() and all(abs(x - b['x']) + abs(y - b['y']) > 120 for b in birds):
            birds.append({'x': x, 'y': y, 'snow': False})
        if len(birds) >= len(w.get('birds', [])) + 16:
            break

    Image.fromarray(ground).save(os.path.join(OUT, 'ground.png'))
    Image.fromarray(flowers).save(os.path.join(OUT, 'flowers.png'))
    Image.fromarray((walk * 255).astype(np.uint8)).save(os.path.join(OUT, 'walk.png'))
    walk.astype(np.uint8).tofile(os.path.join(OUT, 'walk.bin'))
    walk.reshape(H // CELL, CELL, W // CELL, CELL).all(axis=(1, 3)).astype(np.uint8).tofile(
        os.path.join(OUT, 'walk_cells.bin'))
    cells_mat.tofile(os.path.join(OUT, 'ground_mat.bin'))
    w.update(width=W, height=H, sprites=sprites, lights=lights, brook=brook, birds=birds, fireflies=flies)
    with open(os.path.join(OUT, 'world.json'), 'w') as f:
        json.dump(w, f, indent=1)
    print('ok', len(sprites), 'sprites,', len(lights), 'lights,', len(flies), 'swarms', flush=True)


if __name__ == '__main__':
    main()
