# Erinnerungen (Schritt 1) – Bauplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Ziel:** Erreichte Orte landen als Skizzenseite im Buch, beim ersten Betreten von Gebiet oder Ort hängt kurz eine
Schriftrolle mit dem japanischen Namen, ein Lesezeichen am Buchknopf zeigt neue Seiten an.

**Aufbau:** Eine Tabelle (`core/memories.gd`) kennt alle 31 Orte und 6 Gebiete. Ein Wächter (`MemoryKeeper`) bekommt
viermal pro Sekunde die Position und meldet erste Besuche. `main.gd` verteilt die Meldungen an Schriftrolle,
Buch und Spielstand. Die Buchseite baut ein eigenes Skript (`memory_page.gd`), damit `book_ui.gd` nicht weiter wächst.

**Technik:** Godot 4.7.2 (GDScript), Python 3 + Pillow für die Bildvorbereitung, Tests mit `bash tools/test.sh`.

**Spec:** `docs/superpowers/specs/2026-11-16-erinnerungen-design.md`

## Globale Vorgaben
- Keine leeren Seiten, Zähler, Prozent oder Häkchen. Das Buch zeigt nur Gefundenes, in Fundreihenfolge.
- Bildschirm 180 × 400, Buchseite 156 × 236, Inhaltsursprung (18, 20), Text bis x 144 (`PAPER_RIGHT`).
- Skizze 130 × 87 bei Seiten-x 12 bis 142, linear gefiltert (fein, nicht verpixelt).
- Zeile des Mönchs: höchstens 3 Zeilen, Umbruch bei 122 px in `PixelFont.hand()`.
- Schriftrolle: hängend oben links, Kanji senkrecht (Klee One), Umschrift auf einem Schild darunter, etwa 3 s,
  blockiert keine Eingabe (`MOUSE_FILTER_IGNORE`).
- Lesezeichen: goldenes Band aus dem Seitenblock des Buchknopfs, bleibt bis zum Öffnen des Buchs.
- Testsprünge (`Reisen (Test)`, nur Debug) zählen als Fund.
- Namen und Texte genau aus `~/akahana-skizzen/texte.py` (abgenommen). Keine Secrets, keine Co-Authored-By-Trailer.
- Vorschau-Maße: `~/akahana-skizzen/vorschau/vorschau.py` (abgenommen) ist die Vorlage für Rolle, Strich und Band.

## Review-Schwerpunkte
1. Am Gebietsrand hin und her laufen: keine Rolle, solange man nicht 1,5 s im neuen Gebiet steht (Test in Task 4).
2. Alter Spielstand ohne Abschnitt `erinnerungen`: leeres Buch, kein Absturz (Test in Task 3).
3. Gebiet und Ort im selben Schritt (Spielstart am Lager): erst Gebiets-, dann Ortsrolle, nie gleichzeitig (Test in Task 5).
4. Buch geöffnet, während eine neue Seite dazukommt: Seite ist beim nächsten Öffnen da, Lesezeichen bleibt bis dahin (Test in Task 6).
5. Im Raum (Höhle, Glashaus) liegen die Koordinaten neben der Welt: Außenorte dürfen dort nicht auslösen (Test in Task 4).

---

### Task 1: Bilder, Namen, Kanji-Schrift

**Files:**
- Create: `tools/prep_memories.py`, `assets/erinnerungen/<schlüssel>.png` (31), `tools/tests/test_memory_assets.py`
- Modify: `docs/namen.md` (Tabelle „Erinnerungsorte“ mit allen 31 Kanji + Umschrift, Dorf heißt 忘れ里 Wasure-zato,
  Gewächshaus 硝子室 Garasu-muro, Hütte am See 湖畔の小屋 Kohan-no-koya), `assets/ui/kanji.png`/`kanji.json`
  (neu erzeugt mit `python3 tools/gen_kanji_font.py`), `docs/CREDITS.md` (Skizzen: mit ChatGPT und Higgsfield nach
  Spielausschnitten gezeichnet, Buchfilter eigen)

**Interfaces:**
- Produces: `res://assets/erinnerungen/<schlüssel>.png`, 800 px breit, Schlüssel wie in Task 2.

- [ ] **Step 1: Test schreiben** `tools/tests/test_memory_assets.py`: `test_every_page_has_a_picture` (genau die 31
  Schlüssel aus Task 2 als PNG vorhanden), `test_pictures_are_small` (Breite 800, Datei < 600 kB).
- [ ] **Step 2:** `python3 -m unittest tools.tests.test_memory_assets` → FAIL (Ordner fehlt).
- [ ] **Step 3:** `prep_memories.py <quellordner>` verkleinert `~/akahana-skizzen/seiten/*.png` auf 800 px Breite
  (LANCZOS) und speichert optimiert; Quellordner als Argument, kein fester Heimpfad im Repo.
- [ ] **Step 4:** Test grün; `namen.md` ergänzen, Kanji-Schrift neu erzeugen, `bash tools/test.sh` grün
  (test_pixel_font darf nicht brechen).
- [ ] **Step 5: Commit** `Erinnerungen: Skizzen, Namen, Kanji-Schrift`

### Task 2: Die Tabelle

**Files:**
- Create: `core/memories.gd`, `tests/test_memories.gd`
- Modify: `tests/run_tests.gd` (SUITES)

**Interfaces:**
- Produces: `class_name Memories extends RefCounted` mit
  - `const PLACES: Array[Dictionary]` – je `{key, region, kanji, romaji, title, at: Vector2, r: float, room: String, text}`;
    `room` ist `"cave"`/`"glashaus"` für die Innenräume, sonst `""`.
  - `const REGIONS: Array[Dictionary]` – je `{key, kanji, romaji}`; Schlüssel `mitte, kogarashi, norden, osten, sueden, westen`.
  - `static func place(key: String) -> Dictionary`, `static func region(key: String) -> Dictionary`
  - `static func place_at(p: Vector2) -> String` (nächster Ort, dessen Kreis p enthält, Innenräume nie; sonst `""`)
  - `static func place_in_room(room: String) -> String`
  - `static func region_at(p: Vector2) -> String`
  - `static func wrap_text(text: String) -> PackedStringArray` (Umbruch bei 122 px in `PixelFont.hand()`)

Mittelpunkte (Weltpixel), Radius 70 wo nicht anders genannt: lager 1143,2270 · schrein 1204,2103 (r 50, liegt nah am
Lager) · ruine 1129,1552 · bachbruecke 1170,1855 · gluehwuermchen 1262,3150 · baeche 1400,3770 · seesteg 1474,4145 ·
seehuette 1670,4520 · graeber 1860,1750 · steinbruecke 2240,1820 · waldteich 1870,2550 · ritual 2522,2282 · jizo
2290,2650 · felstor 1174,1190 · holzfaeller 1230,860 · hoehle 1050,705 · schlucht 1460,545 · aussicht 1686,412 · pass
1370,125 · bergsee 2100,620 · dorfplatz 520,2330 · gewaechshaus 680,2604 · dorfschrein 424,1860 · obstwiese 635,1740 ·
muehle 500,3288 · bambus 168,2287 · fischer 570,4110 · teehaus 880,4085 · einsiedelei 362,400 · hoehle_innen room cave ·
gewaechshaus_innen room glashaus. Titel/Kanji/Umschrift/Text aus `texte.py` (Feld 5 = Titel, Feld 3/4 = Kanji/Umschrift,
Feld 7 = Text; Titel der Innenräume „Eishöhle, innen“, „Glashaus, innen“; schrein-Titel „Schrein der roten Blume“).

Gebiete (Reihenfolge der Prüfung): `norden` y < 1200 · `westen` x < 900 · `osten` x ≥ 1700 und y < 2950 ·
`kogarashi` y < 1650 · `sueden` y ≥ 2950 · sonst `mitte`.

- [ ] **Step 1: Tests** in `tests/test_memories.gd`:
  - `test_there_are_31_places_and_6_regions` (Anzahl, Schlüssel eindeutig, jedes Feld nicht leer)
  - `test_regions_at_known_spots`: Lager (1143,2270)→mitte, Ruine (1129,1552)→kogarashi, Bergsee (2100,620)→norden,
    Waldteich (1870,2550)→osten, Gräber (1860,1750)→osten, Glühwürmchen (1262,3150)→sueden, Hütte am See
    (1670,4520)→sueden, Fischer (570,4110)→westen, Einsiedelei (362,400)→norden, Dorfplatz (520,2330)→westen, Bachbrücke (1170,1855)→mitte
  - `test_place_at_finds_places_and_not_the_gaps`: (500,3288)→"muehle", (1143,2270)→"lager", (1204,2103)→"schrein",
    (1600,3000)→"", Höhlen-Innenraum nie über `place_at`
  - `test_rooms_have_their_page`: `place_in_room("cave")`→"hoehle_innen", `("glashaus")`→"gewaechshaus_innen", `("x")`→""
  - `test_texts_fit_three_lines`: für jeden Ort `wrap_text(text).size() <= 3`, jede Zeile ≤ 122 px
  - `test_every_kanji_is_in_the_font`: jedes Zeichen aus Ort- und Gebiets-Kanji hat `PixelFont.kanji().has_char()`
- [ ] **Step 2:** `bash tools/test.sh` → FAIL (`Memories` fehlt).
- [ ] **Step 3:** `core/memories.gd` schreiben.
- [ ] **Step 4:** `bash tools/test.sh` → grün.
- [ ] **Step 5: Commit** `Erinnerungen: Tabelle der Orte und Gebiete`

### Task 3: Spielstand

**Files:**
- Modify: `core/save_data.gd`, `tests/test_save_data.gd`

**Interfaces:**
- Produces: in `SaveData`: `var found := PackedStringArray()` (Fundreihenfolge), `var regions_seen := PackedStringArray()`,
  `var bookmark := false`; ConfigFile-Abschnitt `erinnerungen`, Schlüssel `orte`, `gebiete`, `lesezeichen`.

- [ ] **Step 1: Tests:** `test_memories_survive_a_round_trip` (found ["lager","muehle"] in der Reihenfolge, regions,
  bookmark true); `test_old_save_has_an_empty_book` (Datei nur mit `weg`/`ton` → found leer, bookmark false).
- [ ] **Step 2:** rot. **Step 3:** laden/speichern ergänzen. **Step 4:** grün.
- [ ] **Step 5: Commit** `Erinnerungen: im Spielstand`

### Task 4: Der Wächter

**Files:**
- Create: `scenes/memory_keeper.gd`, `tests/test_memory_keeper.gd`
- Modify: `tests/run_tests.gd`

**Interfaces:**
- Consumes: `Memories` (Task 2), `SaveData.found/regions_seen/bookmark` (Task 3)
- Produces: `class_name MemoryKeeper extends RefCounted`, `var save: SaveData`,
  `const DWELL := 1.5`, `func step(p: Vector2, room: String, dt: float) -> Array[Dictionary]` – gibt neue Ereignisse
  `{kind: "region"|"place", key: String}` zurück, Gebiet vor Ort; trägt Funde in `save` ein und setzt
  `save.bookmark = true` bei jedem neuen Ort. `room` ist `""` draußen, sonst der Raumname.
  Gebiete zählen erst nach `DWELL` Sekunden ununterbrochen im selben Gebiet; Orte sofort.

- [ ] **Step 1: Tests:**
  - `test_first_visit_brings_region_then_place`: am Lager, `step(..., 2.0)` → [region mitte, place lager]
  - `test_second_visit_brings_nothing`
  - `test_found_keeps_the_order`: muehle, dann lager → `save.found == ["muehle","lager"]`
  - `test_region_needs_dwell`: 0,5 s in kogarashi, zurück nach mitte, wieder 0,5 s → kein kogarashi-Ereignis
  - `test_room_gives_its_page_and_no_outside_place`: `step(Vector2(1143,2270), "cave", 2.0)` → nur place hoehle_innen
  - `test_new_place_sets_the_bookmark`
- [ ] **Step 2:** rot. **Step 3:** schreiben. **Step 4:** grün.
- [ ] **Step 5: Commit** `Erinnerungen: Wächter`

### Task 5: Die Schriftrolle

**Files:**
- Create: `scenes/name_scroll.gd`, `tests/test_name_scroll.gd`
- Modify: `tests/run_tests.gd`

**Interfaces:**
- Produces: `class_name NameScroll extends Control` (Vollbild, `MOUSE_FILTER_IGNORE`),
  `func show_name(kanji: String, romaji: String) -> void` (stellt in eine Warteschlange), `func showing() -> String`
  (Kanji der gerade sichtbaren Rolle oder `""`), `const HOLD := 3.0`, `const ROLL := 0.4`.
  Zeichnet mit `_draw` nach `vorschau.py` `scroll_v`: Stab oben (mit Schnur), roter Streifen, Papier 24 px breit,
  je Kanji 17 px, Stab unten, Schild mit Umschrift an zwei Schnüren. Position (14, 8). Auf- und Abrollen über die
  Papierlänge in `ROLL` Sekunden.

- [ ] **Step 1: Tests:** `test_names_come_one_after_another` (zwei Namen: erst erster sichtbar, nach
  `ROLL*2+HOLD+0.1` s der zweite, danach `""`); `test_scroll_lets_taps_through` (mouse_filter IGNORE);
  `test_scroll_stays_on_screen` (längster Name: Rechteck inkl. Schild innerhalb 180 × 400).
- [ ] **Step 2:** rot. **Step 3:** schreiben (Zeit über `_process`, im Test `advance(dt)` als öffentliche Hilfe).
  **Step 4:** grün.
- [ ] **Step 5: Commit** `Erinnerungen: Schriftrolle`

### Task 6: Buchseiten und Lesezeichen

**Files:**
- Create: `scenes/memory_page.gd`, `tools/gen_bookmark.py`, `assets/ui/buch_lesezeichen.png`, `tests/test_memory_book.gd`
- Modify: `scenes/book_ui.gd` (Mode MEMORIES, Hauptmenü-Eintrag, Blättern, Lesezeichen), `tests/run_tests.gd`

**Interfaces:**
- Consumes: `Memories.place/wrap_text`
- Produces:
  - `class_name MemoryPage extends RefCounted`, `static func build(into: Control, key: String) -> void` – Titel
    (Handschrift, `GRAPHITE`) bei y 0, Strich `MemoryStroke` bei y 21 (schnell gezogen, Rezept `strich` aus
    vorschau.py), Umschrift `FAINT` bei y 23, Skizze `TextureRect` bei (-6, 40) Größe 130 × 87, `TEXTURE_FILTER_LINEAR`,
    Zeilen ab y 133 im Abstand 13.
  - in `BookUI`: `var memories := PackedStringArray()`, `signal bookmark_seen`, `func set_bookmark(on: bool)`,
    `func has_bookmark() -> bool`, Mode `MEMORIES` mit `_mem_page`, Eintrag „Erinnerungen“ im Hauptmenü nur wenn
    `memories` nicht leer; „zurück“ wie bei den Reisen, „weiter“ springt auf die nächste Erinnerung, nach der letzten
    zurück zur ersten. `open_in_game()` blendet das Band aus und sendet `bookmark_seen`.
  - `buch_lesezeichen.png`: Band + Spalt aus `vorschau.py` (Lesezeichen-Variante), gleiche Größe/Lage wie
    `buch_knopf` plus Überhang nach unten; wird über dem Knopf gezeichnet.

- [ ] **Step 1: Tests:**
  - `test_no_memories_no_entry` / `test_one_memory_shows_the_entry`
  - `test_memory_page_shows_title_picture_and_text` (Mühle: Label „Wassermühle“, ein TextureRect 130 × 87, 3 Zeilen)
  - `test_memory_text_stays_on_the_page` (alle 31: rechte Kante jedes Labels ≤ `PAPER_RIGHT - 18`)
  - `test_bookmark_shows_until_the_book_opens` (set_bookmark(true) → sichtbar bei CLOSED; open_in_game → weg, Signal kam)
  - `test_new_page_while_book_is_open_is_there_next_time` (memories wächst bei offenem Buch, Lesezeichen bleibt bis zum
    nächsten `open_in_game`)
- [ ] **Step 2:** rot. **Step 3:** schreiben; `gen_bookmark.py` erzeugt das PNG (Test in `tools/tests/test_ui_assets.py`:
  Band ragt unten über den Knopf hinaus, Umriss nur unterhalb des Buchs). **Step 4:** `bash tools/test.sh` grün.
- [ ] **Step 5: Commit** `Erinnerungen: Buchseiten und Lesezeichen`

### Task 7: Einbau, Version, Gerät

**Files:**
- Modify: `scenes/main.gd`, `export_presets.cfg` (version/code 118, version/name "0.23.0"), `tests/test_scenes_compile.gd`
  oder ein neuer Integrationstest in `tests/test_memory_keeper.gd`

**Interfaces:**
- Consumes: alles oben. In `Main`: `var keeper := MemoryKeeper.new()`, `var scroll: NameScroll` (in eigener
  CanvasLayer unter dem Buch, layer 19); alle 0,25 s und direkt nach `_on_travel`: `keeper.step(player.position,
  room-Name falls inside sonst "", dt)`; Ereignisse → `scroll.show_name`, bei Orten `book.memories.append(key)`,
  `book.set_bookmark(true)`, leise `seite_%d` über `book._play`-Weg (SFX_DB „seite“), `_store()`. Beim Start:
  `book.memories = save.found`, `book.set_bookmark(save.bookmark)`; `bookmark_seen` → `save.bookmark = false`, speichern.
  Der Raumname: `room == cave` → "cave", `room == glashaus` → "glashaus".

- [ ] **Step 1: Test** `test_travel_to_the_mill_writes_the_page` (Main-Szene laden, `_on_travel(Vector2(500,3288))`,
  ein Schritt → `save.found` enthält "muehle", Buch hat das Lesezeichen).
- [ ] **Step 2:** rot. **Step 3:** verdrahten. **Step 4:** `bash tools/test.sh` grün inkl. Probelauf.
- [ ] **Step 5: Commit** `0.23.0: Erinnerungen – Skizzenseiten im Buch, Schriftrollen, Lesezeichen`, Push.
- [ ] **Step 6:** `bash tools/build_install.sh` (bei „still in progress“: `gh run watch`, dann erneut), danach
  `~/glenn-push.sh "Akahana 0.23.0 ist drauf: Erinnerungen im Buch" "Akahana"`.
