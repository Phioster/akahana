#!/usr/bin/env bash
# Startet Godot headless mit diesem Projekt (Termux-eigenes Godot 4.7.2).
# Erzeugt vorher den Script-Class-Cache, den sonst der Editor schreiben wuerde (siehe gen_class_cache.py).
set -euo pipefail
PROJECT="${PROJECT:-$(cd "$(dirname "$0")/.." && pwd)}"
python3 "$PROJECT/tools/gen_class_cache.py" "$PROJECT" >/dev/null
export GODOT_SILENCE_ROOT_WARNING=1
exec godot --headless --path "$PROJECT" "$@"
