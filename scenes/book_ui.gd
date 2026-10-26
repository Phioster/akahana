## The journal: start screen, settings and (later) the memory pages are one book lying on the meadow.
## Closed with its title on the start screen; opened it shows handwritten pages; in the game it waits
## small in the bottom right corner. Everything is drawn from tools/gen_book.py, text in pencil (Caveat).
class_name BookUI
extends CanvasLayer

signal start_walking(fresh: bool)
signal camera_mode_changed(on: bool)
signal volumes_changed(music: float, sounds: float)

enum Mode { START, MAIN, SETTINGS, CLOSED, CAMERA }

const GRAPHITE := Color(58 / 255.0, 54 / 255.0, 54 / 255.0)
const FAINT := Color(120 / 255.0, 112 / 255.0, 100 / 255.0)
const CHALK := Color(236 / 255.0, 230 / 255.0, 216 / 255.0)
const BRASS := Color(186 / 255.0, 150 / 255.0, 84 / 255.0)
const UI := "res://assets/ui/"

var mode := Mode.START
var has_save := false
var music := 1.0
var sounds := 1.0

var _root: Control
var _dim: ColorRect
var _cover: Control
var _page: Control
var _content: Control
var _button: TextureButton
var _hint: Label
var _sfx: AudioStreamPlayer
var _confirm_restart := false
var _in_game := false               # opened from the game (not from the start screen)


func _ready() -> void:
	layer = 20
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(_root)
	_dim = ColorRect.new()
	_dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	var sh := Shader.new()
	sh.code = """shader_type canvas_item;
uniform float amount = 1.0;
void fragment() {
	vec2 c = (UV - 0.5) * vec2(1.0, 0.55) * 2.0;
	COLOR = vec4(0.05, 0.03, 0.03, amount * (0.32 + 0.38 * clamp(dot(c, c), 0.0, 1.0)));
}"""
	var mat := ShaderMaterial.new()
	mat.shader = sh
	_dim.material = mat
	_dim.gui_input.connect(_on_dim_input)
	_root.add_child(_dim)
	_cover = _build_cover()
	_root.add_child(_cover)
	_page = _build_page()
	_root.add_child(_page)
	_button = TextureButton.new()
	_button.texture_normal = _tex("buch_knopf")
	_button.pressed.connect(open_in_game)
	_root.add_child(_button)
	var bs := _image("buch_knopf_schatten")
	bs.name = "KnopfSchatten"
	_root.add_child(bs)
	_root.move_child(bs, _root.get_child_count() - 2)
	_hint = _label("", 8, CHALK, false)
	_hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_root.add_child(_hint)
	_sfx = AudioStreamPlayer.new()
	_sfx.bus = AudioSetup.SOUNDS
	add_child(_sfx)
	get_viewport().size_changed.connect(_layout)
	_layout()
	_apply_mode()


# ---------------------------------------------------------------- building blocks

func _tex(name: String) -> Texture2D:
	return TextureLoader.load_texture(UI + name + ".png")


func _image(name: String) -> TextureRect:
	var r := TextureRect.new()
	r.texture = _tex(name)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	return r


func _label(text: String, size: int, color: Color, hand: bool = true) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", PixelFont.hand() if hand else PixelFont.get_font())
	l.add_theme_font_size_override("font_size", PixelFont.HAND_SIZE if hand else PixelFont.SIZE)
	l.add_theme_color_override("font_color", color)
	l.add_theme_constant_override("line_spacing", -4 if hand else 0)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if size > PixelFont.HAND_SIZE:
		l.scale = Vector2(2, 2)
	return l


func _build_cover() -> Control:
	var c := Control.new()
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var s := _image("buch_schatten")
	s.position = Vector2(-4, 4)
	c.add_child(s)
	c.add_child(_image("buch_deckel"))
	var title := _label("Mohnweg", 16, BRASS)
	title.add_theme_color_override("font_shadow_color", Color(0.12, 0.08, 0.06))
	title.add_theme_constant_override("shadow_offset_x", 1)
	title.add_theme_constant_override("shadow_offset_y", 1)
	title.name = "Titel"
	c.add_child(title)
	var hint := _label("tippen zum Aufschlagen", 16, CHALK)
	hint.add_theme_color_override("font_shadow_color", Color(0.1, 0.08, 0.08))
	hint.add_theme_constant_override("shadow_offset_x", 1)
	hint.add_theme_constant_override("shadow_offset_y", 1)
	hint.name = "Hinweis"
	c.add_child(hint)
	return c


func _build_page() -> Control:
	var p := Control.new()
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var s := _image("buch_schatten_offen")
	s.position = Vector2(-4, 4)
	p.add_child(s)
	p.add_child(_image("buch_seite"))
	_content = Control.new()
	_content.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_content.position = Vector2(18, 20)
	p.add_child(_content)
	return p


func _layout() -> void:
	var v := get_viewport().get_visible_rect().size
	var cs: Vector2 = _cover.get_child(1).texture.get_size()
	_cover.position = ((v - cs) * Vector2(0.5, 0.42)).round()
	var title: Label = _cover.get_node("Titel")
	var tw := PixelFont.hand().get_string_size("Mohnweg", HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.HAND_SIZE).x * 2.0
	title.position = Vector2(13 + (cs.x - 13 - tw) * 0.5, 112).round()
	var hint: Label = _cover.get_node("Hinweis")
	var hw := PixelFont.hand().get_string_size(hint.text, HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.HAND_SIZE).x
	hint.position = Vector2((cs.x - hw) * 0.5, cs.y + 14).round()
	var ps: Vector2 = _page.get_child(1).texture.get_size()
	_page.position = ((v - ps) * Vector2(0.5, 0.45)).round()
	var bs := _button.texture_normal.get_size()
	_button.position = (v - bs - Vector2(7, 9)).round()
	var shadow: TextureRect = _root.get_node("KnopfSchatten")
	shadow.position = _button.position + Vector2(-7, -5)
	_hint.position = Vector2(0, v.y - 30)
	_hint.size = Vector2(v.x, 12)


# ---------------------------------------------------------------- pages

func _clear() -> void:
	for c in _content.get_children():
		c.queue_free()


func _heading(text: String, y: float) -> float:
	var l := _label(text, 16, GRAPHITE)
	l.position = Vector2(0, y)
	_content.add_child(l)
	var w := PixelFont.hand().get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.HAND_SIZE).x
	var line := PencilLine.new()
	line.position = Vector2(1, y + 21)
	line.length = w + 2
	_content.add_child(line)
	return y + 34


func _entry(icon: int, text: String, y: float, on_tap: Callable, x: float = 0.0) -> float:
	var e := TapArea.new()
	e.position = Vector2(x - 4, y - 2)
	e.size = Vector2(124 - x, 22)
	e.tapped.connect(on_tap)
	_content.add_child(e)
	if icon >= 0:
		var d := TextureRect.new()
		var at := AtlasTexture.new()
		at.atlas = _tex("kritzel")
		at.region = Rect2(icon * 9, 0, 9, 9)
		d.texture = at
		d.position = Vector2(x, y + 6)
		d.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_content.add_child(d)
	var l := _label(text, 16, GRAPHITE)
	l.position = Vector2(x + 13, y)
	l.name = "Text"
	e.set_meta("label", l)
	_content.add_child(l)
	return y + 26


func _slider(text: String, value: float, y: float, on_change: Callable) -> float:
	var l := _label(text, 16, GRAPHITE)
	l.position = Vector2(0, y)
	_content.add_child(l)
	var s := PencilSlider.new()
	s.position = Vector2(2, y + 20)
	s.size = Vector2(110, 10)
	s.value = value
	s.knob = _tex("mohn_knopf")
	s.changed.connect(on_change)
	_content.add_child(s)
	return y + 38


func _show_main() -> void:
	_clear()
	_confirm_restart = false
	var y := _heading("Mohnweg", 0)
	y += 4
	if _in_game:
		y = _entry(2, "weiterlaufen", y, close)
	else:
		y = _entry(2, "weiterlaufen" if has_save else "loslaufen", y, func(): _start(false))
		if has_save:
			y = _entry(3, "von vorn", y, _restart_tapped)
	y = _entry(-1, "Einstellungen", y, func(): _turn_to(Mode.SETTINGS))
	var poppy := TextureRect.new()                     # the little red poppy in front of "Einstellungen"
	poppy.texture = _tex("mohn_knopf")
	poppy.position = Vector2(1, y - 26 + 7)
	poppy.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_content.add_child(poppy)
	var tag := _label("ein Spaziergang im Mohn", 16, FAINT)
	tag.position = Vector2(0, 176)
	_content.add_child(tag)


func _show_settings() -> void:
	_clear()
	var y := _heading("Einstellungen", 0)
	y = _slider("Musik", music, y, func(v): music = v; volumes_changed.emit(music, sounds))
	y = _slider("Geräusche", sounds, y, func(v): sounds = v; volumes_changed.emit(music, sounds))
	y += 6
	if _in_game:
		y = _entry(0, "Kameramodus", y, _camera_on)
		y = _entry(1, "zum Hauptmenü", y, _to_start)
		_entry(2, "weiterlaufen", 172, close, 44)
	else:
		_entry(3, "zurück", 172, func(): _turn_to(Mode.MAIN), 44)



# ---------------------------------------------------------------- flow

func show_start(save_exists: bool) -> void:
	has_save = save_exists
	_in_game = false
	mode = Mode.START
	_apply_mode()


func open_in_game() -> void:
	_in_game = true
	_play("seite_%d" % (randi() % 3))
	mode = Mode.MAIN
	_apply_mode()
	_slide_in(_page)


func close() -> void:
	_play("buch_zu_0")
	mode = Mode.CLOSED
	_apply_mode()


## Android back button. Returns false only when there is nothing left to go back from (quit).
func back() -> bool:
	match mode:
		Mode.CAMERA:
			camera_off()
		Mode.SETTINGS:
			_turn_to(Mode.MAIN)
		Mode.MAIN:
			if _in_game:
				close()
			else:
				mode = Mode.START
				_apply_mode()
		Mode.CLOSED:
			open_in_game()
		Mode.START:
			return false
	return true


func camera_off() -> void:
	mode = Mode.CLOSED
	camera_mode_changed.emit(false)
	_apply_mode()


func _camera_on() -> void:
	mode = Mode.CAMERA
	camera_mode_changed.emit(true)
	_apply_mode()
	_hint.text = "zweimal tippen zum Beenden"
	_hint.modulate.a = 1.0
	var tw := create_tween()
	tw.tween_interval(2.5)
	tw.tween_property(_hint, "modulate:a", 0.0, 0.8)


func _start(fresh: bool) -> void:
	_in_game = true
	_play("buch_zu_0")
	mode = Mode.CLOSED
	_apply_mode()
	start_walking.emit(fresh)


func _restart_tapped() -> void:
	if not _confirm_restart:                          # ask once, right in the book, before forgetting
		_confirm_restart = true
		for c in _content.get_children():
			if c is TapArea and c.has_meta("label") and c.get_meta("label").text == "von vorn":
				c.get_meta("label").text = "wirklich von vorn?"
		return
	_start(true)


func _to_start() -> void:
	_in_game = false
	_play("seite_%d" % (randi() % 3))
	mode = Mode.START
	_apply_mode()


func _turn_to(m: int) -> void:
	_play("seite_%d" % (randi() % 3))
	mode = m
	var tw := create_tween()
	tw.tween_property(_content, "modulate:a", 0.0, 0.12)
	tw.tween_callback(_apply_mode)
	tw.tween_property(_content, "modulate:a", 1.0, 0.18)


func _on_dim_input(e: InputEvent) -> void:
	if mode == Mode.START and e is InputEventMouseButton and not e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
		_play("seite_%d" % (randi() % 3))
		mode = Mode.MAIN
		_apply_mode()
		_slide_in(_page)


func _slide_in(n: Control) -> void:
	var to := n.position
	n.position = to + Vector2(0, 40)
	n.modulate.a = 0.0
	var tw := create_tween().set_parallel()
	tw.tween_property(n, "position", to, 0.3).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.tween_property(n, "modulate:a", 1.0, 0.25)


func _apply_mode() -> void:
	var book_open := mode in [Mode.START, Mode.MAIN, Mode.SETTINGS]
	_dim.visible = book_open
	_dim.mouse_filter = Control.MOUSE_FILTER_STOP if book_open else Control.MOUSE_FILTER_IGNORE
	_cover.visible = mode == Mode.START
	_page.visible = mode in [Mode.MAIN, Mode.SETTINGS]
	_button.visible = mode == Mode.CLOSED
	_root.get_node("KnopfSchatten").visible = mode == Mode.CLOSED
	_hint.visible = mode == Mode.CAMERA
	if mode == Mode.MAIN:
		_show_main()
	elif mode == Mode.SETTINGS:
		_show_settings()


func is_blocking() -> bool:
	return mode in [Mode.START, Mode.MAIN, Mode.SETTINGS]


## Paper sounds stay small: the book is a quiet thing in the hand, not an event.
const SFX_DB := {"seite": -7.0}            # closing the book stays at full level


func _play(name: String) -> void:
	var s := SoundBank.get_stream(name)
	if s != null:
		_sfx.stream = s
		_sfx.volume_db = SFX_DB.get(name.rsplit("_", true, 1)[0], 0.0)
		_sfx.play()
