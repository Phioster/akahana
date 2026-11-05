extends TestCase

func _cave() -> Cave:
	var c := Cave.new()
	c.setup(Vector2(1800, 4800))
	return c

func test_the_cave_lies_beside_the_world() -> void:
	var c := _cave()
	assert_true(c.ok, "Höhle geladen")
	assert_true(c.position.x >= 1800.0 + 200.0, "nichts von der Welt im Bild")
	assert_false(c.at_exit(c.inside_at(c.start), Vector2.UP), "hereinkommen ist nicht hinausgehen")
	assert_true(c.at_exit(c.inside_at(Vector2(c.start.x, c.size.y - 20)), Vector2.DOWN), "nicht erst ganz unten am Rand")
	assert_false(c.at_exit(c.inside_at(c.start_to), Vector2.DOWN))
	c.free()

func test_inside_he_walks_from_the_way_in_to_the_candle() -> void:
	var c := _cave()
	var way := c.find_path(c.inside_at(c.start), Vector2(float(c.light["x"]), float(c.light["y"]) + 8.0))
	assert_true(way.size() > 1, "Weg zur Kerze")
	assert_true(c.contains(way[way.size() - 1]))
	c.free()

func test_the_mouth_takes_him_in_and_the_way_out_does_not_again() -> void:
	var c := _cave()
	assert_true(c.at_mouth(c.mouth.get_center(), Vector2.UP))
	assert_true(c.at_mouth(c.mouth.end - Vector2(5, 1), Vector2.UP), "schon an der Schwelle")
	assert_false(c.at_mouth(c.mouth.get_center(), Vector2.RIGHT), "vorbeigehen holt ihn nicht hinein")
	assert_false(c.at_mouth(c.out, Vector2.UP), "hinaus ist nicht gleich wieder hinein")
	c.free()

func test_inside_the_lantern_always_hangs() -> void:
	var pl := Player.new()
	(Engine.get_main_loop() as SceneTree).root.add_child(pl)
	pl.lantern.always_dark = true
	pl.lantern._process(0.0)
	assert_true(pl.is_hanging(), "er hängt die Laterne auf")
	pl.queue_free()

func test_nothing_in_the_cave_swallows_a_tap() -> void:
	# 0.12.0: its black backdrop (a ColorRect) took every touch: he stood in the way in and could not walk
	var c := _cave()
	for n in c.get_children():
		if n is Control:
			assert_eq((n as Control).mouse_filter, Control.MOUSE_FILTER_IGNORE, "%s fängt Tippen ab" % n.name)
	c.free()
