extends TestCase

func test_ground_material_is_read_per_two_pixel_cell() -> void:
	# 2x2 cells: grass, earth / stone, wood
	var g := GroundMat.new(PackedByteArray([0, 1, 2, 3]), 2, 2)
	assert_eq(g.at(Vector2(1, 1)), GroundMat.GRASS)
	assert_eq(g.at(Vector2(3, 0)), GroundMat.EARTH)
	assert_eq(g.at(Vector2(0, 3)), GroundMat.STONE)
	assert_eq(g.at(Vector2(3.9, 3.9)), GroundMat.WOOD)
	assert_eq(g.at(Vector2(-5, 99)), GroundMat.GRASS, "ausserhalb = Gras")

func test_player_steps_twice_per_walk_cycle() -> void:
	var pl := Player.new()
	var steps := [0]
	pl.stepped.connect(func(): steps[0] += 1)
	pl.position = Vector2.ZERO
	pl.walk_to(PackedVector2Array([Vector2(240, 0)]))
	for i in 200:                        # 2 s of strolling: 3 footfalls a second
		pl._process(0.01)
	assert_between(steps[0], 5, 7)
	# how far one footfall carries him must match the stride drawn in the walk frames (feet 5 px apart,
	# tools/gen_char.py STRIDE) - otherwise the planted foot slides and he seems to float
	assert_between(Player.SPEED / Player.STEPS_PER_SEC, 4.5, 5.5)
	pl.free()

func test_standing_player_makes_no_steps() -> void:
	var pl := Player.new()
	var steps := [0]
	pl.stepped.connect(func(): steps[0] += 1)
	for i in 100:
		pl._process(0.01)
	assert_eq(steps[0], 0)
	pl.free()

func test_shy_bird_flies_before_a_bold_one() -> void:
	var shy := BirdBrain.new(1.0)
	var bold := BirdBrain.new(0.0)
	assert_true(shy.flee_distance() > bold.flee_distance())
	shy.update(0.1, 30.0)
	bold.update(0.1, 30.0)
	assert_eq(shy.state, BirdBrain.FLY)
	assert_true(bold.state != BirdBrain.FLY)

func test_bird_watches_before_it_flees() -> void:
	var b := BirdBrain.new(0.0)
	b.update(0.1, b.flee_distance() + 6.0)
	assert_eq(b.state, BirdBrain.WATCH)
	b.update(0.1, 200.0)
	b.update(5.0, 200.0)
	assert_true(b.state == BirdBrain.PECK or b.state == BirdBrain.HOP, "beruhigt sich wieder")

func test_flown_bird_is_gone_and_does_not_come_back_while_watched() -> void:
	var b := BirdBrain.new(0.5)
	b.update(0.1, 1.0)
	assert_eq(b.state, BirdBrain.FLY)
	b.update(BirdBrain.FLY_TIME + 0.1, 1.0)
	assert_eq(b.state, BirdBrain.GONE)
	b.update(999.0, 1.0)
	assert_eq(b.state, BirdBrain.GONE, "kommt nicht zurueck, solange man daneben steht")

func test_wisp_drifts_away_when_approached_and_returns_later() -> void:
	var w := Wisp.new()
	w.anchor = Vector2(100, 100)
	w.position = w.anchor
	w.step(0.1, Vector2(300, 300))
	assert_true(w.visible_amount() > 0.0)
	for i in 40:
		w.step(0.1, Vector2(104, 100))
	assert_true(w.position.distance_to(Vector2(104, 100)) > Wisp.SHY, "weicht aus")
	for i in 400:
		w.step(0.1, Vector2(400, 400))
	assert_true(w.position.distance_to(w.anchor) < 12.0, "kehrt zurueck")
	w.free()

func test_footsteps_follow_the_ground_and_the_snow_gets_deeper_uphill() -> void:
	assert_eq(SoundBank.step_set(GroundMat.GRASS, 900), "schritt_gras")
	assert_eq(SoundBank.step_set(GroundMat.WOOD, 650), "schritt_holz")
	assert_eq(SoundBank.step_set(GroundMat.WET, 660), "schritt_nass")
	assert_eq(SoundBank.step_set(GroundMat.SNOW, 400), "schritt_schnee_wenig")
	assert_eq(SoundBank.step_set(GroundMat.SNOW, 200), "schritt_schnee")
	assert_eq(SoundBank.step_set(GroundMat.SNOW, 60), "schritt_schnee_hart")

func test_every_footstep_set_has_several_recordings() -> void:
	for s in ["schritt_gras", "schritt_erde", "schritt_stein", "schritt_holz", "schritt_nass",
			"schritt_schnee_wenig", "schritt_schnee", "schritt_schnee_hart"]:
		assert_true(SoundBank.variants(s).size() >= 8, s)

func test_ambience_recordings_exist() -> void:
	for s in ["nacht", "wind_ruhig", "abendwiese", "bergwind_a", "bergwind_b", "bach_klein", "bach_mittel",
			"bach_gross", "feuer", "kerze", "knistern", "schimmer", "vogel_0", "fluegel_0", "glocke", "frosch",
			"seite_0", "buch_zu_0"]:
		assert_true(SoundBank.get_stream(s) != null, s)

func test_trail_remembers_steps_and_lets_them_close() -> void:
	var t := Trail.new()
	for i in 10:
		t.update(0.13, Vector2(i * 2, 0), Vector2.RIGHT, true)
	assert_true(t.points.size() >= 8, "Punkte gemerkt")
	assert_true(t.points.size() <= Trail.SIZE)
	var u: Array = t.uniforms()
	assert_eq(u[0].size(), Trail.SIZE)
	assert_true(u[1][0] > 0.9, "frischester Schritt ist voll stark")
	for i in 30:
		t.update(0.13, Vector2.ZERO, Vector2.ZERO, false)
	assert_eq(t.points.size(), 0, "die Gasse hat sich geschlossen")

func test_trail_wake_is_long_and_fits_the_shader() -> void:
	# a long V behind him: the flowers swing back over about 3 s, and the shader takes every point
	assert_between(Trail.LIFE, 2.5, 4.0)
	assert_true(Trail.SIZE * Trail.EVERY >= Trail.LIFE, "genug Punkte für den ganzen Schweif")
	var code: String = (load("res://shaders/flowers.gdshader") as Shader).code
	assert_true(code.contains("const int TRAIL = %d;" % Trail.SIZE), "Shader kennt alle Punkte")

func test_trail_parts_the_poppies_ahead_of_the_feet() -> void:
	# the flowers should give way before he reaches them, not when he is already past
	var t := Trail.new()
	t.update(0.13, Vector2(100, 50), Vector2.RIGHT, true)
	var newest: Vector2 = t.points[0][0]
	assert_true(newest.x >= 100.0 + Trail.LEAD - 0.01, "frischester Punkt liegt vor den Füßen")
	assert_between(Trail.LEAD, 2.0, 4.0)   # at his front edge: further reads as an aura

func test_book_paper_sounds_are_turned_down() -> void:
	# the book should not sound bigger than the meadow: the pages clearly lower
	var b := BookUI.new()
	assert_true(b.SFX_DB["seite"] <= -5.0, "Blättern abgesenkt")
	b.free()

func test_closed_book_lets_taps_through_to_the_world() -> void:
	# with the book closed only its small button may catch a touch - everything else must reach the meadow
	var tree := Engine.get_main_loop() as SceneTree
	var b := BookUI.new()
	tree.root.add_child(b)
	b.show_start(false)
	b._start(false)
	var catching: Array = []
	var stack: Array = [b]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		stack.append_array(n.get_children())
		if n is Control and n.is_visible_in_tree() and n.mouse_filter != Control.MOUSE_FILTER_IGNORE and not (n is TextureButton):
			catching.append(n.name)
	assert_eq(catching, [], "fängt Tipps ab")
	b.queue_free()

func test_book_text_stays_on_the_page() -> void:
	# every handwritten line must end before the page's right edge, in every page of the book
	var tree := Engine.get_main_loop() as SceneTree
	var b := BookUI.new()
	tree.root.add_child(b)
	var page_w: float = BookUI.PAPER_RIGHT - b._content.position.x - 4.0   # the paper, not the leather
	var setups := [
		func(): b.has_save = false; b.show_start(false); b.mode = BookUI.Mode.MAIN; b._apply_mode(),
		func(): b.has_save = true; b.show_start(true); b.mode = BookUI.Mode.MAIN; b._apply_mode(),
		func(): b._in_game = true; b.mode = BookUI.Mode.MAIN; b._apply_mode(),
		func(): b._in_game = true; b.mode = BookUI.Mode.SETTINGS; b._apply_mode(),
		func(): b._in_game = false; b.mode = BookUI.Mode.SETTINGS; b._apply_mode(),
	]
	for i in setups.size():
		setups[i].call()
		for c in b._content.get_children():
			if c is Label and not c.is_queued_for_deletion():
				var w: float = c.size.x if c.autowrap_mode != TextServer.AUTOWRAP_OFF else c.get_minimum_size().x
				assert_true(c.position.x + w <= page_w + 0.5, "Seite %d: '%s' endet bei %.0f > %.0f" % [i, c.text, c.position.x + w, page_w])
	b.queue_free()

func test_ducking_lowers_music_and_backdrop_then_brings_them_back() -> void:
	# a bird taking off or the book: music and the ambient bed step back, then return softly
	AudioSetup.ensure_buses()
	var d := Ducker.new()
	(Engine.get_main_loop() as SceneTree).root.add_child(d)
	var music := AudioServer.get_bus_index(AudioSetup.MUSIC_TRACK)
	var bed := AudioServer.get_bus_index(AudioSetup.BACKDROP)
	assert_true(music >= 0 and bed >= 0, "Busse da")
	Ducker.duck()
	for i in 30:
		d._process(0.01)
	assert_true(AudioServer.get_bus_volume_db(music) < -4.0, "Musik abgesenkt")
	assert_true(AudioServer.get_bus_volume_db(bed) < -4.0, "Kulisse abgesenkt")
	for i in 400:
		d._process(0.01)
	assert_almost_eq(AudioServer.get_bus_volume_db(music), 0.0, 0.05, "Musik wieder da")
	assert_almost_eq(AudioServer.get_bus_volume_db(bed), 0.0, 0.05, "Kulisse wieder da")
	# the sliders still reach them: both routes end in the slider buses
	assert_eq(AudioServer.get_bus_send(music), AudioSetup.MUSIC)
	assert_eq(AudioServer.get_bus_send(bed), AudioSetup.SOUNDS)
	d.queue_free()

func test_campfire_can_be_heard_from_the_path() -> void:
	var a := Ambience.new()
	assert_true(a.FIRE_DB >= -4.0 and a.FIRE_REACH >= 150.0, "Feuer laut genug und weit genug")
	a.free()

func test_the_wanderer_carries_the_ear() -> void:
	# without a 2D listener Godot measures distances in screen pixels - on a phone that is ~5x the world,
	# so the fire, brooks and birds all fell out of reach and were silent
	var tree := Engine.get_main_loop() as SceneTree
	var pl := Player.new()
	tree.root.add_child(pl)
	var ear: AudioListener2D = null
	for c in pl.get_children():
		if c is AudioListener2D:
			ear = c
	assert_true(ear != null, "Hörer am Mönch")
	assert_true(ear != null and ear.is_current(), "Hörer ist aktiv")
	pl.queue_free()
