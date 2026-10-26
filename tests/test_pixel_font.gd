extends TestCase

func test_font_measures_text_with_the_atlas_advances() -> void:
	var f := PixelFont.get_font()
	assert_true(f != null, "Schrift laedt")
	# M 8 + o 6 + h 6 = 20 art px: glyph width + 1 px gap, one font pixel per art pixel
	assert_eq(int(f.get_string_size("Moh", HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.SIZE).x), 20)

func test_font_has_the_german_letters() -> void:
	var f := PixelFont.get_font()
	for c in "äöüÄÖÜß":
		assert_true(f.has_char(c.unicode_at(0)), c)

func test_font_is_shared() -> void:
	assert_true(PixelFont.get_font() == PixelFont.get_font())

func test_handwriting_font_loads_with_umlauts_and_its_own_advances() -> void:
	var f := PixelFont.hand()
	assert_true(f != null, "Handschrift laedt")
	assert_true(f.has_char("ä".unicode_at(0)) and f.has_char("ß".unicode_at(0)), "Umlaute")
	var j: Dictionary = JSON.parse_string(FileAccess.open("res://assets/ui/hand.json", FileAccess.READ).get_as_text())
	var expect := 0
	for c in "Mohn":
		expect += int(j["glyphs"][str(c.unicode_at(0))]["adv"])
	assert_eq(int(f.get_string_size("Mohn", HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.HAND_SIZE).x), expect)
	assert_true(f != PixelFont.get_font(), "zwei verschiedene Schriften")
