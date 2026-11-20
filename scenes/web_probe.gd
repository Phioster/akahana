## Browser test run (only with ?probe in the address): walks, jumps, opens the book, lets it rain, and
## prints frame times and memory per stage as "PROBE {json}" lines for the test page to collect.
class_name WebProbe
extends Node

const HITCH_MS := 50.0                 # a frame this long is a visible stutter

var main: Node
var _stage := ""
var _frames: PackedFloat32Array = []
var _flags := ""                       # from the address: noreflect, stay (narrowing down a fault)
var _beat := 0.0


static func wanted() -> bool:
	if not OS.has_feature("web"):
		return false
	return str(JavaScriptBridge.eval("location.search", true)).contains("probe")


## Frame times (ms) to the numbers the report keeps.
static func stats(ms: PackedFloat32Array) -> Dictionary:
	if ms.is_empty():
		return {"frames": 0}
	var s := ms.duplicate()
	s.sort()
	var total := 0.0
	var hitches := 0
	for v in ms:
		total += v
		if v >= HITCH_MS:
			hitches += 1
	return {"frames": ms.size(), "fps": snappedf(1000.0 * ms.size() / total, 0.1),
			"p95_ms": snappedf(s[int(0.95 * (s.size() - 1))], 0.1), "max_ms": snappedf(s[s.size() - 1], 0.1),
			"hitches": hitches}


func _process(delta: float) -> void:
	if _stage != "":
		_frames.append(delta * 1000.0)
	_beat += delta
	if _beat >= 1.0:                   # a heartbeat: the last one before a fault shows where it stood
		_beat = 0.0
		var m := _memory()
		m["stage"] = _stage
		m["pos"] = main.player.position
		_report("beat", m)


func _ready() -> void:
	_run.call_deferred()


func _report(kind: String, data: Dictionary) -> void:
	data["kind"] = kind
	data["t_ms"] = Time.get_ticks_msec()
	print("PROBE " + JSON.stringify(data))


func _memory() -> Dictionary:
	return {"static_mb": snappedf(Performance.get_monitor(Performance.MEMORY_STATIC) / 1048576.0, 0.1),
			"video_mb": snappedf(Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED) / 1048576.0, 0.1),
			"texture_mb": snappedf(Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED) / 1048576.0, 0.1),
			"objects": Performance.get_monitor(Performance.OBJECT_COUNT)}


func _measure(stage: String, seconds: float, until := Callable()) -> void:
	_stage = stage
	_frames = PackedFloat32Array()
	var left := seconds
	while left > 0.0:
		await get_tree().process_frame
		left -= get_process_delta_time()
		if until.is_valid() and until.call():
			break
	_stage = ""
	var r := stats(_frames)
	r.merge(_memory())
	r["stage"] = stage
	_report("stage", r)


func _run() -> void:
	_report("boot", {"adapter": RenderingServer.get_video_adapter_name(), "vendor": RenderingServer.get_video_adapter_vendor(),
			"api": RenderingServer.get_video_adapter_api_version(), "screen": DisplayServer.screen_get_size(),
			"window": DisplayServer.window_get_size()})
	_flags = str(JavaScriptBridge.eval("location.search", true))
	var book: BookUI = main.book
	if _flags.contains("noreflect"):
		main.player.mirror.material = null
		main.player.mirror.visible = false
		main.player.mirror.set_process(false)
	await _measure("startbild", 3.0)
	book._start(true)
	await _measure("lager_stehen", 5.0)
	if _flags.contains("stay"):
		await _measure("nur_stehen", 60.0)
		_report("done", _memory())
		return
	for target in [Vector2(1200, 2600), Vector2(1262, 3150), Vector2(1494, 3500)]:
		var way: PackedVector2Array = main.pathing.find_path_in(main.store, main.player.position, target)
		main.player.walk_to(way)
		await _measure("laufen_%d_%d" % [target.x, target.y], 25.0, func(): return not main.player.is_walking())
	for p in [["norden_pass", Vector2(1380, 135)], ["bergsee", Vector2(1990, 680)], ["ostwald", Vector2(2150, 2900)],
			["seesteg", Vector2(1474, 4145)], ["dorf", Vector2(536, 2344)], ["muehle", Vector2(560, 3340)]]:
		main._on_travel(p[1])
		await _measure("sprung_" + p[0], 4.0)
	main.weather.toggle_now()
	await _measure("regen", 8.0)
	book.open_in_game()
	await _measure("buch_auf", 2.0)
	book._turn_to(BookUI.Mode.MEMORIES)
	await _measure("erinnerungen", 2.0)
	for i in 3:
		book._mem_page += 1
		book._turn_to(BookUI.Mode.MEMORIES)
		await _measure("umblaettern_%d" % i, 1.5)
	_report("done", _memory())
