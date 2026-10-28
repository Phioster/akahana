## Diagnosis aid (0.7.10, like 0.4.1): the last 1500 frames, each with its frame time, whether he walks,
## where the view's corner lies between two pixels and how far it moved - into user://frames.log, read back
## with adb run-as. For the half-pixel moments and the felt stutter; remove once both are found.
class_name FrameLog
extends Node

const PATH := "user://frames.log"
const KEEP := 1500                   # about 25 s at 60 frames
const LATE := 1.5 / 60.0

var frames := 0
var late := 0
var lines := PackedStringArray()
var _flush_in := 5.0
var _t := 0.0


## corner: the view's top-left in world pixels; screen: the canvas origin in screen pixels.
func note(delta: float, walking: bool, corner: Vector2, moved: Vector2, screen: Vector2, what: String) -> void:
	frames += 1
	_t += delta
	if delta > LATE:
		late += 1
	var fx := corner - corner.floor()
	lines.append("%.2f %4.1fms %s ecke %.2f,%.2f schritt %.2f,%.2f bild %.2f,%.2f %s" % [_t, delta * 1000.0,
			"L" if walking else "S", fx.x, fx.y, moved.x, moved.y, screen.x - floorf(screen.x),
			screen.y - floorf(screen.y), what])
	if lines.size() > KEEP:
		lines = lines.slice(lines.size() - KEEP)


func _process(delta: float) -> void:
	_flush_in -= delta
	if _flush_in <= 0.0:
		_flush_in = 5.0
		flush()


func flush() -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f == null:
		return
	f.store_line("Bilder %d, zu spät %d, fps %d" % [frames, late, Engine.get_frames_per_second()])
	for l in lines:
		f.store_line(l)
