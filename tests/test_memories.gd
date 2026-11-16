extends TestCase
## The table of places and regions behind the memory pages and the name scrolls.

func test_there_are_31_places_and_6_regions() -> void:
	assert_eq(Memories.PLACES.size(), 31)
	assert_eq(Memories.REGIONS.size(), 6)
	var keys := {}
	for p in Memories.PLACES:
		keys[p.key] = true
		for f in ["key", "region", "kanji", "romaji", "title", "text"]:
			assert_true(str(p[f]) != "", "%s.%s leer" % [p.key, f])
	assert_eq(keys.size(), 31, "Schlüssel eindeutig")


func test_regions_at_known_spots() -> void:
	var spots := {
		Vector2(1143, 2270): "mitte", Vector2(1129, 1552): "kogarashi", Vector2(2100, 620): "norden",
		Vector2(1870, 2550): "osten", Vector2(1860, 1750): "osten", Vector2(1262, 3150): "sueden",
		Vector2(1670, 4520): "sueden", Vector2(570, 4110): "westen", Vector2(362, 400): "norden",
		Vector2(520, 2330): "westen", Vector2(1170, 1855): "mitte",
	}
	for p in spots:
		assert_eq(Memories.region_at(p), spots[p], str(p))


func test_place_at_finds_places_and_not_the_gaps() -> void:
	assert_eq(Memories.place_at(Vector2(500, 3288)), "muehle")
	assert_eq(Memories.place_at(Vector2(1143, 2270)), "lager")
	assert_eq(Memories.place_at(Vector2(1204, 2103)), "schrein")
	assert_eq(Memories.place_at(Vector2(1600, 3000)), "")
	for p in Memories.PLACES:
		if p.room != "":
			assert_eq(p.at, Vector2.INF, "%s hat keinen Weltort" % p.key)


func test_rooms_have_their_page() -> void:
	assert_eq(Memories.place_in_room("cave"), "hoehle_innen")
	assert_eq(Memories.place_in_room("glashaus"), "gewaechshaus_innen")
	assert_eq(Memories.place_in_room("x"), "")


func test_texts_fit_three_lines() -> void:
	var f := PixelFont.hand()
	for p in Memories.PLACES:
		var lines := Memories.wrap_text(p.text)
		assert_true(lines.size() >= 1 and lines.size() <= 3, "%s: %d Zeilen" % [p.key, lines.size()])
		for l in lines:
			var w := f.get_string_size(l, HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.HAND_SIZE).x
			assert_true(w <= Memories.TEXT_W, "%s: '%s' %d px" % [p.key, l, w])


func test_every_kanji_is_in_the_font() -> void:
	var f := PixelFont.kanji()
	var all := ""
	for p in Memories.PLACES:
		all += p.kanji
	for r in Memories.REGIONS:
		all += r.kanji
	for c in all:
		assert_true(f.has_char(c.unicode_at(0)), "fehlt: " + c)
