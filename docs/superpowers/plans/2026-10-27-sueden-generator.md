# Süden: Generator (Entwürfe → Spieldaten) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die vier abgenommenen Süden-Zonen werden zu echten Spieldaten (Kacheln, Sprites, Begehbarkeit, Boden, Lichter, Glühwürmchen), die Welt wächst auf 900 × 3600.

**Architecture:** Die Zonen-Entwürfe bleiben die einzige Quelle der Optik. Ein Sammler (`layers.py`) hängt sich in ihre Zeichenschleifen und trennt jedes Ding in Boden / wiegende Schicht / stehendes Sprite. `gen_south.py` setzt alte Welt (pixelgleich) + Ostwald + Süden zu Vollbildern zusammen, `split_chunks.py` schneidet wie bisher. Das Spiel liest alles über world.json; neu sind nur Glühwürmchen und das Bündeln des Aktivierers nach Kacheln.

**Tech Stack:** Python 3 (numpy, Pillow, scipy nur lokal), Godot 4.7.2 GDScript.

**Spec:** `docs/superpowers/specs/2026-10-26-sueden-see-design.md`

## Global Constraints

- Welt 5 × 18 Kacheln à 180 × 200 = 900 × 3600 Kunstpixel; alte Welt (x < 540, y < 1200) **bildgleich**, Daten an der Naht dürfen sich ändern.
- Kein Neuwürfeln: `gen_world.py` bleibt unangetastet; Zufall in den Entwürfen bleibt, wie er ist (Ausgabe = abgenommenes Bild).
- Python-Tests unter `tools/tests` ohne scipy (CI); Generator-Tests mit scipy liegen unter `tools/world/south/` und laufen nur lokal.
- Keine Konturen, kein Schachbrett, keine Halbtransparenz in Bildern; Pixelgrafik nie skalieren.
- Schwere Läufe einzeln, `nice`, Akku ≤ 45 °C.
- Keine Secrets, keine Attribution-Zeilen in Commits.

## Review Focus

1. Sackgassen: jeder begehbare Weg-Pixel muss vom Start aus erreichbar sein (Brücken, Brett, Trittsteine, Steg, Hütten-Anleger).
2. Tiefensortierung: Bäume/Hütte/Laternen werden vom Wanderer korrekt verdeckt (Fußpunkt), Schatten liegen im Boden, nicht im Sprite.
3. Naht alte Welt / Süden: kein Streifen, keine doppelten Rand-Tannen, unterer Rand der alten Welt offen.
4. Leistung: ~1000+ Sprite-Einträge dürfen den Aktivierer nicht jedes Bild linear durchlaufen.
5. Wasser: Bäche/tiefer See nie begehbar, flacher Seerand/Pfützen begehbar als WET.

---

### Task 1: Sammler `layers.py` und Haken in den Entwürfen

**Files:**
- Create: `tools/world/south/layers.py`, `tools/world/south/test_layers.py`
- Modify: `tools/world/south/zone{1,2,3,4}_draft.py` (nur die Zeichenschleife `for t in sorted(...)`)

**Interfaces:**
- Produces: `layers.paint(items, img, G)` — ersetzt die Schleife; ohne aktiven Sammler zeichnet es exakt wie vorher. `layers.collect()` (Kontextmanager) liefert ein `Collected` mit `ground (H,W,3)`, `sway (H,W,4)`, `sprites: list[dict(kind, rgba, x, y, foot, frames)]` in Leinwand-Koordinaten der Zone-4-Leinwand.
- Klassen: FLAT = Bruecke, Brett, Trittsteine, Steg, Boot, Seerosen, WasserStein, Treibholz; SWAY = Blade, Wildflower, Schilf, Rohrkolben, Farn (+ Mohnköpfe aus `STASH['heads']`); alles andere STAND.
- Schatten: geänderte Pixel, die nur abgedunkelt sind (neu ≈ alt·k, 0,3 < k < 0,97, Kanäle gleichmäßig), gehen in den Boden, nicht ins Sprite.

- [ ] Test `test_paint_without_collector_is_unchanged`: `zone4_draft.render(w, raw=True)[0]` vor/nach Umbau md5-gleich (Referenz-md5 vorher notieren).
- [ ] Test `test_layers_recompose_the_draft`: ground + sway + Sprites nach Fuß sortiert ergibt ≥ 99 % gleiche Pixel wie das raw-Bild.
- [ ] Test `test_shadows_land_in_ground`: Steg/Laubbaum-Schattenpixel stecken in `ground`, Sprite-Pixel dort transparent.
- [ ] Implementieren, Tests grün, Commit.

### Task 2: Laternen als Bildstreifen

**Files:** Modify `layers.py`, `zone2_draft.py` (Lantern-Klasse), `zone3_draft.py` (Holzlaterne)

- Laternen-Klassen bekommen `frames = 64` und `draw_at(img, G, t)`; der Sammler zeichnet 64 Bilder (t = k/8 s) in einen Streifen wie `holzlaterne0` der alten Welt.
- [ ] Test `test_lanterns_become_64_frame_strips` (Breite = 64 × w, Bilder nicht alle gleich). Commit.

### Task 3: Ostwald-Platzhalter (Spalten 3–4, Reihen 0–5)

**Files:** Create `tools/world/south/east_wood.py`

- Dichter Tannenwald aus `zone1_draft.Fir` wie Zone 1s Waldsaum (versetzte Reihen, kein Raster), nach oben in Fels/Schnee auslaufend (Schnee-Anteil der Tannen steigt nach oben). Inneres als ein Bild in den Boden, nur die westliche Vorderreihe als Sprites. Nicht begehbar.
- **Neue Optik → Vorschau auf die Abnahme-Seite, Okay abwarten.**
- [ ] Test: Streifen unbegehbar, alte Welt unberührt. Commit nach Abnahme.

### Task 4: `gen_south.py` – Vollbilder, Begehbarkeit, Boden, world.json

**Files:** Create `tools/world/gen_south.py`, `tools/world/south/test_gen_south.py`; Modify `tools/world/make_world.sh`, `tools/tests/test_world_assets.py`

- Eingang: `build/world_full/*` + `build/world_full/world_old.json` (beim ersten Lauf aus `assets/world/world.json` gesichert).
- Ausgang wie gen_world (`assets/world/ground.png, flowers.png, walk.bin, walk_cells.bin, ground_mat.bin`, Sprites `s_<zone>_<n>.png`), world.json zusammengeführt: width 900, height 3600, alte Sprites ohne die Rand-Tannen am alten Südrand (Filter wie zone1_draft Z. 242), neue Sprites, Lichter, `brook` + Süd-Bäche, `birds` + offene Süd-Stellen, neu `fireflies: [{x, y, n, r}]`.
- Begehbar: Wege EARTH; Brücke/Brett/Steg WOOD; Trittsteine STONE mit WET-Furt dazwischen; flacher Seerand + Pfützen WET; Gras GRASS. Gesperrt: Bach, tiefer See (> flacher Rand), Schilfmeer/Seitenränder ab dem Nebel, Stamm-/Hütten-/Bank-Füße, Ostwald.
- [ ] Tests (lokal): alte Welt-Region bildgleich (x < 540, y < 1040 exakt; Nahtreihen dürfen sich ändern); Start begehbar; **alle Weg-Zellen vom Start erreichbar**; Bach-Zellen nie begehbar; Steg-Ende, Hütte, Bank, Quelle erreichbar.
- [ ] `tools/tests/test_world_assets.py`: Größe 900 × 3600, `chunks == [5, 18]` (CI-tauglich, ohne scipy).
- [ ] make_world.sh: gen_world → gen_south → split_chunks. Lauf, Commit.

### Task 5: Spiel – Aktivierer nach Kacheln, Glühwürmchen

**Files:** Modify `core/activator.gd`, `core/world_data.gd`; Create `scenes/fireflies.gd`; Modify `scenes/main.gd`; Tests `tests/test_chunks.gd`, `tests/test_life.gd`

- Activator: Einträge in Eimer je Kachel; `update` prüft nur Eimer im Umkreis der Ansicht ± far (+ aktive Knoten).
- WorldData liest `fireflies`; Fireflies-Knoten zeichnet den Schwarm wie `Swarm` im Entwurf (gleiche Bahnen, Leuchtpunkte), meldet seine Lichter als `dyn_light`.
- [ ] Tests: `test_activator_only_visits_nearby_buckets`, `test_fireflies_load_from_world`. `bash tools/test.sh` grün. Commit.

### Task 6: Vorschau aus den Spieldaten

**Files:** Create `tools/world/south/preview_game.py`

- Setzt die Karte aus den **Kacheln und Sprites** (wie das Spiel) zusammen und stuft sie mit `mood_map` ein; Abweichung je Zone gegen die abgenommenen Entwürfe in Prozent.
- [ ] Ganze Karte + Ausschnitte (Naht, Brücke, Steg, Hütte, Ostwald) auf die Abnahme-Seite (Schritt 19), ZIP an Philip. Commit, Memory.
