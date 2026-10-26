## Where you tapped: a red ring that pulls together and fades, with a dark shadow pixel under it so it
## reads on snow as well as on dark wood.
class_name TapMarker
extends Node2D

const LIFE := 0.8
const RED := Color(0.78, 0.22, 0.17)
const SHADOW := Color(0.16, 0.10, 0.09)

var _life := 0.0


func _ready() -> void:
	z_index = 12


func show_at(p: Vector2) -> void:
	position = p.round()
	_life = LIFE
	queue_redraw()


func _process(delta: float) -> void:
	if _life > 0.0:
		_life -= delta
		queue_redraw()


func _draw() -> void:
	if _life <= 0.0:
		return
	var t := 1.0 - _life / LIFE
	var r := 6.0 - 4.0 * t
	var a := clampf(_life / LIFE * 2.2, 0.0, 1.0)
	var done := {}
	for k in 28:
		var ang := TAU * k / 28.0
		var q := Vector2(cos(ang) * r, sin(ang) * r * 0.65).round()   # flattened like the ground
		if done.has(q):
			continue
		done[q] = true
		draw_rect(Rect2(q + Vector2(0, 1), Vector2.ONE), Color(SHADOW, a))
	for q in done:
		draw_rect(Rect2(q, Vector2.ONE), Color(RED, a))
