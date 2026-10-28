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
var _open: Image                             # full size: open water, no stones, jetty or boat in it
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
	var o := TextureLoader.load_texture("res://assets/world/open_water.png")
	_open = o.get_image() if o != null else null


func depth_at(p: Vector2) -> int:
	if _map == null:
		return 0
	var x := int(p.x / 2.0)
	var y := int(p.y / 2.0)
	if x < 0 or y < 0 or x >= _map.get_width() or y >= _map.get_height():
		return 0
	return int(round(_map.get_pixel(x, y).r * 255.0))


## Depth where something can swim: none on a stone, the jetty or the boat (the half-size map has them as lake).
func swim_depth(p: Vector2) -> int:
	if _open != null:
		var x := int(p.x)
		var y := int(p.y)
		if x < 0 or y < 0 or x >= _open.get_width() or y >= _open.get_height() or _open.get_pixel(x, y).r < 0.5:
			return 0
	return depth_at(p)


## A way on from p that stays at least min_depth deep: straight on if it can, else the smallest turn,
## first to the side it turned last time (so it does not swing back and forth at an edge).
func steer(p: Vector2, heading: Vector2, min_depth: int, side: float) -> Vector2:
	for a in [0.0, 0.5, 1.0, 1.6, 2.2, 2.8]:
		for sgn in [side, -side]:
			var h := heading.rotated(a * sgn)
			if swim_depth(p + h * 6.0) >= min_depth and swim_depth(p + h * 2.0) >= min_depth:
				return h
			if a == 0.0:
				break
	return -heading


## A random point at least min_depth deep inside r, or (-1, -1) if none was found.
func random_spot(r: Rect2, min_depth: int) -> Vector2:
	for i in 24:
		var p := Vector2(randf_range(r.position.x, r.end.x), randf_range(r.position.y, r.end.y))
		if swim_depth(p) >= min_depth and swim_depth(p + Vector2(8, 0)) >= min_depth \
				and swim_depth(p - Vector2(8, 0)) >= min_depth:
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
	var _side := 1.0                             # which way it turns at an edge, kept for its whole life
	var _shown := Vector2.ZERO
	var pos := Vector2.ZERO                      # the true, smooth spot; the node stands on _shown
	var centre := Vector2.ZERO
	var radius := 10.0
	var _a := 0.0
	var _t := 0.0

	func setup(l: LakeLife, at: Vector2) -> void:
		lake = l
		brain = FishBrain.new(randf_range(6.0, 16.0))
		pos = at
		length = float(randi_range(7, 9))
		heading = Vector2.RIGHT.rotated(randf() * TAU)
		circling = randf() < 0.5                     # a few rounds, or off in one direction
		radius = randf_range(8.0, 15.0)
		centre = at - heading.orthogonal() * radius
		_a = (at - centre).angle()
		speed = randf_range(4.0, 7.0)
		_side = 1.0 if randf() < 0.5 else -1.0
		z_index = -1
		_shown = at.round()
		position = _shown

	func live(delta: float, player_at: Vector2, wading: bool) -> void:
		_t += delta
		brain.update(delta, pos.distance_to(player_at), wading)
		var next := pos
		if brain.state == FishBrain.DART:            # off and down, away from the feet
			heading = (pos - player_at).normalized()
			next = pos + heading * 30.0 * delta
		elif circling:
			_a += speed / radius * delta
			next = centre + Vector2.from_angle(_a) * radius
			heading = Vector2.from_angle(_a + PI / 2.0)
		else:
			next = pos + heading * speed * delta
		if lake.swim_depth(next) < LakeLife.FISH_DEPTH and brain.state != FishBrain.DART:
			circling = false                         # shallow ahead: turn once, the smallest way, and go on
			heading = lake.steer(pos, heading, LakeLife.FISH_DEPTH, _side)
			next = pos + heading * speed * delta
			if lake.swim_depth(next) < LakeLife.FISH_DEPTH:
				next = pos
		pos = next
		_shown = PixelSnap.sticky(_shown, pos)   # whole pixels, without shaking round a pixel's middle
		position = _shown
		queue_redraw()

	func _draw() -> void:
		var shown := brain.shown()
		if shown <= 0.0:
			return
		var L := length / 2.0
		var c := heading.normalized()
		var r := int(L) + 3
		var origin := _shown
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
				var at := Vector2(i, j)
				if absf(u) <= L and absf(v) <= half:
					draw_rect(Rect2(at, Vector2.ONE), BODY)
				elif u > L * 0.3 and absf(u) <= L + 1.0 and absf(v) <= half + 1.0 and (i * 7 + j * 3) % 3 != 0:
					draw_rect(Rect2(at, Vector2.ONE), BOW)
		if brain.state == FishBrain.SWIM and absf(heading.angle_to(Vector2.RIGHT.rotated(_t))) < 0.05:
			draw_rect(Rect2(Vector2.ZERO, Vector2.ONE), GLINT)   # turning, a flank catches the light
		if brain.state == FishBrain.RISE:                # where it came up, a small ring spreads
			var rr := 1.5 + _t * 4.0
			for k in int(8 + rr * 5):
				var p := (origin + Vector2(cos(k * TAU / (8 + rr * 5)) * rr, 0.6 * rr * sin(k * TAU / (8 + rr * 5)))).round()
				if lake.depth_at(p) >= 25:
					draw_rect(Rect2(p - origin, Vector2.ONE), RING)


## One duck: a small brown body with a dark green head and a pale V of wake behind it.
class Duck:
	extends Node2D
	const BODY := [Color8(59, 51, 44), Color8(94, 82, 70), Color8(138, 122, 104)]
	const HEAD := Color8(47, 74, 58)
	const BILL := Color8(201, 162, 78)
	const WAKE := [Color8(85, 112, 121), Color8(127, 152, 156)]
	const TIP := Color8(186, 170, 146)
	const SPLASH := Color8(150, 176, 182)
	const SHADOW := Color8(22, 30, 36)
	static var _swim_sheet: Texture2D
	const RUN := 0.75                            # seconds running over the water before it lifts off
	const RUN_SPEED := 36.0
	const ELEVATION := [78.0, 30.0, -55.0, 30.0] # wing: up, half, down, half (degrees, up is positive)
	# the flying duck, facing right: neck out, pointed tail; the middle of the body is at (6, 1)
	const FLY_BODY := ["..........HH..", "..01111111HHb.", "...0111111....", "....0111......"]
	var lift := 0.0                              # how high above the water (art px), 0 while it runs
	var _fly_t := 0.0
	var brain: DuckBrain
	var lake: LakeLife
	var heading := Vector2.RIGHT
	var facing := 1                              # which way it looks; only turns on a clear sideways heading
	var _turn_in := 2.0
	var _side := 1.0
	var _t := 0.0
	var pos := Vector2.ZERO                      # the true, smooth spot; the node stands on _shown
	var _shown := Vector2.ZERO

	func setup(l: LakeLife, at: Vector2, towards: Vector2) -> void:
		lake = l
		brain = DuckBrain.new(randf_range(20.0, 40.0))
		pos = at
		heading = (towards - at).normalized().rotated(randf_range(-0.5, 0.5))
		_side = 1.0 if randf() < 0.5 else -1.0
		facing = 1 if heading.x >= 0.0 else -1
		_shown = at.round()
		position = _shown

	func live(delta: float, player_at: Vector2, view: Rect2) -> void:
		_t += delta
		brain.update(delta, pos.distance_to(player_at))
		var speed := 3.0
		match brain.state:
			DuckBrain.FLY:
				if _fly_t == 0.0:
					heading = (pos - player_at).normalized()          # away from you, and it keeps that course
					if absf(heading.x) > 0.3:
						facing = 1 if heading.x > 0.0 else -1
				_fly_t += delta
				var v := RUN_SPEED
				if _fly_t < RUN:                     # the run: speeding up, on the water
					v = RUN_SPEED * pow(_fly_t / RUN, 1.4)
					lift = 0.0
					if lake.swim_depth(pos + heading * 4.0) < LakeLife.DUCK_DEPTH:
						_fly_t = RUN                 # land ahead: lifts off right here
				else:
					var u := _fly_t - RUN
					lift = 14.0 * u + 3.0 * u * u
				pos += heading * v * delta
				_shown = pos.round()
				position = _shown
				queue_redraw()
				return
			DuckBrain.LEAVE:
				heading = (pos - view.get_center()).normalized()
				speed = 5.0
			_:
				_turn_in -= delta
				if _turn_in <= 0.0:
					_turn_in = randf_range(2.0, 5.0)
					heading = heading.rotated(randf_range(-1.0, 1.0))
		var next := pos + heading * speed * delta
		if lake.swim_depth(next) < LakeLife.DUCK_DEPTH:
			heading = lake.steer(pos, heading, LakeLife.DUCK_DEPTH, _side)
			_turn_in = randf_range(2.0, 5.0)         # and keep that course a while
			next = pos + heading * speed * delta
		if lake.swim_depth(next) >= LakeLife.DUCK_DEPTH:
			pos = next
		if absf(heading.x) > 0.3:
			facing = 1 if heading.x > 0.0 else -1
		_shown = PixelSnap.sticky(_shown, pos)
		position = _shown
		queue_redraw()

	## The wing's lift above the body's line (degrees) at a moment of the beat; low while it runs.
	static func wing_elevation(t: float, running: bool) -> float:
		var e: float = ELEVATION[int(t / (0.05 if running else 0.075)) % 4]
		return clampf(e, -30.0, 40.0) if running else e

	func _px(at: Vector2, col: Color) -> void:
		draw_rect(Rect2(at.round(), Vector2.ONE), col)

	func _wing(elev_deg: float, far: bool) -> void:
		var d := float(facing)
		var a := deg_to_rad(elev_deg)
		var dir := Vector2(-cos(a) * d, -sin(a))
		var perp := Vector2(-dir.y, dir.x)
		var from := Vector2(1.0 * d + (d if far else 0.0), -1.0 - (1.0 if far else 0.0) - lift)   # the shoulder
		var length := 5.5
		for k in range(int(length) + 1):
			var th := maxi(1, roundi(2.4 * (1.0 - k / length) + 0.7))
			for s in th:
				var col: Color = BODY[1] if far else (TIP if k > 3 or s == th - 1 else BODY[2])
				_px(from + dir * k + perp * (s - (th - 1) / 2.0), col)

	func _draw() -> void:
		var d := facing
		if brain.state == DuckBrain.FLY:
			var running := _fly_t < RUN
			if running:                              # splash and a wake behind it
				var n := int(_fly_t * 24.0)
				for k in 3:
					_px(Vector2(-d * (4 + k * 2) - ((n + k) % 2) * d, 1 + (n * 7 + k * 5) % 3 - 1), SPLASH)
				for k in range(8, 14):
					_px(Vector2(-d * (k + 1), 1 + (k % 3 - 1)), WAKE[1] if k % 2 == 1 else WAKE[0])
			else:                                    # the shadow on the water, smaller the higher it is
				var w := maxi(1, roundi(4.0 * (1.0 - minf(lift, 40.0) / 50.0)))
				for i in range(-w, w + 1):
					_px(Vector2(i - 2 * d, 1), SHADOW)
			var elev := wing_elevation(_fly_t, running)
			_wing(elev, true)
			for j in FLY_BODY.size():
				for i in FLY_BODY[j].length():
					var ch: String = FLY_BODY[j][i]
					if ch == ".":
						continue
					var col: Color = BODY[0] if ch == "0" else (BODY[1] if ch == "1" else (HEAD if ch == "H" else BILL))
					_px(Vector2((i - 6) * d, j - 2 - lift), col)
			_wing(elev, false)
			return
		# swimming: a drawn picture, 4 phases (the head nods, the wake streams away); the cell is 28 x 20, its
		# body's middle at (14, 8), mirrored when it looks left
		if _swim_sheet == null:
			_swim_sheet = TextureLoader.load_texture("res://assets/life/ente.png")
		var cell := Rect2(Vector2((-14.0 if d > 0 else -13.0), -7.0), Vector2(28.0 * d, 20.0))
		draw_texture_rect_region(_swim_sheet, cell, Rect2(float(int(_t * 5.0) % 4) * 28.0, 0.0, 28.0, 20.0))
