## Builds the world from the generated assets, follows the wanderer, feeds the atmosphere shader.
extends Node2D

const MAX_LIGHTS := 16
const KINDS := {"fire": 0.0, "lantern": 1.0, "wood": 2.0, "candle": 3.0}
const GLOW := {"fire": 40.0, "lantern": 6.0, "wood": 8.0, "candle": 4.0}   # glowing pixels per light, for bloom

var world: WorldData
var pathing := Pathing.new()
var player: Player
var cam: Camera2D
var post: ShaderMaterial
var animated: Array = []             # [Sprite2D, frames, fps]
var marker: Node2D
var _time := 0.0


func _ready() -> void:
	world = WorldData.load_default()
	if world == null:
		return
	var ground := _flat("res://assets/world/ground.png")
	add_child(ground)
	var flowers := _flat("res://assets/world/flowers.png")
	var fmat := ShaderMaterial.new()
	fmat.shader = load("res://shaders/flowers.gdshader")
	fmat.set_shader_parameter("tex_size", Vector2(world.width, world.height))
	flowers.material = fmat
	add_child(flowers)

	var sorted := Node2D.new()
	sorted.y_sort_enabled = true
	add_child(sorted)
	for s in world.sprites:
		var sp := Sprite2D.new()
		sp.texture = TextureLoader.load_texture("res://assets/world/sprites/%s.png" % s["name"])
		sp.centered = false
		sp.hframes = int(s["frames"])
		sp.position = Vector2(float(s["x"]), float(s["foot"]))
		sp.offset = Vector2(0, float(s["y"]) - float(s["foot"]))
		sorted.add_child(sp)
		if int(s["frames"]) > 1:
			animated.append([sp, int(s["frames"]), float(s["fps"])])

	player = Player.new()
	player.position = world.start
	sorted.add_child(player)

	marker = TapMarker.new()
	add_child(marker)

	var cells := FileAccess.open(WorldData.DIR + "walk_cells.bin", FileAccess.READ)
	if cells != null:
		pathing.build_cells(cells.get_buffer(cells.get_length()), world.width / Pathing.CELL, world.height / Pathing.CELL)
	else:
		pathing.build(world.walk, world.width, world.height)

	cam = Camera2D.new()
	cam.limit_left = 0
	cam.limit_top = 0
	cam.limit_right = world.width
	cam.limit_bottom = world.height
	add_child(cam)
	cam.make_current()

	var layer := CanvasLayer.new()
	layer.layer = 10
	add_child(layer)
	var rect := ColorRect.new()
	rect.set_anchors_preset(Control.PRESET_FULL_RECT)
	rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	post = ShaderMaterial.new()
	post.shader = load("res://shaders/post.gdshader")
	post.set_shader_parameter("mist1", TextureLoader.load_texture(WorldData.DIR + "mist1.png"))
	post.set_shader_parameter("mist2", TextureLoader.load_texture(WorldData.DIR + "mist2.png"))
	rect.material = post
	layer.add_child(rect)

	Music.start(self)


func _flat(path: String) -> Sprite2D:
	var sp := Sprite2D.new()
	sp.texture = TextureLoader.load_texture(path)
	sp.centered = false
	return sp


func _unhandled_input(event: InputEvent) -> void:
	var pressed := false
	if event is InputEventScreenTouch and event.pressed:
		pressed = true
	elif event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		pressed = true
	if not pressed:
		return
	var target: Vector2 = get_canvas_transform().affine_inverse() * event.position
	var way := pathing.find_path(player.position, target)
	if way.size() > 0:
		player.walk_to(way)
		marker.show_at(way[way.size() - 1])


func _process(delta: float) -> void:
	if world == null:
		return
	_time += delta
	for a in animated:
		a[0].frame = int(_time * a[2]) % a[1]
	var view := get_viewport().get_visible_rect().size
	var c := player.position                    # no rounding: the camera glides in screen pixels
	c.x = clampf(c.x, view.x * 0.5, world.width - view.x * 0.5)
	c.y = clampf(c.y, view.y * 0.5, world.height - view.y * 0.5)
	cam.position = c
	var top_left := cam.position - view * 0.5
	post.set_shader_parameter("view_world", view)
	post.set_shader_parameter("cam_pos", top_left)
	_feed_lights(Rect2(top_left, view))


func _feed_lights(view: Rect2) -> void:
	var pos: Array[Vector4] = []
	var info: Array[Vector4] = []
	for l in world.lights:
		var p := Vector2(float(l["x"]), float(l["y"]))
		var r := float(l["r"]) + 30.0
		if not view.grow(r).has_point(p):
			continue
		pos.append(Vector4(p.x, p.y, float(l["r"]), float(l["k"])))
		var kind: String = l["kind"]
		info.append(Vector4(KINDS.get(kind, 3.0), p.x, p.y, GLOW.get(kind, 4.0)))
		if pos.size() >= MAX_LIGHTS:
			break
	while pos.size() < MAX_LIGHTS:
		pos.append(Vector4.ZERO)
		info.append(Vector4.ZERO)
	post.set_shader_parameter("lights", pos)
	post.set_shader_parameter("light_info", info)
	post.set_shader_parameter("light_count", _count(pos))


func _count(pos: Array[Vector4]) -> int:
	var n := 0
	for p in pos:
		if p.z > 0.0:
			n += 1
	return n
