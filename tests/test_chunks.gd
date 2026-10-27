extends TestCase

func test_chunk_of_maps_points_to_their_chunk() -> void:
	var g := ChunkGrid.new(3, 6)
	assert_eq(g.chunk_of(Vector2(179.9, 0)), Vector2i(0, 0))
	assert_eq(g.chunk_of(Vector2(180, 0)), Vector2i(1, 0))
	assert_eq(g.chunk_of(Vector2(0, 399.9)), Vector2i(0, 1))

func test_chunks_in_covers_a_view_and_clips_to_the_world() -> void:
	var g := ChunkGrid.new(3, 6)
	var cs := g.chunks_in(Rect2(170, 190, 180, 400))
	assert_eq(cs.size(), 2 * 3, "2×3 Kacheln")
	assert_eq(cs[0], Vector2i(0, 0))
	for c in g.chunks_in(Rect2(-500, -500, 2000, 3000)):
		assert_true(g.contains(c), "außerhalb: %s" % c)
	assert_eq(g.chunks_in(Rect2(-500, -500, 2000, 3000)).size(), 18)

func test_rect_of_round_trips() -> void:
	var g := ChunkGrid.new(3, 6)
	assert_eq(g.rect_of(Vector2i(2, 4)), Rect2(360, 800, 180, 200))
	assert_eq(g.chunk_of(g.rect_of(Vector2i(2, 4)).position), Vector2i(2, 4))

func _store() -> ChunkStore:
	var w := WorldData.load_default()
	return ChunkStore.new(ChunkGrid.new(w.chunks.x, w.chunks.y))

func test_store_answers_walkable_for_loaded_ground() -> void:
	# the cell data itself is proven equal to the generator's mask in tools/tests/test_chunks.py
	var w := WorldData.load_default()
	var s := ChunkStore.new(w.grid)
	s.load_now(w.grid.chunk_of(w.start))
	assert_true(s.walkable(w.start), "Start begehbar")
	s.load_now(Vector2i(0, 0))
	assert_false(s.walkable(Vector2(3, 3)), "Weltrand zu")

func test_unloaded_ground_is_not_walkable() -> void:
	var s := _store()
	assert_false(s.walkable(Vector2(250, 1070)))
	assert_eq(s.material_at(Vector2(250, 1070)), GroundMat.GRASS)

func test_want_forgets_what_is_not_kept() -> void:
	var s := _store()
	s.want([Vector2i(0, 0), Vector2i(1, 0)])
	assert_eq(s.loaded_count(), 2)
	s.want([])
	assert_eq(s.loaded_count(), 0)

func test_textures_arrive_through_poll() -> void:
	var s := _store()
	var c := Vector2i(1, 5)
	s.want([c])
	var t := Time.get_ticks_msec()
	while not s.is_ready(c) and Time.get_ticks_msec() - t < 4000:
		s.poll()
		OS.delay_msec(10)
	assert_true(s.is_ready(c), "Bilder geladen")
	assert_true(s.ground_tex(c) != null and s.flowers_tex(c) != null)
	assert_eq(s.flowers_tex(c).get_size(), Vector2(196, 216))

func _counter() -> Dictionary:
	return {"made": 0, "dropped": 0}

func test_activates_inside_near_and_drops_beyond_far() -> void:
	var a := Activator.new()
	var n := _counter()
	var id := a.add(Rect2(500, 500, 10, 10), 40.0, 120.0, func(): n["made"] += 1; return Node.new(),
			func(x): n["dropped"] += 1; x.free())
	a.update(Rect2(0, 0, 100, 100))
	assert_eq(a.active_count(), 0, "weit weg")
	a.update(Rect2(400, 400, 80, 80))              # 20 px away
	assert_eq(a.active_count(), 1)
	assert_true(a.node(id) != null)
	a.update(Rect2(0, 0, 100, 100))
	assert_eq(a.active_count(), 0)
	assert_eq(n["dropped"], 1)

func test_no_flapping_between_near_and_far() -> void:
	var a := Activator.new()
	var n := _counter()
	a.add(Rect2(500, 500, 10, 10), 40.0, 120.0, func(): n["made"] += 1; return Node.new(), func(x): x.free())
	for i in 100:
		var gap := 30.0 if i % 2 == 0 else 100.0       # inside near, then between near and far
		a.update(Rect2(500 - gap - 50, 500, 50, 10))
	assert_eq(n["made"], 1, "nur einmal erzeugt")
	a.clear()

func test_activator_only_visits_nearby_buckets() -> void:
	# the grown world has some 1200 things: a look at every one each frame would cost, so only those
	# whose neighbourhood the view touches are checked
	var a := Activator.new()
	for i in 1000:
		a.add(Rect2((i % 40) * 250, (i / 40) * 250, 20, 20), 40.0, 120.0, func(): return Node.new(), func(x): x.free())
	a.visited = 0
	a.update(Rect2(1000, 1000, 180, 400))
	assert_between(a.active_count(), 1, 12)
	assert_true(a.visited < 60, "nur Eintraege in der Naehe geprueft (%d)" % a.visited)
	a.update(Rect2(20000, 20000, 180, 400))
	assert_eq(a.active_count(), 0, "die Alten fallen weg, obwohl ihr Eimer nicht mehr in Sicht ist")
	a.clear()

func test_clear_drops_everything() -> void:
	var a := Activator.new()
	for i in 5:
		a.add(Rect2(i * 10, 0, 1, 1), 40.0, 120.0, func(): return Node.new(), func(x): x.free())
	a.update(Rect2(0, 0, 50, 10))
	assert_eq(a.active_count(), 5)
	a.clear()
	assert_eq(a.active_count(), 0)

func _view(at: Rect2) -> WorldView:
	var tree := Engine.get_main_loop() as SceneTree
	var v := WorldView.new()
	v.world = WorldData.load_default()
	v.store = ChunkStore.new(v.world.grid)
	v.sorted = Node2D.new()
	tree.root.add_child(v)
	v.add_child(v.sorted)
	var t := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t < 4000:
		v.update(at)
		if v.chunk_nodes() >= v.wanted_count():
			break
		OS.delay_msec(10)
	return v

func test_view_loads_only_what_the_camera_needs() -> void:
	var v := _view(Rect2(180, 400, 180, 400))
	assert_true(v.chunk_nodes() > 0, "etwas geladen")
	assert_true(v.chunk_nodes() <= 12, "höchstens 3×4 Kacheln: %d" % v.chunk_nodes())
	v.queue_free()

func test_objects_appear_only_near_the_view() -> void:
	var at := Rect2(180, 400, 180, 400)
	var v := _view(at)
	var expect := 0
	for s in v.world.sprites:
		var r := Rect2(float(s["x"]), float(s["y"]), float(s["w"]), float(s["h"]))
		if Activator._gap(r, at) < 40.0:
			expect += 1
	assert_eq(v.object_nodes(), expect)
	assert_true(expect < v.world.sprites.size(), "nicht alle Objekte")
	v.queue_free()

func test_water_moves_on_the_ground_of_a_brook_chunk() -> void:
	# the old brook runs through chunk (1, 3): its ground carries the water shader and its water map
	var v := _view(Rect2(200, 600, 180, 120))
	var c := Vector2i(1, 3)
	assert_true(v._chunks.has(c), "Kachel mit dem alten Bach geladen")
	var g: Sprite2D = v._chunks[c][0]
	var m := g.material as ShaderMaterial
	assert_true(m != null and m.shader.resource_path.ends_with("water.gdshader"), "Wasser-Shader am Boden")
	var wt: Texture2D = m.get_shader_parameter("water_tex")
	assert_true(wt != null and wt.get_size() == Vector2(180, 200), "Wasserkarte der Kachel")
	assert_eq(m.get_shader_parameter("origin"), Vector2(180, 600))
	v.queue_free()

func test_the_lake_mirrors_what_stands_on_its_shore() -> void:
	# the jetty chunk (3, 14): the still things' reflections come baked, with an apron for the ripples
	var v := _view(Rect2(540, 2880, 120, 120))
	var c := Vector2i(3, 14)
	assert_true(v._chunks.has(c), "Kachel am Steg geladen")
	var m := (v._chunks[c][0] as Sprite2D).material as ShaderMaterial
	var rt: Texture2D = m.get_shader_parameter("refl_tex")
	assert_true(rt != null and rt.get_size() == Vector2(196, 216), "Spiegelbild mit Rand")
	var img := rt.get_image()
	var any := 0
	for y in range(0, img.get_height(), 2):
		for x in range(0, img.get_width(), 2):
			if img.get_pixel(x, y).a > 0.0:
				any += 1
	assert_true(any > 50, "das Ufer spiegelt sich: %d" % any)
	var lamps: PackedVector2Array = m.get_shader_parameter("lamps")
	assert_true(lamps.size() >= 1, "die Laterne am Steg wirft ihren Lichtweg")
	v.queue_free()

func test_blades_bend_with_their_height_map() -> void:
	# grass and reeds bend from the foot (bend map per chunk, with the flowers' apron); poppies move whole
	var v := _view(Rect2(90, 2040, 180, 120))
	var c := Vector2i(0, 10)
	assert_true(v._chunks.has(c), "Kachel im Grasland geladen")
	var m := (v._chunks[c][1] as Sprite2D).material as ShaderMaterial
	var bt: Texture2D = m.get_shader_parameter("bend_tex")
	assert_true(bt != null and bt.get_size() == Vector2(196, 216), "Höhenkarte mit Rand")
	var code: String = (load("res://shaders/flowers.gdshader") as Shader).code
	assert_true(code.contains("BEND_H"))
	v.queue_free()

func test_water_shader_keeps_its_noise_small() -> void:
	# on the phone the GPU computes in 32 bit: sin() of big world coordinates turns the noise into stripes
	var code: String = (load("res://shaders/water.gdshader") as Shader).code
	assert_true(code.contains("mod(p, 289.0)"))
	assert_true(code.contains("mod(TIME, LOOP)"))

func test_flower_shader_reads_world_coordinates() -> void:
	var code: String = (load("res://shaders/flowers.gdshader") as Shader).code
	assert_true(code.contains("uniform vec2 origin"))
	assert_true(code.contains("origin + floor(UV * tex_size)"))

func test_ground_arriving_before_its_flowers_is_not_lost() -> void:
	# review: poll took the ground, then dropped it while the flowers were still loading - a hole for good
	var s := _store()
	var c := Vector2i(1, 2)
	var g := s._base(c) + "ground.png"
	var f := s._base(c) + "flowers.png"
	s._pending[c] = true
	s._images[g] = Image.create(180, 200, false, Image.FORMAT_RGB8)
	s.poll()
	s._images[f] = Image.create(196, 216, false, Image.FORMAT_RGBA8)
	s.poll()
	s._images[s._base(c) + "water.png"] = Image.create(180, 200, false, Image.FORMAT_RGBA8)
	s.poll()
	s._images[s._base(c) + "bend.png"] = Image.create(196, 216, false, Image.FORMAT_L8)
	s.poll()
	if not ResourceLoader.exists(s._base(c) + "refl.png"):    # imported (CI): an earlier test may have it loaded
		assert_false(s.is_ready(c), "das Spiegelbild fehlt noch")
	s._images[s._base(c) + "refl.png"] = Image.create(196, 216, false, Image.FORMAT_RGBA8)
	s.poll()
	assert_true(s.is_ready(c), "Kachel fertig, als alle Bilder da waren")
