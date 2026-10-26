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

func test_corners_are_walked_round_not_snapped() -> void:
	# at a waypoint he turned in one frame; the camera follows him, so every kink jolted the view
	var pl := Player.new()
	pl.position = Vector2(0, 0)
	pl.walk_to(PackedVector2Array([Vector2(0, 30), Vector2(30, 30)]))
	var last_dir := Vector2.ZERO
	var worst := 0.0
	var prev := pl.position
	for i in 400:
		pl._process(1.0 / 60.0)
		var v := pl.position - prev
		prev = pl.position
		if v.length() > 0.0001:
			var d := v.normalized()
			if last_dir != Vector2.ZERO:
				worst = maxf(worst, absf(rad_to_deg(last_dir.angle_to(d))))
			last_dir = d
	assert_true(absf(worst) < 20.0, "größter Richtungswechsel je Bild: %.0f°" % worst)
	assert_true(pl.position.distance_to(Vector2(30, 30)) < 0.5, "kommt trotzdem an")
	pl.free()
