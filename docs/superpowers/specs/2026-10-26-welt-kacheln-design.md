# Welt in Kacheln – Design

Stand 2026-10-26. Ausbaustufe 2 aus `docs/ideenblatt.md`.

## Warum

Die Welt soll für 1,5–2 Stunden Entdecken reichen: Mohnfeld in der Mitte, See im Süden, Berge im
Norden, Wald mit Ritualort im Osten, später der Westen. Das ist ein Vielfaches der heutigen Karte
(540 × 1200 Kunstpixel). Heute liegt alles auf einmal im Speicher: Boden und Mohn als je ein großes
Bild, alle 199 Objekte als Knoten (6,2 MB Bildfläche, alle animiert), alle Vögel, Irrlichter und
Ortsklänge, ein Wegsuch-Raster über die ganze Welt und eine Begehbarkeits-Maske mit einem Byte je
Pixel. Bei der fünf- bis zehnfachen Fläche geht das auf dem Handy nicht mehr.

## Ziel

Für Philip sieht und klingt die Welt genau wie heute: durchgehend, ohne Nähte, ohne Ruckler beim
Nachladen. Im Hintergrund ist nur da, was er gerade sehen oder hören kann, plus ein Rand zum
Vorladen. Alles andere ist Daten auf der Festplatte.

## Nicht-Ziele

- Keine neuen Regionen in dieser Stufe (See, Norden, Osten kommen danach).
- Keine neue Optik, nichts zum Abnehmen. Die Karte bleibt inhaltlich gleich.
- Kein Umbau des Weltgenerators selbst; er schreibt weiter große Bilder, ein eigener Schritt zerlegt sie.

## Anti-Ziele (wäre ein Fehlschlag, auch wenn es technisch läuft)

- Sichtbare Kanten zwischen Kacheln, besonders im Mohn (Wind und Ausweichen verschieben Blüten
  bis zu 4 Pixel – über Kachelgrenzen hinweg dürfen dabei keine Blüten abgeschnitten werden).
- Ein Ruckler, wenn eine Kachel nachlädt.
- Vögel, Irrlicht oder Klänge, die plötzlich vor den Augen auf- oder abtauchen.
- Speicher, der beim Durchwandern der ganzen Karte wächst statt gleich zu bleiben.

## Entscheidungen

- **Kachelgröße 180 × 200 Kunstpixel** (eine Bildschirmbreite, eine halbe Bildschirmhöhe). Die heutige
  Welt sind 3 × 6 Kacheln. Künftige Weltgrößen sind Vielfache davon.
- **Rand (Apron) von 8 Pixeln** um jedes Mohnbild, damit der Shader über die Kachelkante hinaus
  lesen kann. Gezeichnet wird nur das Innere.
- **Geladen wird**, was die Kamera sieht, plus eine Kachel Rand (Vorladen). Freigegeben wird erst ab
  zwei Kacheln Abstand (Hysterese, kein Hin-und-her an der Grenze).
- **Bilder laden im Hintergrund** (eigener Thread), Daten (Begehbarkeit, Boden) sind klein und laden sofort.
- **Objekte, Tiere, Klänge, Lichter**: ein gemeinsamer „Aktivierer“. Jeder Eintrag hat einen Ort und
  einen Radius; sein Knoten entsteht beim Hereinkommen in den Radius und verschwindet erst beim
  Verlassen eines größeren Radius. Objekte und Lichter: Sichtweite + Rand. Klänge: ihre Hörweite + Rand.
  Vögel und Irrlicht: außerhalb der Sicht, damit niemand das Auftauchen sieht.
- **Wegsuche lokal**: Getippt wird immer auf etwas Sichtbares, also wird das Raster nur für das Rechteck
  um Start und Ziel (plus Rand) aus den geladenen Kacheln gebaut.
- **Daten bleiben klein und global** in `world.json`: Objektliste, Lichter, Vogelplätze, Bach, Irrlicht,
  Feuer, Startpunkt, Kachelmaße.
