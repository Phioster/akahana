## A testing aid only (Philip, 2026-10-28): places to jump to from the book, so testing does not mean
## walking the whole map each time. The game itself has no fast travel; the book shows this only in debug
## builds (BookUI.travel_offered).
class_name TestTravel
extends RefCounted

## World coordinates since the north grew on top (0.11: +1200 rows).
const PLACES := [
	["Lager", Vector2(243, 2270)],
	["Bachbrücke", Vector2(270, 1855)],
	["Kogarashi", Vector2(250, 1370)],
	["Grasland", Vector2(300, 2600)],
	["Glühwürmchen", Vector2(362, 3150)],
	["Bäche", Vector2(594, 3500)],
	["Steg", Vector2(574, 4145)],
	["Hütte am See", Vector2(770, 4520)],
	["Waldteich", Vector2(1000, 2580)],
	["Ostwald", Vector2(1250, 2900)],
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
