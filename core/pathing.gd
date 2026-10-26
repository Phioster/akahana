## Tap-to-walk route finding on the walkable mask, on a coarse grid (CELL art px per cell).
class_name Pathing
extends RefCounted

const CELL := 2
const OFF_PATH := 3.0                # grass and snow cost this much more than paths, bridges, stones

var grid := AStarGrid2D.new()
var cols := 0
var rows := 0


func build(walk: PackedByteArray, width: int, height: int) -> void:
	cols = width / CELL
	rows = height / CELL
	grid.region = Rect2i(0, 0, cols, rows)
	grid.cell_size = Vector2(CELL, CELL)
	grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.default_compute_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.default_estimate_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.update()
	for cy in rows:
		for cx in cols:
			# a cell is free only if its whole 2x2 patch is walkable: no squeezing through walls
			var free := true
			for dy in CELL:
				for dx in CELL:
					if walk[(cy * CELL + dy) * width + cx * CELL + dx] == 0:
						free = false
			if not free:
				grid.set_point_solid(Vector2i(cx, cy), true)


func cell_of(p: Vector2) -> Vector2i:
	var r := grid.region
	return Vector2i(clampi(floori(p.x / CELL), r.position.x, r.end.x - 1), clampi(floori(p.y / CELL), r.position.y, r.end.y - 1))


func is_free(c: Vector2i) -> bool:
	return grid.is_in_boundsv(c) and not grid.is_point_solid(c)


## The free cell nearest to c, searching outward in rings; c itself if it is free.
func nearest_free(c: Vector2i, max_r: int = 40) -> Vector2i:
	if is_free(c):
		return c
	for r in range(1, max_r + 1):
		var best := Vector2i(-1, -1)
		var best_d := INF
		for dy in range(-r, r + 1):
			for dx in range(-r, r + 1):
				if maxi(absi(dx), absi(dy)) != r:
					continue
				var n := c + Vector2i(dx, dy)
				if is_free(n):
					var d := Vector2(dx, dy).length()
					if d < best_d:
						best_d = d
						best = n
		if best.x >= 0:
			return best
	return Vector2i(-1, -1)


## World-space waypoints from a to b (cell centres), empty if there is no way.
func find_path(a: Vector2, b: Vector2) -> PackedVector2Array:
	var out := PackedVector2Array()
	var ca := nearest_free(cell_of(a))
	var cb := nearest_free(cell_of(b))
	if ca.x < 0 or cb.x < 0:
		return out
	var ids := grid.get_id_path(ca, cb)
	for id in ids:
		out.append(Vector2(id.x * CELL + CELL * 0.5, id.y * CELL + CELL * 0.5))
	return smooth(out)


## Pull the grid staircase straight: from each point jump to the furthest later point that a straight,
## free line reaches without costing more meadow than the steps it replaces. The camera followed every
## little kink of the staircase, which made slanting walks look choppy.
func smooth(way: PackedVector2Array) -> PackedVector2Array:
	if way.size() < 3:
		return way
	var out := PackedVector2Array([way[0]])
	var i := 0
	while i < way.size() - 1:
		var best := i + 1
		var stairs := 0.0
		for j in range(i + 1, way.size()):
			stairs += _seg_cost(way[j - 1], way[j])
			if j > i + 1 and _line_ok(way[i], way[j], stairs * 1.15 + 6.0):   # small detours are not worth a kink
				best = j
		_add_clean(out, way[best])
		i = best
	return out


## A shallow slant scrolls one axis only a pixel every few frames, which reads as stutter. Straight and
## exact 45-degree legs scroll evenly, so a slanting leg becomes a 45-degree part plus a straight part,
## if that is free and not much dearer; the wanderer walks the bend between them round.
func _add_clean(out: PackedVector2Array, b: Vector2) -> void:
	var a := out[out.size() - 1]
	var d := b - a
	var m := minf(absf(d.x), absf(d.y))
	if m < 0.01 or absf(absf(d.x) - absf(d.y)) < 0.01:
		out.append(b)
		return
	var diag := Vector2(signf(d.x) * m, signf(d.y) * m)
	var limit := (_line_cost(a, b) if _line_cost(a, b) >= 0.0 else INF) * 1.25 + 6.0
	for corner in [a + diag, b - diag]:
		var c1 := _line_cost(a, corner)
		var c2 := _line_cost(corner, b)
		if c1 >= 0.0 and c2 >= 0.0 and c1 + c2 <= limit:
			out.append(corner)
			out.append(b)
			return
	out.append(b)


## Cost of walking the straight line a-b, or -1 if it is blocked.
func _line_cost(a: Vector2, b: Vector2) -> float:
	var len := a.distance_to(b)
	if len < 0.01:
		return 0.0
	var n := int(ceil(len / (CELL * 0.5)))
	var cost := 0.0
	for k in range(1, n + 1):
		var c := cell_of(a.lerp(b, float(k) / n))
		if not is_free(c):
			return -1.0
		cost += len / n * grid.get_point_weight_scale(c)
	return cost


func _seg_cost(a: Vector2, b: Vector2) -> float:
	return a.distance_to(b) * grid.get_point_weight_scale(cell_of(b))


## Free all along, and no dearer than limit.
func _line_ok(a: Vector2, b: Vector2, limit: float) -> bool:
	var n := int(ceil(a.distance_to(b) / (CELL * 0.5)))
	var cost := 0.0
	var step := a.distance_to(b) / n
	for k in range(1, n + 1):
		var c := cell_of(a.lerp(b, float(k) / n))
		if not is_free(c):
			return false
		cost += step * grid.get_point_weight_scale(c)
	return cost <= limit


## Faster start-up: the generator already wrote one byte per cell (1 = free).
func build_cells(cells: PackedByteArray, c: int, r: int) -> void:
	cols = c
	rows = r
	grid.region = Rect2i(0, 0, cols, rows)
	grid.cell_size = Vector2(CELL, CELL)
	grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.default_compute_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.default_estimate_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.update()
	for i in cells.size():
		if cells[i] == 0:
			grid.set_point_solid(Vector2i(i % cols, i / cols), true)


## Paths, bridges, stepping stones and the stone court are cheap; open meadow and snow cost OFF_PATH.
## So he keeps to the ways that are there and only cuts across where you really tapped out in the open.
func apply_ground(ground: GroundMat) -> void:
	if ground == null or ground.cells.is_empty():
		return
	for cy in mini(rows, ground.h):
		for cx in mini(cols, ground.w):
			var m := ground.cells[cy * ground.w + cx]
			if m == GroundMat.GRASS or m == GroundMat.SNOW:
				grid.set_point_weight_scale(Vector2i(cx, cy), OFF_PATH)


## Tap-to-walk on the streamed world: the grid covers only the box round start and goal (taps are
## always on screen), built from the loaded chunks; unloaded ground counts as wall. If the way needs a
## detour outside the box, it looks once more in a box twice as wide.
func find_path_in(store: ChunkStore, a: Vector2, b: Vector2, margin: float = 60.0) -> PackedVector2Array:
	for m in [margin, margin * 2.0]:
		var lo := (a.min(b) - Vector2(m, m)) / CELL
		var hi := (a.max(b) + Vector2(m, m)) / CELL
		var r := Rect2i(Vector2i(floori(lo.x), floori(lo.y)), Vector2i.ZERO)
		r.end = Vector2i(ceili(hi.x), ceili(hi.y))
		_build_from(store, r)
		var way := find_path(a, b)
		if way.size() > 0 and way[way.size() - 1].distance_to(b) < CELL * 2.0:
			return way
		if m == margin * 2.0:
			return way
	return PackedVector2Array()


func _build_from(store: ChunkStore, r: Rect2i) -> void:
	grid = AStarGrid2D.new()
	grid.region = r
	grid.cell_size = Vector2(CELL, CELL)
	grid.diagonal_mode = AStarGrid2D.DIAGONAL_MODE_ONLY_IF_NO_OBSTACLES
	grid.default_compute_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.default_estimate_heuristic = AStarGrid2D.HEURISTIC_OCTILE
	grid.update()
	cols = r.end.x
	rows = r.end.y
	for y in range(r.position.y, r.end.y):
		for x in range(r.position.x, r.end.x):
			var c := Vector2i(x, y)
			if not store.cell_free(c):
				grid.set_point_solid(c, true)
			else:
				var wgt := store.cell_weight(c)
				if wgt != 1.0:
					grid.set_point_weight_scale(c, wgt)
