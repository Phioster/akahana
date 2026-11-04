## The red paper lantern on the tip of his staff: in the dark places (grade_field R, the wood's darkness)
## he stops and hangs it up (Player.hang_lantern, drawn in wanderer_laterne.png), on leaving them he takes
## it down again. While it hangs this node draws it and it is a moving light.
class_name Lantern
extends Node2D

const TIP_X := [9, 2, 7, 3]          # the staff's tip per facing (Player.Dir), in the 12x16 frame
const HANG_X := [10, 1, 8, 2]        # the lantern's middle: on the staff's outer side, in profile right against it
const HELD := [[Vector2i(9, 13), Vector2i(11, 9)], [Vector2i(2, 13), Vector2i(0, 9)],   # its glowing pixel while in
		[Vector2i(8, 13), Vector2i(9, 9)], [Vector2i(2, 13), Vector2i(1, 9)]]       # his hand (phases 0, 1 per facing)
const TIP_Y := [1, 1, 0, 1, 0, 0, 1, 0]   # the tip bobs with the frame (sheet columns)
const DARK_ON := 0.55                # grade_field darkness from which he hangs it up ...
const DARK_OFF := 0.35               # ... and below which he takes it down (apart: no dithering at the edge)
const FRAME_OFFSET := Vector2(-6, -15)   # the plain frame's top-left from his feet (Player)
const WOOD := Color8(156, 126, 94)
const CAP := Color8(52, 38, 34)
const RED := Color8(196, 62, 44)
const HOT := Color8(255, 186, 104)
const DEEP := Color8(120, 34, 30)

var player: Player
var world_size := Vector2(1800, 3600)   # main sets the real one
var lit := 0.0
var carried := false                 # it hangs on the staff
var _field: Image
var _cell := Vector2i(-1, -1)


func _ready() -> void:
	add_to_group("dyn_light")
	var t := TextureLoader.load_texture(WorldData.DIR + "grade_field.png")
	if t != null:
		_field = t.get_image()


## 0 on the meadow .. 1 deep in the wood.
func darkness(world: Vector2, world_size: Vector2) -> float:
	if _field == null:
		return 0.0
	var p := Vector2i((world / world_size * Vector2(_field.get_size())).floor())
	p = p.clamp(Vector2i.ZERO, _field.get_size() - Vector2i.ONE)
	return _field.get_pixelv(p).r


func _process(_delta: float) -> void:
	if player == null:
		return
	var d := darkness(player.global_position, world_size)
	if not player.is_hanging():
		if not carried and d >= DARK_ON:
			player.hang_lantern(true)
		elif carried and d <= DARK_OFF:
			carried = false                  # in his hand again: the sheet shows it from here
			player.hang_lantern(false)
	var p := player.hang_progress()
	if p >= 0.0:
		lit = p if player._hang_up else 1.0 - p
	else:
		lit = 1.0 if carried else 0.0
	var key := Vector2i(player.sprite.frame, 1 if carried and not player.is_hanging() else 0)
	if key != _cell:
		_cell = key
		queue_redraw()


## The lantern's glowing pixel in the 12x16 frame (feet at (6, 15)).
func hang_point() -> Vector2i:
	if player.is_hanging():
		var k := player.hang_phase()
		if k <= 1:
			return HELD[player.dir][k]
	var ty := 1 if player.is_hanging() else int(TIP_Y[player.sprite.frame % Player.COLS])
	return Vector2i(HANG_X[player.dir], ty + 3)


func light_data() -> Dictionary:
	var p := player.global_position.round() + Vector2(hang_point()) + FRAME_OFFSET + Vector2(0.5, 0.5)
	return {"x": p.x, "y": p.y, "r": 30.0, "k": 0.9 * lit, "kind": "lantern", "own": true}   # own: not on his robe


func _draw() -> void:
	if player == null or not carried or player.is_hanging():
		return
	var tx: int = TIP_X[player.dir]
	var cx: int = HANG_X[player.dir]
	var ty: int = TIP_Y[player.sprite.frame % Player.COLS]
	var o := FRAME_OFFSET
	var px := func(x: int, y: int, c: Color): draw_rect(Rect2(o + Vector2(x, y), Vector2.ONE), c)
	for x in range(mini(tx, cx), maxi(tx, cx) + 1):   # the hook from the staff's tip out to the string
		if x != tx:
			px.call(x, ty, WOOD)
	var y0 := ty + 2
	px.call(cx, ty + 1, CAP)
	for x in [cx - 1, cx, cx + 1]:
		px.call(x, y0, CAP)
	px.call(cx - 1, y0 + 1, RED)
	px.call(cx, y0 + 1, HOT)
	px.call(cx + 1, y0 + 1, RED)
	px.call(cx - 1, y0 + 2, DEEP)
	px.call(cx, y0 + 2, RED)
	px.call(cx + 1, y0 + 2, DEEP)
	px.call(cx, y0 + 3, CAP)
