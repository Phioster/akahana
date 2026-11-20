extends TestCase
## The browser test run: off in the game itself, and the numbers it reports.

func test_probe_stays_off_outside_the_browser() -> void:
	assert_false(WebProbe.wanted())


func test_frame_stats() -> void:
	var r := WebProbe.stats(PackedFloat32Array([10.0, 10.0, 20.0, 60.0]))
	assert_eq(r["frames"], 4)
	assert_eq(r["fps"], 40.0)
	assert_eq(r["max_ms"], 60.0)
	assert_eq(r["hitches"], 1)
	assert_eq(WebProbe.stats(PackedFloat32Array())["frames"], 0)
