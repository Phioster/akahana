extends TestCase

const PATH := "user://test_save.cfg"

func test_fresh_save_has_full_volume_and_no_position() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH))
	var s := SaveData.load_from(PATH)
	assert_false(s.has_position)
	assert_almost_eq(s.music, 1.0)
	assert_almost_eq(s.sounds, 1.0)

func test_position_and_volumes_survive_a_round_trip() -> void:
	var s := SaveData.new()
	s.set_position(Vector2(123.5, 456.0))
	s.music = 0.25
	s.sounds = 0.0
	s.save_to(PATH)
	var r := SaveData.load_from(PATH)
	assert_true(r.has_position)
	assert_eq(r.position, Vector2(123.5, 456.0))
	assert_almost_eq(r.music, 0.25)
	assert_almost_eq(r.sounds, 0.0)

func test_forget_position_starts_over_but_keeps_volumes() -> void:
	var s := SaveData.new()
	s.set_position(Vector2(5, 5))
	s.music = 0.5
	s.forget_position()
	s.save_to(PATH)
	var r := SaveData.load_from(PATH)
	assert_false(r.has_position)
	assert_almost_eq(r.music, 0.5)

func test_volume_maps_to_decibels_and_silence() -> void:
	assert_almost_eq(AudioSetup.to_db(1.0), 0.0)
	assert_true(AudioSetup.to_db(0.5) < -5.0 and AudioSetup.to_db(0.5) > -7.0, "halb = ca. -6 dB")
	assert_true(AudioSetup.to_db(0.0) <= -80.0, "null = stumm")

func test_old_position_moves_down_when_the_north_grew_on_top() -> void:
	var c := ConfigFile.new()                  # a save from before 0.11: no world height stored
	c.set_value("weg", "position", Vector2(243, 1070))
	c.save(PATH)
	var r := SaveData.load_from(PATH)
	r.fit_to(4800)
	assert_eq(r.position, Vector2(243, 2270))
	r.save_to(PATH)
	var again := SaveData.load_from(PATH)
	again.fit_to(4800)
	assert_eq(again.position, Vector2(243, 2270), "nur einmal verschieben")

func test_old_position_moves_right_when_the_west_grew_on_the_left() -> void:
	var c := ConfigFile.new()                  # a save from before 0.18: no world width stored
	c.set_value("weg", "position", Vector2(243, 2270))
	c.set_value("weg", "welthoehe", 4800)
	c.save(PATH)
	var r := SaveData.load_from(PATH)
	r.fit_to(4800, 2700)
	assert_eq(r.position, Vector2(1143, 2270))
	r.save_to(PATH)
	var again := SaveData.load_from(PATH)
	again.fit_to(4800, 2700)
	assert_eq(again.position, Vector2(1143, 2270), "nur einmal verschieben")
