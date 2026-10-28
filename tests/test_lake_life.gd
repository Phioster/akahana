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

func test_the_duck_s_wings_beat_in_four_positions_and_low_on_the_run() -> void:
	var beat := []
	for i in 4:
		beat.append(LakeLife.Duck.wing_elevation(i * 0.075 + 0.01, false))
	assert_eq(beat, [78.0, 30.0, -55.0, 30.0], "hoch, halb, runter, halb")
	assert_eq(LakeLife.Duck.wing_elevation(4 * 0.075 + 0.01, false), 78.0, "und wieder von vorn")
	for i in 40:
		var e: float = LakeLife.Duck.wing_elevation(i * 0.01, true)
		assert_true(e >= -30.0 and e <= 40.0, "beim Anlauf flach über dem Wasser: %.0f" % e)
