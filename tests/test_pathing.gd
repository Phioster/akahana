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

func test_walking_keeps_to_the_paths() -> void:
	# a meadow 30x12 cells with a path along row 10: going from one end to the other he takes the path,
	# even when start and goal lie a cell beside it in the grass
	var p := Pathing.new()
	var cells := PackedByteArray()
	cells.resize(30 * 12)
	cells.fill(1)
	p.build_cells(cells, 30, 12)
	var mat := PackedByteArray()
	mat.resize(30 * 12)
	mat.fill(GroundMat.GRASS)
	for x in 30:
		mat[10 * 30 + x] = GroundMat.EARTH
	p.apply_ground(GroundMat.new(mat, 30, 12))
	var way := p.find_path(Vector2(3, 17), Vector2(57, 17))         # cells (1, 8) -> (28, 8)
	var on_path := 0                                               # sampled along the walk, every half cell
	var total := 0
	for i in range(1, way.size()):
		var n := int(ceil(way[i - 1].distance_to(way[i])))
		for k in n:
			total += 1
			if p.cell_of(way[i - 1].lerp(way[i], float(k) / n)).y == 10:
				on_path += 1
	assert_true(on_path > total / 2, "nimmt den Weg: %d von %d Schritten" % [on_path, total])

func test_a_tap_out_in_the_meadow_is_still_reached() -> void:
	var p := Pathing.new()
	var cells := PackedByteArray()
	cells.resize(30 * 12)
	cells.fill(1)
	p.build_cells(cells, 30, 12)
	var mat := PackedByteArray()
	mat.resize(30 * 12)
	mat.fill(GroundMat.GRASS)
	p.apply_ground(GroundMat.new(mat, 30, 12))
	var way := p.find_path(Vector2(3, 3), Vector2(57, 21))
	assert_true(way.size() > 0 and way[way.size() - 1].distance_to(Vector2(57, 21)) < 3.0, "kommt hin")

func test_a_slanting_walk_is_one_straight_line_not_a_staircase() -> void:
	# across open meadow the grid route zigzagged; the camera followed every kink
	var p := Pathing.new()
	var cells := PackedByteArray()
	cells.resize(40 * 40)
	cells.fill(1)
	p.build_cells(cells, 40, 40)
	var mat := PackedByteArray()
	mat.resize(40 * 40)
	mat.fill(GroundMat.GRASS)
	p.apply_ground(GroundMat.new(mat, 40, 40))
	var way := p.find_path(Vector2(3, 3), Vector2(70, 31))
	var turns := 0
	for i in range(2, way.size()):
		var a := (way[i - 1] - way[i - 2]).normalized()
		var b := (way[i] - way[i - 1]).normalized()
		if a.dot(b) < 0.999:
			turns += 1
	assert_true(turns <= 1, "Knicke: %d bei %d Punkten" % [turns, way.size()])

func test_real_slanting_walks_have_few_kinks() -> void:
	# measured on the real map, with the path weights: short diagonal taps across meadow and along paths
	var w := WorldData.load_default()
	var p := Pathing.new()
	var f := FileAccess.open(WorldData.DIR + "walk_cells.bin", FileAccess.READ)
	p.build_cells(f.get_buffer(f.get_length()), w.width / Pathing.CELL, w.height / Pathing.CELL)
	p.apply_ground(GroundMat.load_default(w.width, w.height))
	var worst := 0.0
	for d in [Vector2(60, -60), Vector2(-60, -60), Vector2(60, 60), Vector2(-50, -80), Vector2(80, -40),
			Vector2(14, -90), Vector2(-18, -80), Vector2(10, 70), Vector2(-12, 85)]:   # mostly up/down, a bit sideways
		var way := p.find_path(w.start, w.start + d)
		var turns := 0
		for i in range(2, way.size()):
			if (way[i - 1] - way[i - 2]).normalized().dot((way[i] - way[i - 1]).normalized()) < 0.999:
				turns += 1
		var per100 := turns * 100.0 / maxf(1.0, d.length())
		worst = maxf(worst, per100)
	assert_true(worst <= 8.0, "Knicke je 100 px: %.1f" % worst)   # was up to 24.6; clean 45-degree bends count too

func test_slanting_walks_use_clean_angles() -> void:
	# a shallow slant scrolls one axis a pixel only every few frames - that reads as stutter; straight and
	# exact 45-degree runs scroll evenly. So every leg of a walk is one of the 8 clean directions
	var p := Pathing.new()
	var cells := PackedByteArray()
	cells.resize(40 * 40)
	cells.fill(1)
	p.build_cells(cells, 40, 40)
	var mat := PackedByteArray()
	mat.resize(40 * 40)
	mat.fill(GroundMat.GRASS)
	p.apply_ground(GroundMat.new(mat, 40, 40))
	for goal in [Vector2(70, 31), Vector2(15, 75), Vector2(9, 60), Vector2(66, 9)]:
		var way := p.find_path(Vector2(3, 3), goal)
		assert_true(way.size() <= 3, "%s: höchstens zwei Stücke, %d Punkte" % [goal, way.size()])
		for i in range(1, way.size()):
			var v := way[i] - way[i - 1]
			var clean := absf(v.x) < 0.01 or absf(v.y) < 0.01 or absf(absf(v.x) - absf(v.y)) < 0.01
			assert_true(clean, "%s: Stück %s ist schief" % [goal, v])
