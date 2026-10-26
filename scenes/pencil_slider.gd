## A volume slider drawn in pencil: a faint line, the set part traced darker, a small poppy to drag.
class_name PencilSlider
extends Control

signal changed(value: float)

const PENCIL := Color(128 / 255.0, 122 / 255.0, 114 / 255.0)
const INK := Color(62 / 255.0, 46 / 255.0, 38 / 255.0)

var value := 1.0
var knob: Texture2D
var _drag := false


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP


func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT:
		_drag = e.pressed
		if e.pressed:
			_set_from(e.position.x)
		accept_event()
	elif e is InputEventMouseMotion and _drag:
		_set_from(e.position.x)
		accept_event()


func _set_from(x: float) -> void:
	var v := clampf(x / size.x, 0.0, 1.0)
	v = roundf(v * 20.0) / 20.0                         # 5 % steps: easy to hit with a finger
	if v != value:
		value = v
		changed.emit(value)
		queue_redraw()


func _draw() -> void:
	var y := size.y * 0.5
	var k := int(size.x * value)
	for x in int(size.x):
		draw_rect(Rect2(x, roundf(y + 0.5 * sin(x * 0.45 + 1.0)), 1, 1), INK if x < k else PENCIL)
	if knob != null:
		draw_texture(knob, Vector2(k - 3, roundf(y) - 3))
