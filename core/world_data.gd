## The generated world: sizes, sprites, lights and how it is cut into chunks (the ground itself streams).
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
	return d

