## What the ground is made of, per 2-px cell (from gen_world.py's ground_mat.bin): picks the footstep sound.
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


static func load_default(world_w: int, world_h: int) -> GroundMat:
	var f := FileAccess.open(WorldData.DIR + "ground_mat.bin", FileAccess.READ)
	if f == null:
		return GroundMat.new()
	return GroundMat.new(f.get_buffer(f.get_length()), world_w / CELL, world_h / CELL)


func at(p: Vector2) -> int:
	var x := int(floor(p.x / CELL))
	var y := int(floor(p.y / CELL))
	if x < 0 or y < 0 or x >= w or y >= h:
		return GRASS
	return cells[y * w + x]
