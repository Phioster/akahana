extends TestCase
## The browser's picture: as tall as the app on tall screens, wider on wider ones (iPad), up to MAX_W.

func test_tall_screen_keeps_the_apps_width() -> void:
	var f := WebFit.fit(Vector2(1260, 2800))
	assert_eq(f["size"], Vector2i(180, 400))
	assert_eq(f["aspect"], Window.CONTENT_SCALE_ASPECT_KEEP_WIDTH)


func test_phone_with_address_bar_grows_a_little() -> void:
	var f := WebFit.fit(Vector2(1260, 2469))
	assert_eq(f["size"], Vector2i(204, 400))
	assert_eq(f["aspect"], Window.CONTENT_SCALE_ASPECT_KEEP)


func test_ipad_upright_fills_the_screen() -> void:
	assert_eq(WebFit.fit(Vector2(834, 1194))["size"], Vector2i(279, 400))


func test_wide_screens_stop_at_max_width() -> void:
	assert_eq(WebFit.fit(Vector2(1194, 834))["size"], Vector2i(WebFit.MAX_W, 400))
