## Butterflies over the open meadow: a few at a time flutter in from beyond the view's edge, wander about
## their patch with sudden turns, settle on a flower now and then and slowly open and shut; come close and
## they rise and drift off. None in the dark wood, on snow, or while it rains. The look is
## tools/world/life/butterfly_art.py (approved 0.19): 7 kinds, a shadow pixel shows how high one flies.
class_name Butterflies
extends Node

const MAX := 4
const KINDS := 7                             # rows of assets/life/falter.png
const DROP := 80.0
const OPEN_WOOD := 0.25                      # WorldData.wood_at above this is wood: none there

var world: WorldData
var player: Node2D
var sorted: Node2D
var store: ChunkStore
var weather: Weather
var _list: Array = []
var _spawn_in := 2.0


func count() -> int:
	return _list.size()


## Open meadow: grass, out of the dark wood.
func meadow(p: Vector2) -> bool:
	if store != null and store.material_at(p) != GroundMat.GRASS:
		return false
	return world == null or world.wood_at(p) <= OPEN_WOOD


func step(delta: float, view: Rect2) -> void:
	var rain := weather != null and weather.raining()
	_spawn_in -= delta
	if _spawn_in <= 0.0:
		_spawn_in = randf_range(2.0, 5.0)
		if not rain and _list.size() < MAX:
			_spawn(view)
	var at := player.position if player != null else Vector2(-9999, -9999)
	for f in _list.duplicate():
		if rain:
			f.leave = true
		f.live(delta, at)
		var gone: bool = (f.flee or f.leave) and not view.grow(10.0).has_point(f.position)
		if gone or not view.grow(DROP).has_point(f.position):
			_list.erase(f)
			f.queue_free()


func _spawn(view: Rect2) -> void:
	for i in 12:
		var p := Vector2(randf_range(view.position.x - 20, view.end.x + 20),
				randf_range(view.position.y - 20, view.end.y + 20)).round()
		if view.grow(4.0).has_point(p):
			continue
		var home := p.move_toward(view.get_center(), 34.0) + Vector2(randf_range(-12, 12), randf_range(-12, 12))
		if not meadow(p) or not meadow(home):
			continue
		var kind := randi() % KINDS
		for k in (2 if randf() < 0.25 else 1):            # now and then two of a kind together
			var f := Flutter.new()
			f.setup(kind, p + Vector2(k * 6, k * 3), home, meadow)
			(sorted if sorted != null else self).add_child(f)
			_list.append(f)
		return


## One butterfly. The node stands where its shadow falls; the drawing floats `alt` px above it.
class Flutter:
	extends Node2D
	const FLEE_NEAR := 26.0
	const SHADOW := Color(0, 0, 0, 0.4)
	static var _sheet: Texture2D

	var kind := 0
	var pos := Vector2.ZERO
	var v := Vector2.ZERO
	var home := Vector2.ZERO
	var alt := 8.0
	var flee := false
	var leave := false
	var sat := false
	var _sit := 0.0
	var _settle_in := 5.0
	var _landing := Vector2.INF
	var _ph := 0.0
	var _t := 0.0
	var _age := 0.0
	var _life := 50.0
	var _ok: Callable                         # where it may settle (the meadow)

	func setup(k: int, at: Vector2, h: Vector2, ok: Callable = Callable()) -> void:
		kind = k
		pos = at
		home = h
		_ok = ok
		v = (h - at).normalized() * 8.0
		_ph = randf() * 6.0
		_settle_in = randf_range(4.0, 12.0)
		_life = randf_range(35.0, 70.0)
		position = pos.round()

	func live(delta: float, player_at: Vector2) -> void:
		_t += delta
		_age += delta
		if _age > _life:
			leave = true
		var d := pos - player_at
		if not flee and d.length() < FLEE_NEAR:
			flee = true
			sat = false
			_landing = Vector2.INF
			v = (d.normalized() if d.length() > 0.1 else Vector2.UP) * 18.0
		if sat:
			alt = maxf(0.0, alt - 12.0 * delta)
			_sit -= delta
			if _sit <= 0.0 or leave:
				sat = false
				_settle_in = randf_range(6.0, 15.0)
		elif _landing != Vector2.INF:
			var to := _landing - pos
			if to.length() < 1.0:
				pos = _landing
				_landing = Vector2.INF
				sat = true
				_sit = randf_range(3.0, 8.0)
			else:
				v = to.normalized() * 8.0
				alt = maxf(0.0, alt - 4.0 * delta)
				pos += v * delta
		else:
			_settle_in -= delta
			if _settle_in <= 0.0 and not flee and not leave:
				var spot := (pos + Vector2(randf_range(-10, 10), randf_range(-6, 6))).round()
				if not _ok.is_valid() or _ok.call(spot):
					_landing = spot
				_settle_in = randf_range(6.0, 15.0)
			if randf() < delta * 2.5:                    # a sudden turn now and then
				v = v * 0.4 + Vector2(randfn(0.0, 7.0), randfn(0.0, 7.0))
			if not flee and not leave:
				v += (home - pos) * 0.6 * delta           # stays over its patch
			elif leave and not flee:
				v += (pos - home).normalized() * 6.0 * delta
			var top := 22.0 if flee else 11.0
			if v.length() > top:
				v = v.normalized() * top
			alt = (14.0 if flee else 8.0) + 3.0 * sin(_t * 5.0 + _ph)
			if flee:                                     # turns, but always away from him
				v += (d.normalized() if d.length() > 0.1 else Vector2.UP) * 30.0 * delta
				v.y -= 6.0 * delta
			pos += v * delta
		position = pos.round()
		z_index = 20 if alt > 11.0 else 0                # high up: over the grass and low things
		queue_redraw()

	func frame() -> int:
		if sat:                                         # slow open and shut on the flower
			var u := fmod(_t, 2.4)
			return 0 if u < 1.1 else (1 if u < 1.3 or u > 2.2 else 2)
		return [0, 1, 2, 1][int((_t + _ph) * 14.0) % 4]

	func _draw() -> void:
		if _sheet == null:
			_sheet = TextureLoader.load_texture("res://assets/life/falter.png")
		var a := roundf(alt)
		if a > 1.0:
			draw_rect(Rect2(Vector2.ZERO, Vector2.ONE), SHADOW)
		draw_texture_rect_region(_sheet, Rect2(Vector2(-2, -a - 3), Vector2(5, 3)),
				Rect2(float(frame() * 5), float(kind * 3), 5, 3))
