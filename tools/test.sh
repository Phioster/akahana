#!/usr/bin/env bash
# Laesst die Testsuite laufen und ist NUR gruen, wenn auch kein
# Laufzeitfehler auftrat.
#
# Der Grund: ein Zugriff auf ein Feld, das es nicht mehr gibt, bricht in
# GDScript still die umgebende Funktion ab. Der Test meldet dann "ok",
# obwohl seine Zusicherungen nie liefen. Genau so sind beim Umbau auf
# Lebenspunkte fuenf Tests monatelang ins Leere gelaufen.
set -uo pipefail
OUT="$(mktemp)"
trap 'rm -f "$OUT"' EXIT

# Auf dem Geraet laeuft Godot im proot-Debian (tools/godot.sh), in der CI
# direkt. Beides landet hier.
if [ -x "$(dirname "$0")/godot.sh" ] && [ -d /data/data/com.termux ]; then
	bash "$(dirname "$0")/godot.sh" --script res://tests/run_tests.gd 2>&1 | tee "$OUT"
else
	"${GODOT:-godot}" --headless --script res://tests/run_tests.gd 2>&1 | tee "$OUT"
fi

if grep -qE "^(SCRIPT ERROR|USER SCRIPT ERROR|SHADER ERROR)" "$OUT"; then
	echo
	echo "FEHLGESCHLAGEN: Laufzeitfehler im Testlauf -- betroffene Tests haben nichts geprueft."
	grep -E "^(SCRIPT ERROR|USER SCRIPT ERROR|SHADER ERROR)" "$OUT" | sort -u | head -20
	exit 1
fi
if grep -q "SUITE KAPUTT" "$OUT"; then
	echo
	echo "FEHLGESCHLAGEN: eine Testsuite liess sich nicht laden."
	exit 1
fi
if ! grep -qE "^[0-9]+ Tests, 0 fehlgeschlagen$" "$OUT"; then
	echo
	echo "FEHLGESCHLAGEN: Tests rot oder Zusammenfassung fehlt."
	exit 1
fi
echo "Godot-Suite gruen, keine Laufzeitfehler."

# Probelauf: das ganze Spiel 300 Bilder lang ohne Bildschirm. Fängt, was die Tests nicht sehen:
# Shader, die erst beim Zeichnen übersetzt werden, und Fehler im Zusammenspiel der Szenen.
echo
echo "Probelauf des Spiels..."
SMOKE="$(mktemp)"
trap 'rm -f "$OUT" "$SMOKE"' EXIT
if [ -x "$(dirname "$0")/godot.sh" ] && [ -d /data/data/com.termux ]; then
	timeout 180 bash "$(dirname "$0")/godot.sh" --quit-after 300 > "$SMOKE" 2>&1
else
	timeout 180 "${GODOT:-godot}" --headless --quit-after 300 > "$SMOKE" 2>&1
fi
if grep -qE "SHADER ERROR|SCRIPT ERROR|Shader compilation failed|Parse Error" "$SMOKE"; then
	echo "FEHLGESCHLAGEN: Fehler im Probelauf:"
	grep -E -A2 "SHADER ERROR|SCRIPT ERROR|Shader compilation failed|Parse Error" "$SMOKE" | head -30
	exit 1
fi
echo "Probelauf sauber."

# Python-Tests
echo
echo "Python-Tests..."
PYOUT="$(mktemp)"
# Beide Dateien in EINEN trap: ein zweites trap ... EXIT ersetzt das erste.
trap 'rm -f "$OUT" "$PYOUT" "$SMOKE"' EXIT
python3 -m unittest discover -s tools/tests -t . 2>&1 | tee "$PYOUT"
if grep -qE "^(FAILED|ERROR)" "$PYOUT"; then
	echo
	echo "FEHLGESCHLAGEN: Python-Tests rot."
	exit 1
fi
if ! grep -q "^Ran [0-9]\+ test" "$PYOUT"; then
	echo
	echo "FEHLGESCHLAGEN: Python-Zusammenfassung fehlt oder nicht lesbar."
	exit 1
fi
echo "Alles gruen, alle Suites OK."
