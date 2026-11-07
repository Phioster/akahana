#!/usr/bin/env python3
"""Quick look while drawing: the village things alone on a patch of meadow, graded like the game, 6x."""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [HERE, os.path.join(HERE, '..', 'lib'), os.path.join(HERE, '..'), os.path.join(HERE, '..', 'south')]
from field6 import ground_organic  # noqa: E402
import mood_map  # noqa: E402
import objects_west as o  # noqa: E402

rng = np.random.default_rng(2)
H, W = 90, 300
img = ground_organic(H, W, np.full((H, W), 0.7), np.full((H, W), 0.2), rng).astype(float)
G = np.random.default_rng(3).random((H, W))
things = [o.Minka(32, 70, seed=1, ruin=0.3), o.Minka(96, 70, seed=2, ruin=0.8, kind='kaya', roof=19),
          o.Brunnen(150, 70), o.Hortensie(176, 72, 6, 'blau'), o.Hortensie(192, 74, 5, 'lila', 5),
          o.Hortensie(206, 72, 5, 'rosa', 6), o.Beet(222, 74), o.Obstbaum(262, 74),
          o.Bambuszaun([(150, 86), (200, 88), (240, 86)]), o.Steinmauer([(8, 86), (60, 88), (120, 86)]),
          o.Waescheleine(250, 88), o.Korb(285, 86)]
for t in sorted(things, key=lambda t: t.box()[3]):
    t.draw(img, G)
img = np.clip(mood_map.grade(img), 0, 255).astype(np.uint8)
Image.fromarray(img).resize((W * 4, H * 4), Image.NEAREST).save(sys.argv[1])
