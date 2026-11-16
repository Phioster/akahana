## The quick pencil stroke under a memory's name (approved 2026-11-16): sets down heavy, rises a little,
## thins out and flicks past the end of the word. Never a straight ruler line.
class_name MemoryStroke
extends Control

const INK := Color(58 / 255.0, 54 / 255.0, 54 / 255.0)

var length := 40.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _draw() -> void:
	var n := int(length + 7.0)
	for i in n:
		var t := float(i) / n
		var y := 1.2 - 2.6 * t + 1.4 * t * t
		if t > 0.86:
			y -= (t - 0.86) * 14.0
		var a := 0.95 if t < 0.7 else 0.95 - (t - 0.7) * 2.2
		a *= 0.85 + 0.15 * absf(sin(i * 12.9898))              # steady grain, the same every time
		draw_rect(Rect2(i, roundf(y), 1, 1), Color(INK, maxf(a, 0.15)))
		if t > 0.06 and t < 0.55:
			draw_rect(Rect2(i, roundf(y) + 1, 1, 1), Color(INK, 0.55 * a))
