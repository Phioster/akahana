## The world cut into chunks of SIZE art pixels: which chunk a point lies in, which chunks a view needs.
class_name ChunkGrid
extends RefCounted

const SIZE := Vector2i(180, 200)     # one screen wide, half a screen tall (tools/world/split_chunks.py)
const APRON := 8                     # extra poppy pixels round each chunk, for shifts across the edge

var cols := 0
var rows := 0


func _init(c: int = 0, r: int = 0) -> void:
	cols = c
	rows = r


func chunk_of(p: Vector2) -> Vector2i:
	return Vector2i(floori(p.x / SIZE.x), floori(p.y / SIZE.y))


func contains(c: Vector2i) -> bool:
	return c.x >= 0 and c.y >= 0 and c.x < cols and c.y < rows


func rect_of(c: Vector2i) -> Rect2:
	return Rect2(Vector2(c * SIZE), Vector2(SIZE))


## All chunks touching r, clipped to the world, row by row.
func chunks_in(r: Rect2) -> Array[Vector2i]:
	var out: Array[Vector2i] = []
	var a := chunk_of(r.position)
	var b := chunk_of(r.end - Vector2(0.001, 0.001))
	for y in range(maxi(a.y, 0), mini(b.y, rows - 1) + 1):
		for x in range(maxi(a.x, 0), mini(b.x, cols - 1) + 1):
			out.append(Vector2i(x, y))
	return out
