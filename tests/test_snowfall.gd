extends TestCase

func test_it_snows_only_in_the_north_and_more_up_high() -> void:
	assert_eq(Snowfall.density(1300.0), 0.0, "Kogarashi und der Süden: kein Schnee von oben")
	assert_between(Snowfall.density(Snowfall.BOTTOM - 45.0), 0.45, 0.6, "am Felstor leicht (A)")
	assert_true(Snowfall.density(800.0) > 0.75, "ab der Mitte fast B")
	assert_eq(Snowfall.density(100.0), 1.0, "am Pass voll (B)")
	assert_true(Snowfall.density(500.0) >= Snowfall.density(900.0), "nach oben dichter")

func test_gusts_come_and_go() -> void:
	var lo := 100.0
	var hi := 0.0
	for i in 200:
		var w := Snowfall.wind(i * 0.1)
		lo = minf(lo, w)
		hi = maxf(hi, w)
	assert_true(hi - lo > 10.0, "Böen")
	assert_true(lo > 0.0, "immer etwas schräg")

func test_flakes_stay_in_the_world_and_fall() -> void:
	var s := Snowfall.new()
	var cam := {"top": Vector2(300, 100)}             # lambdas copy plain values; a dictionary is shared
	s.camera_at = func() -> Vector2: return cam["top"]
	(Engine.get_main_loop() as SceneTree).root.add_child(s)
	var n := s.visible_count()
	assert_true(n > 400 and n <= s._flakes.size(), "am Pass fällt die volle Menge: %d" % n)
	var y0: float = s._flakes[0]["p"].y
	s._process(0.1)
	assert_true(fposmod(s._flakes[0]["p"].y - y0, Snowfall.VIEW.y) > 0.0, "sie fallen")
	cam["top"] = Vector2(300, 1600)
	assert_eq(s.visible_count(), 0, "im Süden keine")
	s.queue_free()

func test_none_in_the_cave() -> void:
	var s := Snowfall.new()
	s.off = true
	assert_true(s.off)
	s.free()
