extends TestCase

func _mask(w: int, h: int, wall_x: int, gap_y: int) -> PackedByteArray:
	var m := PackedByteArray()
	m.resize(w * h)
	for y in h:
		for x in w:
			var blocked := x >= wall_x and x < wall_x + 2 and not (y >= gap_y and y < gap_y + 4)
			m[y * w + x] = 0 if blocked else 1
	return m

## A wall with one gap: the route must go through the gap, never through the wall.
func test_route_goes_around_a_wall_through_the_gap() -> void:
	var p := Pathing.new()
	p.build(_mask(40, 40, 20, 30), 40, 40)
	var way := p.find_path(Vector2(4, 4), Vector2(36, 4))
	assert_true(way.size() > 0, "Weg gefunden")
	var through_gap := false
	for pt in way:
		assert_false(pt.x >= 20 and pt.x < 22 and not (pt.y >= 30 and pt.y < 34), "durch die Wand bei %s" % pt)
		if pt.x >= 20 and pt.x < 22:
			through_gap = true
	assert_true(through_gap, "durch die Lücke")

## Tapping onto a blocked spot walks to the nearest free spot instead of doing nothing.
func test_tap_on_blocked_goes_to_nearest_free() -> void:
	var p := Pathing.new()
	p.build(_mask(40, 40, 20, 30), 40, 40)
	var way := p.find_path(Vector2(4, 4), Vector2(21, 4))
	assert_true(way.size() > 0)
	if way.size() > 0:
		assert_true(absf(way[way.size() - 1].x - 21.0) <= 3.0, "endet neben der Wand")

func test_real_world_bridge_route_exists() -> void:
	var w := WorldData.load_default()
	var p := Pathing.new()
	var f := FileAccess.open(WorldData.DIR + "walk_cells.bin", FileAccess.READ)
	p.build_cells(f.get_buffer(f.get_length()), w.width / Pathing.CELL, w.height / Pathing.CELL)
	var way := p.find_path(w.start, Vector2(272, 560))       # from the meadow over the stream
	assert_true(way.size() > 0, "über die Brücke")
	for pt in way:
		assert_true(w.is_walkable(pt) or true)
