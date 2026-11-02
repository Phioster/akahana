extends TestCase

func _run(b, secs: float, dist: float, in_water: bool) -> void:
	for i in int(secs * 20.0):
		b.update(0.05, dist, in_water)

func test_a_fish_rises_swims_a_while_and_sinks_away() -> void:
	var b := FishBrain.new(8.0)
	assert_eq(b.state, FishBrain.RISE)
	_run(b, 1.0, 999.0, false)
	assert_eq(b.state, FishBrain.SWIM, "aufgetaucht")
	_run(b, 8.0, 999.0, false)                          # 8 s life from 0.8 s on: just sinking at 9 s
	assert_eq(b.state, FishBrain.SINK, "nach seiner Zeit taucht er ab")
	_run(b, 1.0, 999.0, false)
	assert_eq(b.state, FishBrain.GONE)

func test_a_fish_darts_off_when_you_wade_close() -> void:
	var b := FishBrain.new(30.0)
	_run(b, 1.0, 999.0, false)
	_run(b, 0.2, 20.0, true)
	assert_eq(b.state, FishBrain.DART, "flieht")
	_run(b, 1.0, 20.0, true)
	assert_eq(b.state, FishBrain.GONE, "weg")

func test_a_fish_stays_when_you_stand_on_the_bank() -> void:
	var b := FishBrain.new(30.0)
	_run(b, 1.0, 999.0, false)
	_run(b, 2.0, 20.0, false)
	assert_eq(b.state, FishBrain.SWIM)

func test_a_duck_flies_off_when_you_come_close_and_paddles_on_otherwise() -> void:
	var d := DuckBrain.new(30.0)
	_run(d, 5.0, 999.0, false)
	assert_eq(d.state, DuckBrain.PADDLE)
	_run(d, 0.2, 20.0, false)
	assert_eq(d.state, DuckBrain.FLY)
	_run(d, 3.0, 20.0, false)
	assert_eq(d.state, DuckBrain.GONE)

func test_the_lake_map_knows_deep_water() -> void:
	var w := WorldData.load_default()
	var l := LakeLife.new()
	l.world = w
	l.load_map()
	assert_true(l.depth_at(Vector2(430, 3060)) > 80, "Mitte des Sees ist tief")
	assert_eq(l.depth_at(Vector2(100, 900)), 0, "das Mohnfeld ist kein See")
	var spot := l.random_spot(Rect2(300, 2950, 260, 200), 80)
	assert_true(spot.x >= 0.0 and l.depth_at(spot) > 80, "ein Platz im tiefen Wasser")
	l.free()

func test_lake_life_keeps_a_few_animals_near_the_view_only() -> void:
	var w := WorldData.load_default()
	var l := LakeLife.new()
	l.world = w
	var tree := Engine.get_main_loop() as SceneTree
	tree.root.add_child(l)
	l.sorted = l
	l.player = Node2D.new()
	l.add_child(l.player)
	l.player.position = Vector2(100, 900)
	for i in 400:
		l.step(0.05, Rect2(300, 2900, 180, 400))
	assert_true(l.fish_count() >= 1 and l.fish_count() <= LakeLife.MAX_FISH, "ein paar Fische: %d" % l.fish_count())
	assert_true(l.duck_count() <= LakeLife.MAX_DUCKS)
	for i in 40:
		l.step(0.05, Rect2(100, 700, 180, 400))
	assert_eq(l.fish_count(), 0, "weit weg vom See keine Fische")
	l.queue_free()

func _lake() -> LakeLife:
	var l := LakeLife.new()
	l.world = WorldData.load_default()
	l.load_map()
	return l

func test_a_duck_at_the_shallows_turns_once_and_does_not_flicker() -> void:
	# phone 0.7.0: a duck by a stone turned every frame and its face flickered left/right
	var l := _lake()
	var d := LakeLife.Duck.new()
	d.setup(l, Vector2(519, 3223), Vector2(900, 3223))        # heading east, into the shallows
	d.heading = Vector2.RIGHT
	var faces := []
	for i in 120:
		d.live(1.0 / 30.0, Vector2(-999, -999), Rect2(0, 0, 9999, 9999))
		faces.append(d.facing)
	var flips := 0
	for i in range(1, faces.size()):
		if faces[i] != faces[i - 1]:
			flips += 1
	assert_true(flips <= 1, "dreht sich einmal um, nicht hin und her: %d" % flips)
	assert_true(l.swim_depth(d.pos) >= LakeLife.DUCK_DEPTH, "bleibt im Wasser")
	d.free()
	l.free()

func test_a_fish_at_the_shallows_turns_away_and_keeps_its_course() -> void:
	var l := _lake()
	var f := LakeLife.Fish.new()
	f.setup(l, Vector2(593, 3225))
	f.circling = false
	f.heading = Vector2.RIGHT
	f.brain = FishBrain.new(30.0)
	var turns := 0
	var last := f.heading
	for i in 120:
		f.live(1.0 / 30.0, Vector2(-999, -999), false)
		if f.heading.angle_to(last) > 1.0 or f.heading.angle_to(last) < -1.0:
			turns += 1
		last = f.heading
	assert_true(turns <= 2, "wendet einmal, zappelt nicht: %d" % turns)
	assert_true(l.swim_depth(f.pos) >= LakeLife.FISH_DEPTH, "bleibt im tiefen Wasser")
	f.free()
	l.free()

func test_ducks_keep_off_stones_in_the_water() -> void:
	var l := _lake()
	var ow := Image.load_from_file(ProjectSettings.globalize_path("res://assets/world/open_water.png"))
	var stone := Vector2(-1, -1)
	for y in range(2900, 3500, 3):                             # a lake pixel that is not open water: a stone
		for x in range(100, 800, 3):
			if l.depth_at(Vector2(x, y)) > 60 and ow.get_pixel(x, y).r < 0.5:
				stone = Vector2(x, y)
				break
		if stone.x >= 0.0:
			break
	assert_true(stone.x >= 0.0, "ein Stein im See gefunden")
	assert_eq(l.swim_depth(stone), 0, "auf dem Stein schwimmt nichts")
	l.free()

func test_a_duck_taking_off_runs_over_the_water_first_then_climbs() -> void:
	# approved flight (step 30): a run over the water (wings beating low, splash), then flat climb, with a shadow
	var l := _lake()
	var d := LakeLife.Duck.new()
	d.setup(l, Vector2(430, 3060), Vector2(900, 3060))
	d.heading = Vector2.RIGHT
	d.brain.state = DuckBrain.FLY
	var start := d.pos
	var lift_in_run := 0.0
	for i in 20:                                              # 0.5 s of the run
		d.live(1.0 / 40.0, Vector2(-999, -999), Rect2(0, 0, 9999, 9999))
		lift_in_run = maxf(lift_in_run, d.lift)
	assert_eq(lift_in_run, 0.0, "auf dem Wasser, noch nicht in der Luft")
	assert_true(d.pos.x > start.x + 1.0, "läuft schon los")
	for i in 60:                                              # then 1.5 s of climbing
		d.live(1.0 / 40.0, Vector2(-999, -999), Rect2(0, 0, 9999, 9999))
	assert_true(d.lift > 8.0, "steigt: %.1f" % d.lift)
	d.free()
	l.free()

func test_the_duck_has_four_flying_and_two_running_pictures_that_differ() -> void:
	var img := TextureLoader.load_texture("res://assets/life/ente.png").get_image()
	assert_true(img.get_width() >= 10 * 28, "zehn Bilder im Blatt: %d breit" % img.get_width())
	var sums := []
	for k in range(4, 10):                                    # 4, 5 running; 6..9 the wing up, half, down, half
		var n := 0
		for y in 20:
			for x in 28:
				if img.get_pixel(k * 28 + x, y).a > 0.0:
					n += x * 31 + y * 17 + 1
		sums.append(n)
	assert_true(sums[0] != sums[1], "Anlauf: zwei verschiedene Bilder")
	assert_true(sums[2] != sums[3] and sums[3] != sums[4] and sums[2] != sums[4], "Flug: Flügel hoch, halb, runter")

func test_the_fish_come_in_sixteen_headings_three_shades_and_four_tail_phases() -> void:
	var img := TextureLoader.load_texture("res://assets/life/fisch.png").get_image()
	assert_eq([img.get_width(), img.get_height()], [176, 2112], "16 Richtungen x (3 Helligkeiten x 4 Schwanzphasen x 16 Viertelpixel), je 11 x 11")
	for row in 192:
		for col in 16:
			var n := 0
			for y in 11:
				for x in 11:
					if img.get_pixel(col * 11 + x, row * 11 + y).a > 0.0:
						n += 1
			assert_true(n >= 8 and n <= 40, "Fisch %d/%d: %d Pixel" % [col, row, n])
	var diff := 0                                    # the tail really moves: phase 1 differs from phase 0
	for y in 11:
		for x in 11:
			if img.get_pixel(x, 128 * 11 + y).a != img.get_pixel(x, 144 * 11 + y).a:
				diff += 1
	assert_true(diff >= 1, "Schwanzphasen unterscheiden sich")

func test_the_swimming_duck_is_a_drawn_picture_of_four_phases() -> void:
	var tex := TextureLoader.load_texture("res://assets/life/ente.png")
	assert_true(tex.get_width() >= 4 * 28 and tex.get_height() == 20, "Blatt 28 x 20 je Bild: %dx%d" % [tex.get_width(), tex.get_height()])
	var img := tex.get_image()
	var widths := []
	for k in 4:
		var x0 := 999
		var x1 := -1
		for x in 28:
			for y in 20:
				var c := img.get_pixel(k * 28 + x, y)
				if c.a > 0.0 and absf(c.r - 0.33) < 0.12 and c.g < 0.4 and c.b < 0.3:        # the body's browns, not the wake
					x0 = mini(x0, x)
					x1 = maxi(x1, x)
		widths.append(x1 - x0 + 1)
	for w in widths:
		assert_true(w >= 5 and w <= 9, "Körper nicht länglich: %d breit (Philip: zu lang)" % w)

func test_a_new_duck_spot_lies_outside_the_view_and_is_found_nearly_every_time() -> void:
	# phone 0.8.7: no duck on a whole round of the lake. random_spot gave the first deep point, mostly one
	# inside the view; the duck was then dropped and the next try came 14-30 s later.
	var l := _lake()
	var view := Rect2(300, 2950, 180, 400)
	var found := 0
	for i in 40:
		var p := l.random_spot(view.grow(70.0), LakeLife.DUCK_DEPTH, view)
		if p.x >= 0.0:
			found += 1
			assert_false(view.has_point(p), "ausserhalb des Bildes: %s" % p)
	assert_true(found >= 36, "fast immer ein Platz gefunden: %d von 40" % found)
	l.free()
