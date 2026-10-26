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
var brook: Array = []                # points along the stream, for its sound and the frogs
var birds: Array = []                # open spots where small birds land
var wisps: Array = []                # where the will-o'-the-wisps live
var fire := {}
var walk := PackedByteArray()        # one byte per art pixel, 1 = walkable (until the chunks take over)
var chunks := Vector2i.ZERO          # how many chunks across and down
var grid: ChunkGrid


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
	d.brook = j.get("brook", [])
	d.birds = j.get("birds", [])
	d.wisps = j.get("wisps", [])
	d.fire = j.get("fire", {})
	var cs: Array = j.get("chunks", [0, 0])
	d.chunks = Vector2i(int(cs[0]), int(cs[1]))
	d.grid = ChunkGrid.new(d.chunks.x, d.chunks.y)
	var size: Array = j.get("chunk", [ChunkGrid.SIZE.x, ChunkGrid.SIZE.y])
	if Vector2i(int(size[0]), int(size[1])) != ChunkGrid.SIZE:
		push_error("world.json: Kachelgröße passt nicht zu ChunkGrid.SIZE")
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
