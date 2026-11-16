extends TestCase
## The hanging name scroll: one name after another, never in the way.

func test_names_come_one_after_another() -> void:
	var s := NameScroll.new()
	s.show_name("赤花の原", "Akahana-no-hara")
	s.show_name("焚き火", "Takibi")
	assert_eq(s.showing(), "赤花の原")
	s.advance(NameScroll.ROLL * 2.0 + NameScroll.HOLD + 0.1)
	assert_eq(s.showing(), "焚き火")
	s.advance(NameScroll.ROLL * 2.0 + NameScroll.HOLD + 0.1)
	assert_eq(s.showing(), "")
	s.free()


func test_scroll_lets_taps_through() -> void:
	var s := NameScroll.new()
	assert_eq(s.mouse_filter, Control.MOUSE_FILTER_IGNORE)
	s.free()


func test_scroll_stays_on_screen() -> void:
	var longest := ""
	var romaji := ""
	for p in Memories.PLACES:
		if p.kanji.length() > longest.length():
			longest = p.kanji
			romaji = p.romaji
	var r := NameScroll.bounds(longest, romaji)
	assert_true(Rect2(0, 0, 180, 400).encloses(r), str(r))
	var wide := ""
	for p in Memories.PLACES:
		if p.romaji.length() > wide.length():
			wide = p.romaji
	r = NameScroll.bounds("火", wide)
	assert_true(Rect2(0, 0, 180, 400).encloses(r), "Schild " + str(r))
