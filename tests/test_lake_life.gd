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
