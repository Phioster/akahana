extends TestCase
## The animals of 0.19: squirrel, butterflies, the leaping fish.

const TREE := Vector3i(100, 200, 185)          # trunk x, foot y, crown's lower edge


func _squirrel(at: Vector2, shy := 0.5) -> Squirrels.Squirrel:
	var s := Squirrels.Squirrel.new()
	s.setup(TREE, at, shy)
	return s


func test_squirrel_eats_while_nobody_is_near() -> void:
	var s := _squirrel(Vector2(120, 206))
	var seen := {}
	for i in 60:
		s.live(0.05, Vector2(900, 900))
		seen[s.frame_name] = true
	assert_eq(s.state, Squirrels.Squirrel.EAT)
	assert_true(seen.has("eat_up") and seen.has("eat_dn"), "nagt: Kopf runter und hoch")
	assert_eq(s.facing, -1.0, "frisst mit Blick zu seinem Baum")
	s.free()


func test_squirrel_flees_up_its_tree_and_is_gone_in_the_crown() -> void:
	var s := _squirrel(Vector2(125, 207))
	var climbed_at := Vector2.INF
	var paused := false
	var last_up := 0
	for i in 400:
		s.live(0.02, Vector2(140, 210))
		if s.state == Squirrels.Squirrel.CLIMB:
			if climbed_at == Vector2.INF:
				climbed_at = s.position
			if s.up == last_up and s.up == Squirrels.Squirrel.SPURT:
				paused = true
			last_up = s.up
		if s.state == Squirrels.Squirrel.GONE:
			break
	assert_eq(climbed_at, Vector2(TREE.x + 4, TREE.y + 2), "klettert am Stamm")
	assert_true(paused, "haelt nach dem ersten Schub kurz inne")
	assert_eq(s.state, Squirrels.Squirrel.GONE, "in der Krone verschwunden")
	s.free()


func test_climbing_squirrel_is_cut_off_where_the_crown_begins() -> void:
	var s := _squirrel(Vector2(104, 202))
	s.state = Squirrels.Squirrel.CLIMB
	s.up = 0                                   # top of the picture at 202 - 12 = 190: below the crown
	assert_eq(s.hidden_rows(), 0)
	s.up = 8                                   # top at 182: 3 rows inside the leaves
	assert_eq(s.hidden_rows(), 3)
	s.free()


func test_squirrel_hops_in_bounds_not_glides() -> void:
	var s := _squirrel(Vector2(130, 207))
	var last := s.position
	for i in 200:
		s.live(0.01, Vector2(150, 210))
		var step := s.position.distance_to(last)
		assert_true(step == 0.0 or step <= Squirrels.Squirrel.HOP_STEP + 0.75, "Spruenge von 5 px, auf ganze Pixel")
		last = s.position
	s.free()


func test_trees_file_has_trunks_under_crowns() -> void:
	var sq := Squirrels.new()
	sq.load_trees()
	assert_true(sq.trees.size() > 100, "Laubbaeume gefunden")
	for t in sq.trees:
		assert_true(t.z < t.y, "Krone ueber dem Stammfuss")
	sq.free()


func test_butterfly_rises_and_flees_from_the_wanderer() -> void:
	var f := Butterflies.Flutter.new()
	f.setup(4, Vector2(50, 50), Vector2(50, 50))
	for i in 20:
		f.live(0.05, Vector2(500, 500))
	assert_false(f.flee)
	var before := f.pos.distance_to(Vector2(56, 52))
	for i in 40:
		f.live(0.05, Vector2(56, 52))
	assert_true(f.flee)
	assert_true(f.pos.distance_to(Vector2(56, 52)) > before + 10.0, "flattert davon")
	assert_true(f.alt > 9.0, "steigt hoeher")
	f.free()


func test_butterfly_settles_and_opens_slowly() -> void:
	var f := Butterflies.Flutter.new()
	f.setup(0, Vector2(50, 50), Vector2(50, 50))
	f._settle_in = 0.0
	for i in 200:
		f.live(0.05, Vector2(500, 500))
		if f.sat:
			break
	assert_true(f.sat, "setzt sich")
	var frames := []
	for i in 48:                               # 2.4 s on the flower
		f.live(0.05, Vector2(500, 500))
		frames.append(f.frame())
	assert_true(frames.count(0) > 15, "lange offen")
	assert_true(frames.has(2), "klappt zu")
	assert_eq(f.alt, 0.0)
	f.free()


func test_fish_leap_arcs_and_ends() -> void:
	var l := LakeLife.FishLeap.new()
	l.setup(Vector2(10, 10), -1)
	assert_eq(l.air_at(), Vector2.INF, "erst unter Wasser")
	var top := 0.0
	var steps := 0
	while not l.done() and steps < 1000:
		l._process(0.02)
		var a := l.air_at()
		if a != Vector2.INF:
			top = minf(top, a.y)
			assert_true(a.x <= 0.0, "springt in seine Richtung")
		steps += 1
	assert_true(l.done())
	assert_eq(top, -LakeLife.FishLeap.HIGH)
	l.free()

func test_the_last_sounds_are_there() -> void:
	for n in ["wasserfall", "tannenwind", "schneesturm", "muehle", "enten", "platsch_a_00", "platsch_b_00"]:
		assert_true(SoundBank.get_stream(n) != null, "%s fehlt" % n)
	for k in 4:
		for p in ["knarzen", "eichhorn", "ente"]:
			assert_true(SoundBank.get_stream("%s_%02d" % [p, k]) != null, "%s_%02d fehlt" % [p, k])
