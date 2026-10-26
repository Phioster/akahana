#!/usr/bin/env bash
# Generates the world, cuts it into chunks and moves the big images out of the game's assets.
set -euo pipefail
cd "$(dirname "$0")/../.."
nice -n 10 python3 tools/world/gen_world.py
python3 tools/world/split_chunks.py
mkdir -p build/world_full
for f in ground.png flowers.png walk.bin walk.png walk_cells.bin ground_mat.bin; do
	mv -f "assets/world/$f" build/world_full/
	rm -f "assets/world/$f.import"
done
echo "Welt fertig: assets/world/chunks, Vollbilder in build/world_full"
