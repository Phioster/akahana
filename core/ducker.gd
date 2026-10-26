## Lowers music and the ambient backdrop for a moment when something happens close by (a bird
## taking off, the book opening or closing), then lets them come back softly.
class_name Ducker
extends Node

const DEPTH := -7.0                  # dB, about half as loud
const HOLD := 0.5                    # seconds held down after the last trigger
const ATTACK := 0.12                 # seconds to go down
const RELEASE := 1.4                 # seconds to come back

static var _active: Ducker

var _hold := 0.0
var _offset := 0.0


func _enter_tree() -> void:
	_active = self


func _exit_tree() -> void:
	if _active == self:
		_active = null


static func duck(hold: float = HOLD) -> void:
	if _active != null:
		_active._hold = maxf(_active._hold, hold)


func _process(delta: float) -> void:
	var target := DEPTH if _hold > 0.0 else 0.0
	_hold = maxf(_hold - delta, 0.0)
	var rate := -DEPTH / (ATTACK if target < _offset else RELEASE)
	_offset = move_toward(_offset, target, rate * delta)
	for bus in [AudioSetup.MUSIC_TRACK, AudioSetup.BACKDROP]:
		var i := AudioServer.get_bus_index(bus)
		if i >= 0:
			AudioServer.set_bus_volume_db(i, _offset)
