## A will-o'-the-wisp: a small amber flame-ball (Glenn, without a face). It hovers near its home spot,
## drifts away if you come close, and slips back once you have gone. Not a goal, not a guide, just there.
class_name Wisp
extends Node2D

const WHOOSH_DB := -14.0             # recording -20 -> about -34, under the crackle
const SHY := 30.0                    # closer than this and it drifts off
const HOME := 60.0                   # never further from its spot; fades out instead
const BREATH := 2.4                  # seconds per breath: the whole flame grows and sinks back
const FLICKER := 8.0                 # flame frames per second
const EMBER := Color8(150, 52, 30)
const ORANGE := Color8(226, 110, 40)
const AMBER := Color8(255, 176, 70)
const CORE := Color8(255, 236, 170)
const RED := Color8(205, 62, 36)
# One shape: the ball runs out upward into a flame. Per column (x = -3..3) how far it is stretched up,
# drawn by hand for each flicker frame; the colour goes by distance from the centre, so the tip is red.
const STRETCH := [[0.0, 0.6, 1.4, 2.2, 1.2, 0.4, 0.0],
		[0.2, 1.0, 1.8, 1.6, 1.0, 0.5, 0.0],
		[0.0, 0.5, 1.2, 2.6, 1.6, 0.8, 0.2],
		[0.3, 1.2, 1.0, 2.0, 1.4, 0.3, 0.0],
		[0.0, 0.8, 1.8, 2.3, 0.9, 0.6, 0.1],
		[0.1, 0.5, 1.5, 1.8, 1.8, 0.9, 0.0]]
const SPARK := [0, 0, 1, 0, -1, 0]   # a loose spark above the flame in these frames (column), 0 = none

var anchor := Vector2.ZERO
var player: Node2D
var _t := randf() * 100.0
var _sounds: Array[AudioStreamPlayer2D] = []
var _alpha := 1.0
var _hidden := false                 # faded out, waiting until the coast is clear
var _whoosh: AudioStreamPlayer2D
var _last_breath := -1


func _ready() -> void:
	add_to_group("dyn_light")
	z_index = 15                                   # floats above the ground things
	# it sounds like a tiny fire: a soft crackle (recording -42 -> about -32), and with every breath a
	# soft torch-swing whoosh
	var a := AudioStreamPlayer2D.new()
	a.stream = SoundBank.looped("knistern")
	a.max_distance = 70.0
	a.bus = AudioSetup.SOUNDS
	add_child(a)
	a.play(randf() * 5.0)
	_sounds.append(a)
	_whoosh = AudioStreamPlayer2D.new()
	_whoosh.stream = SoundBank.get_stream("fackel")
	_whoosh.max_distance = 70.0
	_whoosh.bus = AudioSetup.SOUNDS
	add_child(_whoosh)


func _process(delta: float) -> void:
	step(delta, player.position if player != null else Vector2(-9999, -9999))
	var v := visible_amount()
	_sounds[0].volume_db = 10.0 + linear_to_db(maxf(v, 0.001))
	var b := int(_t / BREATH)
	if b != _last_breath:                          # a new in-breath: the flame swings up
		_last_breath = b
		if v > 0.2 and _whoosh.stream != null:
			_whoosh.volume_db = WHOOSH_DB + linear_to_db(v)
			_whoosh.pitch_scale = randf_range(0.92, 1.06)
			_whoosh.play()
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
	elif pl.distance_to(anchor) > SHY + 40.0 and dist > SHY + 20.0:
		# home only when that does not lead toward you: between "shy" (40) and this (50) it just hovers,
		# otherwise, standing between it and its home, it stepped away and back every frame
		var drift := Vector2(sin(_t * 0.7) * 5.0, sin(_t * 1.1) * 3.0)
		position = position.move_toward(anchor + drift, 6.0 * delta)


func visible_amount() -> float:
	if _hidden:
		return 0.0
	return _alpha


static func breath(t: float) -> float:
	return 0.5 + 0.5 * sin(t * TAU / BREATH)


## The flame's pixels around its centre at time t; scale 0..1 shrinks it away (no transparency).
static func flame_pixels(t: float, scale: float) -> Dictionary:
	var p := breath(t)
	var r := (2.3 + 0.9 * p) * scale
	var out := {}
	if r < 0.9:
		return out
	var f := int(t * FLICKER) % STRETCH.size()
	var top := 0
	for y in range(-12, 5):
		for x in range(-4, 5):
			var st: float = minf(STRETCH[f][x + 3], 1.5) if absi(x) <= 3 else 0.0   # capped: higher is a thin spike
			var yy := float(y) / (1.0 + st * (0.55 + 0.45 * p)) if y < 0 else float(y)
			var q := sqrt(x * x + yy * yy) / r
			if q > 1.0:
				continue
			var c := CORE if q < 0.28 else AMBER if q < 0.55 else ORANGE if q < 0.8 else (RED if y < -1 else EMBER)
			out[Vector2i(x, y)] = c
			top = mini(top, y)
	if SPARK[f] != 0 and p > 0.3 and scale > 0.8:
		out[Vector2i(SPARK[f], top - 2)] = RED             # free above the flame, never touching it
	return out


## For the atmosphere shader: a warm light that breathes with the flame.
func light_data() -> Dictionary:
	var v := visible_amount()
	return {"x": position.x, "y": position.y, "r": 24.0 + 6.0 * breath(_t), "k": (0.45 + 0.3 * breath(_t)) * v, "kind": "wisp"}


func _draw() -> void:
	var o := position.round() - position          # draw on whole art pixels
	var px := flame_pixels(_t, visible_amount())
	for q in px:
		draw_rect(Rect2(o + Vector2(q), Vector2.ONE), px[q])
