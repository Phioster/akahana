## The generated world: sizes, sprites, lights and the walkable mask.
## Everything comes from tools/world/gen_world.py; nothing here is hand-placed.
class_name WorldData
extends RefCounted

const DIR := "res://assets/world/"

var width := 0
var height := 0
var frames := 1
var fps := 8.0
var start := Vector2.ZERO
var sprites: Array = []
var lights: Array = []
var walk := PackedByteArray()        # one byte per art pixel, 1 = walkable


static func load_default() -> WorldData:
	var d := WorldData.new()
	var f := FileAccess.open(DIR + "world.json", FileAccess.READ)
	if f == null:
		push_error("world.json fehlt")
		return null
	var j: Dictionary = JSON.parse_string(f.get_as_text())
	d.width = int(j["width"])
	d.height = int(j["height"])
	d.frames = int(j["frames"])
	d.fps = float(j["fps"])
	d.start = Vector2(float(j["start"]["x"]), float(j["start"]["y"]))
	d.sprites = j["sprites"]
	d.lights = j["lights"]
	var w := FileAccess.open(DIR + "walk.bin", FileAccess.READ)
	if w == null:
		push_error("walk.bin fehlt")
		return null
	d.walk = w.get_buffer(d.width * d.height)
	return d


func is_walkable(p: Vector2) -> bool:
	var x := int(floor(p.x))
	var y := int(floor(p.y))
	if x < 0 or y < 0 or x >= width or y >= height:
		return false
	return walk[y * width + x] != 0
