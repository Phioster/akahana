extends TestCase

func test_chunk_of_maps_points_to_their_chunk() -> void:
	var g := ChunkGrid.new(3, 6)
	assert_eq(g.chunk_of(Vector2(179.9, 0)), Vector2i(0, 0))
	assert_eq(g.chunk_of(Vector2(180, 0)), Vector2i(1, 0))
	assert_eq(g.chunk_of(Vector2(0, 399.9)), Vector2i(0, 1))

func test_chunks_in_covers_a_view_and_clips_to_the_world() -> void:
	var g := ChunkGrid.new(3, 6)
	var cs := g.chunks_in(Rect2(170, 190, 180, 400))
	assert_eq(cs.size(), 2 * 3, "2×3 Kacheln")
	assert_eq(cs[0], Vector2i(0, 0))
	for c in g.chunks_in(Rect2(-500, -500, 2000, 3000)):
		assert_true(g.contains(c), "außerhalb: %s" % c)
	assert_eq(g.chunks_in(Rect2(-500, -500, 2000, 3000)).size(), 18)

func test_rect_of_round_trips() -> void:
	var g := ChunkGrid.new(3, 6)
	assert_eq(g.rect_of(Vector2i(2, 4)), Rect2(360, 800, 180, 200))
	assert_eq(g.chunk_of(g.rect_of(Vector2i(2, 4)).position), Vector2i(2, 4))

func _store() -> ChunkStore:
	var w := WorldData.load_default()
	return ChunkStore.new(ChunkGrid.new(w.chunks.x, w.chunks.y))

func test_store_answers_walkable_like_the_old_mask() -> void:
	var w := WorldData.load_default()
	var s := ChunkStore.new(w.grid)
	s.load_now(w.grid.chunk_of(w.start))
	assert_true(s.walkable(w.start), "Start begehbar")
	assert_eq(s.walkable(w.start), w.is_walkable(w.start))
	s.load_now(Vector2i(0, 0))
	assert_false(s.walkable(Vector2(3, 3)), "Weltrand zu")
	var same := 0
	for i in 400:
		var p := Vector2(randf_range(0, 180), randf_range(0, 200))
		var cell := Vector2i(p / 2.0)
		var full := true                                   # the old 1-px mask, read as 2x2 cells
		for dy in 2:
			for dx in 2:
				full = full and w.walk[(cell.y * 2 + dy) * w.width + cell.x * 2 + dx] != 0
		if s.walkable(p) == full:
			same += 1
	assert_eq(same, 400, "gleich wie die alte Maske")

func test_unloaded_ground_is_not_walkable() -> void:
	var s := _store()
	assert_false(s.walkable(Vector2(250, 1070)))
	assert_eq(s.material_at(Vector2(250, 1070)), GroundMat.GRASS)

func test_want_forgets_what_is_not_kept() -> void:
	var s := _store()
	s.want([Vector2i(0, 0), Vector2i(1, 0)])
	assert_eq(s.loaded_count(), 2)
	s.want([])
	assert_eq(s.loaded_count(), 0)

func test_textures_arrive_through_poll() -> void:
	var s := _store()
	var c := Vector2i(1, 5)
	s.want([c])
	var t := Time.get_ticks_msec()
	while not s.is_ready(c) and Time.get_ticks_msec() - t < 4000:
		s.poll()
		OS.delay_msec(10)
	assert_true(s.is_ready(c), "Bilder geladen")
	assert_true(s.ground_tex(c) != null and s.flowers_tex(c) != null)
	assert_eq(s.flowers_tex(c).get_size(), Vector2(196, 216))

func _counter() -> Dictionary:
	return {"made": 0, "dropped": 0}

func test_activates_inside_near_and_drops_beyond_far() -> void:
	var a := Activator.new()
	var n := _counter()
	var id := a.add(Rect2(500, 500, 10, 10), 40.0, 120.0, func(): n["made"] += 1; return Node.new(),
			func(x): n["dropped"] += 1; x.free())
	a.update(Rect2(0, 0, 100, 100))
	assert_eq(a.active_count(), 0, "weit weg")
	a.update(Rect2(400, 400, 80, 80))              # 20 px away
	assert_eq(a.active_count(), 1)
	assert_true(a.node(id) != null)
	a.update(Rect2(0, 0, 100, 100))
	assert_eq(a.active_count(), 0)
	assert_eq(n["dropped"], 1)

func test_no_flapping_between_near_and_far() -> void:
	var a := Activator.new()
	var n := _counter()
	a.add(Rect2(500, 500, 10, 10), 40.0, 120.0, func(): n["made"] += 1; return Node.new(), func(x): x.free())
	for i in 100:
		var gap := 30.0 if i % 2 == 0 else 100.0       # inside near, then between near and far
		a.update(Rect2(500 - gap - 50, 500, 50, 10))
	assert_eq(n["made"], 1, "nur einmal erzeugt")
	a.clear()

func test_clear_drops_everything() -> void:
	var a := Activator.new()
	for i in 5:
		a.add(Rect2(i * 10, 0, 1, 1), 40.0, 120.0, func(): return Node.new(), func(x): x.free())
	a.update(Rect2(0, 0, 50, 10))
	assert_eq(a.active_count(), 5)
	a.clear()
	assert_eq(a.active_count(), 0)
