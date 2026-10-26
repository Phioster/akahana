## How one small bird reacts to the wanderer. Shy birds leave early, bold ones watch first.
## Pure logic, no drawing, so it can be tested alone.
class_name BirdBrain
extends RefCounted

enum { PECK, HOP, WATCH, FLY, GONE }
const FLY_TIME := 2.5                # seconds in the air before it is out of sight
const CALM_TIME := 3.0               # how long it keeps watching after you stepped back

var shyness := 0.5                   # 0 bold .. 1 shy
var state := PECK
var _t := 0.0
var _next := 1.0


func _init(s: float = 0.5) -> void:
	shyness = s
	_next = randf_range(0.6, 2.5)


func flee_distance() -> float:
	return lerpf(16.0, 40.0, shyness)


func update(delta: float, dist: float) -> void:
	_t += delta
	match state:
		FLY:
			if _t >= FLY_TIME:
				_go(GONE)
		GONE:
			pass
		_:
			if dist < flee_distance():
				_go(FLY)
			elif dist < flee_distance() + 14.0:
				if state != WATCH:
					_go(WATCH)
			elif state == WATCH:
				if _t >= CALM_TIME:
					_go(PECK)
			elif _t >= _next:                        # busy: peck, hop a little, peck again
				_go(HOP if state == PECK and randf() < 0.4 else PECK)


func _go(s: int) -> void:
	state = s
	_t = 0.0
	_next = randf_range(0.6, 2.5) if s == PECK else 0.35
