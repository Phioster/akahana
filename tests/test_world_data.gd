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
