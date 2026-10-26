# Welt in Kacheln – Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die Welt wird in Kacheln zerlegt und nur um die Kamera herum geladen; Objekte, Tiere, Klänge und Lichter entstehen erst, wenn sie gebraucht werden – ohne dass sich Bild oder Klang für den Spieler ändern.

**Architecture:** Ein eigenes Python-Werkzeug zerlegt die großen Generator-Bilder in Kacheln (180 × 200 px, Mohn mit 8 px Rand). Im Spiel rechnet `ChunkGrid` die Kachelmathematik, `ChunkStore` lädt Kacheldaten sofort und Kachelbilder im Hintergrund, `Activator` erzeugt und entfernt Knoten aller Art nach Abstand mit Hysterese. `WorldView` setzt das zusammen; die Wegsuche baut ihr Raster nur noch für das Rechteck um Start und Ziel.

**Tech Stack:** Godot 4.7.2 (GDScript, GL Compatibility), Python 3 + numpy + Pillow für Werkzeuge, eigener Testlauf `bash tools/test.sh` (GDScript-Tests + Python-unittest + Probelauf).

**Spec:** `docs/superpowers/specs/2026-10-26-welt-kacheln-design.md`

## Global Constraints

- Kachelgröße `Vector2i(180, 200)` Kunstpixel; Mohn-Rand `APRON = 8` px; Wegsuch-Zelle bleibt `Pathing.CELL = 2`.
- Laden: sichtbar + 1 Kachel; Freigeben ab 2 Kacheln Abstand.
- Keine Halbtransparenz, keine neuen Grafiken; das Bild muss pixelgleich zu heute bleiben.
- Kommentare kurz (1–2 Zeilen, das Warum), Code-Kommentare Englisch, Testmeldungen Deutsch.
- Tests laufen mit `bash tools/test.sh` aus `~/mohnweg`; schwere Läufe einzeln und mit `nice` (Handy-Hitze ≤ 45 °C).
- Commits ohne Co-Authored-By/Claude-Zeilen, Identität Phioster.
- Bauen/Installieren nur über `bash tools/build_install.sh`, am Ende einer Aufgabe, die Philip spüren kann.

## Review Focus

1. **Naht im Mohn:** Wind (bis 2 px) und Ausweichen (bis 4 px) lesen Nachbarpixel – an einer Kachelkante dürfen keine Blüten fehlen oder doppelt erscheinen. → Test in Task 1 (Rand = Nachbarinhalt) und Task 5 (Shader liest mit `origin`).
2. **Start an einem gespeicherten Ort weit weg:** Die Kachel unter dem Mönch muss vor dem ersten Bild da sein, sonst „steht er nicht auf begehbarem Boden“ und springt zum Start. → Test in Task 3.
3. **Tipp an den Rand des Geladenen / Ziel hinter einem Hindernis:** Der Weg braucht einen Umweg außerhalb des Suchrechtecks → einmal mit doppeltem Rand neu suchen statt „kein Weg“. → Test in Task 6.
4. **Vogel fliegt gerade, als sein Platz entladen wird:** muss sauber verschwinden, ohne Fehler und ohne liegen gebliebene Knoten. → Test in Task 7.
5. **Ganze Karte durchwandern:** Zahl der geladenen Kacheln, Objekte und Klangquellen bleibt begrenzt. → Test in Task 8.

---

### Task 1: Kacheln zerlegen (Werkzeug)

**Files:**
- Create: `tools/world/split_chunks.py`, `tools/world/make_world.sh`
- Modify: `export_presets.cfg` (`include_filter` um `assets/world/chunks/*.bin`), `tools/tests/test_world_assets.py`
- Test: `tools/tests/test_chunks.py`

**Interfaces:**
- Produces: Ordner `assets/world/chunks/` mit je Kachel `c_<cx>_<cy>_ground.png` (180×200), `c_<cx>_<cy>_flowers.png` (196×216, inkl. 8 px Rand; außerhalb der Welt transparent), `c_<cx>_<cy>_cells.bin` (90×100 Bytes, 1 = begehbar), `c_<cx>_<cy>_mat.bin` (90×100 Bytes, `GroundMat`-Werte). In `world.json` neu: `"chunk": [180, 200]`, `"chunks": [cols, rows]`, `"apron": 8`. Die großen Dateien `ground.png`, `flowers.png`, `walk.bin`, `walk.png`, `walk_cells.bin`, `ground_mat.bin` wandern nach `build/world_full/` (nicht im Export, nicht im Repo).
- `split(src_dir: str, out_dir: str, chunk=(180, 200), apron=8) -> dict` gibt den Index-Eintrag zurück.

- [ ] **Step 1: Failing tests** in `tools/tests/test_chunks.py` (mit kleiner Kunstwelt 360×400 aus Zufallsbildern in einem Temp-Ordner):
  - `test_reassembled_chunks_equal_the_original` – alle `ground`-Kacheln nebeneinander = Originalbild; alle `cells`/`mat` zusammengesetzt = Original-Bytes.
  - `test_flower_apron_holds_the_neighbours_pixels` – Randstreifen rechts von Kachel (0,0) = linker Innenstreifen von (1,0); Rand außerhalb der Welt hat Alpha 0.
  - `test_index_counts_the_chunks` – `split(...)["chunks"] == [2, 2]`.
- [ ] **Step 2:** `python3 -m unittest tools.tests.test_chunks -v` → FAIL (Modul fehlt).
- [ ] **Step 3:** `split()` mit numpy-Ausschnitten implementieren; `make_world.sh` ruft `gen_world.py`, dann `split_chunks.py`, dann verschiebt die großen Dateien nach `build/world_full/`.
- [ ] **Step 4:** Tests grün; dann `bash tools/world/make_world.sh` echt ausführen (mit `nice`), `test_world_assets.py` auf die neue Ablage umstellen (prüft: jede Kachel hat alle vier Dateien, Größen stimmen).
- [ ] **Step 5:** Commit „Welt: Kacheln zerlegen“.

### Task 2: Kachelmathematik

**Files:**
- Create: `core/chunk_grid.gd`
- Test: `tests/test_chunks.gd` (in `tests/run_tests.gd` → `SUITES` eintragen)

**Interfaces:**
- Produces: `class_name ChunkGrid extends RefCounted`; `const SIZE := Vector2i(180, 200)`; `const APRON := 8`; `var cols: int`, `var rows: int`; `func _init(c: int, r: int)`; `func chunk_of(p: Vector2) -> Vector2i`; `func contains(c: Vector2i) -> bool`; `func rect_of(c: Vector2i) -> Rect2`; `func chunks_in(r: Rect2) -> Array[Vector2i]` (auf die Welt beschnitten, Reihenfolge zeilenweise).

- [ ] **Step 1: Failing tests:** `test_chunk_of_maps_points_to_their_chunk` (`(179.9, 0)` → `(0,0)`, `(180, 0)` → `(1,0)`, `(0, 399.9)` → `(0,1)`); `test_chunks_in_covers_a_view_and_clips_to_the_world` (Rect `(170, 190, 180, 400)` bei 3×6 → 2×3 Kacheln; Rect über den Rand hinaus liefert keine Kacheln außerhalb); `test_rect_of_round_trips`.
- [ ] **Step 2:** `bash tools/test.sh` → FAIL (Klasse fehlt).
- [ ] **Step 3:** Implementieren.
- [ ] **Step 4:** grün. **Step 5:** Commit.

### Task 3: Kachelspeicher

**Files:**
- Create: `core/chunk_store.gd`
- Modify: `core/world_data.gd` (liest `chunk`, `chunks`, `apron`; `walk` und `is_walkable` entfallen)
- Test: `tests/test_chunks.gd`

**Interfaces:**
- Consumes: `ChunkGrid` (Task 2), Kacheldateien (Task 1).
- Produces: `class_name ChunkStore extends RefCounted`; `func _init(grid: ChunkGrid, dir: String = WorldData.DIR + "chunks/")`; `func want(keep: Array[Vector2i]) -> void` (lädt `cells`/`mat` sofort, startet Bilder im `WorkerThreadPool`, vergisst alles nicht in `keep`); `func poll() -> Array[Vector2i]` (macht fertig geladene Bilder auf dem Hauptthread zu Texturen, gibt die neu fertigen zurück); `func load_now(c: Vector2i) -> void` (alles synchron, für den Start); `func is_ready(c) -> bool`; `func ground_tex(c) -> Texture2D`; `func flowers_tex(c) -> Texture2D`; `func walkable(p: Vector2) -> bool` (Zelle frei; `false` wenn nicht geladen); `func material_at(p: Vector2) -> int` (`GroundMat.GRASS` wenn nicht geladen); `func cell_free(cell: Vector2i) -> bool`; `func cell_weight(cell: Vector2i) -> float` (3.0 für Gras/Schnee wie `Pathing.OFF_PATH`); `func loaded_count() -> int`.
- `WorldData`: neu `var chunks := Vector2i.ZERO`, `var grid: ChunkGrid`.

- [ ] **Step 1: Failing tests:** `test_store_answers_walkable_like_the_old_mask` (echte Welt: `load_now` für die Kachel des Startpunkts; `walkable(world.start) == true`; ein Punkt im Bach `false`); `test_unloaded_ground_is_not_walkable`; `test_want_forgets_what_is_not_kept` (`loaded_count()` fällt nach `want([])` auf 0); `test_textures_arrive_through_poll` (nach `want([c])` und wiederholtem `poll()` bis 2 s: `is_ready(c)`).
- [ ] **Step 2:** FAIL. **Step 3:** Implementieren (`TextureLoader`-Weg für Bilder beibehalten; im Thread nur `Image.load_from_file`/`load`, Textur erst im Hauptthread). **Step 4:** grün. **Step 5:** Commit.

### Task 4: Aktivierer

**Files:**
- Create: `core/activator.gd`
- Test: `tests/test_chunks.gd`

**Interfaces:**
- Produces: `class_name Activator extends RefCounted`; `func add(where: Rect2, near: float, far: float, make: Callable, drop: Callable) -> int` (`where` = Objektrechteck, für Punkte `Rect2(p, Vector2.ZERO)`; `make.call() -> Node`, `drop.call(node)`); `func update(area: Rect2) -> void` (Abstand = kleinster Abstand zwischen `where` und `area`, 0 bei Überlappung; erzeugt bei `< near`, entfernt bei `> far`); `func node(id: int) -> Node` (oder `null`); `func active_count() -> int`; `func clear() -> void`.

- [ ] **Step 1: Failing tests:** `test_activates_inside_near_and_drops_beyond_far`; `test_no_flapping_between_near_and_far` (Bereich 100 Schritte zwischen `near` und `far` hin und her → `make` genau einmal aufgerufen); `test_clear_drops_everything`.
- [ ] **Step 2–5** wie üblich.

### Task 5: Weltansicht aus Kacheln

**Files:**
- Create: `scenes/world_view.gd`
- Modify: `shaders/flowers.gdshader` (`uniform vec2 origin;` – Weltkoordinate der linken oberen Ecke des Mohnbilds inkl. Rand; `p = origin + floor(UV * tex_size)`, Abtasten weiter im eigenen Bild), `scenes/main.gd` (Boden/Mohn/Objekte nicht mehr selbst bauen)
- Test: `tests/test_chunks.gd`, `tests/test_scenes_compile.gd` (neue Szene eintragen)

**Interfaces:**
- Consumes: `ChunkStore`, `Activator`, `WorldData`.
- Produces: `class_name WorldView extends Node2D`; `var world: WorldData`; `var store: ChunkStore`; `var sorted: Node2D` (y-sortierte Ebene, Mönch/Vögel bleiben dort); `func update(view: Rect2) -> void` (Kacheln wollen/pollen, Boden- und Mohn-`Sprite2D` je fertige Kachel anlegen/entfernen, Objekte über einen `Activator` mit `near = 40`, `far = 120`, `where` = Objektrechteck aus `x, y, w, h`); `func set_trail(points: Array, k: Array) -> void` (an alle geladenen Mohn-Materialien); `func chunk_nodes() -> int`; `func object_nodes() -> int`.
- Mohn-Sprite: Textur 196×216, `region_rect = Rect2(8, 8, 180, 200)`, `region_enabled = true`, Position = Kachelecke; eigenes `ShaderMaterial` je Kachel mit `origin = Kachelecke - (8, 8)` und `tex_size = (196, 216)`.

- [ ] **Step 1: Failing tests:** `test_view_loads_only_what_the_camera_needs` (View 180×400 mitten in der Karte → nach `update` und Pollen ≤ 3×4 Kacheln mit Knoten); `test_objects_appear_only_near_the_view` (Objektknoten nur für Objekte, deren Rechteck ≤ 40 px vom View entfernt ist); `test_flower_shader_reads_world_coordinates` (Shadercode enthält `uniform vec2 origin` und `origin + floor(UV * tex_size)`).
- [ ] **Step 2:** FAIL. **Step 3:** Implementieren; `main.gd` ruft je Bild `world_view.update(Rect2(top_left, view))` und gibt die Spur über `set_trail` weiter. Start: vor dem ersten Bild `store.load_now` für die Kacheln um den Startort.
- [ ] **Step 4:** grün + Probelauf sauber. **Step 5:** Commit.

### Task 6: Wegsuche im Ausschnitt

**Files:**
- Modify: `core/pathing.gd` (neue Funktion, alte `build*` bleiben für Tests), `scenes/main.gd` (Tipp nutzt die neue Funktion)
- Test: `tests/test_pathing.gd`

**Interfaces:**
- Consumes: `ChunkStore.cell_free`, `ChunkStore.cell_weight`.
- Produces: `func find_path_in(store: ChunkStore, a: Vector2, b: Vector2, margin: float = 60.0) -> PackedVector2Array` – baut `grid.region` auf das Zellrechteck um a und b plus `margin`, nicht geladene Zellen sind fest; danach `smooth()` wie heute. Findet es nichts, einmal mit `margin * 2` erneut.

- [ ] **Step 1: Failing tests:** `test_local_search_finds_the_same_ways_as_the_whole_map` (echte Welt, alle Kacheln `load_now`: für die fünf Strecken aus `test_real_slanting_walks_have_few_kinks` hat der Weg aus `find_path_in` höchstens 10 % mehr Länge als der aus dem alten Ganz-Raster); `test_detour_outside_the_box_is_found_with_a_wider_margin` (Kunstwelt mit Wand quer, Lücke 80 px seitlich → Weg gefunden); `test_unloaded_cells_are_walls`.
- [ ] **Step 2–5.**

### Task 7: Tiere, Irrlicht, Klänge, Lichter bei Bedarf

**Files:**
- Modify: `scenes/birds.gd` (Schwärme über `Activator`: `near` = 60 px außerhalb des Views, `far` = 160; die „kommen wieder“-Logik bleibt je Platz erhalten), `scenes/ambience.gd` (Bach-, Feuer-, Kerzenklänge über `Activator` am Mönch: `near = Reichweite + 20`, `far = Reichweite + 60`; Frösche nur aus geladenen Bachpunkten), `scenes/main.gd` (Irrlicht über `Activator` am View: `near = 60`, `far = 160`; `_feed_lights` nimmt weiter nur Lichter nahe dem View), `scenes/footsteps.gd` (`store.material_at` statt `GroundMat`)
- Test: `tests/test_life.gd`

**Interfaces:**
- Consumes: `Activator`, `ChunkStore.material_at`.
- Produces: `Birds.update_area(view: Rect2) -> void`, `Birds.flock_nodes() -> int`, `Ambience.spot_nodes() -> int`.

- [ ] **Step 1: Failing tests:** `test_birds_live_only_near_the_view`; `test_a_flock_dropped_in_flight_leaves_nothing_behind` (Vogel im Zustand Fliegen, dann View weit weg → `flock_nodes() == 0`, keine Bird-Knoten mehr im Baum); `test_only_audible_spots_have_players` (Mönch am Start: Zahl der `AudioStreamPlayer2D` in Ambience ≤ Zahl der Orte in Hörweite + Rand); `test_footsteps_ask_the_store_for_the_ground`.
- [ ] **Step 2–5.**

### Task 8: Alles zusammen, Speicher bleibt flach

**Files:**
- Modify: `scenes/main.gd` (Kamera-Grenzen aus `world.width/height`, Speichern/Startprüfung über `store.walkable`, `GroundMat.load_default`/`walk_cells.bin` raus), `core/ground_mat.gd` (nur noch Konstanten, falls nichts anderes mehr lädt)
- Test: `tests/test_life.gd`

- [ ] **Step 1: Failing test:** `test_walking_the_whole_map_keeps_memory_flat` – Main-Szene; Mönch wird in 40-px-Sprüngen über ein Zickzack durch die ganze Karte gesetzt, je Sprung 30 Bilder `_process`; danach gilt jederzeit: `world_view.chunk_nodes() <= 12`, `store.loaded_count() <= 20`, `world_view.object_nodes() <=` Objekte in View+120 px, Ambience-Spieler ≤ 8.
- [ ] **Step 2:** FAIL bis alles verdrahtet ist. **Step 3:** Verdrahten, alte Ganz-Welt-Pfade entfernen. **Step 4:** `bash tools/test.sh` komplett grün, Probelauf sauber.
- [ ] **Step 5:** Version hochzählen (0.4.0), Commit, `bash tools/build_install.sh`, Push-Nachricht. Philip bitten, gezielt auf Kachelkanten zu achten (Mohn bei Wind, beim Durchlaufen; Objekte, die halb auf zwei Kacheln stehen; kurzes Ruckeln beim Nachladen).
