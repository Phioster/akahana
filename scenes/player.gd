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
const HANG_STEP := 0.22              # s per phase of hanging the lantern up (4 phases, wanderer_laterne.png)

signal stepped                       # a foot touches the ground (twice per walk cycle)

var path := PackedVector2Array()
var dir: int = Dir.DOWN
var sprite: Sprite2D
var lantern: Lantern                 # lit only in the dark places (scenes/lantern.gd)
var mirror: Sprite2D                 # his reflection on the water (shaders/reflection.gdshader)
var _t := 0.0
var _hang_t := -1.0                  # >= 0 while he stands and hangs the lantern up (or takes it down)
var _hang_up := true
var _plain: Texture2D
var _hang_tex: Texture2D
var _last_col := -1
var _heading := Vector2.ZERO
var _shade := {"dim": 1.0, "dir": Vector2.DOWN, "len": 6.0, "a": 0.0}


func _ready() -> void:
	sprite = Sprite2D.new()
	sprite.texture = TextureLoader.load_texture("res://assets/char/wanderer.png")
	sprite.hframes = COLS
	sprite.vframes = 4
	sprite.centered = false
	sprite.offset = Vector2(-6, -15)    # feet at the node's position
	_plain = sprite.texture
	_hang_tex = TextureLoader.load_texture("res://assets/char/wanderer_laterne.png")
	add_child(sprite)
	lantern = Lantern.new()
	lantern.player = self
	sprite.add_child(lantern)
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
	var pd := TextureLoader.load_texture("res://assets/world/puddles.png")
	if pd != null:
		mm.set_shader_parameter("puddles", pd)
	mirror.material = mm
	add_child(mirror)
	# the ear: without it Godot measures sound distances in (stretched) screen pixels, not world pixels
	var ear := AudioListener2D.new()
	ear.position = Vector2(0, -8)
	add_child(ear)
	ear.make_current()
	queue_redraw()


## Main feeds the light on him (PlayerLight.at): robe darker in the glow, shadow away from the lamp.
func set_light(r: Dictionary) -> void:
	sprite.modulate = Color(r["dim"], r["dim"], r["dim"])
	mirror.modulate = sprite.modulate
	if absf(float(r["a"]) - float(_shade["a"])) > 0.02 or (r["dir"] - _shade["dir"]).length() > 0.03 \
			or absf(float(r["len"]) - float(_shade["len"])) > 0.4:
		_shade = r
		queue_redraw()


## A soft shadow on the ground under the feet: it is what makes him stand ON the meadow.
func _draw() -> void:
	var dark := Color(0.08, 0.06, 0.07)
	for y in range(-1, 2):
		var half := 5 - absi(y) * 2
		for x in range(-half, half + 1):
			var edge := absf(float(x)) / (half + 1)
			draw_rect(Rect2(x, y, 1, 1), Color(dark, 0.42 * (1.0 - 0.6 * edge)))
	# the cast shadow: a tapering smear from the feet away from the strongest light, on whole pixels
	var a: float = _shade["a"]
	if a > 0.0:
		var away: Vector2 = _shade["dir"]
		var ln: float = _shade["len"]
		var steps := int(ln)
		for i in steps:
			var s := float(i) / maxf(1.0, ln)
			var c := Vector2(roundf(away.x * ln * s), roundf(away.y * ln * s * 0.6))
			var hw := int(roundf(3.4 - 1.2 * s))
			var hh := 1 if s < 0.6 else 0
			for y in range(-hh, hh + 1):
				for x in range(-hw, hw + 1):
					draw_rect(Rect2(c.x + x, c.y + y, 1, 1), Color(0.05, 0.04, 0.06, a * 0.5 * (1.0 - 0.5 * s)))


func walk_to(points: PackedVector2Array) -> void:
	path = points


func is_walking() -> bool:
	return not path.is_empty() and not is_hanging()


func is_hanging() -> bool:
	return _hang_t >= 0.0


## He stops, holds the lantern up and hangs it on his staff (up) or takes it down again; the way he was
## going waits until he is done.
func hang_lantern(up: bool) -> void:
	if is_hanging() or _hang_tex == null:
		return
	_hang_up = up
	_hang_t = 0.0
	_show_sheet(true)


## 0..1 how far the hanging has come (the lantern's light follows it).
func hang_progress() -> float:
	if not is_hanging():
		return -1.0
	return clampf(_hang_t / (HANG_STEP * 4.0), 0.0, 1.0)


## Which of the four drawn phases shows now (0 = in his hand .. 3 = hung), -1 when not hanging.
func hang_phase() -> int:
	if not is_hanging():
		return -1
	var k := mini(int(_hang_t / HANG_STEP), 3)
	return k if _hang_up else 3 - k


## Where he is drawn right now, for what stands in front of him (shaders/canopy.gdshader):
## the sheet, his frame's world rect and its uv rect, and the hung lantern's world rect (size 0 if none).
func silhouette() -> Dictionary:
	var tex := sprite.texture
	var size := Vector2(tex.get_size()) / Vector2(sprite.hframes, sprite.vframes)
	var cell := Vector2(sprite.frame % sprite.hframes, sprite.frame / sprite.hframes)
	var top := global_position.round() + sprite.offset
	var lamp := Rect2()
	if lantern != null and lantern.carried and not is_hanging():
		var c := Vector2(lantern.hang_point()) + Lantern.FRAME_OFFSET + global_position.round()
		lamp = Rect2(c + Vector2(-1, -3), Vector2(3, 6))     # hook row down to the bottom knob
	return {"tex": tex, "rect": Rect2(top, size), "uv": Rect2(cell * size / Vector2(tex.get_size()),
			size / Vector2(tex.get_size())), "lamp": lamp}


func _show_sheet(hang: bool) -> void:
	for s in [sprite, mirror]:
		s.texture = _hang_tex if hang else _plain
		s.hframes = 4 if hang else COLS
	sprite.offset = Vector2(-8, -15) if hang else Vector2(-6, -15)
	mirror.offset = Vector2(-8, 1) if hang else Vector2(-6, 1)


func _process(delta: float) -> void:
	_t += delta
	if is_hanging():
		_hang_t += delta
		var k := int(_hang_t / HANG_STEP)
		if k >= 4:
			_hang_t = -1.0
			_show_sheet(false)
			lantern.carried = _hang_up
			_last_col = -1
		else:
			sprite.frame = dir * 4 + hang_phase()
			mirror.frame = sprite.frame
			sprite.position = global_position.round() - global_position
			mirror.position = sprite.position
			return
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
		# drawn on whole world pixels: the post shader reads the world per art pixel and cut a sprite
		# between two of them in half (he walks 0.25 px a frame)
		sprite.position = global_position.round() - global_position
		mirror.position = sprite.position
		(mirror.material as ShaderMaterial).set_shader_parameter("foot_y", global_position.y)


func _face(v: Vector2) -> void:
	if absf(v.x) > absf(v.y) * 1.2:
		dir = Dir.RIGHT if v.x > 0.0 else Dir.LEFT
	else:
		dir = Dir.DOWN if v.y > 0.0 else Dir.UP
