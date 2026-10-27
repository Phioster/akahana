extends TestCase

## The game draws in the wallpaper's art resolution and only scales up, never smooths.
func test_art_resolution_and_nearest_filter() -> void:
	assert_eq(ProjectSettings.get_setting("display/window/size/viewport_width"), 180)
	assert_eq(ProjectSettings.get_setting("display/window/size/viewport_height"), 400)
	# canvas_items: drawn at full screen resolution, so the camera glides instead of jumping 7 screen px
	assert_eq(ProjectSettings.get_setting("display/window/stretch/mode"), "canvas_items")
	assert_eq(ProjectSettings.get_setting("rendering/textures/canvas_textures/default_texture_filter"), 0)

func test_portrait() -> void:
	assert_eq(ProjectSettings.get_setting("display/window/handheld/orientation"), 1)

func test_runs_at_a_steady_60_frames() -> void:
	# a fixed frame rate makes the scroll steps predictable, also on a 120 Hz screen
	assert_eq(int(ProjectSettings.get_setting("application/run/max_fps", 0)), 60)

func test_the_app_icon_is_the_journal() -> void:
	var f := FileAccess.open("res://export_presets.cfg", FileAccess.READ)
	var cfg := f.get_as_text()
	assert_true(cfg.contains('adaptive_foreground_432x432="res://assets/icon/vordergrund.png"'), "kein Godot-Logo mehr")
	assert_true(FileAccess.file_exists("res://assets/icon/vordergrund.png"))
	# themed launchers (Nothing) tint icons one colour: give them our own drawing, not a washed-out book
	assert_true(cfg.contains('adaptive_monochrome_432x432="res://assets/icon/einfarbig.png"'))

func test_the_game_is_called_akahana() -> void:
	assert_eq(ProjectSettings.get_setting("application/config/name"), "Akahana")
	var cfg := FileAccess.open("res://export_presets.cfg", FileAccess.READ).get_as_text()
	assert_true(cfg.contains('package/name="Akahana"'), "Name unter dem Symbol")
	assert_true(cfg.contains('package/unique_name="org.phioster.mohnweg"'), "Paket bleibt, sonst geht der Spielstand verloren")
	assert_eq(BookUI.TITLE, "Akahana")
