## The rain (approved 2026-11-06, build/preview/regen/rain.py round 5): slanted streaks in three depths that
## really fall, small splashes on the ground, rings running out on open water. How much of it comes down is
## Weather.intensity(); where snow falls (the north) no rain. Drawn over the evening light like the snow, on a
## layer that follows the camera, the drops in a box of one screen wrapped round the view.
class_name Rain
extends Node2D

const VIEW := Vector2(180, 400)
# (share of the drops, streak px, colour, alpha, fall px/s)
const LAYERS := [
	[0.5, 3, Color8(150, 160, 175), 0.35, 160.0],
	[0.35, 4, Color8(175, 185, 200), 0.45, 205.0],
	[0.15, 6, Color8(200, 208, 222), 0.55, 250.0],
]
const DROPS := 27.0                     # per 10k px at the full shower
const SLANT := 0.3                      # px sideways per px down: the wind
const SPLASH := 30.0                    # splashes per s per 10k px of ground at the full shower
const RINGS := 110.0                    # rings per s per 10k px of water
const RING_LIFE := 0.5
const SPLASH_COL := Color8(205, 212, 222)
const RING_COL := Color8(200, 210, 222)
const SNOW_EDGE := Snowfall.BOTTOM + 40.0   # above this the snow falls: no rain

var world: WorldData
var weather: Weather
var camera_at: Callable
var off := false                         # inside the cave
var _drops: Array[Dictionary] = []
var _splashes: Array = []                # [Vector2i, frames left]
var _rings: Array = []                   # [Vector2i, age]
var _water: Image
var _rng := RandomNumberGenerator.new()


func _ready() -> void:
	_rng.seed = 23
	for i in LAYERS.size():
		var L: Array = LAYERS[i]
		var n := int(DROPS * float(L[0]) * VIEW.x * VIEW.y / 10000.0)
		for k in n:
			_drops.append({"p": Vector2(_rng.randf() * VIEW.x, _rng.randf() * VIEW.y), "layer": i, "rank": _rng.randf()})
	var t := TextureLoader.load_texture(WorldData.DIR + "open_water.png")
	if t != null:
		_water = t.get_image()


## 0 where the snow falls .. 1 a little below its edge: rain and snow never fall together.
static func reach(y: float) -> float:
	return clampf((y - SNOW_EDGE) / 60.0, 0.0, 1.0)


func strength() -> float:
	return 0.0 if weather == null or off else weather.intensity()


func is_water(q: Vector2i) -> bool:
	if _water == null or q.x < 0 or q.y < 0 or q.x >= _water.get_width() or q.y >= _water.get_height():
		return false
	return _water.get_pixelv(q).r > 0.5


func _process(delta: float) -> void:
	var r := strength()
	for d in _drops:
		var L: Array = LAYERS[int(d["layer"])]
		var v: float = L[4]
		var p: Vector2 = d["p"] + Vector2(v * SLANT, v) * delta
		d["p"] = Vector2(fposmod(p.x, VIEW.x), fposmod(p.y, VIEW.y))
	var keep: Array = []
	for s in _splashes:
		s[1] -= 1
		if s[1] > 0:
			keep.append(s)
	_splashes = keep
	keep = []
	for g in _rings:
		g[1] += delta
		if g[1] < RING_LIFE:
			keep.append(g)
	_rings = keep
	if r > 0.0 and camera_at.is_valid():
		var top: Vector2 = camera_at.call()
		var area := VIEW.x * VIEW.y / 10000.0
		for i in _count(SPLASH * r * area * delta):
			var q := Vector2i(top + Vector2(_rng.randf() * VIEW.x, _rng.randf() * VIEW.y))
			if reach(q.y) > _rng.randf() and not is_water(q):
				_splashes.append([q, 2])
		for i in _count(RINGS * r * area * delta):
			var q := Vector2i(top + Vector2(_rng.randf() * VIEW.x, _rng.randf() * VIEW.y))
			if reach(q.y) > _rng.randf() and is_water(q):
				_rings.append([q, 0.0])
	queue_redraw()


## A whole number of events for a fractional expectation, so slow rates still happen now and then.
func _count(expect: float) -> int:
	var n := int(expect)
	if _rng.randf() < expect - n:
		n += 1
	return n


func _dim(at: Vector2) -> float:
	return 1.0 - 0.45 * world.wood_at(at) if world != null else 1.0   # in the dark wood they must not glow


func _draw() -> void:
	var r := strength()
	if r <= 0.0 and _rings.is_empty() and _splashes.is_empty() or not camera_at.is_valid():
		return
	var top: Vector2 = camera_at.call()
	for g in _rings:                                   # a pixel, then a ring of 1, then 2, fading
		var at: Vector2i = g[0]
		var age: float = g[1]
		var rad := age / 0.12
		var a := maxf(0.0, 1.0 - age / RING_LIFE) * 0.5
		var c := Color(RING_COL, a)
		if rad < 0.6:
			draw_rect(Rect2(Vector2(at), Vector2.ONE), c)
		else:
			var R := roundi(rad)
			var seen := {}
			for i in 8 * R:
				var t := TAU * i / (8 * R)
				var o := Vector2i(roundi(R * cos(t)), roundi(R * sin(t) * 0.6))
				if not seen.has(o) and is_water(at + o):
					seen[o] = true
					draw_rect(Rect2(Vector2(at + o), Vector2.ONE), c)
	for s in _splashes:                                # two frames: a dot, then a hint round it
		var at: Vector2i = s[0]
		if s[1] == 2:
			draw_rect(Rect2(Vector2(at), Vector2.ONE), Color(SPLASH_COL, 0.6 * _dim(Vector2(at))))
		else:
			for o in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, -1)]:
				draw_rect(Rect2(Vector2(at + o), Vector2.ONE), Color(SPLASH_COL, 0.3 * _dim(Vector2(at))))
	if r <= 0.0:
		return
	for d in _drops:
		var at := top + Vector2(fposmod(d["p"].x - top.x, VIEW.x), fposmod(d["p"].y - top.y, VIEW.y))
		if float(d["rank"]) >= r * reach(at.y):
			continue
		var L: Array = LAYERS[int(d["layer"])]
		var col: Color = L[2]
		var dim := _dim(at)
		var c := Color(col.r * dim, col.g * dim, col.b * dim, float(L[3]))
		for j in int(L[1]):                            # the streak, slanted with the wind
			draw_rect(Rect2((at + Vector2(j * SLANT, j)).floor(), Vector2.ONE), c)


func visible_drops() -> int:
	if not camera_at.is_valid():
		return 0
	var top: Vector2 = camera_at.call()
	var r := strength()
	var n := 0
	for d in _drops:
		var at := top + Vector2(fposmod(d["p"].x - top.x, VIEW.x), fposmod(d["p"].y - top.y, VIEW.y))
		if float(d["rank"]) < r * reach(at.y):
			n += 1
	return n
