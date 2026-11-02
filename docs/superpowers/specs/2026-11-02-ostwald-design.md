# Ostwald (Hotarumori): dunkler Wald mit vereinzelten Lichtungen – Design

Stand 2026-11-02, Entwurf zur Abnahme. Aus `docs/ideenblatt.md` („Osten: Schreine und besondere Orte“), Namen in `docs/namen.md`
(蛍森 Hotarumori, 祈りの場 Inori-no-ba).

## Was Philip will
- Dunkel, mystisch, KEIN Herbstwald. Vereinzelte Lichtungen im Wald (nicht offen, nicht überall eng).
- Moodboard (2026-11-02, Pinterest): riesiger moosbehangener Baum an stillem Wasser mit Spiegelung und Nebel; hohe türkisgrüne
  Lichtschächte durch überwucherten Wald; Lichtung mit bemoosten Grabsteinen, Steinhaufen, Schwertern im Boden unter Mondlicht;
  Mondnacht mit verfallener Kapelle, Steinweg, krummem Baum. Gemeinsam: Dunkelheit + EINE kühle Lichtfarbe, Moos, Ruinen, Spiegelung.
- Irrlicht (Glenn) lebt schon bei (496, 820) am Westrand des Ostens. Es ist der warme Punkt im Kühlen.

## Ziele
- Welt wächst nach OSTEN (Spalten 3–4 sind heute der Waldsaum-Platzhalter, wird ersetzt); alte Welt und Süden bleiben pixelgleich.
- Ein Gebiet von ca. 1200 × 1400 Kunstpixeln ab x 540, y 300…1700, dazu ein Waldsaum nach Süden (bis y 2900) als Übergang vom See; der Rest ringsum bleibt dichter Wald/Nebel (keine harten Weltgrenzen, Vision Kartenform).
- Orte (Plan Abnahme-Seite Schritt 37, Runde 3): 0 Mohn-Übergang (weich, ~200 px), 1 Waldtor, 2 Moosweg, 3 Gräberlichtung, 4 Wasserplatz mit Riesenbaum (Bach zum See),
  6 alte Steinbrücke mit Bögen über einen Fluss (Philip 2026-11-02, ersetzt die Kapelle; der Fluss fließt von Norden über die Brücke zum Wasserplatz, von dort der Bach zum See), 7 Jizō-Weg, 5 Ritualplatz GANZ HINTEN im Osten (nur über zwei lange Pfade), 9 Waldwiese, 10 Waldsaum vom See nach Nordosten (Wiese → dunkler Wald), zweiter Eingang über die Fischerhütte.
- Abgenommen 2026-11-02 (Plan Runde 3): manche Orte abseits (z. B. Gräber), manche direkt am Weg (Kapelle, Wasserplatz).
- Lichtungen unregelmäßig, Pfade stark gewunden (Philip: „natürlicher, viel mehr hin und her durch die Bäume“).
- Wege sind schmale Pfade; dazwischen undurchdringlicher Wald (nur Pfade und Lichtungen begehbar), keine Sackgassen außer 8.

## Nicht-Ziele
- Keine Kämpfe, Rätsel, Aufgaben, Erklärtexte. Keine Schwerter als Waffen: Stäbe/Stelen statt Schwerter im Boden.
- Kein Herbstlaub, keine Sommerfarben, kein starkes Leuchten.

## Anti-Ziele
- Pixelmatsch durch Dunkelheit: Sprites müssen lesbar bleiben (Lehre aus dem Mönch im Licht).
- Zweite Lichtfarbe neben der kühlen; das Warme bleibt Laternen, Feuer, Glenn.

## Entscheidungen (meine Vorschläge, zur Abnahme)
- Licht: Mond-/Türkis-Grün als einzige kühle Farbe; Glühwürmchen im Ostwald kühl türkis (Name Hotarumori), im Süden bleiben sie warm.
- Region-Grade: eigenes Feld (wie mist_fields) dunkelt Boden und Bäume ab, färbt grün-blau, Dithering bleibt.
- Bausteine aus `tools/world/lib` und den Süd-Klassen (Laterne, Wegstein, Steg, Seerosen, Spiegelung, Wasser-Shader) wiederverwenden.
- Abnahme Zone für Zone (Plan → Entwurf je Ort), Auslieferung auf einmal; neue Klänge zuletzt (Wind in Nadeln, Tropfen, Glöckchen).

## Dem Bauenden überlassen
- Genaue Pfadführung und Baumdichte, solange die Lichtungen wie im Plan verbunden sind.
