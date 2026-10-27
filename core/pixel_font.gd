## The game's fonts, both pre-rasterised by tools/ and rebuilt here as bitmap FontFiles, so one font
## pixel stays one art pixel: Pixel Operator 8 for short hints, Caveat as pencil handwriting for anything
## somebody wrote (the book, notes, descriptions), Klee One as pencil for the Japanese names. Godot's TTF path would draw both smooth at screen size.
class_name PixelFont
extends RefCounted

const SIZE := 8                      # Pixel Operator
const HAND_SIZE := 16                # Caveat, x-height 6 art px
const KANJI_SIZE := 15               # Klee One, the place names in Japanese (tools/gen_kanji_font.py)
const DIR := "res://assets/ui/"

static var _fonts := {}


static func get_font() -> FontFile:
	return _cached("font", SIZE)


static func hand() -> FontFile:
	return _cached("hand", HAND_SIZE)


static func kanji() -> FontFile:
	return _cached("kanji", KANJI_SIZE)


static func _cached(name: String, size: int) -> FontFile:
	if not _fonts.has(name):
		_fonts[name] = _build(name, size)
	return _fonts[name]


static func _build(name: String, size: int) -> FontFile:
	var fj := FileAccess.open(DIR + name + ".json", FileAccess.READ)
	var tex := TextureLoader.load_texture(DIR + name + ".png")
	if fj == null or tex == null:
		push_error("Schrift fehlt: " + name)
		return null
	var j: Dictionary = JSON.parse_string(fj.get_as_text())
	var f := FontFile.new()
	f.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	f.fixed_size = size
	f.fixed_size_scale_mode = TextServer.FIXED_SIZE_SCALE_INTEGER_ONLY
	var sz := Vector2i(size, 0)
	f.set_texture_image(0, sz, 0, tex.get_image())
	f.set_cache_ascent(0, size, float(j["ascent"]))
	f.set_cache_descent(0, size, float(j["descent"]))
	var glyphs: Dictionary = j["glyphs"]
	for k in glyphs:
		var g: Dictionary = glyphs[k]
		var c := int(k)                                   # bitmap fonts: glyph index = character code
		f.set_glyph_advance(0, size, c, Vector2(float(g["adv"]), 0.0))
		f.set_glyph_offset(0, sz, c, Vector2(float(g["ox"]), float(g["oy"])))
		f.set_glyph_size(0, sz, c, Vector2(float(g["w"]), float(g["h"])))
		f.set_glyph_uv_rect(0, sz, c, Rect2(float(g["x"]), float(g["y"]), float(g["w"]), float(g["h"])))
		f.set_glyph_texture_idx(0, sz, c, 0)
	return f
