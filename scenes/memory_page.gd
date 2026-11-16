## One memory page of the book (approved preview C, 2026-11-16): the place's name in the hand with a quick
## pencil stroke under it, the romaji faint below, the sketch from paper edge to paper edge (drawn at the
## phone's resolution, not in art pixels) and up to three lines from the monk. Room below for finds later.
class_name MemoryPage
extends RefCounted

const GRAPHITE := Color(58 / 255.0, 54 / 255.0, 54 / 255.0)
const FAINT := Color(120 / 255.0, 112 / 255.0, 100 / 255.0, 0.85)
const PIC := Rect2(-6, 40, 130, 87)  # in the page's text frame (origin 18/20): page x 12 to 142
const LINES_Y := 133.0
const LINE_STEP := 13.0


static func build(into: Control, key: String) -> void:
	var p := Memories.place(key)
	if p.is_empty():
		return
	into.add_child(_label(p.title, Vector2(0, 0), GRAPHITE))
	var stroke := MemoryStroke.new()
	stroke.position = Vector2(-1, 21)
	stroke.length = PixelFont.hand().get_string_size(p.title, HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.HAND_SIZE).x
	into.add_child(stroke)
	into.add_child(_label(p.romaji, Vector2(0, 23), FAINT))
	var pic := TextureRect.new()
	pic.texture = TextureLoader.load_texture("res://assets/erinnerungen/%s.png" % key)
	pic.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	pic.stretch_mode = TextureRect.STRETCH_SCALE
	pic.position = PIC.position
	pic.size = PIC.size
	pic.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	var mul := CanvasItemMaterial.new()          # the sketch's paper melts into the page's paper
	mul.blend_mode = CanvasItemMaterial.BLEND_MODE_MUL
	pic.material = mul
	pic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	into.add_child(pic)
	var y := LINES_Y
	for line in Memories.wrap_text(p.text):
		into.add_child(_label(line, Vector2(0, y), GRAPHITE))
		y += LINE_STEP


static func _label(text: String, at: Vector2, color: Color) -> Label:
	var l := Label.new()
	l.text = text
	l.position = at
	l.add_theme_font_override("font", PixelFont.hand())
	l.add_theme_font_size_override("font_size", PixelFont.HAND_SIZE)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l
