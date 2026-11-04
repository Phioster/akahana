# Norden: Einbau ins Spiel – Bauplan

Stand 2026-11-04. Grundlage: `docs/superpowers/specs/2026-11-04-norden-design.md`. Alle vier Zonen sind abgenommen
(Abnahme-Seite Schritte 51–54, Entwürfe in `tools/world/north/zone{1..4}_draft.py`, Höhle innen in `cave_inside.py`).

## Grundidee
- `tools/world/gen_north.py` läuft als letzter Generator, nach gen_east und vor split_chunks.
- Er nimmt die fertige Welt (assets/world + Vollbilder) und setzt **1200 Reihen oben drauf** (NORTH_H, = 6 Kachelreihen).
- Alle Vollbilder wachsen oben mit: ground, flowers, bend, water, low, refl, walk, walk_cells, ground_mat,
  open_water, lake, mist_fields, grade_field.
- Alle Koordinaten in world.json rücken um +1200 nach unten: sprites, lights, start, brook, birds, wisps,
  fireflies, lamp_paths, fire, places. mood wird oben mit Reihen ergänzt.
- Im Spiel rücken die festen Koordinaten mit: test_travel, ambience.RUIN. Ein alter Spielstand
  (Höhe 3600) wird beim Laden einmalig um +1200 verschoben.

## Schritte
1. **Verschieben ohne Inhalt.** gen_north mit einem Platzhalter-Norden: Schnee, nicht begehbar. Er verschiebt alles,
   und das Spiel zieht nach. Prüfung: Tests grün, Testreisen landen am selben Ort, die Welt sieht unverändert aus.
2. **Boden und Figuren.** Die vier Zonen-Entwürfe werden zu einer Leinwand von 1800 × (1200 + Überhang) zusammengesetzt.
   Ein Sammler nach dem Muster von `south/layers.py` trennt Boden und stehende Dinge (Figuren mit Fuß).
   Lichter: Hütte, Laternen, Höhlenkerze.
3. **Begehbarkeit, Bodenart, Wasser.**
   - Begehbar: Wege, Lichtungen, Schnee zwischen den Tannen.
   - Gesperrt: Felsen, Stämme, Schlucht (außer dem Steg), Wasser, Gipfel, Nebelrand.
   - Bodenart: Schnee (SNOW).
   - Wasser: See, Fluss und Bach in water.png. Das Eis bleibt starr.
   - Der Wasserfall wird ein Sprite-Streifen mit 8 Bildern.
4. **Dunkelheit (grade_field/mood).** Dunkel sind der dichte Nadelwald und der Höhlenhügel, hell sind Schnee und Pass.
   Die Laterne folgt dem von selbst.
5. **Höhle.** Ein eigener Bildschirm (180×400). Übergang am Eingang hin und zurück. Innen gilt es immer als dunkel,
   die Laterne wird aufgehängt.
6. **Testreisen.** Felstor, Hütte, Höhle, Pass, Aussicht, Bergsee. Karte/Buch, falls nötig.
7. **Klänge.** Wind, Schritte im Schnee, Holzknacken an der Hütte, Wasserfall.
8. **Build und Version.** Danach folgen die Schnee-Fußspuren als eigene Aufgabe.

## Regeln
- Die Vollerzeugung (`build/check/rebuild_full.sh`) läuft im Hintergrund mit nice. Akkutemperatur beachten.
- Vor `tools/build_install.sh` immer pushen.
