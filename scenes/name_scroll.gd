## The name scroll (approved preview B, 2026-11-16): a hanging kakemono in the top left corner with the
## Japanese name written downwards; the romaji hang below it on a small paper tag, dark, so they read on
## snow and on poppies alike. It unrolls, hangs for HOLD seconds, rolls up; names wait their turn.
## Never takes a tap (MOUSE_FILTER_IGNORE).
class_name NameScroll
extends Control

const HOLD := 3.0
const ROLL := 0.4
const AT := Vector2(14, 12)          # left edge of the paper, its top (the cord peaks 10 px higher)
const W := 24                        # paper width
const STEP := 17                     # per kanji
const PAPER := Color(233 / 255.0, 224 / 255.0, 203 / 255.0)
const WOOD := Color(92 / 255.0, 62 / 255.0, 40 / 255.0)
const CORD := Color(70 / 255.0, 50 / 255.0, 36 / 255.0)
const SILK := Color(150 / 255.0, 60 / 255.0, 48 / 255.0)
const INK := Color(58 / 255.0, 54 / 255.0, 54 / 255.0)
const SHADOW := Color(10 / 255.0, 6 / 255.0, 6 / 255.0, 0.35)

var _queue: Array = []               # [kanji, romaji]
var paused := false:                 # the book is open or the camera looks: wait unseen, go on after
	set(v):
		paused = v
		visible = not v
var _t := 0.0


func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)


func show_name(kanji: String, romaji: String) -> void:
	_queue.append([kanji, romaji])
	if _queue.size() == 1:
		_t = 0.0
	queue_redraw()


func showing() -> String:
	return _queue[0][0] if not _queue.is_empty() else ""


func _process(delta: float) -> void:
	if not _queue.is_empty() and not paused:
		advance(delta)


## Moves the scroll on by dt seconds (the game's clock, or a test's).
func advance(dt: float) -> void:
	_t += dt
	while not _queue.is_empty() and _t >= ROLL * 2.0 + HOLD:
		_t -= ROLL * 2.0 + HOLD
		_queue.pop_front()
	if _queue.is_empty():
		_t = 0.0
	queue_redraw()


static func _height(kanji: String) -> int:
	return kanji.length() * STEP + 14


static func _tag(romaji: String) -> Rect2:
	var uw := PixelFont.hand().get_string_size(romaji, HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.HAND_SIZE).x
	var tw := int(uw) + 8
	return Rect2(maxf(2.0, AT.x + (W - tw) / 2.0), 0, tw, 13)


## Everything the scroll covers when fully open: rod and cord on top to the tag below.
static func bounds(kanji: String, romaji: String) -> Rect2:
	var h := _height(kanji)
	var tag := _tag(romaji)
	tag.position.y = AT.y + h + 4
	var r := Rect2(AT.x - 3, AT.y - 10, W + 6, h + 10)
	return r.merge(Rect2(tag.position, tag.size + Vector2(2, 2)))


func _draw() -> void:
	if _queue.is_empty():
		return
	var kanji: String = _queue[0][0]
	var romaji: String = _queue[0][1]
	var open := clampf(minf(_t, ROLL * 2.0 + HOLD - _t) / ROLL, 0.0, 1.0)
	var x := AT.x
	var y := AT.y
	var h := _height(kanji)
	var vis := roundf(h * open)                  # how much paper has rolled down
	draw_line(Vector2(x + W / 2 - 6, y - 6), Vector2(x + W / 2, y - 10), CORD)
	draw_line(Vector2(x + W / 2 + 6, y - 6), Vector2(x + W / 2, y - 10), CORD)
	if vis > 2.0:
		draw_rect(Rect2(x + 2, y - 2, W, vis), SHADOW)
		draw_rect(Rect2(x, y - 4, W, vis), PAPER)
		draw_rect(Rect2(x + 1, y - 4, W - 2, 3), SILK)
		var kf := PixelFont.kanji()
		for i in kanji.length():
			var top := y + 2 + i * STEP
			if top + STEP - 2 > y - 4 + vis:
				break
			var c := kanji[i]
			var cw := kf.get_string_size(c, HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.KANJI_SIZE).x
			draw_string(kf, Vector2(roundf(x + (W - cw) / 2.0), top + kf.get_ascent(PixelFont.KANJI_SIZE)), c,
				HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.KANJI_SIZE, INK)
	draw_rect(Rect2(x - 3, y - 6, W + 6, 3), WOOD)                    # top rod
	draw_rect(Rect2(x - 3, y - 4 + maxf(vis, 3.0), W + 6, 3), WOOD)   # bottom rod, rides down as it unrolls
	if open >= 1.0:
		var tag := _tag(romaji)
		tag.position.y = y + h + 4
		draw_line(Vector2(x + W / 2 - 3, y + h - 1), Vector2(tag.position.x + 3, tag.position.y), CORD)
		draw_line(Vector2(x + W / 2 + 3, y + h - 1), Vector2(tag.end.x - 4, tag.position.y), CORD)
		draw_rect(Rect2(tag.position + Vector2(2, 2), tag.size), SHADOW)
		draw_rect(tag, PAPER)
		var hf := PixelFont.hand()
		draw_string(hf, Vector2(tag.position.x + 4, tag.position.y - 3 + hf.get_ascent(PixelFont.HAND_SIZE)), romaji,
			HORIZONTAL_ALIGNMENT_LEFT, -1, PixelFont.HAND_SIZE, INK)
