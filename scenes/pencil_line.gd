## A pencil underline: one pixel high, slightly wavy, like drawn by hand.
class_name PencilLine
extends Control

const PENCIL := Color(128 / 255.0, 122 / 255.0, 114 / 255.0)

var length := 40.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _draw() -> void:
	for x in int(length):
		draw_rect(Rect2(x, roundf(0.6 * sin(x * 0.45)), 1, 1), PENCIL)
