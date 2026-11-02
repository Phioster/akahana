extends TestCase

func test_far_from_every_light_he_is_untouched() -> void:
	var r := PlayerLight.at([{"x": 0.0, "y": 0.0, "r": 30.0, "k": 1.0}], Vector2(200, 200))
	assert_eq(r["dim"], 1.0)
	assert_eq(r["a"], 0.0, "kein Schatten ohne Licht")

func test_in_the_glow_his_robe_is_darker_and_his_shadow_falls_away_from_the_lamp() -> void:
	var r := PlayerLight.at([{"x": 100.0, "y": 100.0, "r": 30.0, "k": 0.7}], Vector2(110, 100))
	assert_true(r["dim"] < 0.8, "dunkler im Licht")
	assert_true(r["a"] > 0.3, "Schatten sichtbar")
	assert_true(r["dir"].x > 0.9, "Schatten zeigt von der Lampe weg (nach rechts)")

func test_the_shadow_is_longer_the_closer_to_the_light() -> void:
	var lamp := [{"x": 100.0, "y": 100.0, "r": 30.0, "k": 0.7}]
	var near := PlayerLight.at(lamp, Vector2(106, 100))
	var far := PlayerLight.at(lamp, Vector2(128, 100))
	assert_true(near["len"] > far["len"])
