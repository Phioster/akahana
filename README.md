# Akahana · Poppyveil

Ein ruhiges Wanderspiel im Hochformat: ein kleiner Wanderer in der Welt des Kirschbaum-Hintergrunds.
Tippen, wohin er gehen soll – stehen bleiben, schauen, Musik hören. Kein Ziel, keine Aufgaben.

- **Welt:** `tools/world/gen_world.py` erzeugt die ganze Karte mit dem Code, der auch das Hintergrundvideo
  gezeichnet hat (`tools/world/lib/`). Ausgabe in `assets/world/`. Vorschau: `tools/world/preview.py`.
- **Bild:** Godot rendert in Kunstauflösung 180×400 und skaliert ohne Glätten hoch. `shaders/post.gdshader`
  ist die 1:1-Übertragung von Stimmung, Licht, Nebel und Bayer-Raster aus dem Video.
- **Figur:** `tools/gen_char.py`, **Musik:** `tools/gen_music.py` (selbst erzeugt, keine fremden Rechte).
- **Tests:** `bash tools/test.sh` (Godot-Suite + Python), **Build:** `gh workflow run build.yml`, dann
  `bash tools/sign.sh <apk> --install` (Schlüssel nur in `~/.mohnweg-release/`).
