# Erinnerungen: Skizzenseiten, Schriftrollen, Hinweis am Buch (Schritt 1)

Stand 2026-11-16, von Philip abgenommen.

## Absicht
Das Buch soll die Wanderung festhalten. Wer einen Ort zum ersten Mal erreicht, bekommt die Skizze des Mönchs
von diesem Ort ins Buch, mit Name und ein, zwei Zeilen. Beim ersten Betreten eines Gebiets oder Orts zeigt
eine Schriftrolle kurz dessen japanischen Namen (so beschlossen am 2026-10-27, `docs/namen.md`). Es bleibt ein
ruhiges Wanderspiel: Das Buch wächst mit dem, was man gesehen hat, und zeigt nie, was noch fehlt.

## Ziele
- 31 Erinnerungsseiten (29 Orte + Mühle + Schrein), Bilder abgenommen am 2026-11-16, gefiltert in
  `~/akahana-skizzen/seiten/` (Schlüssel = Dateiname, z. B. `lager.png`).
- Eine Seite kommt dazu, wenn der Mönch dem Ort nahe genug kommt; Höhle innen und Gewächshaus innen beim Betreten.
- Schriftrolle mit Kanji und Umschrift beim ersten Betreten jedes Gebiets (6) und Orts (31).
- Leiser Hinweis, dass eine Seite dazugekommen ist: Lesezeichen am Buchknopf und Papierrascheln.
- Alles bleibt über einen Neustart erhalten.

## Nicht-Ziele (dieser Schritt)
- Fundstücke (Kaki, Federn, eingeklebte Blätter): Schritt 2, eigener Entwurf. Platz dafür auf der Seite ist vorgesehen.
- Neue Zeichnungen oder neue Orte.

## Anti-Ziele (wäre ein Fehlschlag, auch wenn es läuft)
- Leere Seiten, Zähler, „12 von 31“, Prozent, Häkchen oder irgendetwas, das nach Sammelliste aussieht
  (Philip: „sonst will man alles finden und es ist wieder wie so ein Fortschrittsbalken“; `ideenblatt.md`).
- Eine Schriftrolle, die den Weg blockiert, ein Tippen verlangt oder sich ständig wiederholt.
- Verpixelte Skizzen: Die Seiten sollen feiner aussehen als die Pixelwelt.

## Randbedingungen
- Godot 4.7.2, Bildschirm 180 × 400 (Hochformat), `stretch canvas_items`: UI wird in echter Handyauflösung
  gezeichnet, eine hochaufgelöste Textur bleibt also scharf, wenn man sie verkleinert zeichnet (Filter linear).
- Buchseite `buch_seite` ist 156 × 236; Text geht bis x 144 (`PAPER_RIGHT`), unten bis etwa y 220.
- Schriften: Handschrift Caveat (`PixelFont.hand()`, kann ō ū ā), Kanji Klee One (`PixelFont.kanji()`, vorbereitet, noch
  unbenutzt).
- Umblättern (`page_turn.gdshader`, Stapel `_sheets`) gibt es; die Erinnerungen nutzen es mit.
- Spielstand: `SaveData` in `user://mohnweg.cfg` (ConfigFile).
- Optik und Klang erst als Vorschau zur Abnahme, dann bauen (Schriftrolle, Seitenaufbau, Strich am Knopf).
- Tests: `tests/run_tests.gd`, CI muss grün sein, bevor installiert wird; keine CI-Fehlermails (vorher lokal testen).

## Wege (abgewogen)
- **A, Ortstabelle und Wächter (gewählt von Philip):** eine Tabelle aller Orte und Gebiete, ein kleiner Knoten
  prüft ein paar Mal pro Sekunde die Position. Alles an einer Stelle, leicht zu testen, Schritt 2 hängt Einträge an.
- B, Auslöseflächen in der Welt (Area2D): Godot-üblich, aber die Welt kommt aus Python, die Orte wären verstreut.
- C, Gebietskarte als Bild: genau an Rändern, für ein paar Kreise zu aufwendig.

## Entwurf

### 1. Die Tabelle (`core/memories.gd`, Name ist Sache des Bauenden)
Je Ort: Schlüssel, Gebiet, Kanji, Umschrift, deutscher Name, Mittelpunkt (Weltkoordinaten wie `TestTravel.PLACES`),
Radius, Bilddatei, Text (1–2 Zeilen). Innenräume statt Mittelpunkt mit dem Raum (Höhle, Gewächshaus).
Je Gebiet: Schlüssel, Kanji, Umschrift. Gebiete: Akahana-no-hara (Mohnfeld), Kogarashi, Yukimine-tōge (Norden),
Hotarumori (Ostwald), Kagami-ko (Süden/See), das Dorf im Westen.
Namen und Texte kommen von der Namen-und-Texte-Abnahme (unten) und werden erst danach eingetragen.

### 2. Der Wächter
- Prüft etwa 4-mal pro Sekunde, wo der Mönch steht (nicht im Kameramodus; Testsprünge siehe Offen).
- Ort zum ersten Mal im Radius → an die Fundliste anhängen (Reihenfolge = Reihenfolge des Findens), speichern,
  Schriftrolle zeigen, Hinweis am Buch setzen.
- Gebiet zum ersten Mal betreten → nur Schriftrolle, keine Seite.
- Höhle innen und Gewächshaus innen: beim Betreten des Raums (die Räume kennt `main.gd` schon).
- Gebietserkennung: aus dem, was das Spiel schon weiß (`Music.weights`: wald, berge, see, dorf, mohnfeld;
  `Ambience.altitude`), ergänzt um Grenzen für Kogarashi und Ostwald. Ein Gebiet zählt erst, wenn man klar
  drin ist (kein Flackern am Rand).

### 3. Die Schriftrolle (abgenommen 2026-11-16, Vorschau B)
- Hängende Rolle (Kakemono) oben links: Holzstab mit Schnur oben, roter Streifen, Papierbahn, Kanji senkrecht
  untereinander (Klee One), Holzstab unten.
- Die Umschrift hängt an zwei Schnüren auf einem kleinen Papierschild unter der Rolle, dunkle Bleistiftschrift
  (Caveat), damit sie auf jedem Boden lesbar ist.
- Etwa 3 Sekunden sichtbar, rollt sich ab und wieder auf (oder blendet weich); keine Eingabe nötig,
  Tippen geht durch zur Welt.
- Kommen Gebiet und Ort gleichzeitig, erst das Gebiet, dann der Ort.
- Vorschau-Skript: `~/akahana-skizzen/vorschau/vorschau.py` (Maße dort), wird beim Bauen ins Repo
  (`build/preview/erinnerungen/`) übernommen.

### 4. Die Seiten im Buch (abgenommen 2026-11-16, Vorschau C)
- Im Hauptmenü ein Eintrag „Erinnerungen“, sichtbar erst ab der ersten gefundenen Seite.
- Eine Erinnerung pro Buchseite, Blättern mit der vorhandenen Animation, Knöpfe „zurück“/„weiter“ wie bei den Reisen.
- Aufbau (Inhaltsursprung 18/20 wie bisher): deutscher Name in Handschrift, darunter ein schnell gezogener
  Bleistiftstrich (setzt kräftig an, steigt leicht, wird dünn und läuft über das Wort hinaus, nicht gerade);
  Umschrift blass darunter; die Skizze 130 × 87 von Papierrand zu Papierrand (Seiten-x 12 bis 142), in
  Handyauflösung gezeichnet, ihr Papierton multipliziert sich in die Seite; darunter bis 3 Zeilen vom Mönch
  (Umbruch bei 122 px); darunter frei für Fundstücke (Schritt 2).
- Bilder: aus `~/akahana-skizzen/seiten/` verkleinert auf etwa 800 px Breite ins Projekt (`assets/erinnerungen/`),
  linear gefiltert gezeichnet. Größe der APK im Blick behalten.

### 5. Hinweis am Buchknopf (abgenommen 2026-11-16, Vorschau „Lesezeichen“)
- Neue Seite → ein goldenes Lesezeichenband kommt aus einem Spalt im hellen Seitenblock des Buchknopfs, liegt
  über der Seitenkante und hängt unten heraus; dunkler Umriss nur, wo es über dem Boden hängt. Dazu leises
  Papierrascheln.
- Das Band bleibt, bis das Buch geöffnet wird.
- (Feder ist für die Fundstücke reserviert, Bleistiftstrich und Blatt waren auf dem Boden schlecht zu sehen.)

### 6. Speichern
- Neuer Abschnitt in `mohnweg.cfg`: gefundene Orte (Liste in Fundreihenfolge), gesehene Gebiete.
- Alte Spielstände ohne den Abschnitt starten mit leerem Buch.

## Namen und Texte (eigene Abnahme vor dem Eintragen)
Vorhanden (`namen.md`, Norden- und Westen-Abnahme): 23 der 31 Seiten. Ich schlage vor:
- Namen für Gräberlichtung, Alte Steinbrücke, Waldteich, Jizō-Weg, Pass und Einsiedelei.
- Höhle innen und Gewächshaus innen tragen den Namen von außen.
- Auflösung der Doppelungen: Ryōshi-goya (Hütte am See und Fischerhütte), Hanamuro/Garasu-muro (Gewächshaus),
  Mizuguruma-mura/Wasure-zato (Dorf).
- 31 Texte zu je 1–2 Zeilen aus Sicht des Mönchs.
Abnahme wie bei den Bildern: eine Seite, Ja/Nein und Notiz.

## Reihenfolge
1. Namen und Texte: abgenommen 2026-11-16, Quelle `~/akahana-skizzen/texte.py` (Abnahmeseite RqZZab9jpMTUxgyuYfWuqE).
2. Vorschau Schriftrolle, Seitenaufbau, Lesezeichen am Knopf: abgenommen 2026-11-16.
3. Plan (writing-plans), dann bauen mit Tests; Version 0.23.0; bauen, installieren, Push.

## Dem Bauenden überlassen
Radien je Ort (Richtwert 60–80 Weltpixel, so dass man den Ort auf dem Bildschirm sieht), genaue Gebietsgrenzen,
Dateinamen, Bildformat und -größe der Seiten, Prüftakt des Wächters.

## Entschieden
- Ein Testsprung („Reisen (Test)“, nur Debug-Builds) zählt Orte als gefunden, damit sich das Buch am Gerät schnell
  prüfen lässt (Philip, 2026-11-16).
- Entwurf abgenommen am 2026-11-16.
