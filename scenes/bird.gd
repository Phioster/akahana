## One small bird on the ground: pecks, hops, looks up when you come close, flies off when you come too
## close. The decisions are BirdBrain's; this only draws and moves.
class_name Bird
extends Sprite2D

const FRAME := {"stand": 0, "peck": 1, "hop": 2, "up": 3, "down": 4}

signal took_off(bird: Bird)

var brain: BirdBrain
var _t := randf() * 3.0
var _vel := Vector2.ZERO
var _was := BirdBrain.PECK


func setup(kind: String, shyness: float) -> void:
	texture = TextureLoader.load_texture("res://assets/life/vogel_%s.png" % kind)
	hframes = 5
	centered = false
	offset = Vector2(-4, -8)                 # feet at the node position, like everything y-sorted
	brain = BirdBrain.new(shyness)
	flip_h = randf() < 0.5


func step(delta: float, player: Vector2) -> void:
	_t += delta
	brain.update(delta, position.distance_to(player))
	var s := brain.state
	if s != _was:
		if s == BirdBrain.FLY:
			var away := (position - player).normalized()
			_vel = Vector2(away.x * 40.0 + randf_range(-10, 10), -48.0 + away.y * 10.0)
			flip_h = _vel.x < 0.0
			z_index = 20                     # in the air: over trees and roofs
			took_off.emit(self)
		elif s == BirdBrain.HOP:
			var d := Vector2(randf_range(-1, 1), randf_range(-0.5, 0.5)).normalized() * 3.0
			position += d.round()
			flip_h = d.x < 0.0
		_was = s
	match s:
		BirdBrain.PECK:
			frame = FRAME["peck"] if fmod(_t, 0.9) < 0.25 else FRAME["stand"]
		BirdBrain.HOP:
			frame = FRAME["hop"]
		BirdBrain.WATCH:
			frame = FRAME["stand"]
		BirdBrain.FLY:
			position += _vel * delta
			_vel.y -= 10.0 * delta
			frame = FRAME["up"] if fmod(_t, 0.16) < 0.08 else FRAME["down"]
	visible = s != BirdBrain.GONE
