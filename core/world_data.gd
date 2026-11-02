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
var fireflies: Array = []            # swarms: home spot and every fly's loop
var lamp_paths: Array = []           # lanterns by the lake: where their light's path on the water starts
var fire := {}
var places := {}                     # named spots of the Ostwald: ritual, pond, graves (for their sounds)
var mood: Array = []                 # the wood's darkness 0..100 per MOOD_CELL px square, rows of mood_w
var mood_w := 0
const MOOD_CELL := 20.0
var chunks := Vector2i.ZERO          # how many chunks across and down
var grid: ChunkGrid


## How deep in the dark wood this spot is: 0 on the meadow and in the south .. 1 deep in the Ostwald.
func wood_at(p: Vector2) -> float:
	if mood.is_empty() or mood_w <= 0:
		return 0.0
	var x := clampi(int(p.x / MOOD_CELL), 0, mood_w - 1)
	var y := clampi(int(p.y / MOOD_CELL), 0, mood.size() / mood_w - 1)
	return float(mood[y * mood_w + x]) / 100.0


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
	d.fireflies = j.get("fireflies", [])
	d.lamp_paths = j.get("lamp_paths", [])
	d.fire = j.get("fire", {})
	d.places = j.get("places", {})
	d.mood = j.get("mood", [])
	d.mood_w = int(j.get("mood_w", 0))
	var cs: Array = j.get("chunks", [0, 0])
	d.chunks = Vector2i(int(cs[0]), int(cs[1]))
	d.grid = ChunkGrid.new(d.chunks.x, d.chunks.y)
	var size: Array = j.get("chunk", [ChunkGrid.SIZE.x, ChunkGrid.SIZE.y])
	if Vector2i(int(size[0]), int(size[1])) != ChunkGrid.SIZE:
		push_error("world.json: Kachelgröße passt nicht zu ChunkGrid.SIZE")
	return d

