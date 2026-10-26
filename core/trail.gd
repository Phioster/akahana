## Where the wanderer walked in the last moments: feeds the poppy shader, which parts the flowers there.
class_name Trail
extends RefCounted

const SIZE := 14
const EVERY := 0.12                  # seconds between remembered points
const LIFE := 1.6                    # until the lane has closed again
const LEAD := 6.0                    # px ahead of the feet: the poppies give way before he arrives

var points: Array = []               # [Vector2 pos, Vector2 dir, float age]
var _since := EVERY                  # the first step parts them at once


func update(delta: float, pos: Vector2, dir: Vector2, walking: bool) -> void:
	for p in points:
		p[2] += delta
	points = points.filter(func(p): return p[2] < LIFE)
	_since += delta
	if walking and _since >= EVERY and dir.length() > 0.01:
		_since = 0.0
		var d := dir.normalized()
		points.push_front([pos + d * LEAD, d, 0.0])
		if points.size() > SIZE:
			points.resize(SIZE)


## Smoothstep strength: full right after the step, closing softly.
static func strength(age: float) -> float:
	var t := clampf(1.0 - age / LIFE, 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)


func uniforms() -> Array:
	var pos: Array[Vector4] = []
	var k: Array[float] = []
	for i in SIZE:
		if i < points.size():
			var p: Array = points[i]
			pos.append(Vector4(p[0].x, p[0].y, p[1].x, p[1].y))
			k.append(strength(p[2]))
		else:
			pos.append(Vector4.ZERO)
			k.append(0.0)
	return [pos, k]
