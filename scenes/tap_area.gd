## An invisible area on a book page that reacts to a tap (finger lifted inside it).
class_name TapArea
extends Control

signal tapped


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_STOP


func _gui_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and e.button_index == MOUSE_BUTTON_LEFT and not e.pressed:
		if Rect2(Vector2.ZERO, size).has_point(e.position):
			tapped.emit()
			accept_event()
