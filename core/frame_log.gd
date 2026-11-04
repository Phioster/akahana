## Diagnosis aid (0.10.2, like 0.7.10): the last 3000 frames with frame time, whether he walks, how many objects
## were made and how many of their pictures had to load on the spot, and the world update's own time - into
## user://frames.log, read back with adb run-as. Remove once the forest's mini stutter is understood.
class_name FrameLog
extends Node

const PATH := "user://frames.log"
const KEEP := 3000                   # about 50 s at 60 frames
const LATE := 1.5 / 60.0

var frames := 0
var late := 0
var lines := PackedStringArray()
var _flush_in := 5.0
var _t := 0.0


func note(delta: float, walking: bool, at: Vector2, woke: int, woke_sync: int, update_us: int, awake: int) -> void:
	frames += 1
	_t += delta
	if delta > LATE:
		late += 1
	lines.append("%.2f %4.1fms %s bei %d,%d neu %d sofort %d welt %dus wach %d" % [_t, delta * 1000.0,
			"L" if walking else "S", int(at.x), int(at.y), woke, woke_sync, update_us, awake])
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
	f.store_line("Bilder %d, zu spaet %d, fps %d" % [frames, late, Engine.get_frames_per_second()])
	for l in lines:
		f.store_line(l)
