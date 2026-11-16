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
