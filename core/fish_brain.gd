## How one fish in the lake behaves: it rises into sight, swims a few rounds or off in one direction, and
## sinks away again; wade close and it darts off. Pure logic, no drawing, so it can be tested alone.
class_name FishBrain
extends RefCounted

enum { RISE, SWIM, SINK, DART, GONE }
const RISE_TIME := 0.8
const SINK_TIME := 0.8
const DART_TIME := 0.6
const SHY := 28.0                    # wading closer than this frightens it

var life := 10.0                     # seconds it stays in sight
var state := RISE
var _t := 0.0


func _init(l: float = 10.0) -> void:
	life = l


## 0..1 how much of it shows: rising, swimming, sinking.
func shown() -> float:
	match state:
		RISE: return clampf(_t / RISE_TIME, 0.0, 1.0)
		SINK: return 1.0 - clampf(_t / SINK_TIME, 0.0, 1.0)
		DART: return 1.0 - clampf(_t / DART_TIME, 0.0, 1.0)
		GONE: return 0.0
	return 1.0


func update(delta: float, dist: float, wading: bool) -> void:
	_t += delta
	if state in [RISE, SWIM] and wading and dist < SHY:
		_go(DART)
		return
	match state:
		RISE:
			if _t >= RISE_TIME:
				_go(SWIM)
		SWIM:
			if _t >= life:
				_go(SINK)
		SINK:
			if _t >= SINK_TIME:
				_go(GONE)
		DART:
			if _t >= DART_TIME:
				_go(GONE)


func _go(s: int) -> void:
	state = s
	_t = 0.0
