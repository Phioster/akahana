## The world as the camera sees it: ground and poppies chunk by chunk, the standing objects only near
## the view. Loads a chunk ahead, lets go two chunks behind, so walking never meets an empty edge.
class_name WorldView
extends Node2D

const OBJ_NEAR := 40.0               # objects appear this far outside the view ...
const OBJ_FAR := 120.0               # ... and go only beyond this

var world: WorldData
var store: ChunkStore
var sorted: Node2D                   # the y-sorted layer objects stand in (the wanderer lives there too)
var _shader: Shader = preload("res://shaders/flowers.gdshader")
var _chunks := {}                    # Vector2i -> [ground Sprite2D, flowers Sprite2D]
var _keep: Array[Vector2i] = []
var _objects := Activator.new()
var _objects_ready := false
var _animated := {}                  # Sprite2D -> [frames, fps]
var _t := 0.0
var _trail := [[], []]


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
	_objects.update(view)


## Load the chunks under a spot right now (the start: the ground must be there before frame one).
func load_around(p: Vector2) -> void:
	var size := Vector2(ChunkGrid.SIZE)
	for c in store.grid.chunks_in(Rect2(p - size, size * 2.0)):
		store.load_now(c)


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
	_feed(m)
	f.material = m
	add_child(f)
	_chunks[c] = [g, f]


func _add_objects() -> void:
	_objects_ready = true
	for s in world.sprites:
		var where := Rect2(float(s["x"]), float(s["y"]), float(s["w"]), float(s["h"]))
		_objects.add(where, OBJ_NEAR, OBJ_FAR, _make_object.bind(s), _drop_object)


func _make_object(s: Dictionary) -> Node:
	var sp := Sprite2D.new()
	sp.texture = TextureLoader.load_texture("res://assets/world/sprites/%s.png" % s["name"])
	sp.centered = false
	sp.hframes = int(s["frames"])
	sp.position = Vector2(float(s["x"]), float(s["foot"]))
	sp.offset = Vector2(0, float(s["y"]) - float(s["foot"]))
	sorted.add_child(sp)
	if int(s["frames"]) > 1:
		_animated[sp] = [int(s["frames"]), float(s["fps"])]
	return sp


func _drop_object(n: Node) -> void:
	_animated.erase(n)
	n.queue_free()
