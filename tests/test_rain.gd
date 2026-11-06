extends TestCase

func test_a_shower_swells_from_a_drizzle_and_dies_away() -> void:
	var w := Weather.new(3)
	assert_eq(w.intensity(), 0.0, "zuerst trocken")
	var seen := []
	var last := 0.0
	var rising := true
	for i in int((Weather.DRY_MAX + Weather.SHOWER_MAX) / 5.0) + 2:
		w.step(5.0)
		var r := w.intensity()
		if r > 0.0:
			seen.append(r)
			if r < last - 0.0001:
				rising = false
			elif not rising and r > last + 0.0001:
				assert_true(false, "steigt nach dem Abklingen wieder an")
			last = r
		elif not seen.is_empty():
			break
	assert_true(seen.size() * 5.0 >= Weather.SHOWER_MIN - 10.0, "ein Schauer dauert Minuten")
	assert_true(seen[0] < 0.1, "fängt als Niesel an (Philip)")
	assert_true(seen.max() > 0.95, "wird zum Schauer")
	assert_true(seen[seen.size() - 1] < 0.1, "klingt wieder ab")

func test_showers_come_now_and_then() -> void:
	assert_between(Weather.DRY_MIN / 60.0, 10.0, 20.0)
	assert_between(Weather.DRY_MAX / 60.0, 20.0, 30.0)

func test_the_test_entry_starts_and_stops_a_shower() -> void:
	var w := Weather.new(5)
	w.toggle_now()
	w.step(Weather.SHOWER_MAX * Weather.SWELL)
	assert_true(w.intensity() > 0.9, "jetzt regnet es")
	w.toggle_now()
	w.step(Weather.SHOWER_MAX * Weather.FADE + 1.0)
	assert_eq(w.intensity(), 0.0, "und hört wieder auf")

func test_no_rain_where_the_snow_falls() -> void:
	assert_eq(Rain.reach(500.0), 0.0, "im Norden schneit es")
	assert_eq(Snowfall.density(Rain.SNOW_EDGE + 1.0), 0.0, "unter der Schneegrenze fällt kein Schnee")
	assert_eq(Rain.reach(2000.0), 1.0, "im Mohnfeld regnet es")

func test_drops_fall_and_follow_the_shower() -> void:
	var w := Weather.new(7)
	var r := Rain.new()
	r.weather = w
	var cam := {"top": Vector2(800, 2000)}
	r.camera_at = func() -> Vector2: return cam["top"]
	(Engine.get_main_loop() as SceneTree).root.add_child(r)
	assert_eq(r.visible_drops(), 0, "trocken: keine Tropfen")
	w.toggle_now()
	w.step(Weather.SHOWER_MAX * Weather.SWELL)
	var n := r.visible_drops()
	assert_true(n > 150, "im Schauer viele: %d" % n)
	var y0: float = r._drops[0]["p"].y
	r._process(0.05)
	assert_true(fposmod(r._drops[0]["p"].y - y0, Rain.VIEW.y) >= 7.0, "fallen zügig (Philip: nicht zu langsam)")
	r.off = true
	assert_eq(r.visible_drops(), 0, "in der Höhle keiner")
	r.queue_free()

func test_in_the_rain_he_takes_the_lantern() -> void:
	var pl := Player.new()
	(Engine.get_main_loop() as SceneTree).root.add_child(pl)
	pl.position = Vector2(900, 2000)
	pl.lantern.rain = 1.0
	pl.lantern._process(0.0)
	assert_true(pl.is_hanging(), "im Regen hängt er die Laterne auf")
	pl.queue_free()

func test_the_ground_stays_wet_a_while_and_dries() -> void:
	var w := Weather.new(7)
	assert_eq(w.wetness(), 0.0, "zuerst trocken")
	w.toggle_now()
	for i in 60:
		w.step(Weather.SHOWER_MAX * Weather.SWELL / 60.0)
	assert_true(w.wetness() > 0.9, "im Schauer nass")
	while w.raining():
		w.step(5.0)
	w.step(Weather.WET_HOLD - 10.0)
	assert_true(w.wetness() > 0.9, "nach dem Schauer noch Minuten nass")
	w.step(20.0 + Weather.WET_DRY * 0.5)
	assert_between(w.wetness(), 0.2, 0.8)
	for i in 40:
		w.step(Weather.WET_DRY / 20.0)
	assert_eq(w.wetness(), 0.0, "und trocknet ab")
