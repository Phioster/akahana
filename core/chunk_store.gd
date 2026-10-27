## The chunks around the camera: their small data (walkable cells, ground material) loads at once,
## their pictures in the background so walking never stalls. Everything not wanted is forgotten.
class_name ChunkStore
extends RefCounted

const CELLS := Vector2i(ChunkGrid.SIZE.x / Pathing.CELL, ChunkGrid.SIZE.y / Pathing.CELL)
const OFF_PATH := 3.0                # grass and snow cost this much more than paths (as Pathing)

var grid: ChunkGrid
var dir := ""
var _cells := {}                     # Vector2i -> PackedByteArray
var _mat := {}
var walls := {}                      # Vector2i -> PackedInt32Array of wall cell indices (for Pathing)
var paths := {}                      # ... and of the cheap ground
var _tex := {}                       # Vector2i -> [ground, flowers] once ready
var _pending := {}                   # Vector2i -> {path: loader} for pictures still loading
var _mutex := Mutex.new()
var _images := {}                    # path -> Image, filled by worker threads (dev device only)


func _init(g: ChunkGrid, d: String = WorldData.DIR + "chunks/") -> void:
	grid = g
	dir = d


func _base(c: Vector2i) -> String:
	return dir + "c_%d_%d_" % [c.x, c.y]


func want(keep: Array[Vector2i]) -> void:
	for c in _cells.keys():
		if not keep.has(c):
			_cells.erase(c)
			_mat.erase(c)
			walls.erase(c)
			paths.erase(c)
			_tex.erase(c)
			_pending.erase(c)
	for c in keep:
		if grid.contains(c) and not _cells.has(c):
			_load_data(c)
			_start_pictures(c)


## Turns pictures that finished loading into textures (main thread); returns the chunks now ready.
func poll() -> Array[Vector2i]:
	var done: Array[Vector2i] = []
	for c in _pending.keys():
		var g := _base(c) + "ground.png"
		var f := _base(c) + "flowers.png"
		var wt := _base(c) + "water.png"
		var bd := _base(c) + "bend.png"
		if not (_arrived(g) and _arrived(f) and _arrived(wt) and _arrived(bd)):   # all or none: a taken one is gone
			continue
		_tex[c] = [_take(g), _take(f), _take(wt), _take(bd)]
		_pending.erase(c)
		done.append(c)
	return done


## Everything at once, for the start: the ground under the wanderer must be there before frame one.
func load_now(c: Vector2i) -> void:
	if not grid.contains(c):
		return
	if not _cells.has(c):
		_load_data(c)
	_tex[c] = [TextureLoader.load_texture(_base(c) + "ground.png"), TextureLoader.load_texture(_base(c) + "flowers.png"),
			TextureLoader.load_texture(_base(c) + "water.png"), TextureLoader.load_texture(_base(c) + "bend.png")]
	_pending.erase(c)


func is_ready(c: Vector2i) -> bool:
	return _tex.has(c)


func ground_tex(c: Vector2i) -> Texture2D:
	return _tex[c][0] if _tex.has(c) else null


func flowers_tex(c: Vector2i) -> Texture2D:
	return _tex[c][1] if _tex.has(c) else null


func water_tex(c: Vector2i) -> Texture2D:
	return _tex[c][2] if _tex.has(c) else null


func bend_tex(c: Vector2i) -> Texture2D:
	return _tex[c][3] if _tex.has(c) else null


func loaded_count() -> int:
	return _cells.size()


## Cell coordinates are world-wide (Pathing.CELL px each).
func cell_free(cell: Vector2i) -> bool:
	var b: PackedByteArray = _cells.get(_chunk_of_cell(cell), PackedByteArray())
	return not b.is_empty() and b[_index(cell)] != 0


func cell_weight(cell: Vector2i) -> float:
	var b: PackedByteArray = _mat.get(_chunk_of_cell(cell), PackedByteArray())
	if b.is_empty():
		return OFF_PATH
	var m := b[_index(cell)]
	return OFF_PATH if m == GroundMat.GRASS or m == GroundMat.SNOW else 1.0


func walkable(p: Vector2) -> bool:
	return cell_free(Vector2i(floori(p.x / Pathing.CELL), floori(p.y / Pathing.CELL)))


func material_at(p: Vector2) -> int:
	var cell := Vector2i(floori(p.x / Pathing.CELL), floori(p.y / Pathing.CELL))
	var b: PackedByteArray = _mat.get(_chunk_of_cell(cell), PackedByteArray())
	return GroundMat.GRASS if b.is_empty() else b[_index(cell)]


func _chunk_of_cell(cell: Vector2i) -> Vector2i:
	return Vector2i(floori(float(cell.x) / CELLS.x), floori(float(cell.y) / CELLS.y))


func _index(cell: Vector2i) -> int:
	return posmod(cell.y, CELLS.y) * CELLS.x + posmod(cell.x, CELLS.x)


func _load_data(c: Vector2i) -> void:
	for pair in [[_cells, "cells.bin"], [_mat, "mat.bin"]]:
		var f := FileAccess.open(_base(c) + pair[1], FileAccess.READ)
		pair[0][c] = f.get_buffer(f.get_length()) if f != null else PackedByteArray()
	for pair in [[walls, "walls.bin"], [paths, "paths.bin"]]:
		var f := FileAccess.open(_base(c) + pair[1], FileAccess.READ)
		pair[0][c] = f.get_buffer(f.get_length()).to_int32_array() if f != null else PackedInt32Array()


## Exported game: Godot's threaded loader. Dev device (no import cache): an Image on a worker thread.
func _start_pictures(c: Vector2i) -> void:
	_pending[c] = true
	for path in [_base(c) + "ground.png", _base(c) + "flowers.png", _base(c) + "water.png", _base(c) + "bend.png"]:
		if ResourceLoader.exists(path):
			ResourceLoader.load_threaded_request(path)
		else:
			var full := ProjectSettings.globalize_path(path)
			WorkerThreadPool.add_task(func():
				var img := Image.load_from_file(full)
				_mutex.lock()
				_images[path] = img
				_mutex.unlock())


func _arrived(path: String) -> bool:
	if ResourceLoader.exists(path):
		return ResourceLoader.load_threaded_get_status(path) == ResourceLoader.THREAD_LOAD_LOADED
	_mutex.lock()
	var there := _images.has(path)
	_mutex.unlock()
	return there


## Rebuilds a chunk's wall and path lists from its cells (hand-made grids in tests; old chunk files).
func reindex(c: Vector2i) -> void:
	var w := PackedInt32Array()
	var p := PackedInt32Array()
	var cells: PackedByteArray = _cells[c]
	var mat: PackedByteArray = _mat[c]
	for i in cells.size():
		if cells[i] == 0:
			w.append(i)
		elif mat[i] != GroundMat.GRASS and mat[i] != GroundMat.SNOW:
			p.append(i)
	walls[c] = w
	paths[c] = p


func _take(path: String) -> Texture2D:
	if ResourceLoader.exists(path):
		if ResourceLoader.load_threaded_get_status(path) != ResourceLoader.THREAD_LOAD_LOADED:
			return null
		return ResourceLoader.load_threaded_get(path)
	_mutex.lock()
	var img: Image = _images.get(path)
	if img != null:
		_images.erase(path)
	_mutex.unlock()
	return ImageTexture.create_from_image(img) if img != null else null
