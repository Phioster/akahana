## The squirrels: at most two at a time, each at its own broadleaf tree (assets/world/squirrel_trees.json,
## tools/world/life/squirrel_trees.py). One turns up at a tree just beyond the view's edge, eats a nut at its
## foot, now and then hops to a neighbouring tree; come close and it hops to its trunk, climbs in two spurts
## and is gone in the crown. The look is tools/world/life/squirrel_art.py (approved 0.19).
class_name Squirrels
extends Node

const FILE := "res://assets/world/squirrel_trees.json"
const MAX := 2
const DROP := 200.0                          # beyond this from the view a squirrel is let go
const NEIGHBOUR := 80.0                      # how far it hops over to another tree

var player: Node2D
var sorted: Node2D
var store: ChunkStore                        # to keep their spots off water and walls
var trees: Array[Vector3i] = []              # trunk middle x, trunk foot y, crown's lower edge y
var _list: Array = []
var _spawn_in := 3.0
var _chatter_in := randf_range(12.0, 30.0)
var _voice: AudioStreamPlayer2D              # now and then one chatters (0.22: red squirrel #111393, CC0)
const CHATTER_DB := -16.0                    # recording -20 -> about -36: small, a little way off


func _ready() -> void:
	if trees.is_empty():
		load_trees()
	_voice = AudioStreamPlayer2D.new()
	_voice.bus = AudioSetup.SOUNDS
	_voice.max_distance = 130.0
	add_child(_voice)


func load_trees() -> void:
	var f := FileAccess.open(FILE, FileAccess.READ)
	if f == null:
		return
	var data = JSON.parse_string(f.get_as_text())
	if data is Array:
		for t in data:
			trees.append(Vector3i(int(t[0]), int(t[1]), int(t[2])))


func count() -> int:
	return _list.size()


func step(delta: float, view: Rect2) -> void:
	_spawn_in -= delta
	if _spawn_in <= 0.0:
		_spawn_in = randf_range(3.0, 7.0)
		if _list.size() < MAX:
			_spawn(view)
	_chatter_in -= delta
	if _chatter_in <= 0.0:
		_chatter_in = randf_range(18.0, 45.0)
		var seen := _list.filter(func(x): return view.grow(20.0).has_point(x.position))
		if not seen.is_empty():
			var who: Node2D = seen[randi() % seen.size()]
			_voice.stream = SoundBank.get_stream("eichhorn_%02d" % (randi() % 4))
			_voice.volume_db = CHATTER_DB + randf_range(-3.0, 0.0)
			_voice.pitch_scale = randf_range(0.95, 1.08)
			_voice.global_position = who.global_position
			_voice.play()
	var at := player.position if player != null else Vector2(-9999, -9999)
	for s in _list.duplicate():
		s.live(delta, at)
		if s.state == Squirrel.GONE or not view.grow(DROP).has_point(s.position):
			_list.erase(s)
			s.queue_free()


## At a tree just out of sight, so nobody sees it appear.
func _spawn(view: Rect2) -> void:
	var near := view.grow(60.0)
	var seen := view.grow(4.0)
	var options: Array[Vector3i] = []
	for t in trees:
		var foot := Vector2(t.x, t.y)
		if near.has_point(foot) and not seen.has_point(foot) and _free_tree(t):
			options.append(t)
	if options.is_empty():
		return
	var t: Vector3i = options[randi() % options.size()]
	var spot := _spot_by(t)
	if spot.x < 0.0 or (player != null and spot.distance_to(player.position) < 70.0):
		return
	var s := Squirrel.new()
	s.setup(t, spot, randf(), _wander)
	(sorted if sorted != null else self).add_child(s)
	_list.append(s)


func _free_tree(t: Vector3i) -> bool:
	for s in _list:
		if s.tree == t:
			return false
	return true


## A place in the grass beside a tree's foot, or (-1, -1).
func _spot_by(t: Vector3i) -> Vector2:
	for i in 8:
		var side := 1.0 if randf() < 0.5 else -1.0
		var p := Vector2(t.x + side * randf_range(10.0, 26.0), t.y + randf_range(3.0, 10.0)).round()
		if store == null or (store.walkable(p) and store.material_at(p) != GroundMat.WET):
			return p
	return Vector2(-1, -1)


## Where a busy squirrel hops next: over to a neighbouring tree, or a little way round its own.
func _wander(s: Squirrel) -> Dictionary:
	var here := Vector2(s.tree.x, s.tree.y)
	if randf() < 0.5:
		var near: Array[Vector3i] = []
		for t in trees:
			var d := here.distance_to(Vector2(t.x, t.y))
			if d > 8.0 and d < NEIGHBOUR and _free_tree(t):
				near.append(t)
		if not near.is_empty():
			var t: Vector3i = near[randi() % near.size()]
			var p := _spot_by(t)
			if p.x >= 0.0:
				return {"at": p, "tree": t}
	var p := _spot_by(s.tree)
	return {"at": p, "tree": s.tree} if p.x >= 0.0 else {}


## One squirrel. Its node stands on the ground; climbing only lifts the drawing (so it stays in front of the
## trunk in the y-sort) and the rows that reach into the crown are cut off, as if it went in behind the leaves.
class Squirrel:
	extends Node2D
	enum { EAT, WATCH, HOP, CLIMB, GONE }
	const CELL := 12
	const FRAMES := {"sit": 0, "eat_up": 1, "eat_dn": 2, "eat_tw": 3, "hop1": 4, "hop2": 5, "climb1": 6, "climb2": 7}
	const EAT_CYCLE := [["eat_dn", 0.18], ["eat_up", 0.25], ["eat_dn", 0.18], ["eat_up", 0.25],
			["eat_dn", 0.18], ["eat_up", 0.6], ["eat_tw", 0.15], ["eat_up", 0.45]]
	const HOP_STEP := 5.0                    # px per bound
	const HOP_TIME := 0.11
	const CLIMB_PX := 0.05                   # s per px up the bark
	const SPURT := 9                         # px in the first spurt, then a pause on the bark
	const PAUSE := 0.7
	static var _sheet: Texture2D

	var tree := Vector3i.ZERO
	var state := EAT
	var shyness := 0.5
	var up := 0                              # px climbed
	var frame_name := "sit"
	var facing := 1.0                        # 1 right, -1 left
	var _goal := Vector2.ZERO
	var _goal_tree := Vector3i.ZERO
	var _fleeing := false
	var _t := 0.0
	var _busy := 6.0                         # seconds of eating before it hops somewhere
	var _wander: Callable

	func setup(t: Vector3i, at: Vector2, shy: float, wander: Callable = Callable()) -> void:
		tree = t
		position = at
		shyness = shy
		_wander = wander
		_busy = randf_range(4.0, 10.0)
		_t = randf() * 2.0
		facing = 1.0 if at.x < t.x else -1.0             # eats looking at its tree

	func flee_distance() -> float:
		return lerpf(28.0, 44.0, shyness)

	func trunk_spot() -> Vector2:
		return Vector2(tree.x + 4, tree.y + 2)          # the belly (column 2 of the climb cell) on the trunk

	func live(delta: float, player_at: Vector2) -> void:
		_t += delta
		var dist := position.distance_to(player_at)
		match state:
			EAT, WATCH:
				if dist < flee_distance():
					_hop_to(trunk_spot(), tree, true)
				elif dist < flee_distance() + 14.0:
					state = WATCH
					frame_name = "sit"
					facing = signf(player_at.x - position.x) if player_at.x != position.x else facing
				else:
					state = EAT
					frame_name = _eat_frame()
					_busy -= delta
					if _busy <= 0.0:
						_busy = randf_range(4.0, 10.0)
						var w: Dictionary = _wander.call(self) if _wander.is_valid() else {}
						if not w.is_empty():
							_hop_to(w["at"], w["tree"], false)
			HOP:
				if not _fleeing and dist < flee_distance():
					_hop_to(trunk_spot(), tree, true)
				while _t >= HOP_TIME and state == HOP:
					_t -= HOP_TIME
					var to := _goal - position
					position = _goal if to.length() <= HOP_STEP else (position + to.normalized() * HOP_STEP).round()
					frame_name = "hop1" if frame_name == "hop2" else "hop2"
					if position == _goal:
						tree = _goal_tree
						if _fleeing:
							state = CLIMB
							facing = 1.0
							_t = 0.0
						else:
							state = EAT
							facing = 1.0 if position.x < tree.x else -1.0
			CLIMB:
				var moving := true
				if _t < SPURT * CLIMB_PX:
					up = int(_t / CLIMB_PX)
				elif _t < SPURT * CLIMB_PX + PAUSE:
					up = SPURT
					moving = false
				else:
					up = SPURT + int((_t - SPURT * CLIMB_PX - PAUSE) / CLIMB_PX)
				frame_name = ("climb1" if int(_t / 0.1) % 2 else "climb2") if moving else "climb1"
				if position.y - up <= tree.z:                # its feet are in the leaves: gone
					state = GONE
		queue_redraw()

	func _hop_to(p: Vector2, t: Vector3i, flee: bool) -> void:
		_goal = p
		_goal_tree = t
		_fleeing = flee
		state = HOP
		_t = HOP_TIME                                       # the first bound at once
		if p.x != position.x:
			facing = signf(p.x - position.x)

	func _eat_frame() -> String:
		var total := 0.0
		for e in EAT_CYCLE:
			total += e[1]
		var u := fmod(_t, total)
		for e in EAT_CYCLE:
			if u < e[1]:
				return e[0]
			u -= e[1]
		return "eat_up"

	## How many rows at the top of the picture are already inside the crown.
	func hidden_rows() -> int:
		if state != CLIMB:
			return 0
		var top := int(position.y) - CELL - up
		return clampi(tree.z - top, 0, CELL)

	func _draw() -> void:
		if state == GONE:
			return
		if _sheet == null:
			_sheet = TextureLoader.load_texture("res://assets/life/eichhorn.png")
		var cut := hidden_rows()
		var src := Rect2(float(FRAMES[frame_name] * CELL), float(cut), CELL, CELL - cut)
		var x := -6.0 if facing > 0.0 else 6.0
		var dst := Rect2(Vector2(x, -CELL - up + cut), Vector2(CELL * facing, CELL - cut))
		draw_texture_rect_region(_sheet, dst, src)
