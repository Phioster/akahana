# Norden (Yukimine-tōge): Wald und Gebirge – Design

Stand 2026-11-04, Entwurf zur Abnahme (Plan-Skizze `tools/world/north/plan_north.py`, Abnahme-Seite Schritt 48).
Quelle: `docs/ideenblatt.md` („Norden: Wald und Gebirge“, „Schnee“), Namen in `docs/namen.md` (雪峰峠 Yukimine-tōge).
Philip (2026-11-04): „nach dem Plan einen Entwurf, wieder mit Abnahme-Seite“; offene Punkte fragt er danach selbst ab.

## Was das Ideenblatt will
- Die Landschaft wird nach oben allmählich kälter und felsiger: einzelne Tannen → dichter Nadelwald → steinige Wege
  → verschneite Berglandschaft.
- Felsen, Schluchten, Höhlen, verschneite Lichtungen; eine abgelegene Holzfällerhütte mit Werkzeugen, Holzstapeln
  und Alltagsdingen (bewohnt gewesen, keine erzählte Geschichte); Aussichtspunkte und schmale Bergpfade.
- Schnee sammelt sich im Norden deutlich stärker an; der Untergrund verändert sich sichtbar.

## Ziele
- Die Welt wächst um **1200 Reihen nach oben** über die ganze Breite (1800 → Welt 1800 × 4800).
  Alles Heutige bleibt pixelgleich und rückt nur nach unten.
- Orte (Plan, Nummern wie auf der Skizze):
  1. **Felstor**: Der Weg aus Kogarashi (heute bei x≈275 am Felsband oben) bricht durch das Band.
  2. **Nadelwald**: einzelne verschneite Tannen, die nach oben zum dichten, dunklen Nadelwald werden. Dort kommt die Laterne.
  3. **Holzfällerhütte** auf einer Lichtung: Blockhütte mit warmem Fensterlicht, Holzunterstand mit Stapel, Hackklotz mit Axt,
     Stümpfe, liegende Stämme, Sägebock, Laterne am Pfahl, Trampelpfade zwischen Tür, Holz und Klotz.
  4. **Höhle**: Felsmaul mit Eiszapfen an der Schlucht, ein paar Schritte begehbar, dunkel (Laterne), innen eine Kerze/kleiner Altar.
  5. **Schlucht mit Steg**: Felsspalte von West nach Ost mit zugefrorenem Bach unten, schmaler Holzsteg darüber.
  6. **Serpentinen**: schmaler Bergpfad im Zickzack über den Felshang, Felsen, Krüppelkiefern, mehr Schnee.
  7. **Aussicht**: Felsvorsprung mit Bank und Steinlaterne, Blick nach Osten über den Bergsee und den Wald.
  8. **Pass**: der Sattel zwischen den Gipfeln, Steinmännchen, verschneiter Jizō und Steinlaterne. Dahinter Nebel und Gipfel (Weltrand).
  9. **Bergsee mit Wasserfall**: halb zugefroren, ein Wasserfall fällt über eine Felsstufe hinein, Abfluss = **Quelle des Ostwald-Flusses**
     (der Fluss beginnt heute bei (1260, 300) im dichten Wald).
  10. **Flussweg**: vom Bergsee am Fluss entlang nach Süden bis zur Steinbrücke im Ostwald.
- **Rundweg ohne Sackgassen**: Kogarashi → Felstor → Hütte → Schlucht → Serpentinen → Aussicht → Bergsee → Flussweg → Steinbrücke (Ostwald).
  Abstecher: Höhle und Pass (Endpunkte mit Ziel).
- Schnee nimmt nach oben zu (Boden heller, Wehen an Felsen und Stämmen). Unter dichten Tannen liegt weniger Schnee.
- Der Rand über den Gipfeln wird zu Nebel bzw. Fels, ohne harte Kante (Vision Kartenform: keine sichtbaren Weltgrenzen).

- **Breite Überhänge (Philip, 2026-11-04):** Keine Zone ist vom Nachbarn abgetrennt. Auf rund 300 px greifen sie ineinander:
  - Boden in Flecken: Der alte Boden läuft gespiegelt nach oben, aber ohne seine Pfade und ohne die Felswand.
  - Tannen wachsen nach Kogarashi und zwischen die Ostwaldbäume hinunter, Ostwaldbäume wachsen nach oben zwischen die Tannen.
  - Die alte Felswand am oberen Rand löst sich in verstreute Felsen auf.
  - Bäume, die heute am oberen Weltrand flach abgeschnitten sind, werden ganz neu gezeichnet.

## Nicht-Ziele
- Keine Kämpfe, Kletter-Mechanik, Rätsel, Erklärtexte.
- Keine begehbaren Häuser: Die Hütte bleibt außen, nur das Gewächshaus im Westen ist begehbar.
- Fallender Schnee, Fußspuren im Schnee und Wetter sind eigene spätere Aufgaben. Sie werden hier nur vorbereitet,
  über die Bodenart „Schnee“ in ground_mat.

## Anti-Ziele
- Weiß in Weiß: Objekte und Mönch dürfen im hellen Schnee nicht verschwinden (Lehre LITSTONE/Kontrast aus dem Süden).
- Harte Nähte oder Rechtecke zwischen alt und neu (Lehre aus Ostwald: Rezept der Nachbarzone nutzen, Karten mitdenken).
- Zu viele Lichter: Warm sind nur die Hütte, die Laternen und die Kerze in der Höhle.

## Entscheidungen (meine Vorschläge, zur Abnahme)
- **Bausteine**: Hütte, Holzunterstand, Hackklotz mit Fällaxt, Stümpfe, liegende Stämme, Schneewehen (`drift`) und Tannen
  kommen aus `tools/world/lib/berg_objects.py` (Philips Berg-Sperrbildschirm, abgenommen), passend klein für das Spiel gezeichnet.
  Dazu kommen Fir/Ruine/Felsen aus der alten Welt und Steinlaterne/Jizō aus dem Osten.
- **Dunkelheit**: eigenes Feld wie im Ostwald (grade_field). Dunkel sind der dichte Nadelwald und die Höhle, hell sind Schnee und Pass.
  Die Laterne nutzt dieses Feld schon, sie geht dort also von selbst an.
- **Technik Höhe**: Die Generatoren bekommen einen Versatz `NORTH_H = 1200`. Weltdaten, Spielstand (Position + HN)
  und Testreisen rücken einmalig nach unten. Der Generator `gen_north.py` läuft nach gen_south/gen_east.
- **Glühwürmchen**: keine im Norden, dafür später Schneeflocken.
- **Klänge (zuletzt)**: Wind über Fels, Knirschen im Schnee als Schritt, leises Holzknacken an der Hütte, Wasserfall.
- Abnahme wie beim Süden: Plan → Entwurf je Zone (unten Wald + Hütte, Mitte Schlucht + Höhle, oben Fels + Pass, Osten Bergsee + Fluss)
  → Generator → Karten/Licht → Klänge → Build auf einmal.

## Offen (Philip)
- Namen der Orte (Vorschläge auf der Abnahme-Seite).
- Soll die Höhle eine Kleinigkeit zum Entdecken haben (Kerze/Altar), oder nur Stimmung?

## Dem Bauenden überlassen
- Genaue Pfadführung, Baumdichte, Felsformen, solange Rundweg und Orte wie im Plan verbunden sind.
