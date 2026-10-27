## The life on the lake: fish rising here and there under the surface, swimming a few rounds or off in one
## direction and sinking away again, and now and then a few ducks paddling about. Nothing has a fixed
## place: they turn up at random spots near the view and go again. Wade close and the fish dart off;
## come close and the ducks fly up like the birds. The look is tools/world/south/fish_anim.py.
class_name LakeLife
extends Node2D

const MAP := "res://assets/world/lake.png"   # the lake's depth at half size (tools/world/gen_south.py)
const MAX_FISH := 3
const MAX_DUCKS := 3
const FISH_DEPTH := 80                       # fish keep to the open water, not the shallow rim
const DUCK_DEPTH := 40
const DROP := 200.0                          # beyond this from the view an animal is let go

var world: WorldData
var player: Node2D
var sorted: Node2D
var store: ChunkStore                        # to tell when the wanderer is wading
var _map: Image
var _fish: Array = []
var _ducks: Array = []
var _fish_in := 1.0
var _ducks_in := 6.0
var _wings: AudioStreamPlayer2D


func _ready() -> void:
	if _map == null:
		load_map()
	_wings = AudioStreamPlayer2D.new()
	_wings.bus = AudioSetup.SOUNDS
	_wings.max_distance = 140.0
	add_child(_wings)


func load_map() -> void:
	var t := TextureLoader.load_texture(MAP)
	_map = t.get_image() if t != null else null


func depth_at(p: Vector2) -> int:
	if _map == null:
		return 0
	var x := int(p.x / 2.0)
	var y := int(p.y / 2.0)
	if x < 0 or y < 0 or x >= _map.get_width() or y >= _map.get_height():
		return 0
	return int(round(_map.get_pixel(x, y).r * 255.0))


## A random point at least min_depth deep inside r, or (-1, -1) if none was found.
func random_spot(r: Rect2, min_depth: int) -> Vector2:
	for i in 24:
		var p := Vector2(randf_range(r.position.x, r.end.x), randf_range(r.position.y, r.end.y))
		if depth_at(p) >= min_depth:
			return p.round()
	return Vector2(-1, -1)


func fish_count() -> int:
	return _fish.size()


func duck_count() -> int:
	return _ducks.size()


func _wading() -> bool:
	return store != null and player != null and store.material_at(player.position) == GroundMat.WET


func step(delta: float, view: Rect2) -> void:
	var near := view.grow(30.0)
	_fish_in -= delta
	if _fish_in <= 0.0:
		_fish_in = randf_range(1.5, 4.5)
		if _fish.size() < MAX_FISH:
			var p := random_spot(near, FISH_DEPTH)
			if p.x >= 0.0:
				var f := Fish.new()
				f.setup(self, p)
				add_child(f)
				_fish.append(f)
	_ducks_in -= delta
	if _ducks_in <= 0.0:
		_ducks_in = randf_range(14.0, 30.0)
		if _ducks.is_empty():                        # a small group comes paddling in from out of sight
			var p := random_spot(view.grow(70.0), DUCK_DEPTH)
			if p.x >= 0.0 and not view.has_point(p):
				for i in randi_range(1, MAX_DUCKS):
					var d := Duck.new()
					d.setup(self, p + Vector2(randf_range(-8, 8), randf_range(-4, 4)), view.get_center())
					(sorted if sorted != null else self).add_child(d)
					_ducks.append(d)
	var wading := _wading()
	var at := player.position if player != null else Vector2(-9999, -9999)
	for f in _fish.duplicate():
		f.live(delta, at, wading)
		if f.brain.state == FishBrain.GONE or not view.grow(DROP).has_point(f.position):
			_fish.erase(f)
			f.queue_free()
	for d in _ducks.duplicate():
		var was: int = d.brain.state
		d.live(delta, at, view)
		if was != DuckBrain.FLY and d.brain.state == DuckBrain.FLY:
			_wings.stream = SoundBank.get_stream("fluegel_0")
			_wings.volume_db = -2.0
			_wings.position = d.position
			_wings.pitch_scale = randf_range(0.85, 0.95)   # a heavier bird than the sparrows
			_wings.play()
		var out := not view.grow(20.0).has_point(d.position)
		if d.brain.state == DuckBrain.GONE or (d.brain.state == DuckBrain.LEAVE and out) \
				or not view.grow(DROP).has_point(d.position):
			_ducks.erase(d)
			d.queue_free()


## One fish: a calm, slightly lighter spindle just under the surface, a faint bow wave at its head.
class Fish:
	extends Node2D
	const BODY := Color8(66, 90, 98)
	const BOW := Color8(85, 112, 121)
	const GLINT := Color8(127, 152, 156)
	const RING := Color8(96, 122, 130)
	var brain: FishBrain
	var lake: LakeLife
	var length := 8.0
	var heading := Vector2.RIGHT
	var speed := 6.0
	var circling := false
	var centre := Vector2.ZERO
	var radius := 10.0
	var _a := 0.0
	var _t := 0.0

	func setup(l: LakeLife, at: Vector2) -> void:
		lake = l
		brain = FishBrain.new(randf_range(6.0, 16.0))
		position = at
		length = float(randi_range(7, 9))
		heading = Vector2.RIGHT.rotated(randf() * TAU)
		circling = randf() < 0.5                     # a few rounds, or off in one direction
		radius = randf_range(8.0, 15.0)
		centre = at - heading.orthogonal() * radius
		_a = (at - centre).angle()
		speed = randf_range(4.0, 7.0)
		z_index = -1

	func live(delta: float, player_at: Vector2, wading: bool) -> void:
		_t += delta
		brain.update(delta, position.distance_to(player_at), wading)
		var next := position
		if brain.state == FishBrain.DART:            # off and down, away from the feet
			heading = (position - player_at).normalized()
			next = position + heading * 30.0 * delta
		elif circling:
			_a += speed / radius * delta
			next = centre + Vector2.from_angle(_a) * radius
			heading = Vector2.from_angle(_a + PI / 2.0)
		else:
			next = position + heading * speed * delta
		if lake.depth_at(next) < LakeLife.FISH_DEPTH and brain.state != FishBrain.DART:
			circling = false                         # shallow ahead: turn away from it
			heading = heading.rotated(randf_range(PI * 0.6, PI * 1.4))
			next = position
		position = next
		queue_redraw()

	func _draw() -> void:
		var shown := brain.shown()
		if shown <= 0.0:
			return
		var L := length / 2.0
		var c := heading.normalized()
		var r := int(L) + 3
		var origin := position.round()
		for j in range(-r, r + 1):
			for i in range(-r, r + 1):
				var w := Vector2(i, j) + origin
				if lake.depth_at(w) < 25:
					continue
				var u := Vector2(i, j).dot(c)
				var v := Vector2(i, j).dot(c.orthogonal())
				var half := 1.5 * sqrt(maxf(0.0, 1.0 - (u / L) * (u / L)))
				if u > -L and u < -L + 1.5:
					half += 0.6                          # the tail fin
				# rising and sinking, the shape comes and goes pixel by pixel (no transparency)
				if fposmod(sin(w.x * 12.9898 + w.y * 78.233) * 43758.5453, 1.0) > shown:
					continue
				var at := Vector2(i, j) + origin - position
				if absf(u) <= L and absf(v) <= half:
					draw_rect(Rect2(at, Vector2.ONE), BODY)
				elif u > L * 0.3 and absf(u) <= L + 1.0 and absf(v) <= half + 1.0 and (i * 7 + j * 3) % 3 != 0:
					draw_rect(Rect2(at, Vector2.ONE), BOW)
		if brain.state == FishBrain.SWIM and absf(heading.angle_to(Vector2.RIGHT.rotated(_t))) < 0.05:
			draw_rect(Rect2(origin - position, Vector2.ONE), GLINT)   # turning, a flank catches the light
		if brain.state == FishBrain.RISE:                # where it came up, a small ring spreads
			var rr := 1.5 + _t * 4.0
			for k in int(8 + rr * 5):
				var p := (origin + Vector2(cos(k * TAU / (8 + rr * 5)) * rr, 0.6 * rr * sin(k * TAU / (8 + rr * 5)))).round()
				if lake.depth_at(p) >= 25:
					draw_rect(Rect2(p - position, Vector2.ONE), RING)


## One duck: a small brown body with a dark green head and a pale V of wake behind it.
class Duck:
	extends Node2D
	const BODY := [Color8(59, 51, 44), Color8(94, 82, 70), Color8(138, 122, 104)]
	const HEAD := Color8(47, 74, 58)
	const BILL := Color8(201, 162, 78)
	const WAKE := [Color8(85, 112, 121), Color8(127, 152, 156)]
	var brain: DuckBrain
	var lake: LakeLife
	var heading := Vector2.RIGHT
	var _turn_in := 2.0
	var _t := 0.0

	func setup(l: LakeLife, at: Vector2, towards: Vector2) -> void:
		lake = l
		brain = DuckBrain.new(randf_range(20.0, 40.0))
		position = at
		heading = (towards - at).normalized().rotated(randf_range(-0.5, 0.5))

	func live(delta: float, player_at: Vector2, view: Rect2) -> void:
		_t += delta
		brain.update(delta, position.distance_to(player_at))
		var speed := 3.0
		match brain.state:
			DuckBrain.FLY:
				heading = (position - player_at).normalized()
				position += (heading + Vector2(0, -0.5)) * 40.0 * delta
				queue_redraw()
				return
			DuckBrain.LEAVE:
				heading = (position - view.get_center()).normalized()
				speed = 5.0
			_:
				_turn_in -= delta
				if _turn_in <= 0.0:
					_turn_in = randf_range(2.0, 5.0)
					heading = heading.rotated(randf_range(-1.0, 1.0))
		var next := position + heading * speed * delta
		if lake.depth_at(next) < LakeLife.DUCK_DEPTH:
			heading = heading.rotated(PI * randf_range(0.7, 1.3))
		else:
			position = next
		queue_redraw()

	func _draw() -> void:
		var d := 1 if heading.x >= 0.0 else -1
		var o := Vector2.ZERO
		if brain.state == DuckBrain.FLY:             # wings beating
			var up := int(_t * 8.0) % 2 == 0
			for p in [Vector2(-1, -1), Vector2(-2, -2 if up else 0), Vector2(1, -1), Vector2(2, -2 if up else 0)]:
				draw_rect(Rect2(o + p, Vector2.ONE), BODY[2])
		else:
			for t in range(3, 10):                   # the wake: a pale V behind
				for side in [-1, 1]:
					draw_rect(Rect2(o + Vector2(-d * t, 1 + side * (t / 3)), Vector2.ONE), WAKE[0] if t < 6 else WAKE[1])
		for q in [[0, -1, 2], [-d, -1, 1], [0, 0, 1], [-d, 0, 1], [d, 0, 2], [-2 * d, 0, 1], [-3 * d, 0, 0],
				[0, 1, 0], [-d, 1, 0], [d, 1, 0], [-2 * d, 1, 0], [2 * d, 0, 1]]:
			draw_rect(Rect2(o + Vector2(q[0], q[1]), Vector2.ONE), BODY[q[2]])
		for q in [[2 * d, -1], [2 * d, -2], [3 * d, -2]]:
			draw_rect(Rect2(o + Vector2(q[0], q[1]), Vector2.ONE), HEAD)
		draw_rect(Rect2(o + Vector2(4 * d, -2), Vector2.ONE), BILL)
