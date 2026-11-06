## When it rains (approved 2026-11-06, build/preview/regen/rain.py round 5): now and then a shower passes,
## starting as a drizzle, swelling to a shower and dying away again - by time, not by place (Philip).
class_name Weather
extends RefCounted

const DRY_MIN := 15.0 * 60.0           # s between showers
const DRY_MAX := 25.0 * 60.0
const SHOWER_MIN := 3.0 * 60.0         # s a shower lasts
const SHOWER_MAX := 5.0 * 60.0
const SWELL := 0.4                     # share of the shower it takes to swell ...
const FADE := 0.3                      # ... and to die away
const WET_HOLD := 4.0 * 60.0           # s the ground stays soaked after a shower (wet.py round 3) ...
const WET_DRY := 3.0 * 60.0            # ... then it dries, the puddles shrinking from their rims

var _rng := RandomNumberGenerator.new()
var _t := 0.0
var _start := 0.0                      # when the next (or current) shower begins
var _length := 0.0
var _wet := 0.0
var _since := 0.0                      # s since it last rained


func _init(seed_value: int = -1) -> void:
	if seed_value >= 0:
		_rng.seed = seed_value
	else:
		_rng.randomize()
	_plan(_rng.randf_range(DRY_MIN, DRY_MAX))


func _plan(dry: float) -> void:
	_start = _t + dry
	_length = _rng.randf_range(SHOWER_MIN, SHOWER_MAX)


func step(delta: float) -> void:
	_t += delta
	if _t > _start + _length:
		_plan(_rng.randf_range(DRY_MIN, DRY_MAX))
	var i := intensity()
	if i > 0.0:
		_wet = maxf(_wet, i)               # the puddles fill as the shower swells
		_since = 0.0
	else:
		_since += delta
		if _since > WET_HOLD:
			_wet = maxf(0.0, _wet - delta / WET_DRY)


## 0 dry .. 1 soaked: how wet the ground is, the rain now or a while ago.
func wetness() -> float:
	return _wet


## 0 dry .. 1 the full shower.
func intensity() -> float:
	var k := (_t - _start) / _length
	if k <= 0.0 or k >= 1.0:
		return 0.0
	var up := clampf(k / SWELL, 0.0, 1.0)
	var down := clampf((1.0 - k) / FADE, 0.0, 1.0)
	var e := minf(up, down)
	return e * e * (3.0 - 2.0 * e)


func raining() -> bool:
	return intensity() > 0.0


## Testing aid: a shower right now, or, while one passes, let it die away from where it stands.
func toggle_now() -> void:
	if raining():
		var k := 1.0 - FADE * intensity()          # the point in its fading with about the same strength
		_start = _t - k * _length
	else:
		_start = _t
		_length = SHOWER_MAX
