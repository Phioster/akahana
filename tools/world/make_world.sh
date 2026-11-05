#!/usr/bin/env bash
# Generates the world, cuts it into chunks and moves the big images out of the game's assets.
# gen_world draws the old map (kept apart in build/world_old, the south generator builds on it),
# gen_south grows it south, gen_east lays the Ostwald over its eastern columns, split_chunks cuts the grown world.
set -euo pipefail
cd "$(dirname "$0")/../.."
FULL="ground.png flowers.png walk.bin walk.png walk_cells.bin ground_mat.bin"
nice -n 10 python3 tools/world/gen_world.py
mkdir -p build/world_old build/world_full
for f in $FULL; do
	mv -f "assets/world/$f" build/world_old/
	rm -f "assets/world/$f.import"
done
cp assets/world/world.json build/world_old/world_old.json
nice -n 10 python3 tools/world/gen_south.py
nice -n 10 python3 tools/world/gen_east.py
nice -n 10 python3 tools/world/gen_north.py --save-pre
nice -n 10 python3 tools/world/gen_north.py
nice -n 10 python3 tools/world/gen_cave.py
python3 tools/world/split_chunks.py
for f in $FULL water.png bend.png low.png refl.png; do
	mv -f "assets/world/$f" build/world_full/
	rm -f "assets/world/$f.import"
done
echo "Welt fertig: assets/world/chunks, Vollbilder in build/world_full (alte Karte allein in build/world_old)"
