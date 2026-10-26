#!/usr/bin/env python3
"""Quick look while drawing: each new object alone on a patch of meadow, graded like the game, 8x."""
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'lib'))
sys.path.insert(0, os.path.join(HERE, '..'))
from field6 import ground_organic  # noqa: E402
import mood_map  # noqa: E402
import objects_south as o  # noqa: E402

rng = np.random.default_rng(2)
H, W = 44, 200
ground = ground_organic(H, W, np.full((H, W), 0.7), np.full((H, W), 0.2), rng)
G = np.random.default_rng(3).random((H, W))
img = ground.copy()
for t in [o.Wegstein(16, 34, 'a'), o.Wegstein(36, 34, 'b'), o.Vogelscheuche(64, 38, 'a'),
          o.Vogelscheuche(92, 38, 'b'), o.Mauer([(112, 30), (140, 28), (168, 33), (192, 38)])]:
    t.draw(img, G)
img = np.clip(mood_map.grade(img), 0, 255).astype(np.uint8)
Image.fromarray(img).resize((W * 6, H * 6), Image.NEAREST).save(sys.argv[1])
