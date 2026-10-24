extends TestCase

## The game draws in the wallpaper's art resolution and only scales up, never smooths.
func test_art_resolution_and_nearest_filter() -> void:
	assert_eq(ProjectSettings.get_setting("display/window/size/viewport_width"), 180)
	assert_eq(ProjectSettings.get_setting("display/window/size/viewport_height"), 400)
	assert_eq(ProjectSettings.get_setting("display/window/stretch/mode"), "viewport")
	assert_eq(ProjectSettings.get_setting("rendering/textures/canvas_textures/default_texture_filter"), 0)

func test_portrait() -> void:
	assert_eq(ProjectSettings.get_setting("display/window/handheld/orientation"), 1)
