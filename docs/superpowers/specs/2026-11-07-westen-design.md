# Westen (Wasure-zato): das verlassene Dorf – Design

Stand 2026-11-07, Plan zur Abnahme (Skizze `tools/world/west/plan_west.py`, Abnahme-Seite Schritt 61).
Quellen: `docs/ideenblatt.md` („Westen: Dorf und menschliche Spuren“), Philips ChatGPT-Vorlagen in `docs/west_vorlage/`
(`lebendig.png`: Aufbau, Wiese, Mohn; `verlassen.png`: Zustand der Häuser).

## Was Philip will (2026-11-07)
- Keine Stadt: eine Siedlung, ein Dorf mit Häusern und schönen Gärten, locker, nichts gequetscht.
- Häuser verlassen wie in `verlassen.png` (Moos, eingefallene Dächer, zerbrochene Fenster, Ranken).
- Gärten verwildert, aber schön (Hortensien, Blumen, Obstbäumchen, Beete und Zäune noch erkennbar).
- Das Gewächshaus ist noch ganz, höchstens ein paar Risse im Glas; das einzige begehbare Haus.
- Licht nur von Laternen, Fackeln und Ähnlichem; Fenster bleiben dunkel.
- Größe: 900 px breit (wie Süden/Ostwald), 7–9 Häuser.
- Früher entschieden (2026-10-26): Kathedrale raus; Werkstätten vor den Häusern / offene Unterstände; fester Abend.

## Ziele
- Welt wächst um 900 Spalten nach links (1800 → 2700 × 4800). Alles Heutige bleibt pixelgleich und rückt um +900.
- Dorf etwa 500 × 700 px auf Höhe des Starts (y ≈ 2050–2700), Eingang vom Lagerfeuer (222, 2292) nach Westen.
- Orte (Nummern wie auf der Skizze): 1 Dorfeingang, 2 Dorfplatz mit Brunnen, 3 neun Häuser mit Gärten, 4 Gewächshaus
  (innen eigener Bildschirm wie die Höhle), 5 Steinmetz (offener Unterstand, Meißelspuren auch an Brunnen/Mauern/Laternen),
  6 Dorfschrein mit Treppe, 7 Obstwiese (Weg nach Kogarashi), 8 alte Reisfelder, 9 Wassermühle am Bach in die Seewiesen,
  10 Bambushain (dunkel, Laterne).
- Rundweg ohne Sackgassen: Lagerfeuer → Eingang → Platz → Obstwiese → Kogarashi; Platz → Gewächshaus → Reisfelder →
  Mühle → Seewiesen. Abstecher: Schrein, Bambushain.
- Ränder: Nordwesten Tannenwald (Fortsetzung Kogarashi/Norden), Süden Seewiesen mit Einzelbäumen, Westrand Wald/Nebel.

## Nicht-Ziele
- Keine Bewohner, keine Geschichte in Texten, keine weiteren begehbaren Häuser, keine Kathedrale.
- Klänge und Gewächshaus-Inneres erst nach den Zonen.

## Anti-Ziele
- Gequetschte Häuser oder ein Stadtbild.
- Leuchtende Fenster.
- Nähte/Rechtecke zur alten Welt (Lehre Ostwald: Rezept der Nachbarzone nutzen, alle Karten mitdenken).
- Objekte in Mönchsgröße falsch: Haus ≈ Schrein (56 × 54), Mönch 8 × 15 sichtbar.

## Vorschläge (zur Abnahme)
- Namen: 忘れ里 Wasure-zato, 井戸端 Idobata, 硝子室 Garasu-muro, 石屋 Ishiya, 里の社 Sato-no-yashiro, 果樹の原 Kaju-no-hara,
  古田 Furuta, 水車小屋 Suisha-goya, 竹藪 Takeyabu.
- Technik: Versatz `WEST_W = 900` für Generatoren, Weltdaten, Spielstand und Testreisen (wie NORTH_H); `gen_west.py` nach gen_north.
- Abnahme Zone für Zone: (1) Eingang, Platz, Häuser; (2) Gewächshaus, Steinmetz; (3) Schrein, Obstwiese;
  (4) Reisfelder, Mühle, Bambus → Gewächshaus innen → Einbau → Licht/Grade-Feld → Klänge → Build auf einmal.

## Offen (Philip)
- Plan, Orte, Rundweg, Namen; ob Mühle/Reisfelder/Bambus gewollt sind.
