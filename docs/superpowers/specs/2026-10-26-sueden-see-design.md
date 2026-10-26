# Der Süden: Mohn, Übergang, Wasserläufe, See – Design

Stand 2026-10-26. Ausbaustufe 3 aus `docs/ideenblatt.md` („Süden: Wiesen, Wasser und lebendige Natur“).
Referenzbild (Idee, keine Vorlage): `docs/referenz/sueden-idee.png`.

## Warum

Die Welt soll für 1,5–2 Stunden Entdecken reichen. Seit 0.4.0 lädt sie in Kacheln, also kann sie wachsen.
Der Süden ist der ruhige, lebendige Gegenpol zum Gebirge: Man soll dort einfach stehen, schauen, waten.

## Was Philip will (seine Worte, zusammengefasst)

- Vom Lagerfeuer nach Süden geht das **Mohnfeld noch ein gutes Stück weiter**, mit ein paar eigenen Stellen.
- Dann ein **subtiler, leichter Übergang**: der Mohn wird lichter, andere Wildblumen und Gras kommen dazu,
  **2–3 kleinere Kirschbäume** stehen dort.
- Danach **viele kleine Wasserläufe**, überquert über **kleine Holzbrücken**, **ein einzelnes Brett** oder
  **Trittsteine**.
- Ganz unten der **See, in Schilf gehüllt**, mit ein paar **etwas grüneren Bäumen**.
- Farben **auf unsere Weltatmosphäre angepasst**: abends, Nebel – nicht die Sommerfarben des Referenzbilds.
- Die Karte soll **gut groß** sein und **breiter** werden; größer geht später immer noch.

Von Philip bestätigt: die vier Stellen im Mohnfeld – ein alter bemooster **Wegstein** mit eingeritztem
Zeichen, **Reste einer niedrigen Steinmauer** halb im Mohn, eine einzelne **Vogelscheuche**, eine kleine
**Bank** unter einem der jungen Kirschbäume.

Aus dem Ideenblatt: flacher See, am Rand **watbar**, tiefe Stellen begrenzen den Weg; Seerosen, Schilf,
moosige Felsen; Spritzer beim Waten; Wasser lebendig, aber ruhig.

## Ziele

- Die Welt wächst von 3 × 6 auf **5 × 18 Kacheln** (900 × 3600 Kunstpixel).
  - Süden, Reihen 6–17: Mohn-Verlängerung (+3), Übergang (+2), Wasserläufe (+3), See (+4).
  - Osten, Spalten 3–4: neben der alten Karte vorerst ein **geschlossener Waldsaum** (nicht begehbar,
    dort kommt später der Ostwald mit dem Ritualort hin); im Süden nutzen See und Wasserläufe die volle Breite.
- Die **heutige Welt bleibt pixelgleich** (Spalten 0–2, Reihen 0–5): kein Neuwürfeln, keine Verschiebung,
  gespeicherte Positionen bleiben gültig.
- Der heutige untere Rand unter dem Lager öffnet sich nahtlos in den neuen Süden.
- Neue Klänge: Waten (Freesound 861369 / 612964, schon ausgesucht), Schilf im Wind, Wasser an Brücken;
  vorhandene Frösche und Bäche werden an die neuen Wasserläufe gehängt.

## Nicht-Ziele

- Kein Ostwald, kein Ritualort, kein Westen in dieser Stufe.
- Keine neuen Spielmechaniken außer Waten (langsamer im flachen Wasser, eigener Schrittklang).
- Keine Änderung an Gebirge, Kapelle, Hütte, Lager oder Kirschbaum.

## Anti-Ziele

- Ein harter Schnitt zwischen alter und neuer Welt (Farbe, Mohndichte, Bodenstruktur).
- Ein Labyrinth: Wasserläufe dürfen den Weg lenken, aber keine Sackgassen, die frustrieren.
- Sommerfarben, Sättigung wie im Referenzbild, „Tropen“.
- Eine Gegend, die leer wirkt, weil sie nur größer ist.
- Konturen, Schachbrettraster, Halbtransparenz (stehende Gestaltungsregeln).

## Wie es gebaut wird (Entscheidungen)

- **Eigener Generator für den Süden** (`tools/world/gen_south.py`), der an die Vollbilder der alten Welt
  anschließt: Er liest die untersten Reihen von `build/world_full/*`, um Boden, Mohn und Begehbarkeit an der
  Naht fortzusetzen, und schreibt die vergrößerten Vollbilder. `gen_world.py` bleibt unangetastet, weil schon
  eine andere Größe oder eine andere Zufallsreihenfolge die ganze alte Welt verändern würde.
- Alle neuen Dinge entstehen **aus den vorhandenen Bausteinen** (`tools/world/lib`: field6, extras, objects2,
  tree, atmo) – die Lehre aus den Welt-Bildern: neue Szenen aus diesen Bausteinen bauen, nicht neu erfinden.
- Kirschbäume klein: der große Baum aus `tree.py`, verkleinert gezeichnet (nicht skaliert – Pixelregel).
- **Abnahme zuerst:** Jede neue Optik und jeder neue Klang kommt erst auf die Abnahme-Seite, Zone für Zone,
  mit zwei Varianten nebeneinander, wo es eine echte Wahl gibt. Erst nach Philips Okay wird gebaut.
  Reihenfolge der Zonen: 1 Mohn-Verlängerung mit den vier Stellen, 2 Übergang mit den kleinen Kirschbäumen,
  3 Wasserläufe mit den drei Arten zu queren, 4 See mit Schilf, Seerosen, grüneren Bäumen, Watzone.
- Die Kachel-Technik aus 0.4.0 trägt das; der Aktivierer prüft heute alle Einträge pro Bild – bei der
  größeren Welt nach Kacheln bündeln (aufgeschobener Punkt aus dem Kachel-Review).

## Nach dem Builder-Check entschieden

Von Philip (2026-10-26):
- **Das Wasser bewegt sich und fließt.** Bäche und Wasserläufe fließen sichtbar in ihre Richtung, der See
  kräuselt sich ruhig. Dafür bekommt jede Kachel eine Wasserkarte (wo Wasser ist, wohin es fließt) und das
  Wasser einen eigenen Shader. Der alte Bach fließt dann ebenfalls. Gilt auch für `mood_map.py` (Standbild).
- **Waten nur am flachen Seerand.** Die kleinen Wasserläufe quert man nur über Brücken, Bretter und
  Trittsteine; die Wege dazwischen werden so gelegt, dass es keine Sackgassen gibt.

Meine Festlegungen (von Philip bestätigt):
- Ab Reihe 6 ist **alles 5 Kacheln breit**, auch Mohn-Verlängerung und Übergang. Der Waldsaum steht nur
  neben der alten Karte (Spalten 3–4, Reihen 0–5).
- Der Waldsaum ist ein **Platzhalter**: dichter, geschlossener Baumrand; der große Bach verschwindet darin
  wie heute am Rand, Fels und Schnee laufen oben in die Bäume aus. Endgültig wird es mit dem Ostwald.
- **Abnahme Zone für Zone, Auslieferung auf einmal**, wenn alle vier Zonen abgenommen sind.
- **Pixelgleich gilt für das Bild** der alten Welt. Daten an der Naht dürfen angepasst werden (unteren Rand
  öffnen, Rand-Tannen und Einträge in world.json zusammenführen).

## Dem Bauenden überlassen

- Genaue Lage der Wasserläufe, Brücken, Stellen; Form des Sees – solange es kein Labyrinth wird und die
  Abnahme sie zeigt.
- Wie dicht der Nebel über dem Wasser liegt (Vorschlag in der Abnahme).
