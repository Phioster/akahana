extends TestCase

func test_world_loads_with_sprites_lights_and_mask() -> void:
	var w := WorldData.load_default()
	assert_true(w != null, "world.json")
	if w == null:
		return
	assert_eq(w.chunks * ChunkGrid.SIZE, Vector2i(w.width, w.height))
	assert_true(w.sprites.size() > 20, "Objekte")
	assert_true(w.lights.size() >= 5, "Lichter")

func test_start_point_is_walkable() -> void:
	var w := WorldData.load_default()
	var s := ChunkStore.new(w.grid)
	s.load_now(w.grid.chunk_of(w.start))
	assert_true(s.walkable(w.start), "Start %s" % w.start)

func test_every_sprite_file_exists_and_fits_its_frames() -> void:
	var w := WorldData.load_default()
	for s in w.sprites:
		var path := "res://assets/world/sprites/%s.png" % s["name"]
		var tex := TextureLoader.load_texture(path)
		assert_true(tex != null, path)
		if tex != null:
			assert_eq(tex.get_width(), int(s["w"]) * int(s["frames"]), "Breite " + path)

func test_fireflies_load_from_world() -> void:
	var w := WorldData.load_default()
	assert_true(w.fireflies.size() > 5, "Glühwürmchen-Schwärme im Süden")
	var s: Dictionary = w.fireflies[0]
	assert_true(s.has("x") and s.has("y") and s["flies"].size() > 3)

func test_a_swarm_glows_and_moves() -> void:
	var w := WorldData.load_default()
	var f := Fireflies.new()
	f.setup(w.fireflies[0])
	var a := f.state(0.0)
	var b := f.state(3.0)
	assert_eq(a.size(), b.size())
	assert_true(a[0] != b[0], "die Fliegen ziehen ihre Bahn")
	var lit := 0
	for t in 40:
		for p in f.state(t * 0.25):
			if p.z > 0.45:
				lit += 1
	assert_true(lit > 0, "manche glühen auf")
	f.free()

func test_a_wanderer_in_front_of_a_lantern_is_drawn_over_its_light_disc() -> void:
	# phone 0.8.2: at the jetty's end the wanderer vanished: the lantern's sprite (a disc of lit ground round
	# the post) was sorted by its box bottom, 8 px below the post - it was drawn over him
	var w := WorldData.load_default()
	var found := 0
	for s in w.sprites:
		if int(s["frames"]) != 64 or int(s["w"]) != 73:
			continue                                       # the wooden lanterns: 25 x 30 art + a 24 px margin
		var post_x: float = float(s["x"]) + 36.0
		var post_foot := 0
		for l in w.lights:
			if str(l["kind"]) == "lantern" and absf(float(l["x"]) - post_x) < 3.0:
				post_foot = roundi(float(l["y"]) + 11.5)    # the light sits 10.5 px above the post's foot
		if post_foot == 0:
			continue
		found += 1
		assert_true(int(s["foot"]) <= post_foot + 2, "Laterne bei x=%d: Fuß %d, Pfosten %d" % [int(post_x), int(s["foot"]), post_foot])
	assert_true(found >= 2, "die Holzlaternen gefunden: %d" % found)
