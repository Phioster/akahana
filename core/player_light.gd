## How the lights of the world touch the wanderer: his robe stays darker in the glow (he would blend into
## the lit ground otherwise) and he casts a shadow away from the strongest light. The same pool formula
## as shaders/post.gdshader, without the flicker.
class_name PlayerLight

const SHADOW_MIN := 0.04   # below this much light there is no visible shadow

## lights: Dictionaries {x, y, r, k}. Returns {dim, dir, len, a}:
##   dim - colour factor for his sprite (1 = untouched), dir - unit vector away from the strongest light,
##   len - shadow length in px, a - shadow opacity.
static func at(lights: Array, pos: Vector2) -> Dictionary:
	var total := 0.0
	var best := 0.0
	var away := Vector2.DOWN
	for l in lights:
		var dv: Vector2 = pos - Vector2(float(l["x"]), float(l["y"]))
		var d := Vector2(dv.x, dv.y * 1.35).length() / float(l["r"])
		var li := float(l["k"]) / (1.0 + 4.0 * d * d) * sqrt(clampf(1.0 - d, 0.0, 1.0))
		total += li
		if li > best:
			best = li
			away = dv.normalized() if dv.length() > 0.5 else Vector2.DOWN
	var t := clampf(total, 0.0, 1.2)
	var dim := lerpf(1.0, 0.80 - 0.22 * t, clampf(t * 4.0, 0.0, 1.0))
	var ln := 6.0 + 12.0 * minf(1.0, total)
	var a := 0.0 if total < SHADOW_MIN else clampf(total * 1.8, 0.0, 1.0) * 0.85
	return {"dim": dim, "dir": away, "len": ln, "a": a}
