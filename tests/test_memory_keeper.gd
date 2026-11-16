extends TestCase
## The keeper: first visits of regions and places, in the order found.

func _keeper() -> MemoryKeeper:
	var k := MemoryKeeper.new()
	k.save = SaveData.new()
	return k


func test_first_visit_brings_region_then_place() -> void:
	var k := _keeper()
	var ev := k.step(Vector2(1143, 2270), "", 2.0)
	assert_eq(ev, [{"kind": "region", "key": "mitte"}, {"kind": "place", "key": "lager"}])


func test_second_visit_brings_nothing() -> void:
	var k := _keeper()
	k.step(Vector2(1143, 2270), "", 2.0)
	assert_eq(k.step(Vector2(1143, 2270), "", 2.0), [])


func test_found_keeps_the_order() -> void:
	var k := _keeper()
	k.step(Vector2(500, 3288), "", 0.25)
	k.step(Vector2(1143, 2270), "", 0.25)
	assert_eq(k.save.found, PackedStringArray(["muehle", "lager"]))


func test_region_needs_dwell() -> void:
	var k := _keeper()
	k.step(Vector2(1143, 2270), "", 2.0)                       # mitte seen
	assert_eq(k.step(Vector2(1350, 1450), "", 0.5), [])       # kogarashi for a moment
	k.step(Vector2(1350, 1700), "", 0.5)                       # back in mitte
	assert_eq(k.step(Vector2(1350, 1450), "", 0.5), [], "Zähler beginnt neu")
	assert_false(k.save.regions_seen.has("kogarashi"))
	assert_eq(k.step(Vector2(1350, 1450), "", 1.2), [{"kind": "region", "key": "kogarashi"}])


func test_room_gives_its_page_and_no_outside_place() -> void:
	var k := _keeper()
	var ev := k.step(Vector2(1143, 2270), "cave", 2.0)
	assert_eq(ev, [{"kind": "place", "key": "hoehle_innen"}])


func test_new_place_sets_the_bookmark() -> void:
	var k := _keeper()
	k.save.bookmark = false
	k.step(Vector2(500, 3288), "", 0.25)
	assert_true(k.save.bookmark)


func test_travel_to_the_mill_writes_the_page() -> void:
	# main.gd hands the keeper's events on: scroll, book, bookmark (the game itself is too big to load here)
	var m: Node2D = load("res://scenes/main.gd").new()
	var tree := Engine.get_main_loop() as SceneTree
	m.book = BookUI.new()
	tree.root.add_child(m.book)
	m.scroll = NameScroll.new()
	m.keeper.save = m.save
	m.book.mode = BookUI.Mode.CLOSED
	m._apply_memory_events(m.keeper.step(Vector2(500, 3288), "", 2.0))
	assert_true(m.save.found.has("muehle"))
	assert_eq(m.book.memories, PackedStringArray(["muehle"]))
	assert_true(m.book.has_bookmark(), "Lesezeichen am Buch")
	assert_eq(m.scroll.showing(), Memories.region("westen").kanji, "erst das Gebiet")
	m.book.queue_free()
	m.scroll.free()
	m.free()


func test_start_at_the_camp_brings_the_region_first() -> void:
	# the game ticks every 0.25 s: a place in a region not yet seen brings that region's scroll first
	var k := _keeper()
	var ev := k.step(Vector2(1143, 2270), "", 0.25)
	assert_eq(ev, [{"kind": "region", "key": "mitte"}, {"kind": "place", "key": "lager"}])


func test_memories_wait_while_the_book_is_open_or_the_camera_looks() -> void:
	var m: Node2D = load("res://scenes/main.gd").new()
	var tree := Engine.get_main_loop() as SceneTree
	m.book = BookUI.new()
	tree.root.add_child(m.book)
	m.book.mode = BookUI.Mode.CLOSED
	assert_true(m._memories_allowed(), "Buch zu: ja")
	m.book.mode = BookUI.Mode.MAIN
	assert_false(m._memories_allowed(), "Buch offen: nein")
	m.book.mode = BookUI.Mode.CLOSED
	m._camera_mode = true
	assert_false(m._memories_allowed(), "Kameramodus: nein")
	m.book.queue_free()
	m.free()
