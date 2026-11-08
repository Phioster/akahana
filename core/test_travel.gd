## A testing aid only (Philip, 2026-10-28): places to jump to from the book, so testing does not mean
## walking the whole map each time. The game itself has no fast travel; the book shows this only in debug
## builds (BookUI.travel_offered).
class_name TestTravel
extends RefCounted

## World coordinates since the north grew on top (0.11: +1200 rows) and the west on the left (0.18: +900 columns).
const PLACES := [
	["Lager", Vector2(1143, 2270)],
	["Bachbrücke", Vector2(1170, 1855)],
	["Kogarashi", Vector2(1150, 1370)],
	["Grasland", Vector2(1200, 2600)],
	["Glühwürmchen", Vector2(1262, 3150)],
	["Bäche", Vector2(1494, 3500)],
	["Seesteg", Vector2(1474, 4145)],
	["Hütte am See", Vector2(1670, 4520)],
	["Waldteich", Vector2(1900, 2580)],
	["Ostwald", Vector2(2150, 2900)],
	["Felstor", Vector2(1174, 1190)],
	["Holzfällerhütte", Vector2(1218, 885)],
	["Höhle", Vector2(1050, 722)],
	["Steg", Vector2(1460, 545)],
	["Aussicht", Vector2(1686, 412)],
	["Pass", Vector2(1380, 135)],
	["Bergsee", Vector2(1990, 680)],
	["Dorfplatz", Vector2(536, 2344)],
	["Gewächshaus", Vector2(680, 2630)],
	["Mühle", Vector2(560, 3340)],
	["Westsee", Vector2(596, 4050)],
	["Teehaus", Vector2(850, 4030)],
	["Einsiedelei", Vector2(362, 400)],
]


## The nearest open ground to p (the places are rough spots), searched in rings; p itself if none.
static func nearest_open(store: ChunkStore, p: Vector2) -> Vector2:
	for r in range(0, 40, 2):
		for k in 16:
			var q := (p + Vector2.from_angle(k * TAU / 16.0) * float(r)).round()
			if store.walkable(q):
				return q
			if r == 0:
				break
	return p
