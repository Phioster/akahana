## The little wanderer: follows a list of waypoints, faces where it walks, breathes when it stands.
class_name Player
extends Node2D

const STEPS_PER_SEC := 3.0           # footfalls per second: small legs, a calm stroll
const SPEED := 15.0                  # art px per second = stride drawn in the walk frames (5 px) x pace
const COLS := 8                      # idle 0-1, walk 2-7 (six frames, two footfalls)
const WALK := 6
const CONTACT := [1, 4]              # walk frames where a foot lands
const TURN := 9.0                    # how fast he swings into a new heading: corners become small curves
enum Dir { DOWN, UP, LEFT, RIGHT }

signal stepped                       # a foot touches the ground (twice per walk cycle)

var path := PackedVector2Array()
var dir: int = Dir.DOWN
var sprite: Sprite2D
var mirror: Sprite2D                 # his reflection on the water (shaders/reflection.gdshader)
var _t := 0.0
var _last_col := -1
var _heading := Vector2.ZERO


func _ready() -> void:
	sprite = Sprite2D.new()
	sprite.texture = TextureLoader.load_texture("res://assets/char/wanderer.png")
	sprite.hframes = COLS
	sprite.vframes = 4
	sprite.centered = false
	sprite.offset = Vector2(-6, -15)    # feet at the node's position
	add_child(sprite)
	mirror = Sprite2D.new()              # below his feet, upside down: shows only on open water
	mirror.name = "Spiegelbild"
	mirror.texture = sprite.texture
	mirror.hframes = COLS
	mirror.vframes = 4
	mirror.centered = false
	mirror.flip_v = true
	mirror.offset = Vector2(-6, 1)
	mirror.z_as_relative = false
	mirror.z_index = -2                  # on the ground's water, under the reeds and grass
	var mm := ShaderMaterial.new()
	mm.shader = preload("res://shaders/reflection.gdshader")
	var ow := TextureLoader.load_texture("res://assets/world/open_water.png")
	if ow != null:
		mm.set_shader_parameter("open_water", ow)
		mm.set_shader_parameter("world_size", ow.get_size())
	mirror.material = mm
	add_child(mirror)
	# the ear: without it Godot measures sound distances in (stretched) screen pixels, not world pixels
	var ear := AudioListener2D.new()
	ear.position = Vector2(0, -8)
	add_child(ear)
	ear.make_current()
	queue_redraw()


## A soft shadow on the ground under the feet: it is what makes him stand ON the meadow.
func _draw() -> void:
	var dark := Color(0.08, 0.06, 0.07)
	for y in range(-1, 2):
		var half := 5 - absi(y) * 2
		for x in range(-half, half + 1):
			var edge := absf(float(x)) / (half + 1)
			draw_rect(Rect2(x, y, 1, 1), Color(dark, 0.42 * (1.0 - 0.6 * edge)))

func walk_to(points: PackedVector2Array) -> void:
	path = points


func is_walking() -> bool:
	return not path.is_empty()


func _process(delta: float) -> void:
	_t += delta
	var step := SPEED * delta
	if path.is_empty():
		_heading = Vector2.ZERO
	while step > 0.0 and not path.is_empty():
		var target := path[0]
		var to := target - position
		var d := to.length()
		if path.size() > 1 and d < 3.0:               # nearly there: already head for the next point
			path.remove_at(0)
			continue
		if d <= step:
			position = target
			path.remove_at(0)
			step -= d
			continue
		var want := to / d
		if _heading == Vector2.ZERO or _heading.dot(want) < -0.5:   # starting, or turning back: no curve
			_heading = want
		else:                                         # swing round into the new heading, no kink
			_heading = _heading.lerp(want, 1.0 - exp(-TURN * delta)).normalized()
		_face(_heading)
		position += _heading * step
		step = 0.0
	var col := 0
	if is_walking():
		col = 2 + int(_t * STEPS_PER_SEC / 2.0 * WALK) % WALK   # one cycle = two footfalls
	else:
		col = int(_t * 1.5) % 2          # slow breathing
	if col != _last_col and col - 2 in CONTACT:
		stepped.emit()
	_last_col = col
	if sprite != null:
		sprite.frame = dir * COLS + col
		mirror.frame = sprite.frame
		(mirror.material as ShaderMaterial).set_shader_parameter("foot_y", global_position.y)


func _face(v: Vector2) -> void:
	if absf(v.x) > absf(v.y) * 1.2:
		dir = Dir.RIGHT if v.x > 0.0 else Dir.LEFT
	else:
		dir = Dir.DOWN if v.y > 0.0 else Dir.UP
