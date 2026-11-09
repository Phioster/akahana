extends SceneTree

const SUITES := [
	"res://tests/test_project_settings.gd",
	"res://tests/test_world_data.gd",
	"res://tests/test_pathing.gd",
	"res://tests/test_player.gd",
	"res://tests/test_scenes_compile.gd",
	"res://tests/test_pixel_font.gd",
	"res://tests/test_save_data.gd",
	"res://tests/test_pencil_slider.gd",
	"res://tests/test_life.gd",
	"res://tests/test_lake_life.gd",
	"res://tests/test_chunks.gd",
	"res://tests/test_cave.gd",
	"res://tests/test_snow_trail.gd",
	"res://tests/test_snowfall.gd",
	"res://tests/test_rain.gd",
	"res://tests/test_animals.gd",
]

func _init() -> void:
	await process_frame
	var total := 0
	var failed := 0
	for path in SUITES:
		var script: GDScript = load(path)
		if script == null or not script.can_instantiate():
			_suite_broken("Testdatei nicht ladbar", path)
			failed += 1
			continue
		var suite = script.new()
		if not (suite is TestCase):
			_suite_broken("Keine TestCase", path)
			failed += 1
			continue
		for method in suite.get_method_list():
			var name: String = method.name
			if not name.begins_with("test_"):
				continue
			total += 1
			suite.failures.clear()
			await suite.call(name)
			if suite.failures.is_empty():
				print("  ok    %s::%s" % [path.get_file(), name])
			else:
				failed += 1
				print("  FAIL  %s::%s" % [path.get_file(), name])
				for f in suite.failures:
					print("        %s" % f)
	print("")
	print("%d Tests, %d fehlgeschlagen" % [total, failed])
	quit(1 if failed > 0 else 0)


func _suite_broken(reason: String, path: String) -> void:
	push_error("%s: %s" % [reason, path])
	print("  SUITE KAPUTT  %s -- %s (kein Test daraus lief)" % [path.get_file(), reason])
