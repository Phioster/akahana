"""A small flood fill for the asset tests (the CI runner has numpy, not scipy)."""
from collections import deque

import numpy as np


def reach(mask, seeds, diagonal=False):
    """Cells of mask connected to any seed (y, x)."""
    steps = [(0, 1), (0, -1), (1, 0), (-1, 0)] + ([(1, 1), (1, -1), (-1, 1), (-1, -1)] if diagonal else [])
    seen = np.zeros(mask.shape, bool)
    q = deque((y, x) for y, x in seeds if mask[y, x])
    for y, x in q:
        seen[y, x] = True
    while q:
        y, x = q.popleft()
        for dy, dx in steps:
            ny, nx = y + dy, x + dx
            if 0 <= ny < mask.shape[0] and 0 <= nx < mask.shape[1] and mask[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                q.append((ny, nx))
    return seen


def holes(solid):
    """See-through cells the outside cannot reach: enclosed by solid ones."""
    h, w = solid.shape
    edge = [(y, x) for y in range(h) for x in (0, w - 1)] + [(y, x) for x in range(w) for y in (0, h - 1)]
    return ~solid & ~reach(~solid, edge)
