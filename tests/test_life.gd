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
			"bach_gross", "feuer", "kerze", "knistern", "fackel", "vogel_0", "fluegel_0", "glocke", "frosch",
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

func test_place_sounds_arrive_near_the_music_level() -> void:
	# up close a place sound should reach about the level of music and steps (-26..-30 dB), measured:
	# recording loudness (volumedetect) plus the volume set in the game
	var a := Ambience.new()
	assert_between(-29.3 + a.FIRE_DB, -36.0, -30.0, "Feuer")   # crackle under the steps, not over them
	assert_between(-27.8 + a.BROOK_DB["bach_mittel"], -32.0, -26.0, "Bach")
	a.free()

func test_wisp_flame_breathes_as_one_shape() -> void:
	# ball and flame are one shape that grows on the in-breath (the tongues rise with it)
	var low := Wisp.flame_pixels(Wisp.BREATH * 0.75, 1.0)      # sin at its lowest
	var high := Wisp.flame_pixels(Wisp.BREATH * 0.25, 1.0)     # sin at its highest
	assert_true(high.size() > low.size() + 6, "wächst beim Einatmen: %d -> %d" % [low.size(), high.size()])
	var top_low := 0
	var top_high := 0
	for q in low: top_low = mini(top_low, q.y)
	for q in high: top_high = mini(top_high, q.y)
	assert_true(top_high < top_low, "Flammen schlagen höher")

func test_wisp_fades_by_shrinking_not_by_transparency() -> void:
	# half transparency dithers into a checkerboard - it shrinks away instead, and every pixel is opaque
	assert_eq(Wisp.flame_pixels(1.0, 0.0).size(), 0, "ganz weg")
	for c in Wisp.flame_pixels(1.0, 1.0).values():
		assert_almost_eq(c.a, 1.0, 0.001, "deckend")

func test_wisp_does_not_twitch_when_you_stand_at_the_edge() -> void:
	# it was behind you (you stood between it and its home): "go home" led straight at you, "shy" pushed
	# it back - one step each way, every frame
	var w := Wisp.new()
	w.anchor = Vector2(100, 100)
	w.position = Vector2(100, 214)
	var pl := Vector2(100, 175)                 # 75 px from home, the wisp 39 px behind you
	var flips := 0
	var last_dir := 0.0
	for i in 600:
		var before := w.position
		w.step(1.0 / 60.0, pl)
		var d := signf(w.position.y - before.y)
		if d != 0.0:
			if last_dir != 0.0 and d != last_dir:
				flips += 1
			last_dir = d
	assert_true(flips < 4, "zuckt hin und her: %d Richtungswechsel" % flips)
	w.free()

func test_wisp_glides_while_you_walk_around_it() -> void:
	# walking around near it, it jittered: its drawn pixel stepped one way and straight back again
	var w := Wisp.new()
	w.anchor = Vector2(200, 200)
	w.position = Vector2(200, 200)
	var reversals := 0
	var last := Vector2i(w.position.round())
	var last_step := Vector2i.ZERO
	for i in 900:                                   # 15 s of strolling in a loose circle around it
		var a := i / 60.0 * 0.6
		var pl := Vector2(200, 200) + Vector2(cos(a), sin(a)) * (38.0 + 6.0 * sin(i / 60.0 * 2.3))
		w.step(1.0 / 60.0, pl)
		var now := Vector2i(w.position.round())
		var s := now - last
		if s != Vector2i.ZERO:
			if (s.x != 0 and s.x == -last_step.x) or (s.y != 0 and s.y == -last_step.y):
				reversals += 1
			last_step = s
			last = now
	assert_true(reversals < 15, "zittert: %d Pixel-Rückschritte" % reversals)
	w.free()

func test_wisp_light_sits_on_the_drawn_flame() -> void:
	# the flame is drawn on whole pixels; a glow at the exact sub-pixel spot slid against it -> jitter
	var w := Wisp.new()
	w.position = Vector2(120.4, 80.6)
	var d := w.light_data()
	assert_almost_eq(d["x"], 120.5, 0.001, "Licht x mitten im Kernpixel")
	assert_almost_eq(d["y"], 81.5, 0.001, "Licht y mitten im Kernpixel")
	w.free()

func test_wisp_flicker_is_calm() -> void:
	assert_true(Wisp.FLICKER <= 6.0, "nicht zu schnell")

func test_wisp_breathes_in_steps_not_in_a_tremble() -> void:
	# trembling is the shape changing nearly every frame (a pixel popping in or out at the rim); counted at
	# 30 frames a second over 10 s: in how many frames does the drawn shape change at all
	var events := 0
	var prev := Wisp.flame_pixels(0.0, 1.0)
	for i in range(1, 300):
		var now := Wisp.flame_pixels(i / 30.0, 1.0)
		if now.keys() != prev.keys():
			events += 1
		prev = now
	assert_true(events / 10.0 <= 7.0, "Formwechsel pro Sekunde: %.1f" % (events / 10.0))

func test_wisp_light_breathes_in_the_same_steps_as_the_flame() -> void:
	# a glow whose radius changes every frame makes its dithered rim crawl all around - that was the tremble
	var w := Wisp.new()
	var radii := {}
	for i in 600:
		w._t = i / 60.0
		radii[w.light_data()["r"]] = true
	assert_true(radii.size() <= 3, "Lichtradius nimmt %d Werte an" % radii.size())
	w.free()

func test_wisp_glow_is_warm_like_its_flame() -> void:
	# the bloom kept the old cold mint colour and covered the amber flame in a green-white blob
	var code: String = (load("res://shaders/post.gdshader") as Shader).code
	assert_false(code.contains("vec3(150.0, 240.0, 215.0)"), "kein Mint-Glühen mehr")

func test_wisp_hovers_almost_still_when_left_alone() -> void:
	# you stand still nearby: it should rest in the air, moving a pixel only now and then
	var w := Wisp.new()
	w.anchor = Vector2(100, 100)
	w.position = Vector2(100, 100)
	var pl := Vector2(100, 190)
	var moves := 0
	var last := Vector2i(w.position.round())
	for i in 1800:                                  # 30 s
		w.step(1.0 / 60.0, pl)
		var now := Vector2i(w.position.round())
		if now != last:
			moves += 1
			last = now
	assert_true(moves <= 75, "Pixelsprünge in 30 s: %d" % moves)
	w.free()

func test_wisp_sways_sideways_like_in_the_wind() -> void:
	# it rests in the air but sways left and right a few pixels, hardly up and down
	var w := Wisp.new()
	w.anchor = Vector2(100, 100)
	w.position = Vector2(100, 100)
	var lo := Vector2(INF, INF)
	var hi := -lo
	for i in 1800:
		w.step(1.0 / 60.0, Vector2(100, 190))
		lo = lo.min(w.position)
		hi = hi.max(w.position)
	assert_between(hi.x - lo.x, 5.0, 12.0, "seitlich")
	assert_true(hi.y - lo.y <= 3.0, "kaum hoch und runter: %.0f" % (hi.y - lo.y))
	w.free()

func test_post_shader_knows_where_the_camera_really_is() -> void:
	# the post shader snaps to world pixels using cam_pos; if that lags the real view by a frame while
	# scrolling, small bright things hop a pixel back and forth
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	m.book.mode = BookUI.Mode.CLOSED
	var worst := 0.0
	for i in 20:
		m.player.position += Vector2(0.37, -0.53)          # walking: the camera scrolls a fraction each frame
		m._process(1.0 / 60.0)
		var real := m.get_viewport().get_canvas_transform().affine_inverse() * Vector2.ZERO
		var told: Vector2 = m.post.get_shader_parameter("cam_pos")
		worst = maxf(worst, real.distance_to(told))
	assert_true(worst < 0.01, "Shader liegt %.2f Pixel neben der echten Kamera" % worst)
	m.queue_free()

func test_wisp_stands_on_whole_world_pixels_like_the_ground() -> void:
	# with "snap 2D transforms to pixel" on, a node at a fractional spot is rounded against the scrolling
	# camera, the ground (on whole pixels) is not - so the wisp hopped a pixel in the walking direction
	var w := Wisp.new()
	w.anchor = Vector2(100.3, 100.7)
	w.position = Vector2(100.3, 100.7)
	var pl := Vector2(100, 128)
	for i in 240:
		w.step(1.0 / 60.0, pl)
		assert_true(w.position == w.position.round(), "Bild %d: %s" % [i, w.position])
		if w.position != w.position.round():
			break
	w.free()

func test_camera_eases_after_the_wanderer() -> void:
	# starting and stopping should not jolt the view: the camera follows smoothly, then catches up
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	m._process(1.0 / 60.0)
	var before: Vector2 = m.cam.position
	m.player.position += Vector2(-30, 0)
	m._process(1.0 / 60.0)
	var moved: float = (m.cam.position - before).length()
	assert_true(moved > 0.0 and moved < 4.0, "erstes Bild nur ein Stück: %.2f" % moved)
	for i in 90:
		m._process(1.0 / 60.0)
	assert_almost_eq(m.cam.position.x, before.x - 30.0 + 10.0, 0.6, "holt auf bis zum Rand der Ruhezone")
	m.queue_free()

func test_small_side_steps_leave_the_view_still() -> void:
	# a pixel or two of correction sideways must not shift the whole world; a real walk still scrolls
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	for i in 60:
		m._process(1.0 / 60.0)
	var before: Vector2 = m.cam.position
	m.player.position += Vector2(2, 0)
	for i in 60:
		m._process(1.0 / 60.0)
	assert_almost_eq(m.cam.position.x, before.x, 0.01, "steht still")
	m.player.position += Vector2(30, 0)
	for i in 120:
		m._process(1.0 / 60.0)
	assert_true(m.cam.position.x > before.x + 15.0, "folgt bei echtem Laufen")
	m.queue_free()
