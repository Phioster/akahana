## The furrow the wanderer leaves in fresh snow (approved 2026-11-06, build/preview/spuren/furrow.py): a narrow
## trodden core, a lobe pushed out at each footfall, short streaks dragged by the robe's hem, dents for the feet.
## The wind starts filling it at once, from the walls inward, slowly: gone after FILL seconds (Philip: like the
## flowers righting themselves, never a still pause first).
## Here only the record: per world pixel when it was trodden; shaders/snow_trail.gdshader draws the look.
class_name SnowTrail
extends Node2D

const TILE := 128                    # px per tile; only tiles with a trail exist
const PAD := 6                       # each tile's picture also holds this much of its neighbours (edges, heaps)
const FILL := 240.0                  # s the wind takes to fill it
const TICK := 0.25                   # s per unit of the stored time
const WRAP := 65536.0                # the time is stored in 16 bits
const CORE := 2.6
const RING := 6                      # px round him that may carry a heap of pushed-up snow
const DEPTH := 4

var mat_at: Callable                 # Vector2 -> GroundMat; only snow takes a trail
var player: Player
var _now := 0.0
var _tiles := {}                     # Vector2i -> {"core": Image, "tex": ImageTexture, "sprite": Sprite2D, "newest": float}
var _dirty := {}
var _side := 1.0
var _last := Vector2.INF
var _heading := Vector2.ZERO
var _trod := Vector2.INF            # where the last stamp went: one per pixel walked, not per frame
var _rng := RandomNumberGenerator.new()
var _sweep := 0.0
var _shader: Shader = preload("res://shaders/snow_trail.gdshader")


func _ready() -> void:
	z_index = -1                     # on the ground and its tufts, under everything standing


func _process(delta: float) -> void:
	_now += delta
	if player != null:
		var p := player.position
		if _last != Vector2.INF and p != _last and p.distance_to(_last) < 8.0:
			_heading = (p - _last).normalized()
			if _trod == Vector2.INF or p.distance_to(_trod) >= 1.0 or p.distance_to(_trod) > 8.0:
				tread(p, _heading)
				_trod = p
		elif p.distance_to(_last) >= 8.0:
			_trod = Vector2.INF                      # a journey: no furrow across the map
		_last = p
	flush()
	_sweep -= delta
	if _sweep <= 0.0:
		_sweep = 2.0
		forget_old()
	var t := fposmod(_now / TICK, WRAP)
	for k in _tiles:
		(_tiles[k]["sprite"].material as ShaderMaterial).set_shader_parameter("now", t)


## One frame of walking: the core under him and now and then the hem dragging a streak beside it.
func tread(p: Vector2, heading: Vector2) -> void:
	var side := Vector2(-heading.y, heading.x)
	var cut: Array[Vector2i] = []
	_disc(p, CORE, cut)
	for i in 3:                                # per pixel walked (the preview stamped 1.6 times as often)
		if _rng.randf() < 0.55:
			var s := -1.0 if _rng.randf() < 0.5 else 1.0
			var a := p + side * s * _rng.randf_range(2.3, 4.6) - heading * _rng.randf_range(0.0, 2.0)
			for l in _rng.randi_range(1, 3):
				cut.append(Vector2i((a - heading * l).round()))
	_stamp(cut, p)


## A foot lands: its dent, and the lobe it pushes out to its side.
func step() -> void:
	if player == null or _last == Vector2.INF:
		return
	footfall(player.position, _heading)


func footfall(p: Vector2, heading: Vector2) -> void:
	if heading == Vector2.ZERO:
		return
	var side := Vector2(-heading.y, heading.x)
	var cut: Array[Vector2i] = []
	_disc(p + side * _side * 2.4, _rng.randf_range(1.6, 2.4), cut)
	_stamp(cut, p)
	var along := Vector2i(0, 1 if heading.y > 0 else -1) if absf(heading.y) >= absf(heading.x) \
			else Vector2i(1 if heading.x > 0 else -1, 0)
	var f := Vector2i(p.round()) + Vector2i(-along.y, along.x) * int(_side)
	_side = -_side
	for w in 2:
		_dent(f - along * w)


func _disc(c: Vector2, r: float, out: Array[Vector2i]) -> void:
	var n := ceili(r)
	for dy in range(-n, n + 1):
		for dx in range(-n, n + 1):
			var q := Vector2i(c.round()) + Vector2i(dx, dy)
			if (Vector2(q) - c).length_squared() <= r * r:
				out.append(q)


func is_snow(q: Vector2i) -> bool:
	return mat_at.is_valid() and mat_at.call(Vector2(q) + Vector2(0.5, 0.5)) == GroundMat.SNOW


func _stamp(cut: Array[Vector2i], centre: Vector2) -> void:
	var born := int(fposmod(_now / TICK, WRAP))
	var hit := false
	for q in cut:
		if is_snow(q):
			_put(q, born, 255, -1)
			hit = true
	if not hit:
		return
	var c := Vector2i(centre.round())
	for dy in range(-RING, RING + 1):          # where a heap may lie: snow beside the furrow
		for dx in range(-RING, RING + 1):
			var q := c + Vector2i(dx, dy)
			if raw(q) < 255 and is_snow(q):
				_put(q, born, 128, 0)
	for dy in range(-RING - DEPTH, RING + DEPTH + 1):
		for dx in range(-RING - DEPTH, RING + DEPTH + 1):
			var q := c + Vector2i(dx, dy)
			if raw(q) == 255:
				_set_depth(q, depth_at(q))


## How far in from the furrow's wall a pixel lies (0 at the wall): the wind fills the walls first.
func depth_at(q: Vector2i) -> int:
	var d := DEPTH
	for dir in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
		for r in range(1, d + 1):
			if raw(q + dir * r) != 255:
				d = r - 1
				break
	return d


func _dent(q: Vector2i) -> void:
	if raw(q) == 255:
		var px := _pixel(q)
		var b := int(round(px.b8)) | 1
		_write(q, Color8(px.r8, px.g8, b, 255))


## The stored alpha at a world pixel: 0 nothing, 128 snow beside the furrow, 255 furrow.
func raw(q: Vector2i) -> int:
	var t: Dictionary = _tiles.get(_tile_of(q), {})
	if t.is_empty():
		return 0
	var l := q - _tile_of(q) * TILE
	return (t["core"] as Image).get_pixel(l.x, l.y).a8


func _pixel(q: Vector2i) -> Color:
	var t: Dictionary = _tiles.get(_tile_of(q), {})
	if t.is_empty():
		return Color(0, 0, 0, 0)
	var l := q - _tile_of(q) * TILE
	return (t["core"] as Image).get_pixel(l.x, l.y)


func _put(q: Vector2i, born: int, a: int, depth: int) -> void:
	var px := _pixel(q)
	var b := px.b8 if depth < 0 else depth * 2
	if a == 255 and px.a8 < 255:
		b = 0
	_write(q, Color8(born >> 8, born & 255, b, a))


func _set_depth(q: Vector2i, d: int) -> void:
	var px := _pixel(q)
	_write(q, Color8(px.r8, px.g8, d * 2 | (px.b8 & 1), px.a8))


func _write(q: Vector2i, c: Color) -> void:
	var k := _tile_of(q)
	if not _tiles.has(k):
		_make_tile(k)
	var t: Dictionary = _tiles[k]
	var l := q - k * TILE
	(t["core"] as Image).set_pixel(l.x, l.y, c)
	t["newest"] = _now
	_dirty[k] = true
	# near an edge: the neighbour's picture holds this pixel in its padding
	for dy in [-1, 0, 1]:
		for dx in [-1, 0, 1]:
			if (dx == 0 or (dx < 0 and l.x < PAD) or (dx > 0 and l.x >= TILE - PAD)) \
					and (dy == 0 or (dy < 0 and l.y < PAD) or (dy > 0 and l.y >= TILE - PAD)):
				var n := k + Vector2i(dx, dy)
				if _tiles.has(n):
					_dirty[n] = true


static func _tile_of(q: Vector2i) -> Vector2i:
	return Vector2i(floori(float(q.x) / TILE), floori(float(q.y) / TILE))


func _make_tile(k: Vector2i) -> void:
	var core := Image.create_empty(TILE, TILE, false, Image.FORMAT_RGBA8)
	var pic := Image.create_empty(TILE + 2 * PAD, TILE + 2 * PAD, false, Image.FORMAT_RGBA8)
	var sp := Sprite2D.new()
	sp.centered = false
	sp.position = Vector2(k * TILE)
	sp.region_enabled = true
	sp.region_rect = Rect2(PAD, PAD, TILE, TILE)
	sp.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var m := ShaderMaterial.new()
	m.shader = _shader
	m.set_shader_parameter("origin", Vector2(k * TILE - Vector2i(PAD, PAD)))
	m.set_shader_parameter("fill", FILL / TICK)
	m.set_shader_parameter("wrap", WRAP)
	sp.material = m
	var tex := ImageTexture.create_from_image(pic)
	sp.texture = tex
	m.set_shader_parameter("trail", tex)
	add_child(sp)
	_tiles[k] = {"core": core, "pic": pic, "tex": tex, "sprite": sp, "newest": _now}
	for dy in [-1, 0, 1]:                       # its padding shows what lies at the neighbours' edges
		for dx in [-1, 0, 1]:
			if _tiles.has(k + Vector2i(dx, dy)):
				_dirty[k + Vector2i(dx, dy)] = true


## Pictures of the changed tiles: own core plus the neighbours' edges.
func flush() -> void:
	for k in _dirty:
		if not _tiles.has(k):
			continue
		var t: Dictionary = _tiles[k]
		var pic: Image = t["pic"]
		pic.fill(Color(0, 0, 0, 0))
		for dy in [-1, 0, 1]:
			for dx in [-1, 0, 1]:
				var n: Dictionary = _tiles.get(k + Vector2i(dx, dy), {})
				if n.is_empty():
					continue
				var src := Rect2i(0, 0, TILE, TILE).intersection(
						Rect2i(Vector2i(-dx, -dy) * TILE - Vector2i(PAD, PAD), Vector2i(TILE + 2 * PAD, TILE + 2 * PAD)))
				pic.blit_rect(n["core"], src, src.position + Vector2i(dx, dy) * TILE + Vector2i(PAD, PAD))
		(t["tex"] as ImageTexture).update(pic)
	_dirty.clear()


## Tiles whose newest trace the wind has long filled are let go.
func forget_old() -> void:
	for k in _tiles.keys():
		if _now - float(_tiles[k]["newest"]) > FILL + 2.0:
			_tiles[k]["sprite"].queue_free()
			_tiles.erase(k)


func tile_count() -> int:
	return _tiles.size()


func advance(seconds: float) -> void:
	_now += seconds
