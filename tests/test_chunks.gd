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
