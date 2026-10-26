## What the ground is made of, per 2-px cell. In the game each chunk's _mat.bin holds these values
## (ChunkStore.material_at); this small holder serves hand-made grids in tests.
class_name GroundMat
extends RefCounted

enum { GRASS, EARTH, STONE, WOOD, SNOW, WET }
const CELL := 2

var cells := PackedByteArray()
var w := 0
var h := 0


func _init(data: PackedByteArray = PackedByteArray(), cw: int = 0, ch: int = 0) -> void:
	cells = data
	w = cw
	h = ch


func at(p: Vector2) -> int:
	var x := int(floor(p.x / CELL))
	var y := int(floor(p.y / CELL))
	if x < 0 or y < 0 or x >= w or y >= h:
		return GRASS
	return cells[y * w + x]
