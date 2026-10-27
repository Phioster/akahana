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

func test_a_tiny_diagonal_piece_does_not_jolt_him() -> void:
	# clean 45-degree pieces of only 2 px between long runs: he swings through, no sudden turn
	var pl := Player.new()
	pl.walk_to(PackedVector2Array([Vector2(0, 30), Vector2(2, 32), Vector2(2, 70)]))
	var last_dir := Vector2.ZERO
	var worst := 0.0
	var prev := pl.position
	for i in 500:
		pl._process(1.0 / 60.0)
		var v := pl.position - prev
		prev = pl.position
		if v.length() > 0.0001:
			if last_dir != Vector2.ZERO:
				worst = maxf(worst, absf(rad_to_deg(last_dir.angle_to(v.normalized()))))
			last_dir = v.normalized()
	assert_true(worst < 20.0, "Ruck: %.0f°" % worst)
	assert_true(pl.position.distance_to(Vector2(2, 70)) < 0.5, "kommt an")
	pl.free()

func test_stopping_has_no_last_jump() -> void:
	# coming in on a curve he ended a pixel or two beside the goal and was set onto it in one frame
	var pl := Player.new()
	pl.walk_to(PackedVector2Array([Vector2(0, 30), Vector2(30, 30)]))
	var prev := pl.position
	var worst := 0.0
	for i in 400:
		pl._process(1.0 / 60.0)
		worst = maxf(worst, pl.position.distance_to(prev))
		prev = pl.position
	assert_true(worst <= Player.SPEED / 60.0 + 0.01, "größter Satz in einem Bild: %.2f px" % worst)
	pl.free()

func test_the_wanderer_shows_mirrored_below_his_feet_on_water() -> void:
	var pl := Player.new()
	pl._ready()
	var r: Sprite2D = pl.get_node("Spiegelbild")
	assert_true(r.flip_v, "auf dem Kopf")
	assert_true(r.offset.y >= 0.0, "unter den Füßen")
	assert_true((r.material as ShaderMaterial).shader.resource_path.ends_with("reflection.gdshader"))
	pl.walk_to(PackedVector2Array([Vector2(30, 0)]))
	for i in 7:
		pl._process(0.05)
	assert_eq(r.frame, pl.sprite.frame, "er geht im Spiegel mit")
	pl.free()
