## The little wanderer: follows a list of waypoints, faces where it walks, breathes when it stands.
class_name Player
extends Node2D

const SPEED := 24.0                  # art px per second, a calm stroll
const COLS := 6                      # idle 0-1, walk 2-5
enum Dir { DOWN, UP, LEFT, RIGHT }

var path := PackedVector2Array()
var dir: int = Dir.DOWN
var sprite: Sprite2D
var _t := 0.0


func _ready() -> void:
	sprite = Sprite2D.new()
	sprite.texture = TextureLoader.load_texture("res://assets/char/wanderer.png")
	sprite.hframes = COLS
	sprite.vframes = 4
	sprite.centered = false
	sprite.offset = Vector2(-6, -15)    # feet at the node's position
	add_child(sprite)


func walk_to(points: PackedVector2Array) -> void:
	path = points


func is_walking() -> bool:
	return not path.is_empty()


func _process(delta: float) -> void:
	_t += delta
	var step := SPEED * delta
	while step > 0.0 and not path.is_empty():
		var target := path[0]
		var to := target - position
		var d := to.length()
		if d <= step:
			position = target
			path.remove_at(0)
			step -= d
		else:
			_face(to)
			position += to / d * step
			step = 0.0
	var col := 0
	if is_walking():
		col = 2 + int(_t * 8.0) % 4
	else:
		col = int(_t * 1.5) % 2          # slow breathing
	if sprite != null:
		sprite.frame = dir * COLS + col


func _face(v: Vector2) -> void:
	if absf(v.x) > absf(v.y) * 1.2:
		dir = Dir.RIGHT if v.x > 0.0 else Dir.LEFT
	else:
		dir = Dir.DOWN if v.y > 0.0 else Dir.UP
