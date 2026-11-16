## Notices first visits: a region once you have stood in it for DWELL seconds (no scroll flickering at a
## border), a place as soon as you are in its circle or its room. Writes them into the save and
## hands them back as events, region before place.
class_name MemoryKeeper
extends RefCounted

const DWELL := 1.5

var save: SaveData
var _cand := ""
var _dwell := 0.0


func step(p: Vector2, room: String, dt: float) -> Array[Dictionary]:
	var events: Array[Dictionary] = []
	if room == "":
		var r := Memories.region_at(p)
		if r != _cand:
			_cand = r
			_dwell = 0.0
		_dwell += dt
		if _dwell >= DWELL and not save.regions_seen.has(r):
			save.regions_seen.append(r)
			events.append({"kind": "region", "key": r})
	var key := Memories.place_in_room(room) if room != "" else Memories.place_at(p)
	if key != "" and not save.found.has(key):
		save.found.append(key)
		save.bookmark = true
		events.append({"kind": "place", "key": key})
	return events
