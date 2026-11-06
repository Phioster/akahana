## The world as the camera sees it: ground and poppies chunk by chunk, the standing objects only near
## the view. Loads a chunk ahead, lets go two chunks behind, so walking never meets an empty edge.
class_name WorldView
extends Node2D

const OBJ_NEAR := 40.0               # objects appear this far outside the view ...
const OBJ_FAR := 120.0               # ... and go only beyond this
const PRE_NEAR := 110.0              # their pictures start loading in the background this far out ...
const PRE_FAR := 170.0               # ... and are let go beyond this (0.10.2: loading them on the spot stalled frames)

var world: WorldData
var store: ChunkStore
var sorted: Node2D                   # the y-sorted layer objects stand in (the wanderer lives there too)
var _shader: Shader = preload("res://shaders/flowers.gdshader")
var _water: Shader = preload("res://shaders/water.gdshader")
var _canopy := ShaderMaterial.new()  # shared by every standing object: opens what stands in front of him
var _chunks := {}                    # Vector2i -> [ground Sprite2D, flowers Sprite2D]
var _keep: Array[Vector2i] = []
var _objects := Activator.new()
var _objects_ready := false
var _prefetch := Activator.new()
var _fetched := {}                   # sprite path -> true while its picture loads or waits in the background
var _animated := {}                  # Sprite2D -> [frames, fps]
var _t := 0.0
var _trail := [[], []]
var _puddles: Texture2D               # where it gets wet and where puddles stand (tools/world/gen_wet.py)
var _wet := 0.0
var _rain := 0.0


func _init() -> void:
	_canopy.shader = preload("res://shaders/canopy.gdshader")


func _process(delta: float) -> void:
	_t += delta
	for sp in _animated:
		sp.frame = int(_t * _animated[sp][1]) % _animated[sp][0]


func update(view: Rect2) -> void:
	if not _objects_ready:
		_add_objects()
	var size := Vector2(ChunkGrid.SIZE)
	var near := store.grid.chunks_in(view.grow_individual(size.x, size.y, size.x, size.y))
	var far := store.grid.chunks_in(view.grow_individual(2 * size.x, 2 * size.y, 2 * size.x, 2 * size.y))
	var keep: Array[Vector2i] = near.duplicate()
	for c in _keep:                                    # hysteresis: keep what is still within two chunks
		if far.has(c) and not keep.has(c):
			keep.append(c)
	_keep = keep
	store.want(keep)
	store.poll()
	for c in _chunks.keys():
		if not keep.has(c):
			for n in _chunks[c]:
				n.queue_free()
			_chunks.erase(c)
	for c in keep:
		if not _chunks.has(c) and store.is_ready(c):
			_make_chunk(c)
	_prefetch.update(view)
	_objects.update(view)


## Load the chunks under a spot right now (the start: the ground must be there before frame one).
func load_around(p: Vector2) -> void:
	var size := Vector2(ChunkGrid.SIZE)
	for c in store.grid.chunks_in(Rect2(p - size, size * 2.0)):
		store.load_now(c)


func set_wanderer(feet: Vector2, open_share: float, look: Dictionary = {}) -> void:
	_canopy.set_shader_parameter("wanderer", feet)
	_canopy.set_shader_parameter("open_share", open_share)
	if not look.is_empty():
		var r: Rect2 = look["rect"]
		var uv: Rect2 = look["uv"]
		var lamp: Rect2 = look["lamp"]
		_canopy.set_shader_parameter("monk_tex", look["tex"])
		_canopy.set_shader_parameter("monk_rect", Vector4(r.position.x, r.position.y, r.size.x, r.size.y))
		_canopy.set_shader_parameter("monk_uv", Vector4(uv.position.x, uv.position.y, uv.size.x, uv.size.y))
		_canopy.set_shader_parameter("lamp_rect", Vector4(lamp.position.x, lamp.position.y, lamp.size.x, lamp.size.y))


## After the rain: how wet the ground is and how hard it rains now (Weather), for every chunk's ground.
func set_weather(wet: float, rain_now: float) -> void:
	if absf(wet - _wet) < 0.002 and absf(rain_now - _rain) < 0.002 and (wet > 0.0) == (_wet > 0.0):
		return
	_wet = wet
	_rain = rain_now
	for c in _chunks:
		_feed_weather(_chunks[c][0].material)


func _feed_weather(m: ShaderMaterial) -> void:
	m.set_shader_parameter("wet", _wet)
	m.set_shader_parameter("rain", _rain)


func puddles() -> Texture2D:
	if _puddles == null:
		_puddles = TextureLoader.load_texture(WorldData.DIR + "puddles.png")
	return _puddles


func set_trail(points: Array, k: Array) -> void:
	_trail = [points, k]
	for c in _chunks:
		_feed(_chunks[c][1].material)


func chunk_nodes() -> int:
	return _chunks.size()


func wanted_count() -> int:
	return _keep.size()


func object_nodes() -> int:
	return _objects.active_count()


func _feed(m: ShaderMaterial) -> void:
	if not _trail[0].is_empty():
		m.set_shader_parameter("trail", _trail[0])
		m.set_shader_parameter("trail_k", _trail[1])


func _make_chunk(c: Vector2i) -> void:
	var corner := Vector2(c * ChunkGrid.SIZE)
	var g := Sprite2D.new()
	g.texture = store.ground_tex(c)
	g.centered = false
	g.position = corner
	g.z_index = -2
	var wm := ShaderMaterial.new()                     # the brooks flow, the lake ripples (water map per chunk)
	wm.shader = _water
	wm.set_shader_parameter("water_tex", store.water_tex(c))
	wm.set_shader_parameter("origin", corner)
	wm.set_shader_parameter("refl_tex", store.refl_tex(c))      # the shore mirrored, pulled by the ripples
	wm.set_shader_parameter("apron", float(ChunkGrid.APRON))
	var lamps := PackedVector2Array()                  # lanterns whose light lies on this chunk's water
	for l in world.lamp_paths:
		var at := Vector2(float(l["x"]), float(l["y"]))
		if Rect2(corner - Vector2(4, 40), Vector2(ChunkGrid.SIZE) + Vector2(8, 40)).has_point(at):
			lamps.append(at)
	wm.set_shader_parameter("lamps", lamps)
	wm.set_shader_parameter("lamp_count", lamps.size())
	var wl := PackedVector4Array()                     # lights whose streak over the wet ground reaches this chunk
	for l in world.lights:
		var at := Vector2(float(l["x"]), float(l["y"]))
		if wl.size() < 8 and Rect2(corner - Vector2(40, 64), Vector2(ChunkGrid.SIZE) + Vector2(80, 104)).has_point(at):
			wl.append(Vector4(at.x, at.y, float(l["k"]), 1.0 if l["kind"] == "fire" else 0.0))
	wm.set_shader_parameter("wlights", wl)
	wm.set_shader_parameter("wlight_count", wl.size())
	wm.set_shader_parameter("puddles", puddles())
	wm.set_shader_parameter("world_size", Vector2(world.width, world.height))
	_feed_weather(wm)
	g.material = wm
	add_child(g)
	var f := Sprite2D.new()
	f.texture = store.flowers_tex(c)
	f.centered = false
	f.region_enabled = true                            # draw the chunk, read the apron round it
	f.region_rect = Rect2(Vector2(ChunkGrid.APRON, ChunkGrid.APRON), Vector2(ChunkGrid.SIZE))
	f.position = corner
	f.z_index = -1
	var m := ShaderMaterial.new()
	m.shader = _shader
	m.set_shader_parameter("tex_size", Vector2(ChunkGrid.SIZE + Vector2i(2, 2) * ChunkGrid.APRON))
	m.set_shader_parameter("origin", corner - Vector2(ChunkGrid.APRON, ChunkGrid.APRON))
	m.set_shader_parameter("ground_tex", store.ground_tex(c))   # the trail darkens the ground it lays bare
	m.set_shader_parameter("bend_tex", store.bend_tex(c))
	_feed(m)
	f.material = m
	add_child(f)
	_chunks[c] = [g, f]


func _add_objects() -> void:
	_objects_ready = true
	_objects.step = 3.0              # well inside the 40 px they wake ahead of the view
	_prefetch.step = 12.0            # well inside the 60 px between the prefetch ring and the objects' ring
	for s in world.sprites:
		var where := Rect2(float(s["x"]), float(s["y"]), float(s["w"]), float(s["h"]))
		_objects.add(where, OBJ_NEAR, OBJ_FAR, _make_object.bind(s), _drop_object)
		_prefetch.add(where, PRE_NEAR, PRE_FAR, _fetch.bind(_path(s)), _unfetch.bind(_path(s)))


static func _path(s: Dictionary) -> String:
	return "res://assets/world/sprites/%s.png" % s["name"]


## Export only (the dev device has no import cache and loads on the spot as before). The picture is kept
## while he is within PRE_FAR, so an object dropped and made again does not load it a second time.
func _fetch(path: String) -> Node:
	if ResourceLoader.exists(path) and not _fetched.has(path):
		ResourceLoader.load_threaded_request(path)
		_fetched[path] = null
	return null


func _unfetch(_n: Node, path: String) -> void:
	if _fetched.has(path) and _fetched[path] == null \
			and ResourceLoader.load_threaded_get_status(path) == ResourceLoader.THREAD_LOAD_LOADED:
		ResourceLoader.load_threaded_get(path)      # a finished load waits in the loader until taken
	_fetched.erase(path)


func _texture(path: String) -> Texture2D:
	if _fetched.has(path):
		if _fetched[path] == null and ResourceLoader.load_threaded_get_status(path) == ResourceLoader.THREAD_LOAD_LOADED:
			_fetched[path] = ResourceLoader.load_threaded_get(path)
		if _fetched[path] != null:
			return _fetched[path]
	var t := TextureLoader.load_texture(path)
	if _fetched.has(path) and _fetched[path] == null:
		ResourceLoader.load_threaded_get(path)       # finish the background request (load() shared its result)
		_fetched[path] = t
	return t


func _make_object(s: Dictionary) -> Node:
	var sp := Sprite2D.new()
	sp.texture = _texture(_path(s))
	sp.centered = false
	sp.hframes = int(s["frames"])
	sp.material = _canopy
	# half a pixel below its foot row: standing on that very row he is behind it, for the y-sort and the
	# canopy alike (a tie drew the tree over him without opening it, 0.11.8)
	sp.position = Vector2(float(s["x"]), float(s["foot"]) + 0.5)
	sp.offset = Vector2(0, float(s["y"]) - float(s["foot"]) - 0.5)
	sorted.add_child(sp)
	if int(s["frames"]) > 1:
		_animated[sp] = [int(s["frames"]), float(s["fps"])]
	return sp


func _drop_object(n: Node) -> void:
	_animated.erase(n)
	n.queue_free()
