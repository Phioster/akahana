extends TestCase

func test_player_reaches_the_end_of_its_path() -> void:
	var pl := Player.new()
	pl.position = Vector2.ZERO
	pl.walk_to(PackedVector2Array([Vector2(10, 0), Vector2(10, 10)]))
	for i in 100:
		pl._process(0.05)
	assert_eq(pl.position, Vector2(10, 10))
	assert_false(pl.is_walking())
	pl.free()

func test_player_faces_its_walking_direction() -> void:
	var pl := Player.new()
	pl._face(Vector2(-5, 0))
	assert_eq(pl.dir, Player.Dir.LEFT)
	pl._face(Vector2(0, -5))
	assert_eq(pl.dir, Player.Dir.UP)
	pl.free()
