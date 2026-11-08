## A place you go into, as its own screen beside the world, so world, camera and post shader keep their
## coordinates: the cave in the north (tools/world/gen_cave.py, 180 x 400 art px, lit by its candle) and the
## greenhouse in the west (gen_glashaus.py, 540 x 400, wider than a screen: the camera runs along it; its crowns
## and lianas hang over him on their own layer, its light stays warm). Its own walkable grid; inside the
## lantern hangs on his staff.
class_name Cave
extends Node2D

const DIR := "res://assets/world/cave/"
const GAP := 400.0                   # how far right of the world it lies: nothing of the world shows

var size := Vector2(180, 400)
var mouth := Rect2()                 # in the world: walking into it takes him in
var out := Vector2.ZERO              # in the world: where he steps out ...
var out_to := Vector2.ZERO           # ... and walks on to
var start := Vector2.ZERO            # inside (cave px): where he stands on coming in ...
var start_to := Vector2.ZERO         # ... and walks on to
var exit_y := 376.0                  # inside: walking down past this takes him out
var light := {}
var warm := false                    # its own warm grade (the greenhouse), not the evening's
var pathing := Pathing.new()
var ok := false


## dir/name: where its files lie (name.json, name.png, name_walk.bin, name_canopy.png); slot: how far beyond
## the first place it lies (one place beside the other, never overlapping).
func setup(world_size: Vector2, dir: String = DIR, name_: String = "cave", slot: float = 0.0) -> void:
	var f := FileAccess.open(dir + name_ + ".json", FileAccess.READ)
	if f == null:
		return
	var m: Dictionary = JSON.parse_string(f.get_as_text())
	size = Vector2(m["size"][0], m["size"][1])
	mouth = Rect2(m["mouth"][0], m["mouth"][1], m["mouth"][2], m["mouth"][3])
	out = Vector2(m["out"][0], m["out"][1])
	out_to = Vector2(m["out_to"][0], m["out_to"][1])
	start = Vector2(m["in"][0], m["in"][1])
	start_to = Vector2(m["in_to"][0], m["in_to"][1])
	exit_y = float(m["exit_y"])
	position = Vector2(world_size.x + GAP + slot, roundf(mouth.position.y - size.y * 0.5))   # beside the mouth's height: the same wind
	warm = bool(m.get("warm", false))
	light = (m["light"] as Dictionary).duplicate()
	light["x"] = float(light["x"]) + position.x
	light["y"] = float(light["y"]) + position.y
	# raw bytes like the world's walk.bin: nothing of the import between the generator and the grid
	var bytes := FileAccess.get_file_as_bytes(dir + name_ + "_walk.bin")
	var pic := TextureLoader.load_texture(dir + name_ + ".png")
	if bytes.size() != int(size.x * size.y) or pic == null:
		return
	pathing.build(bytes, int(size.x), int(size.y))
	var back := ColorRect.new()                        # beyond the picture: rock, black
	back.color = Color.BLACK
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE      # 0.12.0: it swallowed every tap inside, he could not walk
	back.position = Vector2(-GAP * 0.5, -size.y)
	back.size = Vector2(size.x + GAP, size.y * 3.0)
	add_child(back)
	var sp := Sprite2D.new()
	sp.texture = pic
	sp.centered = false
	add_child(sp)
	if bool(m.get("canopy", false)):                    # what hangs over him: above the y-sorted layer
		var top := Sprite2D.new()
		top.texture = TextureLoader.load_texture(dir + name_ + "_canopy.png")
		top.centered = false
		top.z_index = 10
		add_child(top)
	ok = true


func rect() -> Rect2:
	return Rect2(position, size)


func contains(p: Vector2) -> bool:
	return ok and rect().grow(8.0).has_point(p)


## In the world: is he walking up into the dark arch? Only going up: passing along below it is no way in.
func at_mouth(p: Vector2, moved: Vector2 = Vector2.UP) -> bool:
	return ok and moved.y < 0.0 and mouth.has_point(p)


## Inside: is he walking down the last stretch of the way out? Coming in he walks up through it.
func at_exit(p: Vector2, moved: Vector2 = Vector2.DOWN) -> bool:
	return moved.y > 0.0 and p.y - position.y >= exit_y


func inside_at(p: Vector2) -> Vector2:
	return position + p


func find_path(a: Vector2, b: Vector2) -> PackedVector2Array:
	var way := pathing.find_path(a - position, b - position)
	for i in way.size():
		way[i] += position
	return way
