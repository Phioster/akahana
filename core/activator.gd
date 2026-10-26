## Brings things into being only when they are needed: an entry's node is made once the area comes
## within `near` of it and dropped only beyond `far`, so nothing flickers in and out at a border.
class_name Activator
extends RefCounted

var _entries: Array = []             # {where: Rect2, near, far, make: Callable, drop: Callable, node}


func add(where: Rect2, near: float, far: float, make: Callable, drop: Callable) -> int:
	_entries.append({"where": where, "near": near, "far": far, "make": make, "drop": drop, "node": null})
	return _entries.size() - 1


func update(area: Rect2) -> void:
	for e in _entries:
		var d := _gap(e["where"], area)
		if e["node"] == null and d < e["near"]:
			e["node"] = e["make"].call()
		elif e["node"] != null and d > e["far"]:
			e["drop"].call(e["node"])
			e["node"] = null


func node(id: int) -> Node:
	return _entries[id]["node"]


func active_count() -> int:
	var n := 0
	for e in _entries:
		if e["node"] != null:
			n += 1
	return n


func clear() -> void:
	for e in _entries:
		if e["node"] != null:
			e["drop"].call(e["node"])
			e["node"] = null


## Shortest distance between two rectangles, 0 when they touch or overlap.
static func _gap(a: Rect2, b: Rect2) -> float:
	var dx := maxf(0.0, maxf(a.position.x - b.end.x, b.position.x - a.end.x))
	var dy := maxf(0.0, maxf(a.position.y - b.end.y, b.position.y - a.end.y))
	return sqrt(dx * dx + dy * dy)
