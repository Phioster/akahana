## Falling snow in the north (approved 2026-11-06, build/preview/spuren/snowfall.py and snowfall_pass.py):
## three depths, the nearer ones with a small shadow down-right on the ground, a slant in the wind and gusts.
## Light at the Felstor, nearly the full fall from the middle of the north up. Drawn over the evening light
## (white on the graded snow would vanish), on a layer that follows the camera so the flakes stay in the world.
class_name Snowfall
extends Node2D

const VIEW := Vector2(180, 400)            # the flakes live in a box of one screen, wrapped round the view
# (per 10k px at full fall, fall px/s, size, colour, alpha, shadow offset = its height)
const LAYERS := [
	[55, 8.0, 1, Color8(214, 218, 226), 0.6, 0],
	[28, 14.0, 1, Color8(232, 235, 240), 0.95, 10],
	[9, 23.0, 2, Color8(246, 247, 250), 1.0, 5],
]
const BOTTOM := 1190.0                     # world y: below this no snow falls (the north's foot, the Felstor)
const FULL := 600.0                        # ... from here up it falls fully
const LIGHT := 0.5                         # share at the foot (A was half of B)

var world: WorldData
var camera_at: Callable                    # -> Vector2 top left of the view in the world
var off := false                           # inside the cave
var _flakes: Array[Dictionary] = []
var _t := 0.0


func _ready() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 11
	for L in LAYERS:
		var n := int(float(L[0]) * VIEW.x * VIEW.y / 10000.0)
		for i in n:
			_flakes.append({"p": Vector2(rng.randf() * VIEW.x, rng.randf() * VIEW.y), "v": float(L[1]) * rng.randf_range(0.8, 1.2),
					"ph": rng.randf() * TAU, "rank": rng.randf(), "size": int(L[2]), "col": L[3], "al": float(L[4]),
					"sh": int(L[5]), "drift": float(L[1]) / 12.0})


## How much of the full fall comes down at this height: none below the north, A at its foot, B up high.
static func density(y: float) -> float:
	if y > BOTTOM + 40.0:
		return 0.0
	var fade_in := clampf((BOTTOM + 40.0 - y) / 80.0, 0.0, 1.0)
	var up := clampf((BOTTOM - y) / (BOTTOM - FULL), 0.0, 1.0)
	return fade_in * lerpf(LIGHT, 1.0, up * up * (3.0 - 2.0 * up))


static func wind(t: float) -> float:
	return 7.0 + 16.0 * pow(maxf(0.0, sin(t * 0.9)), 6.0) + 1.5 * sin(t * 0.37)


func _process(delta: float) -> void:
	_t += delta
	var w := wind(_t)
	for f in _flakes:
		var p: Vector2 = f["p"]
		p.y += float(f["v"]) * delta
		p.x += (w * float(f["drift"]) + 2.0 * sin(_t * 1.7 + float(f["ph"]))) * delta
		f["p"] = Vector2(fposmod(p.x, VIEW.x), fposmod(p.y, VIEW.y))
	queue_redraw()


func _draw() -> void:
	if off or not camera_at.is_valid():
		return
	var top: Vector2 = camera_at.call()
	if density(top.y) <= 0.0 and density(top.y + VIEW.y) <= 0.0:
		return
	for f in _flakes:
		# world-anchored: the box repeats across the world, so walking moves past the flakes
		var at := top + Vector2(fposmod(f["p"].x - top.x, VIEW.x), fposmod(f["p"].y - top.y, VIEW.y))
		var d := density(at.y)
		if world != null:
			d *= 1.0 - 0.6 * world.wood_at(at)              # under dense firs less comes through
		if float(f["rank"]) >= d:
			continue
		var q := at.floor()
		var dim := 1.0
		if world != null:
			dim = 1.0 - 0.45 * world.wood_at(at)            # in the dark wood they must not glow
		if int(f["sh"]) > 0:
			draw_rect(Rect2(q + Vector2(int(f["sh"]) / 2, int(f["sh"])), Vector2.ONE), Color(0, 0, 0, 0.2))
		var c: Color = f["col"]
		c = Color(c.r * dim, c.g * dim, c.b * dim, float(f["al"]))
		if int(f["size"]) == 2:                              # round: three pixels of a 2x2
			draw_rect(Rect2(q, Vector2(2, 1)), c)
			draw_rect(Rect2(q + Vector2(0, 1), Vector2.ONE), c)
		else:
			draw_rect(Rect2(q, Vector2.ONE), c)


func visible_count() -> int:
	if not camera_at.is_valid():
		return 0
	var top: Vector2 = camera_at.call()
	var n := 0
	for f in _flakes:
		var at := top + Vector2(fposmod(f["p"].x - top.x, VIEW.x), fposmod(f["p"].y - top.y, VIEW.y))
		if float(f["rank"]) < density(at.y):
			n += 1
	return n
