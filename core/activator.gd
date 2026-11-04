## Brings things into being only when they are needed: an entry's node is made once the area comes
## within `near` of it and dropped only beyond `far`, so nothing flickers in and out at a border.
## Entries are kept in buckets of the ground they could wake on, so a frame only looks at the
## neighbourhood of the view (the grown world has well over a thousand) and at what is awake.
class_name Activator
extends RefCounted

const BUCKET := 200.0

var visited := 0                     # entries looked at, for the test
var step := 0.0                      # look again only once the area moved this far (0.10.3: 7-8 ms a frame,
                                     # standing still, measured with ~1700 entries awake)
var _last := Rect2()
var _looked := false
var _entries: Array = []             # {where: Rect2, near, far, make: Callable, drop: Callable, node}
var _buckets := {}                   # Vector2i -> Array[int]
var _awake := {}                     # id -> true


func add(where: Rect2, near: float, far: float, make: Callable, drop: Callable) -> int:
	_entries.append({"where": where, "near": near, "far": far, "make": make, "drop": drop, "node": null})
	var id := _entries.size() - 1
	var r := where.grow(near)                          # it can only wake while the view touches this
	for by in range(floori(r.position.y / BUCKET), floori(r.end.y / BUCKET) + 1):
		for bx in range(floori(r.position.x / BUCKET), floori(r.end.x / BUCKET) + 1):
			var k := Vector2i(bx, by)
			if not _buckets.has(k):
				_buckets[k] = []
			_buckets[k].append(id)
	return id


func update(area: Rect2) -> void:
	if _looked and area.size == _last.size and area.position.distance_to(_last.position) < step:
		return
	_looked = true
	_last = area
	for by in range(floori(area.position.y / BUCKET), floori(area.end.y / BUCKET) + 1):
		for bx in range(floori(area.position.x / BUCKET), floori(area.end.x / BUCKET) + 1):
			for id in _buckets.get(Vector2i(bx, by), []):
				visited += 1
				var e: Dictionary = _entries[id]
				if not _awake.has(id) and _gap(e["where"], area) < e["near"]:  # by id: a make may give no node
					e["node"] = e["make"].call()
					_awake[id] = true
	for id in _awake.keys():
		var e: Dictionary = _entries[id]
		if _gap(e["where"], area) > e["far"]:
			e["drop"].call(e["node"])
			e["node"] = null
			_awake.erase(id)


func node(id: int) -> Node:
	return _entries[id]["node"]


func active_count() -> int:
	return _awake.size()


func clear() -> void:
	_looked = false
	for id in _awake.keys():
		_entries[id]["drop"].call(_entries[id]["node"])
		_entries[id]["node"] = null
	_awake.clear()


## Shortest distance between two rectangles, 0 when they touch or overlap.
static func _gap(a: Rect2, b: Rect2) -> float:
	var dx := maxf(0.0, maxf(a.position.x - b.end.x, b.position.x - a.end.x))
	var dy := maxf(0.0, maxf(a.position.y - b.end.y, b.position.y - a.end.y))
	return sqrt(dx * dx + dy * dy)
