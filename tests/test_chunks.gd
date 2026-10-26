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
