## Diagnosis aid (0.4.1): notes every late frame with what was going on, and a run of camera steps
## while walking, into user://frames.log - read back with adb run-as. Remove once the jolt is found.
class_name FrameLog
extends Node

const PATH := "user://frames.log"
const LATE := 1.5 / 60.0             # a frame half again as long as it should be
const STEPS := 240                   # camera steps kept per walk sample

var frames := 0
var late: Array[String] = []
var steps := PackedStringArray()
var _flush_in := 5.0
var _t := 0.0


func note(delta: float, what: String) -> void:
	frames += 1
	_t += delta
	if delta > LATE:
		late.append("%.1f s: %d ms | %s" % [_t, roundi(delta * 1000.0), what])


## One line per frame while walking: frame time and how far the view moved (screen px).
func step(delta: float, cam_move: Vector2) -> void:
	if steps.size() < STEPS:
		steps.append("%.1f ms  %.2f,%.2f" % [delta * 1000.0, cam_move.x, cam_move.y])


func _process(delta: float) -> void:
	_flush_in -= delta
	if _flush_in <= 0.0:
		_flush_in = 5.0
		flush()


func flush() -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	if f == null:
		return
	f.store_line("Bilder %d, zu spät %d" % [frames, late.size()])
	for l in late.slice(-200):
		f.store_line(l)
	f.store_line("--- Kameraschritte beim Laufen (Bildzeit, Verschiebung in Bildschirmpixeln)")
	for s in steps:
		f.store_line(s)
