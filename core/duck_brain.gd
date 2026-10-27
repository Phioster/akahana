## A duck on the lake: paddles about for a while and swims off out of sight; come close and it flies
## up like the birds. Pure logic, so it can be tested alone.
class_name DuckBrain
extends RefCounted

enum { PADDLE, LEAVE, FLY, GONE }
const FLY_TIME := 2.5
const SHY := 34.0

var life := 30.0
var state := PADDLE
var _t := 0.0


func _init(l: float = 30.0) -> void:
	life = l


func update(delta: float, dist: float, _wading: bool = false) -> void:
	_t += delta
	match state:
		PADDLE, LEAVE:
			if dist < SHY:
				_go(FLY)
			elif state == PADDLE and _t >= life:
				_go(LEAVE)                    # the manager lets it go once it is out of sight
		FLY:
			if _t >= FLY_TIME:
				_go(GONE)


func _go(s: int) -> void:
	state = s
	_t = 0.0
