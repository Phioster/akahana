## A will-o'-the-wisp: hovers near its home spot, drifts away if you come close,
## and slips back once you have gone. Not a goal, not a guide, just there.
class_name Wisp
extends Node2D

const SHY := 30.0                    # closer than this and it drifts off
const HOME := 60.0                   # never further from its spot; fades out instead
const COL := Color(0.75, 0.95, 0.9)

var anchor := Vector2.ZERO
var player: Node2D
var _t := randf() * 100.0
var _sounds: Array[AudioStreamPlayer2D] = []
var _alpha := 1.0
var _hidden := false                 # faded out, waiting until the coast is clear


func _ready() -> void:
	add_to_group("dyn_light")
	z_index = 15                                   # floats above the ground things
	# it sounds like a tiny fire: a soft crackle, and far under it a shimmer
	for pair in [["knistern", 10.0], ["schimmer", -20.0]]:      # recordings -42 / -20 -> about -32 / -40
		var a := AudioStreamPlayer2D.new()
		a.stream = SoundBank.looped(pair[0])
		a.volume_db = pair[1]
		a.max_distance = 70.0
		a.bus = AudioSetup.SOUNDS
		add_child(a)
		a.play(randf() * 5.0)
		_sounds.append(a)


func _process(delta: float) -> void:
	step(delta, player.position if player != null else Vector2(-9999, -9999))
	var v := visible_amount()
	for i in _sounds.size():
		_sounds[i].volume_db = (10.0 if i == 0 else -20.0) + linear_to_db(maxf(v, 0.001))
	queue_redraw()


func step(delta: float, pl: Vector2) -> void:
	_t += delta
	var away := position - pl
	var dist := away.length()
	if _hidden:
		if pl.distance_to(anchor) > SHY + 40.0:
			_hidden = false
			position = anchor
		return
	_alpha = minf(1.0, _alpha + delta * 0.5)
	if dist < SHY + 10.0:
		position += away.normalized() * 14.0 * delta if dist > 0.01 else Vector2(14.0 * delta, 0)
		if position.distance_to(anchor) > HOME:
			_alpha = maxf(0.0, _alpha - delta * 1.5)
			if _alpha <= 0.0:
				_hidden = true
	elif pl.distance_to(anchor) > SHY + 40.0:
		var drift := Vector2(sin(_t * 0.7) * 5.0, sin(_t * 1.1) * 3.0)
		position = position.move_toward(anchor + drift, 6.0 * delta)


func visible_amount() -> float:
	if _hidden:
		return 0.0
	return _alpha * (0.75 + 0.25 * sin(_t * 2.3))


## For the atmosphere shader: a small cold light that moves with it.
func light_data() -> Dictionary:
	return {"x": position.x, "y": position.y, "r": 22.0, "k": 0.5 * visible_amount(), "kind": "wisp"}


func _draw() -> void:
	var a := visible_amount()
	if a <= 0.0:
		return
	var o := position.round() - position          # draw on whole art pixels
	var c := COL
	c.a = a
	var d := COL
	d.a = a * 0.45
	draw_rect(Rect2(o + Vector2(-1, -1), Vector2(3, 3)), d)
	draw_rect(Rect2(o, Vector2(1, 1)), c)
	draw_rect(Rect2(o + Vector2(0, 1 + roundf(sin(_t * 3.0))), Vector2(1, 1)), d)   # a faint tail
