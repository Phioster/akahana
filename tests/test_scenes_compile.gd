extends TestCase

func test_scripts_and_shaders_load() -> void:
	for p in ["res://scenes/main.gd", "res://scenes/player.gd", "res://scenes/tap_marker.gd", "res://scenes/book_ui.gd",
			"res://scenes/ambience.gd", "res://scenes/birds.gd", "res://scenes/bird.gd", "res://scenes/wisp.gd",
			"res://scenes/footsteps.gd", "res://scenes/pencil_slider.gd", "res://scenes/pencil_line.gd", "res://scenes/tap_area.gd"]:
		var s: GDScript = load(p)
		assert_true(s != null and s.can_instantiate(), p)
	for p in ["res://shaders/post.gdshader", "res://shaders/flowers.gdshader"]:
		assert_true(load(p) is Shader, p)
