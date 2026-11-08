extends TestCase

func _press(s: PencilSlider, at: Vector2) -> void:
	var e := InputEventMouseButton.new()
	e.button_index = MOUSE_BUTTON_LEFT
	e.pressed = true
	e.position = at
	s._gui_input(e)

func _slider() -> PencilSlider:
	var s := PencilSlider.new()
	s.size = Vector2(110, 10) + 2.0 * PencilSlider.PAD
	s.value = 0.5
	return s

func test_the_touch_room_is_much_taller_than_the_line() -> void:
	# Philip 0.18.3: the sliders were 10 art px tall, hard to hit with a finger
	var s := _slider()
	assert_true(s.size.y >= 30.0, "mindestens 30 px hoch zum Antippen")
	s.free()

func test_a_tap_beside_the_line_still_sets_it_and_the_ends_are_reachable() -> void:
	var s := _slider()
	_press(s, Vector2(PencilSlider.PAD.x + 55.0, 2.0))          # well above the line
	assert_almost_eq(s.value, 0.5, 0.05)
	_press(s, Vector2(s.size.x - 1.0, s.size.y - 1.0))           # right of its end: full
	assert_almost_eq(s.value, 1.0, 0.001)
	_press(s, Vector2(0.0, 0.0))                                  # left of its start: silent
	assert_almost_eq(s.value, 0.0, 0.001)
	s.free()
