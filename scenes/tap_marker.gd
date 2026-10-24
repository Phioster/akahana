## A small ring where you tapped, fading out in the same pixel raster as the rest.
class_name TapMarker
extends Node2D

var _life := 0.0


func show_at(p: Vector2) -> void:
	position = p.round()
	_life = 0.7
	queue_redraw()


func _process(delta: float) -> void:
	if _life > 0.0:
		_life -= delta
		queue_redraw()


func _draw() -> void:
	if _life <= 0.0:
		return
	var r := 2.0 + (0.7 - _life) * 6.0
	var a := clampf(_life / 0.7, 0.0, 1.0)
	for k in 16:
		if (k + int(_life * 20.0)) % 2 == 0:
			continue                                         # every other pixel: a dotted, dithered ring
		var ang := TAU * k / 16.0
		draw_rect(Rect2(Vector2(cos(ang) * r, sin(ang) * r * 0.6).round(), Vector2.ONE), Color(0.95, 0.92, 0.85, a))
