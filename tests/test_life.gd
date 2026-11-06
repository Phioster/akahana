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
	assert_eq(SoundBank.step_set(GroundMat.WET, 1860), "schritt_nass")
	# 0.12.3: the heights moved down with the north (they had stayed where the old map's top had been)
	assert_eq(SoundBank.step_set(GroundMat.SNOW, 1600), "schritt_schnee_wenig")
	assert_eq(SoundBank.step_set(GroundMat.SNOW, 1400), "schritt_schnee")
	assert_eq(SoundBank.step_set(GroundMat.SNOW, 1260), "schritt_schnee_hart", "der alte Gipfel")
	assert_eq(SoundBank.step_set(GroundMat.SNOW, 800), "schritt_schnee", "Wald im Norden")
	assert_eq(SoundBank.step_set(GroundMat.SNOW, 150), "schritt_schnee_hart", "der Pass")
	assert_eq(Ambience.altitude(800.0), 1.0, "der Norden liegt hoch")
	assert_eq(Ambience.altitude(2000.0), 0.0, "das Mohnfeld nicht")

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

func test_the_south_mist_map_reaches_the_post_shader() -> void:
	# thinner over grass and water, calm over the lake, a mist wall at the world's edge (south drafts)
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	var t: Texture2D = m.post.get_shader_parameter("mist_fields")
	assert_true(t != null, "Nebelkarte geladen")
	assert_eq(m.post.get_shader_parameter("world_size"), Vector2(1800, 4800))
	var code: String = (load("res://shaders/post.gdshader") as Shader).code
	assert_true(code.contains("GRASS_MIST") and code.contains("edge"))
	m.queue_free()

func test_the_wood_mood_map_and_cool_flies_reach_the_post_shader() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	assert_true(m.post.get_shader_parameter("grade_field") != null, "Stimmungskarte geladen")
	var code: String = (load("res://shaders/post.gdshader") as Shader).code
	assert_true(code.contains("grade_field") and code.contains("bloomc"))
	var sw := Fireflies.new()
	sw.setup({"x": 10.0, "y": 10.0, "cool": true, "flies": [{"ax": 0.0, "ay": 0.0, "rx": 1.0, "ry": 1.0, "sp": 0.0, "ph": 0.0, "bph": 1.5707963, "blink": 0.0}]})
	var l := sw.lights()
	assert_true(l.size() > 0 and l[0].w < 0.0, "kalte Fliege: negative Staerke")
	sw.free()
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

func test_the_view_comes_to_rest_on_a_whole_pixel() -> void:
	# resting between two art pixels, the post shader read right on their border and the whole picture
	# smeared until you walked on
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	m.player.position += Vector2(-27.5, 0)
	for i in 240:
		m._process(1.0 / 60.0)
	var c: Vector2 = m.cam.position
	assert_true(c == c.round(), "Kamera ruht auf %s" % c)
	var tl: Vector2 = m.post.get_shader_parameter("cam_pos")
	assert_true(tl == tl.round(), "Shader-Ecke %s" % tl)
	m.queue_free()

func test_the_view_settles_without_a_snap() -> void:
	# it crept on by hundredths of a pixel, then jumped the rest at once - seen as a jolt when stopping
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	for i in 30:
		m._process(1.0 / 60.0)
	m.player.walk_to(PackedVector2Array([m.player.position + Vector2(-40, 0)]))
	var prev: Vector2 = m._cam_at                        # the smooth glide behind the whole-pixel view
	var shown: Vector2 = m.cam.position
	var last := 0.0
	var worst_rise := 0.0
	var worst_jump := 0.0
	for i in 300:
		m.player._process(1.0 / 60.0)
		m._process(1.0 / 60.0)
		var d: float = m._cam_at.distance_to(prev)
		prev = m._cam_at
		if not m.player.is_walking() and d > last + 0.001:     # while settling it may only slow down
			worst_rise = maxf(worst_rise, d - last)
		last = d
		worst_jump = maxf(worst_jump, m.cam.position.distance_to(shown))
		shown = m.cam.position
	assert_true(worst_rise < 0.01, "Ruck beim Anhalten: +%.3f px" % worst_rise)
	assert_true(worst_jump <= 1.0, "gezeigt nie mehr als ein Pixel auf einmal: %.2f" % worst_jump)
	m.queue_free()

func _birds_at(view: Rect2) -> Birds:
	var tree := Engine.get_main_loop() as SceneTree
	var b := Birds.new()
	b.world = WorldData.load_default()
	b.sorted = Node2D.new()
	b.player = Node2D.new()
	b.player.position = view.get_center()
	tree.root.add_child(b.sorted)
	tree.root.add_child(b.player)
	tree.root.add_child(b)
	b.update_area(view)
	return b

func test_birds_live_only_near_the_view() -> void:
	var b := _birds_at(Rect2(-5000, -5000, 10, 10))
	assert_eq(b.flock_nodes(), 0, "weit weg: keine Vögel")
	var s: Dictionary = b.world.birds[0]
	b.update_area(Rect2(float(s["x"]) - 90, float(s["y"]) - 200, 180, 400))
	assert_true(b.flock_nodes() >= 1, "am Platz: Vögel da")
	b.sorted.queue_free(); b.player.queue_free(); b.queue_free()

func test_a_flock_dropped_in_flight_leaves_nothing_behind() -> void:
	var s: Dictionary = WorldData.load_default().birds[0]
	var b := _birds_at(Rect2(float(s["x"]) - 90, float(s["y"]) - 200, 180, 400))
	for bird in b.sorted.get_children():
		if bird is Bird:
			bird.brain.state = BirdBrain.FLY
	b.update_area(Rect2(-5000, -5000, 10, 10))
	assert_eq(b.flock_nodes(), 0)
	var left := 0
	for n in b.sorted.get_children():
		if n is Bird and not n.is_queued_for_deletion():
			left += 1
	assert_eq(left, 0, "keine Vögel übrig")
	b.sorted.queue_free(); b.player.queue_free(); b.queue_free()

func test_only_audible_spots_have_players() -> void:
	var tree := Engine.get_main_loop() as SceneTree
	var a := Ambience.new()
	a.world = WorldData.load_default()
	a.player = Node2D.new()
	a.player.position = a.world.start
	tree.root.add_child(a)
	a._process(1.0 / 60.0)
	var everywhere := a.world.brook.size() / 2 + a.world.lights.size() + 1
	assert_true(a.spot_nodes() > 0, "am Feuer etwas zu hören")
	assert_true(a.spot_nodes() < everywhere, "nicht alles: %d von %d" % [a.spot_nodes(), everywhere])
	a.player.free(); a.queue_free()

func test_footsteps_ask_the_store_for_the_ground() -> void:
	var s := ChunkStore.new(ChunkGrid.new(1, 1))
	var mat := PackedByteArray()
	mat.resize(ChunkStore.CELLS.x * ChunkStore.CELLS.y)
	mat.fill(GroundMat.WOOD)
	s._mat[Vector2i(0, 0)] = mat
	s._cells[Vector2i(0, 0)] = mat
	var f := Footsteps.new()
	f.store = s
	assert_eq(f.ground_at(Vector2(20, 20)), GroundMat.WOOD)
	f.free()

func test_walking_the_whole_map_keeps_memory_flat() -> void:
	# chunks, objects and place sounds stay bounded by the view; what lies far behind is let go
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	var size := Vector2(ChunkGrid.SIZE)
	var worst := ""
	for i in 27:
		m.player.position = Vector2(60.0 if i % 2 == 0 else 480.0, 100.0 + i * 40.0)
		m._cam_at = Vector2.INF
		for k in 30:
			m._process(1.0 / 60.0)
		var top_left: Vector2 = m.get_viewport().get_canvas_transform().affine_inverse() * Vector2.ZERO
		var view := Rect2(top_left, m.get_viewport().get_visible_rect().size)
		var reach: int = m.store.grid.chunks_in(view.grow_individual(2 * size.x, 2 * size.y, 2 * size.x, 2 * size.y)).size()
		var objs := 0
		for s in m.world.sprites:
			if Activator._gap(Rect2(float(s["x"]), float(s["y"]), float(s["w"]), float(s["h"])), view) <= 120.0:
				objs += 1
		var amb: Ambience = null
		for n in m.get_children():
			if n is Ambience:
				amb = n
		if m.store.loaded_count() > reach or m.view_node.chunk_nodes() > reach:
			worst = "Kacheln %d/%d bei %s" % [m.store.loaded_count(), reach, view]
		elif m.view_node.object_nodes() > objs:
			worst = "Objekte %d statt höchstens %d" % [m.view_node.object_nodes(), objs]
		elif amb.spot_nodes() > 8:
			worst = "Ortsklänge %d" % amb.spot_nodes()
	assert_eq(worst, "", worst)
	assert_false(m.store.is_ready(Vector2i(0, 0)), "ganz oben vergessen, wenn er unten ist")
	m.queue_free()

func test_a_new_walk_finds_its_ground_at_once() -> void:
	# review: "new walk" jumped to the start while its chunks were long forgotten - empty ground until they came
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	m.player.position = Vector2(270, 100)
	m._cam_at = Vector2.INF
	for k in 30:
		m._process(1.0 / 60.0)
	var c: Vector2i = m.world.grid.chunk_of(m.world.start)
	assert_false(m.store.is_ready(c), "Start vergessen, solange er oben ist")
	m._on_start_walking(true)
	assert_true(m.store.is_ready(c), "Start-Kachel sofort da")
	m.queue_free()

func test_the_view_moves_evenly_while_walking_straight() -> void:
	# measured on the phone (0.4.1): steps went -0.28,-0.26,-0.24,-0.22 in fours - the goal was rounded
	# to whole pixels while walking, jumped a pixel every fourth frame and the view wobbled after it
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	m.player.position = Vector2(270, 800)               # mid-map: at the bottom edge the view is clamped
	m._cam_at = Vector2.INF
	for i in 30:
		m._process(1.0 / 60.0)
	m.player.walk_to(PackedVector2Array([m.player.position + Vector2(0, -300)]))
	var prev: Vector2 = m._cam_at
	var lo := INF
	var hi := -INF
	for i in 400:
		m.player._process(1.0 / 60.0)
		m._process(1.0 / 60.0)
		var d: float = m._cam_at.y - prev.y
		prev = m._cam_at
		if i > 200 and m.player.is_walking():             # settled into the walk
			lo = minf(lo, d)
			hi = maxf(hi, d)
	assert_true(hi - lo < 0.02, "Schritte schwanken %.3f..%.3f" % [lo, hi])
	m.queue_free()

func test_wading_at_the_lake_but_wet_pebbles_at_the_old_ford() -> void:
	assert_eq(SoundBank.step_set(GroundMat.WET, 4200.0), "schritt_waten", "flacher Seerand im Süden")
	assert_eq(SoundBank.step_set(GroundMat.WET, 1880.0), "schritt_nass", "alte Furt")
	assert_true(SoundBank.variants("schritt_waten").size() >= 8)

func test_tall_grass_rustles_on_every_second_step() -> void:
	# south of the poppies (from zone 2 on) the grass is tall: a footfall, and every second one a rustle
	assert_true(Footsteps.rustles(GroundMat.GRASS, 3200.0), "hohes Gras im Süden")
	assert_false(Footsteps.rustles(GroundMat.GRASS, 2100.0), "nicht im Mohnfeld")
	assert_false(Footsteps.rustles(GroundMat.EARTH, 3200.0), "nicht auf dem Weg")
	var f := Footsteps.new()
	var n := 0
	for i in 10:
		if f.next_rustles(GroundMat.GRASS, 3200.0):
			n += 1
	assert_eq(n, 5)
	f.free()
	assert_eq(SoundBank.variants("rascheln").size(), 8)

func test_fireflies_hum_only_close_by() -> void:
	var w := WorldData.load_default()
	var sw := Fireflies.new()
	sw.setup(w.fireflies[0])
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.add_child(sw)
	var hum: AudioStreamPlayer2D = sw.get_node_or_null("Summen")
	assert_true(hum != null and hum.stream != null, "Summen geladen")
	assert_true(hum.max_distance >= 60.0 and hum.max_distance <= 80.0, "nur in der Nähe, aber dort hörbar")
	assert_true(hum.volume_db >= -12.0 and hum.volume_db <= -4.0, "so leise wie das Knistern des Irrlichts (0.7.2: -18 war unhörbar)")
	sw.queue_free()

func test_at_rest_the_view_s_corner_lies_on_a_whole_pixel() -> void:
	# phone: the view is 180 wide and about 400.4 high; a whole-pixel middle left the corner on half a pixel,
	# the world drawn between two pixels (he stood "in" the jetty, everything soft)
	var main := load("res://scenes/main.gd")
	for view in [Vector2(180, 400.4), Vector2(180, 401), Vector2(180, 399.75)]:
		var g: Vector2 = main.rest_goal(Vector2(271.3, 2955.6), view)
		var corner: Vector2 = g - view * 0.5
		assert_eq(corner, corner.round(), "Ecke auf ganzem Pixel bei %s" % view)
		assert_true(g.distance_to(Vector2(271.3, 2955.6)) <= 0.75, "kaum verschoben")

func test_a_hovering_thing_does_not_hop_between_two_pixels() -> void:
	# phone 0.7.0: the wisp and the fish shook back and forth: their true spot swung round a pixel's middle
	var shown := Vector2(3, 7)
	var hops := 0
	for i in 60:
		var p := Vector2(3.5 + 0.08 * sin(i * 1.3), 7.5 + 0.08 * cos(i * 0.9))
		var n := PixelSnap.sticky(shown, p)
		if n != shown:
			hops += 1
		shown = n
	assert_true(hops <= 1, "bleibt stehen: %d Sprünge" % hops)
	var s := Vector2(0, 0)
	var steps := 0
	for i in 100:                                   # steady drift still moves pixel by pixel
		var n := PixelSnap.sticky(s, Vector2(i * 0.1, 0))
		if n != s:
			steps += 1
		s = n
	assert_true(steps >= 8 and steps <= 10, "gleichmäßig weiter: %d" % steps)

func test_a_swimmer_steps_both_axes_together_and_evenly() -> void:
	var shown := Vector2(12, 0)
	var times := []
	for i in 720:                                    # a circle of radius 12 at 6 px/s, 60 fps
		var a := float(i) / 60.0 * 6.0 / 12.0
		var n := PixelSnap.together(shown, Vector2(cos(a), sin(a)) * 12.0)
		if n != shown:
			times.append(i)
			assert_true(absf(n.x - shown.x) <= 1.0 and absf(n.y - shown.y) <= 1.0, "ein Schritt ist hoechstens ein Pixel je Achse")
		shown = n
	assert_true(times.size() >= 55 and times.size() <= 70, "gleichmaessig: %d Schritte" % times.size())
	var longest := 0
	for k in range(1, times.size()):
		longest = maxi(longest, times[k] - times[k - 1])
	assert_true(longest <= 16, "kein Stillstand dazwischen: %d Bilder" % longest)

func test_stopping_never_sends_the_view_back_a_fraction() -> void:
	# phone 0.7.2: on stopping the view now and then stood on half a pixel for a moment: the rounded goal lay
	# behind the camera, which still crept toward the old goal - it went back, then snapped
	var main := load("res://scenes/main.gd")
	var view := Vector2(180, 400.4)
	var at := Vector2(100.3, 1500.0) + view * 0.5           # corner 100.3, moving right toward 100.45
	var goal := Vector2(100.45, 1500.0) + view * 0.5
	var g: Vector2 = main.rest_goal(goal, view, at)
	var corner: Vector2 = g - view * 0.5
	assert_eq(corner, corner.round(), "ganzer Pixel")
	assert_true(corner.x >= 100.3, "nicht zurück: %s" % corner)
	var g2: Vector2 = main.rest_goal(Vector2(271.3, 2955.6), view, Vector2(271.3, 2955.6))
	assert_eq(g2 - view * 0.5, (g2 - view * 0.5).round())

func test_the_test_travel_list_puts_him_on_open_ground_at_every_place() -> void:
	# a tool only for testing (Philip): in the game itself there is no fast travel
	var tree := Engine.get_main_loop() as SceneTree
	var m: Node2D = load("res://scenes/main.gd").new()
	tree.root.add_child(m)
	await tree.process_frame
	if m.world == null:
		m.queue_free()
		return
	assert_true(TestTravel.PLACES.size() >= 6, "genug Orte")
	for place in TestTravel.PLACES:
		m._on_travel(place[1])
		assert_true(m.store.walkable(m.player.position), "begehbar: %s" % place[0])
		assert_true(m.player.position.distance_to(place[1]) < 40.0, "nah am Ziel: %s" % place[0])
		assert_false(m.player.is_walking())
	m.queue_free()

func test_the_book_offers_travel_only_in_test_builds() -> void:
	var b := BookUI.new()
	assert_eq(b.travel_offered(), OS.is_debug_build(), "nur in Testversionen")
	b.free()

func test_no_two_book_entries_lie_on_top_of_each_other() -> void:
	# phone 0.7.8: "Reisen (Test)" landed on the line of "weiterlaufen" and could not be tapped
	var tree := Engine.get_main_loop() as SceneTree
	var b := BookUI.new()
	tree.root.add_child(b)
	for m in [BookUI.Mode.MAIN, BookUI.Mode.SETTINGS, BookUI.Mode.TRAVEL]:
		for in_game in [true, false]:
			b._in_game = in_game
			b.mode = m
			b._apply_mode()
			var areas := []
			for c in b._content.get_children():
				if c is TapArea and not c.is_queued_for_deletion():
					areas.append(Rect2(c.position, c.size))
			for i in areas.size():
				for j in range(i + 1, areas.size()):
					assert_false(areas[i].grow(-1.0).intersects(areas[j].grow(-1.0)),
							"Seite %d (im Spiel %s): Einträge %d und %d überdecken sich" % [m, in_game, i, j])
	b.queue_free()


func test_the_view_glides_in_screen_pixels_not_art_pixels() -> void:
	# Philip 0.7.12: whole art pixels were far too jerky (a step every fourth frame) - glide in the phone's
	# screen pixels (about 6 per art pixel), so world, sprites and post shader agree and it stays smooth
	var main := load("res://scenes/main.gd")
	var view := Vector2(180, 400.4)
	var steps := {}
	var last: Vector2 = main.shown_corner(Vector2(100.0, 1000.0) + view * 0.5, view, 6.0)
	for i in range(1, 41):
		var at := Vector2(100.0, 1000.0 - i * 0.25) + view * 0.5       # 0.25 art px a frame, upwards
		var c: Vector2 = main.shown_corner(at, view, 6.0)
		assert_eq(c * 6.0, (c * 6.0).round(), "auf einem Bildschirmpixel")
		assert_true(c.distance_to(at - view * 0.5) <= 1.0 / 12.0 + 0.0001, "kaum neben der wahren Lage")
		var d := snappedf(last.y - c.y, 0.001)
		steps[d] = true
		last = c
	assert_true(steps.size() <= 2, "gleichmäßig in Bildschirmpixeln: %s" % [steps.keys()])
	assert_false(steps.has(0.0), "rückt jedes Bild weiter, nicht nur jedes vierte")


func test_he_hangs_up_his_lantern_in_the_dark_wood_and_takes_it_down_outside() -> void:
	# Philip 2026-11-04: in the dark he stops, lifts the lantern from his hand onto the staff; outside, back down
	var tree := Engine.get_main_loop() as SceneTree
	var p := Player.new()
	tree.root.add_child(p)
	var w := WorldData.load_default()
	p.lantern.world_size = Vector2(w.width, w.height)
	assert_almost_eq(p.lantern.darkness(Vector2(243, 2270), p.lantern.world_size), 0.0, 0.05, "Lager hell")
	assert_true(p.lantern.darkness(Vector2(1250, 2900), p.lantern.world_size) > 0.9, "Ostwald dunkel")
	p.position = Vector2(243, 2270)
	p.lantern._process(0.1)
	assert_false(p.is_hanging(), "auf der Wiese keine Laterne")
	assert_almost_eq(float(p.lantern.light_data()["k"]), 0.0, 0.001)
	p.position = Vector2(1250, 2900)
	p.walk_to(PackedVector2Array([Vector2(1300, 2900)]))
	p.lantern._process(0.1)
	assert_true(p.is_hanging(), "haengt sie auf")
	assert_false(p.is_walking(), "steht dabei")
	var at := p.position
	p._process(0.3)
	assert_eq(p.position, at, "geht nicht weiter, solange er aufhaengt")
	assert_eq(p.sprite.texture, p._hang_tex)
	assert_eq(p.sprite.frame, p.dir * 4 + 1)
	p.lantern._process(0.0)
	assert_true(p.lantern.lit > 0.2 and p.lantern.lit < 0.5, "Licht kommt mit: %f" % p.lantern.lit)
	for i in 6:
		p._process(0.1)
	assert_false(p.is_hanging())
	assert_true(p.lantern.carried, "haengt am Stab")
	assert_eq(p.sprite.hframes, Player.COLS, "wieder das normale Blatt")
	p.lantern._process(0.0)
	assert_almost_eq(p.lantern.lit, 1.0, 0.001)
	var l: Dictionary = p.lantern.light_data()
	assert_eq(l["kind"], "lantern")
	assert_true(Vector2(l["x"], l["y"]).distance_to(p.position) < 16.0, "Licht am Moench")
	p._process(0.5)
	assert_true(p.position != at, "laeuft danach weiter")
	p.path = PackedVector2Array()
	p.position = Vector2(243, 2270)
	p.lantern._process(0.0)
	assert_true(p.is_hanging() and not p.lantern.carried, "nimmt sie draussen ab")
	for i in 10:
		p._process(0.1)
	p.lantern._process(0.0)
	assert_almost_eq(p.lantern.lit, 0.0, 0.001)
	assert_false(p.lantern.carried)
	p.queue_free()


func test_the_lantern_hangs_off_the_staff_tip_in_every_facing() -> void:
	# Philip: in profile it lies right against the staff, front and back one pixel out on a hook
	for row in 4:
		var tx: int = Lantern.TIP_X[row]
		var cx: int = Lantern.HANG_X[row]
		assert_eq(absi(cx - tx), 1, "Haken ein Pixel")


func test_the_light_sits_on_the_lantern_in_his_hand_while_he_lifts_it() -> void:
	# phone 0.10.7: the glow already hung at the staff tip while the lantern was still at his waist
	var img := TextureLoader.load_texture("res://assets/char/wanderer_laterne.png").get_image()
	for row in 4:
		for k in 2:
			var p: Vector2i = Lantern.HELD[row][k]
			var c := img.get_pixel(k * 16 + p.x + 2, row * 16 + p.y)
			assert_true(c.r > 0.95 and c.g > 0.65 and c.g < 0.8, "Richtung %d Phase %d: kein Glutpixel bei %s" % [row, k, p])


func test_his_outline_stays_open_under_the_crowns() -> void:
	# Philip 0.10.7: under the leaves one saw the lantern's glow, hardly him - crowns in front keep his shape open
	var tree := Engine.get_main_loop() as SceneTree
	var p := Player.new()
	tree.root.add_child(p)
	p.position = Vector2(100.3, 200.6)
	var s: Dictionary = p.silhouette()
	assert_eq(s["rect"], Rect2(Vector2(100, 201) + Vector2(-6, -15), Vector2(12, 16)))
	var uv: Rect2 = s["uv"]
	assert_almost_eq(uv.size.x, 1.0 / Player.COLS, 0.0001)
	assert_eq(s["lamp"], Rect2(), "keine Laterne auf der Wiese")
	p.lantern.carried = true
	var lamp: Rect2 = p.silhouette()["lamp"]
	assert_eq(lamp.size, Vector2(3, 6))
	assert_true(Rect2(s["rect"]).grow(3).encloses(lamp), "Laterne bei ihm")
	p.queue_free()

func test_a_page_turns_over_the_binding_and_stays_lying_back() -> void:
	# 2026-11-06: forward the sheet curls up and stays over the band; back to the first page it comes down
	var tree := Engine.get_main_loop() as SceneTree
	var b := BookUI.new()
	tree.root.add_child(b)
	b.open_in_game()
	assert_false(b._turn.visible, "auf der ersten Seite liegt nichts umgeschlagen")
	b._turn_to(BookUI.Mode.SETTINGS)
	assert_true(b._turning and b._turn.visible, "blättert")
	assert_eq(b.mode, BookUI.Mode.SETTINGS, "die neue Seite liegt schon darunter")
	b._turn_to(BookUI.Mode.MAIN)
	assert_eq(b.mode, BookUI.Mode.SETTINGS, "während des Blätterns kein zweites")
	b._turn_done()
	assert_true(b._turn.visible, "das Blatt bleibt oben liegen")
	assert_eq(b._turn.mouse_filter, Control.MOUSE_FILTER_IGNORE, "es fängt keine Tipps ab")
	b._turn_to(BookUI.Mode.MAIN)
	assert_false(b._turn_mat.get_shader_parameter("forward"), "zurück: es kommt wieder herunter")
	b._turn_done()
	assert_false(b._turn.visible, "wieder auf der ersten Seite")
	b.close()
	assert_false(b._turn.visible, "zugeklappt")
	b.queue_free()

func test_the_page_turn_knows_the_sheet() -> void:
	var img := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/buch_blatt.png"))
	var page := Image.load_from_file(ProjectSettings.globalize_path("res://assets/ui/buch_seite.png"))
	assert_eq(img.get_size(), page.get_size(), "so groß wie die Seite")
	assert_true(img.get_pixel(70, 120).r > 0.5, "Papier in der Mitte")
	assert_true(img.get_pixel(70, 8).g > 0.5 and img.get_pixel(70, 8).r < 0.5, "unter dem Band läuft das Blatt weiter")
	assert_eq(BookUI.TURN_MARGIN.y, 40.0)
	assert_true(load("res://shaders/page_turn.gdshader") is Shader)
