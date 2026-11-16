## Builds the world from the generated assets, follows the wanderer, feeds the atmosphere and poppy
## shaders, and wires in the journal (start, settings, memories), sound, birds, wisps and the saved position.
extends Node2D

const MAX_LIGHTS := 16
const MAX_FLIES := 40
const KINDS := {"fire": 0.0, "lantern": 1.0, "wood": 2.0, "candle": 3.0, "wisp": 4.0, "kerze": 3.0}
const GLOW := {"fire": 22.0, "lantern": 6.0, "wood": 8.0, "candle": 4.0, "wisp": 4.0, "kerze": 1.2}   # glowing pixels, for bloom
const SAVE_EVERY := 5.0
const CAM_EASE := 5.0                # how quickly the view catches up: starting and stopping glide
const CAM_MIN_SPEED := 4.0           # art px/s: the slowest it glides before arriving
const CAM_CALM := Vector2(10, 14)    # a box round the middle: small steps inside it leave the world still

const CANOPY_WALK := 0.6               # share of a crown left out over him while he walks ...
const CANOPY_REST := 0.8               # ... and standing, when he is hardest to find (Philip, 2026-11-04)
const CANOPY_EASE := 0.8               # seconds for the whole way between the two

var _canopy := CANOPY_REST
var world: WorldData
var pathing := Pathing.new()
var player: Player
var cam: Camera2D
var post: ShaderMaterial
var store: ChunkStore
var view_node: WorldView
var marker: TapMarker
var birds: Birds
var lake: LakeLife
var squirrels: Squirrels
var butterflies: Butterflies
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
var snowfall: Snowfall              # falling snow in the north
var weather := Weather.new()          # now and then a shower
var rain: Rain
var snow: SnowTrail                  # the furrow he leaves in fresh snow
var cave: Cave                       # the cave in the north, its own screen beside the world
var glashaus: Cave                   # the greenhouse in the west, three screens wide, beside the cave
var rain_sounds: RainSounds
var room: Cave                       # the place he is in (or last was in)
var inside := false
var _going := false                  # the screen is fading in or out of the cave
var _fade: ColorRect
const FADE := 0.4                    # s to black and back again
const MEM_EVERY := 0.25              # s between the memory keeper's looks at where he is
var keeper := MemoryKeeper.new()     # first visits: name scrolls and pages in the book
var scroll: NameScroll
var _mem_in := 0.0


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
	cave = Cave.new()                                    # under the y-sorted layer: he walks over it
	add_child(cave)
	cave.setup(Vector2(world.width, world.height))
	glashaus = Cave.new()
	add_child(glashaus)
	glashaus.setup(Vector2(world.width, world.height), "res://assets/world/glashaus/", "glashaus", cave.size.x + Cave.GAP)
	room = cave
	snow = SnowTrail.new()                               # over the ground, under everything standing
	snow.mat_at = store.material_at
	add_child(snow)
	sorted = Node2D.new()
	sorted.y_sort_enabled = true
	add_child(sorted)
	view_node.sorted = sorted
	view_node.load_around(_start_position())

	player = Player.new()
	player.position = _start_position()
	sorted.add_child(player)
	snow.player = player
	player.stepped.connect(snow.step)
	player.lantern.world_size = Vector2(world.width, world.height)
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
	squirrels = Squirrels.new()                            # at the broadleaf trees, out of sight at first
	squirrels.player = player
	squirrels.sorted = sorted
	squirrels.store = store
	add_child(squirrels)
	butterflies = Butterflies.new()                        # over the open meadow, not in the rain
	butterflies.world = world
	butterflies.player = player
	butterflies.sorted = sorted
	butterflies.store = store
	butterflies.weather = weather
	add_child(butterflies)

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
	post.set_shader_parameter("grade_field", TextureLoader.load_texture(WorldData.DIR + "grade_field.png"))
	post.set_shader_parameter("world_size", Vector2(world.width, world.height))
	rect.material = post
	layer.add_child(rect)
	var fall := CanvasLayer.new()                        # over the evening light (white on graded snow vanished),
	fall.layer = 10                                      # after it in the tree; it follows the camera like the world
	fall.follow_viewport_enabled = true
	add_child(fall)
	snowfall = Snowfall.new()
	snowfall.world = world
	snowfall.camera_at = func() -> Vector2: return get_viewport().get_canvas_transform().affine_inverse() * Vector2.ZERO
	fall.add_child(snowfall)
	rain = Rain.new()
	rain.world = world
	rain.weather = weather
	rain.camera_at = snowfall.camera_at
	fall.add_child(rain)
	var black := CanvasLayer.new()                       # over the mood: going in and out of the cave
	black.layer = 11
	add_child(black)
	_fade = ColorRect.new()
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.color = Color(0, 0, 0, 0)
	black.add_child(_fade)

	var steps := Footsteps.new()
	steps.player = player
	steps.store = store
	steps.rooms = [cave, glashaus]
	add_child(steps)
	var amb := Ambience.new()
	amb.world = world
	amb.player = player
	add_child(amb)
	add_child(Ducker.new())
	var music := Music.new()
	music.world = world
	music.player = player
	music.weather = weather
	add_child(music)
	rain_sounds = RainSounds.new()                       # the rain's sounds by place and strength, far thunder
	rain_sounds.world = world
	rain_sounds.player = player
	rain_sounds.weather = weather
	rain_sounds.glashaus = glashaus
	add_child(rain_sounds)

	book = BookUI.new()
	book.music = save.music
	book.sounds = save.sounds
	add_child(book)
	book.start_walking.connect(_on_start_walking)
	book.volumes_changed.connect(_on_volumes)
	book.camera_mode_changed.connect(_on_camera_mode)
	book.travel.connect(_on_travel)                       # testing aid (core/test_travel.gd)
	book.rain_test.connect(weather.toggle_now)            # testing aid
	book.memories = save.found.duplicate()
	book.set_bookmark(save.bookmark)
	book.bookmark_seen.connect(func(): save.bookmark = false; save.save_to())
	keeper.save = save
	var scroll_layer := CanvasLayer.new()                 # under the book (layer 20)
	scroll_layer.layer = 19
	add_child(scroll_layer)
	scroll = NameScroll.new()
	scroll_layer.add_child(scroll)
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
	save.fit_to(world.height, world.width)
	if save.has_position:
		store.load_now(world.grid.chunk_of(save.position))
		if store.walkable(save.position):
			return save.position
	return world.start


# ---------------------------------------------------------------- journal and saving

## The view's corner as it is shown: on the nearest screen pixel (px_per_art screen pixels per art pixel).
static func shown_corner(at: Vector2, view: Vector2, px_per_art: float) -> Vector2:
	return ((at - view * 0.5) * px_per_art).round() / px_per_art


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
	if inside:
		_set_inside(false)
	store.load_now(world.grid.chunk_of(to))
	view_node.load_around(to)
	player.path = PackedVector2Array()
	player.position = TestTravel.nearest_open(store, to)
	_cam_at = Vector2.INF
	_last_pos = player.position
	if _apply_memory_events(keeper.step(player.position, "", MemoryKeeper.DWELL)):   # a jump counts as a visit
		_store()


## Hands first visits on: the name scroll for regions and places, the page and the bookmark for places.
## Returns whether anything new was found (then the caller saves).
func _apply_memory_events(events: Array[Dictionary]) -> bool:
	var page := false
	for e in events:
		var d: Dictionary = Memories.region(e.key) if e.kind == "region" else Memories.place(e.key)
		scroll.show_name(d.kanji, d.romaji)
		if e.kind == "place":
			book.memories.append(e.key)
			book.set_bookmark(true)
			page = true
	if page:
		book._play("seite_%d" % (randi() % 3))          # the soft rustle of a page laid in
	return not events.is_empty()


func _room_name() -> String:
	if not inside:
		return ""
	return "cave" if room == cave else "glashaus"


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
	if inside:                                         # saved inside: he starts again at the mouth
		save.set_position(room.out_to)
		save.world_h = world.height
		save.world_w = world.width
	elif world != null and store.walkable(player.position):
		save.set_position(player.position)
		save.world_h = world.height
		save.world_w = world.width
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
	if _going:
		return
	var target: Vector2 = get_canvas_transform().affine_inverse() * event.position
	var way := room.find_path(player.position, target) if inside else pathing.find_path_in(store, player.position, target)
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
	weather.step(delta)
	var wet := rain.strength()
	# he keeps the lantern up after the shower until the ground has dried a good way (Philip 0.17.5)
	player.lantern.rain = maxf(wet, weather.wetness()) * Rain.reach(player.position.y)
	var moved := player.position - _last_pos
	trail.update(delta, player.position, moved, player.is_walking())
	_last_pos = player.position
	_cave_doors(moved)
	_mem_in -= delta
	if _mem_in <= 0.0 and not _going and book.mode != BookUI.Mode.START:
		_mem_in = MEM_EVERY
		if _apply_memory_events(keeper.step(player.position, _room_name(), MEM_EVERY)):
			_store()
	var u: Array = trail.uniforms()
	view_node.set_trail(u[0], u[1])
	_canopy = move_toward(_canopy, CANOPY_WALK if player.is_walking() else CANOPY_REST, delta * (CANOPY_REST - CANOPY_WALK) / CANOPY_EASE)
	view_node.set_wanderer(player.position, _canopy, player.silhouette())

	var view := get_viewport().get_visible_rect().size
	var c := player.position + _cam_offset                # no rounding: the camera glides in screen pixels
	var b := room.rect() if inside else Rect2(0, 0, world.width, world.height)
	for k in 2:
		c[k] = b.get_center()[k] if b.size[k] <= view[k] else clampf(c[k], b.position[k] + view[k] * 0.5, b.end[k] - view[k] * 0.5)
	if _camera_mode:
		_cam_offset = c - player.position                 # stop the offset growing past the world edge
	if _cam_at == Vector2.INF or _camera_mode:          # in camera mode your finger moves it directly
		_cam_at = c
		_cam_goal = c
	else:
		# the view only moves on once he leaves the calm box, and then just enough to keep him at its edge
		for k in 2:
			var off: float = c[k] - _cam_goal[k]
			if absf(off) > CAM_CALM[k]:
				_cam_goal[k] = c[k] - signf(off) * CAM_CALM[k]
		# rest on a whole pixel once he stands. Not while walking: rounding then made the steps uneven
		# (measured 0.7.10: 0.25 / 0.18 / 0 px a frame, felt as stutter); the half pixels were his sprite
		if not player.is_walking():
			_cam_goal = rest_goal(_cam_goal, view, _cam_at)
		# ease out, but never creep: below a small speed it rolls straight onto the goal and stops there
		# (the endless creep ended in a visible snap)
		var left := _cam_at.distance_to(_cam_goal)
		var go := maxf(left * (1.0 - exp(-CAM_EASE * delta)), CAM_MIN_SPEED * delta)
		_cam_at = _cam_at.move_toward(_cam_goal, go)
	# shown on whole SCREEN pixels (about 6 per art pixel): smooth, and world, sprites and post shader all
	# read the same spot (0.7.11: the post shader read at a spot between - the neighbour pixel for a moment)
	var scale := get_tree().root.get_final_transform().get_scale().x
	cam.position = shown_corner(_cam_at, view, maxf(scale, 1.0)) + view * 0.5
	cam.force_update_scroll()                          # apply now: the shader must snap to THIS frame's view
	var top_left := get_viewport().get_canvas_transform().affine_inverse() * Vector2.ZERO
	post.set_shader_parameter("view_world", view)
	post.set_shader_parameter("cam_pos", top_left)
	post.set_shader_parameter("rain", wet * Rain.reach(top_left.y + view.y * 0.5))
	view_node.set_weather(weather.wetness(), wet)       # the wet ground after the rain, its puddles
	var mm := player.mirror.material as ShaderMaterial
	mm.set_shader_parameter("wet", 0.0 if inside else weather.wetness())
	mm.set_shader_parameter("rain", wet)
	view_node.update(Rect2(top_left, view))
	birds.update_area(Rect2(top_left, view))
	lake.step(delta, Rect2(top_left, view))
	if not inside:                                     # no squirrels or butterflies in the cave or greenhouse
		squirrels.step(delta, Rect2(top_left, view))
		butterflies.step(delta, Rect2(top_left, view))
	_life.update(Rect2(top_left, view))
	_feed_lights(Rect2(top_left, view))

	_save_in -= delta
	if _save_in <= 0.0 and not player.is_walking():
		_save_in = SAVE_EVERY
		if book != null and not book.is_blocking():
			_store()


# ---------------------------------------------------------------- the cave and the greenhouse

## Walking up into the dark arch or the greenhouse door takes him in, walking down the end of its way out takes
## him out again.
func _cave_doors(moved: Vector2) -> void:
	if _going or moved == Vector2.ZERO:
		return
	if not inside:
		for r in [cave, glashaus]:
			if r.ok and r.at_mouth(player.position, moved):
				room = r
				_go(true)
				return
	elif room.at_exit(player.position, moved):
		_go(false)


func _go(into: bool) -> void:
	_going = true
	player.path = PackedVector2Array()
	var t := create_tween()
	t.tween_property(_fade, "color:a", 1.0, FADE)
	t.tween_callback(_set_inside.bind(into))
	t.tween_property(_fade, "color:a", 0.0, FADE)
	t.tween_callback(func(): _going = false)


func _set_inside(into: bool) -> void:
	inside = into
	post.set_shader_parameter("inside", 1.0 if into else 0.0)
	post.set_shader_parameter("warm_inside", 1.0 if into and room.warm else 0.0)
	snowfall.off = into                                  # the cave lies at the north's height: no snow in it
	rain.off = into
	if rain_sounds != null:
		rain_sounds.room = room if into else null   # inside the greenhouse its roof drums, in the cave it is quiet
	player.lantern.always_dark = into                    # inside it hangs on his staff, outside it goes as the light says
	var b := room.rect() if into else Rect2(0, 0, world.width, world.height)
	cam.limit_left = int(b.position.x)
	cam.limit_top = int(b.position.y)
	cam.limit_right = int(b.end.x)
	cam.limit_bottom = int(b.end.y)
	var at := room.inside_at(room.start) if into else room.out
	if not into:
		view_node.load_around(at)
	player.position = at
	_cam_at = Vector2.INF
	_cam_offset = Vector2.ZERO
	_last_pos = at
	var to := room.inside_at(room.start_to) if into else room.out_to
	var way := room.find_path(at, to) if into else pathing.find_path_in(store, at, to)
	if way.size() > 0:
		player.walk_to(way)
	if not into:
		_store()


func _feed_lights(view: Rect2) -> void:
	var all: Array = []
	for n in get_tree().get_nodes_in_group("dyn_light"):    # moving lights first: the wisps
		var d: Dictionary = n.light_data()
		if d["k"] > 0.01:
			all.append(d)
	if inside:
		all.append(room.light)
	else:
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
	var near: Array = []                               # everything that lights him, for robe and shadow
	for l in all:
		if not l.get("own", false) and Vector2(float(l["x"]), float(l["y"])).distance_to(player.position) < float(l["r"]) + 4.0:
			near.append(l)
	var flies: Array[Vector4] = []                     # the fireflies' tiny lights: their own list, so the
	for sw in get_tree().get_nodes_in_group("fireflies"):  # lamps keep their 16 slots
		for l in sw.lights():
			if flies.size() < MAX_FLIES and view.grow(10.0).has_point(Vector2(l.x, l.y)):
				flies.append(l)
	var nf := flies.size()
	while flies.size() < MAX_FLIES:
		flies.append(Vector4.ZERO)
	for sw in get_tree().get_nodes_in_group("fireflies"):
		for l in sw.lights():
			if Vector2(l.x, l.y).distance_to(player.position) < l.z + 4.0:
				near.append({"x": l.x, "y": l.y, "r": l.z, "k": absf(l.w)})
	player.set_light(PlayerLight.at(near, player.position))
	post.set_shader_parameter("flies", flies)
	post.set_shader_parameter("fly_count", nf)
	post.set_shader_parameter("lights", pos)
	post.set_shader_parameter("light_info", info)
	post.set_shader_parameter("light_count", n)
