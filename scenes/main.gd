## Builds the world from the generated assets, follows the wanderer, feeds the atmosphere and poppy
## shaders, and wires in the journal (start, settings), sound, birds, wisps and the saved position.
extends Node2D

const MAX_LIGHTS := 16
const MAX_FLIES := 40
const KINDS := {"fire": 0.0, "lantern": 1.0, "wood": 2.0, "candle": 3.0, "wisp": 4.0, "kerze": 3.0}
const GLOW := {"fire": 40.0, "lantern": 6.0, "wood": 8.0, "candle": 4.0, "wisp": 4.0, "kerze": 1.2}   # glowing pixels, for bloom
const SAVE_EVERY := 5.0
const CAM_EASE := 5.0                # how quickly the view catches up: starting and stopping glide
const CAM_MIN_SPEED := 4.0           # art px/s: the slowest it glides before arriving
const CAM_CALM := Vector2(10, 14)    # a box round the middle: small steps inside it leave the world still

var world: WorldData
var pathing := Pathing.new()
var player: Player
var cam: Camera2D
var post: ShaderMaterial
var store: ChunkStore
var view_node: WorldView
var marker: TapMarker
var birds: Birds
var _flog := FrameLog.new()           # diagnosis (half pixels, stutter): remove once found
var _corner_last := Vector2.ZERO
var lake: LakeLife
var _life := Activator.new()         # wisps: made near the view, dropped far from it
var book: BookUI
var save := SaveData.new()
var trail := Trail.new()
var sorted: Node2D
var _time := 0.0
var _save_in := SAVE_EVERY
var _last_pos := Vector2.ZERO
var _camera_mode := false
var _cam_offset := Vector2.ZERO
var _last_tap := -10.0
var _drag_from := Vector2.INF
var _cam_at := Vector2.INF           # where the view is; INF = jump straight there (start, teleport)
var _cam_goal := Vector2.ZERO        # where it is gliding to


func _ready() -> void:
	get_tree().set_auto_accept_quit(false)
	world = WorldData.load_default()
	if world == null:
		return
	save = SaveData.load_from()
	AudioSetup.apply(save)

	store = ChunkStore.new(world.grid)
	view_node = WorldView.new()
	view_node.world = world
	view_node.store = store
	add_child(view_node)
	sorted = Node2D.new()
	sorted.y_sort_enabled = true
	add_child(sorted)
	view_node.sorted = sorted
	view_node.load_around(_start_position())

	player = Player.new()
	player.position = _start_position()
	sorted.add_child(player)
	_last_pos = player.position

	marker = TapMarker.new()
	add_child(marker)

	for w in world.wisps:                                 # wisps appear beyond the view's edge only
		var at := Vector2(float(w["x"]), float(w["y"]))
		_life.add(Rect2(at, Vector2.ZERO), 60.0, 160.0, _make_wisp.bind(at), func(n: Node): n.queue_free())
	for s in world.fireflies:                             # fireflies: only the swarms near the view fly
		var at := Vector2(float(s["x"]), float(s["y"]))
		_life.add(Rect2(at - Vector2(20, 20), Vector2(40, 40)), 40.0, 120.0, _make_swarm.bind(s),
				func(n: Node): n.queue_free())
	birds = Birds.new()
	birds.world = world
	birds.player = player
	birds.sorted = sorted
	add_child(birds)
	lake = LakeLife.new()                                  # fish and ducks turn up near the view on the lake
	lake.world = world
	lake.player = player
	lake.sorted = sorted
	lake.store = store
	add_child(lake)

	cam = Camera2D.new()
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = world.width
	cam.limit_bottom = world.height
	add_child(cam)
	cam.make_current()

	var layer := CanvasLayer.new()
	layer.layer = 10
	add_child(layer)
	var rect := ColorRect.new()
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	post = ShaderMaterial.new()
	post.shader = load("res://shaders/post.gdshader")
	post.set_shader_parameter("mist1", TextureLoader.load_texture(WorldData.DIR + "mist1.png"))
	post.set_shader_parameter("mist2", TextureLoader.load_texture(WorldData.DIR + "mist2.png"))
	post.set_shader_parameter("mist_fields", TextureLoader.load_texture(WorldData.DIR + "mist_fields.png"))
	post.set_shader_parameter("world_size", Vector2(world.width, world.height))
	rect.material = post
	layer.add_child(rect)

	var steps := Footsteps.new()
	steps.player = player
	steps.store = store
	add_child(steps)
	var amb := Ambience.new()
	amb.world = world
	amb.player = player
	add_child(amb)
	add_child(Ducker.new())
	add_child(_flog)
	add_child(Music.new())

	book = BookUI.new()
	book.music = save.music
	book.sounds = save.sounds
	add_child(book)
	book.start_walking.connect(_on_start_walking)
	book.volumes_changed.connect(_on_volumes)
	book.camera_mode_changed.connect(_on_camera_mode)
	book.travel.connect(_on_travel)                       # testing aid (core/test_travel.gd)
	book.show_start(save.has_position)


func _make_wisp(at: Vector2) -> Node:
	var wisp := Wisp.new()
	wisp.anchor = at
	wisp.position = at
	wisp.player = player
	add_child(wisp)
	return wisp


func _make_swarm(s: Dictionary) -> Node:
	var f := Fireflies.new()
	f.setup(s)
	f.z_index = 1                                     # they hover: over the grass and the wanderer's feet
	add_child(f)
	return f


func _start_position() -> Vector2:
	if save.has_position:
		store.load_now(world.grid.chunk_of(save.position))
		if store.walkable(save.position):
			return save.position
	return world.start


# ---------------------------------------------------------------- journal and saving

## Where the view comes to rest: its top-left corner on a whole pixel. The view's height in art pixels is
## rarely whole (180 wide on a tall phone), so a whole-pixel middle would leave the corner on half a pixel.
## Rounded toward where the camera comes from would send it back a fraction and then snap: so a whole pixel
## that is not behind the camera, seen from the goal.
static func rest_goal(goal: Vector2, view: Vector2, at: Vector2 = Vector2.INF) -> Vector2:
	var corner := goal - view * 0.5
	var out := corner.round()
	if at != Vector2.INF:
		var from := at - view * 0.5
		for k in 2:
			var way := corner[k] - from[k]
			if absf(way) > 0.001 and (out[k] - from[k]) * way < 0.0:
				out[k] = ceilf(from[k]) if way > 0.0 else floorf(from[k])
	return out + view * 0.5


func _on_start_walking(fresh: bool) -> void:
	if fresh:
		_cam_at = Vector2.INF
		save.forget_position()
		player.path = PackedVector2Array()
		view_node.load_around(world.start)              # the ground must be there before the jump shows it
		player.position = world.start
		_store()


## Testing aid: put him at a place at once (debug builds only; there is no fast travel in the game).
func _on_travel(to: Vector2) -> void:
	store.load_now(world.grid.chunk_of(to))
	view_node.load_around(to)
	player.path = PackedVector2Array()
	player.position = TestTravel.nearest_open(store, to)
	_cam_at = Vector2.INF
	_last_pos = player.position


func _on_volumes(music: float, sounds: float) -> void:
	save.music = music
	save.sounds = sounds
	AudioSetup.apply(save)
	_store()


func _on_camera_mode(on: bool) -> void:
	_camera_mode = on
	_cam_offset = Vector2.ZERO
	marker.visible = not on


func _store() -> void:
	if world != null and store.walkable(player.position):
		save.set_position(player.position)
	save.save_to()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_PAUSED or what == NOTIFICATION_WM_CLOSE_REQUEST:
		if player != null:
			_store()
		if what == NOTIFICATION_WM_CLOSE_REQUEST:
			get_tree().quit()
	elif what == NOTIFICATION_WM_GO_BACK_REQUEST:
		if book != null and not book.back():
			if player != null:
				_store()
			get_tree().quit()


# ---------------------------------------------------------------- input

func _unhandled_input(event: InputEvent) -> void:
	if book == null or book.is_blocking():
		return
	if _camera_mode:
		_camera_input(event)
		return
	var pressed := false
	if event is InputEventScreenTouch and event.pressed:
		pressed = true
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		pressed = true
	if not pressed:
		return
	var target: Vector2 = get_canvas_transform().affine_inverse() * event.position
	var way := pathing.find_path_in(store, player.position, target)
	if way.size() > 0:
		player.walk_to(way)
		marker.show_at(way[way.size() - 1])


## Camera mode: one finger drags the view, two quick taps end it.
func _camera_input(event: InputEvent) -> void:
	if event is InputEventScreenTouch:
		if event.pressed:
			if _time - _last_tap < 0.35:
				book.camera_off()
				return
			_last_tap = _time
			_drag_from = event.position
		else:
			_drag_from = Vector2.INF
	elif event is InputEventScreenDrag and _drag_from != Vector2.INF:
		var scale := get_canvas_transform().get_scale()
		_cam_offset -= event.relative / scale
		var view := get_viewport().get_visible_rect().size
		_cam_offset = _cam_offset.clamp(-Vector2(world.width, world.height), Vector2(world.width, world.height))


# ---------------------------------------------------------------- frame

func _process(delta: float) -> void:
	if world == null:
		return
	_time += delta
	var moved := player.position - _last_pos
	trail.update(delta, player.position, moved, player.is_walking())
	_last_pos = player.position
	var u: Array = trail.uniforms()
	view_node.set_trail(u[0], u[1])

	var view := get_viewport().get_visible_rect().size
	var c := player.position + _cam_offset                # no rounding: the camera glides in screen pixels
	c.x = clampf(c.x, view.x * 0.5, world.width - view.x * 0.5)
	c.y = clampf(c.y, view.y * 0.5, world.height - view.y * 0.5)
	if _camera_mode:
		_cam_offset = c - player.position                 # stop the offset growing past the world edge
	if _cam_at == Vector2.INF or _camera_mode:          # in camera mode your finger moves it directly
		_cam_at = c
		_cam_goal = c
	else:
		# the view only moves on once he leaves the calm box, and then just enough to keep him at its edge
		var held := true
		for k in 2:
			var off: float = c[k] - _cam_goal[k]
			if absf(off) > CAM_CALM[k]:
				_cam_goal[k] = c[k] - signf(off) * CAM_CALM[k]
				held = false
		# rest on a whole pixel (between two the post shader read on borders) whenever the goal holds still,
		# also while he walks about inside the calm box; a goal that follows him is not rounded (it wobbled)
		if held or not player.is_walking():
			_cam_goal = rest_goal(_cam_goal, view, _cam_at)
		# ease out, but never creep: below a small speed it rolls straight onto the goal and stops there
		# (the endless creep ended in a visible snap)
		var left := _cam_at.distance_to(_cam_goal)
		var go := maxf(left * (1.0 - exp(-CAM_EASE * delta)), CAM_MIN_SPEED * delta)
		_cam_at = _cam_at.move_toward(_cam_goal, go)
	cam.position = _cam_at
	cam.force_update_scroll()                          # apply now: the shader must snap to THIS frame's view
	var top_left := get_viewport().get_canvas_transform().affine_inverse() * Vector2.ZERO
	post.set_shader_parameter("view_world", view)
	post.set_shader_parameter("cam_pos", top_left)
	view_node.update(Rect2(top_left, view))
	var ct := get_viewport().get_canvas_transform()
	_flog.note(delta, player.is_walking(), top_left, top_left - _corner_last, ct.origin,
			"ziel %.2f,%.2f" % [_cam_goal.x - view.x * 0.5, _cam_goal.y - view.y * 0.5])
	_corner_last = top_left
	birds.update_area(Rect2(top_left, view))
	lake.step(delta, Rect2(top_left, view))
	_life.update(Rect2(top_left, view))
	_feed_lights(Rect2(top_left, view))

	_save_in -= delta
	if _save_in <= 0.0 and not player.is_walking():
		_save_in = SAVE_EVERY
		if book != null and not book.is_blocking():
			_store()


func _feed_lights(view: Rect2) -> void:
	var all: Array = []
	for n in get_tree().get_nodes_in_group("dyn_light"):    # moving lights first: the wisps
		var d: Dictionary = n.light_data()
		if d["k"] > 0.01:
			all.append(d)
	all.append_array(world.lights)
	var pos: Array[Vector4] = []
	var info: Array[Vector4] = []
	for l in all:
		var p := Vector2(float(l["x"]), float(l["y"]))
		var r := float(l["r"]) + 30.0
		if not view.grow(r).has_point(p):
			continue
		pos.append(Vector4(p.x, p.y, float(l["r"]), float(l["k"])))
		var kind: String = l["kind"]
		info.append(Vector4(KINDS.get(kind, 3.0), p.x, p.y, GLOW.get(kind, 4.0)))
		if pos.size() >= MAX_LIGHTS:
			break
	var n := pos.size()
	while pos.size() < MAX_LIGHTS:
		pos.append(Vector4.ZERO)
		info.append(Vector4.ZERO)
	var flies: Array[Vector4] = []                     # the fireflies' tiny lights: their own list, so the
	for sw in get_tree().get_nodes_in_group("fireflies"):  # lamps keep their 16 slots
		for l in sw.lights():
			if flies.size() < MAX_FLIES and view.grow(10.0).has_point(Vector2(l.x, l.y)):
				flies.append(l)
	var nf := flies.size()
	while flies.size() < MAX_FLIES:
		flies.append(Vector4.ZERO)
	post.set_shader_parameter("flies", flies)
	post.set_shader_parameter("fly_count", nf)
	post.set_shader_parameter("lights", pos)
	post.set_shader_parameter("light_info", info)
	post.set_shader_parameter("light_count", n)
