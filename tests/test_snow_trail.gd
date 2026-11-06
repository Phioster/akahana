extends TestCase

## Snow left of x 100, a trodden path right of it.
func _trail() -> SnowTrail:
	var s := SnowTrail.new()
	s.mat_at = func(p: Vector2) -> int: return GroundMat.SNOW if p.x < 100.0 else GroundMat.EARTH
	return s

func _walk(s: SnowTrail, from: Vector2, to: Vector2) -> void:
	var d := (to - from).normalized()
	var p := from
	while p.distance_to(to) > 0.5:
		s.tread(p, d)
		p += d * 0.6
	s.flush()

func test_he_leaves_a_furrow_in_snow_but_not_on_the_path() -> void:
	var s := _trail()
	_walk(s, Vector2(50, 40), Vector2(50, 80))
	assert_eq(s.raw(Vector2i(50, 60)), 255, "Furche im Schnee")
	_walk(s, Vector2(140, 40), Vector2(140, 80))
	assert_true(s.raw(Vector2i(140, 60)) < 255, "keine Furche auf dem getretenen Weg")
	s.free()

func test_the_furrow_is_about_as_wide_as_he_is() -> void:
	var s := _trail()
	_walk(s, Vector2(50, 40), Vector2(50, 80))
	var w := 0
	for x in range(40, 61):
		if s.raw(Vector2i(x, 60)) == 255:
			w += 1
	assert_true(w >= 5 and w <= 11, "Breite %d px, der Mönch ist 7" % w)
	assert_eq(s.raw(Vector2i(50 + SnowTrail.RING, 60)), 128, "daneben darf Schnee aufgehäuft liegen")
	s.free()

func test_the_middle_lies_deeper_than_the_walls() -> void:
	var s := _trail()
	_walk(s, Vector2(50, 40), Vector2(50, 80))
	assert_true(s.depth_at(Vector2i(50, 60)) >= 2, "Mitte tief")
	var edge := 50
	while s.raw(Vector2i(edge + 1, 60)) == 255:
		edge += 1
	assert_eq(s.depth_at(Vector2i(edge, 60)), 0, "an der Wand weht es zuerst zu")
	s.free()

func test_a_footfall_leaves_a_dent() -> void:
	var s := _trail()
	_walk(s, Vector2(50, 40), Vector2(50, 80))
	s.footfall(Vector2(50, 70), Vector2.DOWN)
	var dents := 0
	for y in range(66, 74):
		for x in range(46, 55):
			if s._pixel(Vector2i(x, y)).b8 & 1 == 1:
				dents += 1
	assert_eq(dents, 2, "ein Fuß, zwei Pixel")
	s.free()

func test_the_wind_fills_it_slowly_and_then_it_is_let_go() -> void:
	assert_true(SnowTrail.FILL >= 200.0, "langsam: Minuten, nicht Sekunden (Philip)")
	var s := _trail()
	_walk(s, Vector2(50, 40), Vector2(50, 80))
	assert_true(s.tile_count() > 0)
	s.advance(SnowTrail.FILL * 0.5)
	s.forget_old()
	assert_true(s.tile_count() > 0, "halb zugeweht ist noch da")
	s.advance(SnowTrail.FILL)
	s.forget_old()
	assert_eq(s.tile_count(), 0, "zugeweht und vergessen")
	s.free()

func test_a_furrow_on_a_tile_edge_shows_in_both_pictures() -> void:
	var s := _trail()
	_walk(s, Vector2(50, SnowTrail.TILE - 1), Vector2(50, SnowTrail.TILE + 12))
	assert_eq(s.tile_count(), 2)
	var upper: Image = s._tiles[Vector2i(0, 0)]["pic"]
	var p := SnowTrail.PAD
	assert_eq(upper.get_pixel(50 + p, SnowTrail.TILE + p + 2).a8, 255, "der obere sieht den Rand des unteren")
	s.free()

func test_it_lies_on_the_ground_under_what_stands() -> void:
	var s := _trail()
	(Engine.get_main_loop() as SceneTree).root.add_child(s)
	assert_eq(s.z_index, -1)
	assert_true(load("res://shaders/snow_trail.gdshader") is Shader)
	s.queue_free()
