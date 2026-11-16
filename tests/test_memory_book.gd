extends TestCase
## The memory pages in the book and the bookmark on the book button.

func _book() -> BookUI:
	var b := BookUI.new()
	(Engine.get_main_loop() as SceneTree).root.add_child(b)
	b._in_game = true
	return b


func _texts(b: BookUI) -> Array:
	var out := []
	for c in b._content.get_children():
		if c is Label and not c.is_queued_for_deletion():
			out.append(c.text)
	return out


func test_no_memories_no_entry() -> void:
	var b := _book()
	b.mode = BookUI.Mode.MAIN
	b._apply_mode()
	assert_false(_texts(b).has("Erinnerungen"))
	b.queue_free()


func test_one_memory_shows_the_entry() -> void:
	var b := _book()
	b.memories = PackedStringArray(["muehle"])
	b.mode = BookUI.Mode.MAIN
	b._apply_mode()
	assert_true(_texts(b).has("Erinnerungen"))
	b.queue_free()


func test_memory_page_shows_title_picture_and_text() -> void:
	var b := _book()
	b.memories = PackedStringArray(["muehle"])
	b.mode = BookUI.Mode.MEMORIES
	b._apply_mode()
	var texts := _texts(b)
	assert_true(texts.has("Wassermühle"), str(texts))
	assert_true(texts.has("Suisha-goya"), str(texts))
	var pics := []
	for c in b._content.get_children():
		if c is TextureRect and c.size == Vector2(130, 87):
			pics.append(c)
	assert_eq(pics.size(), 1, "eine Skizze 130 × 87")
	if pics.size() == 1:
		assert_eq(pics[0].texture_filter, CanvasItem.TEXTURE_FILTER_LINEAR, "fein, nicht verpixelt")
		assert_true(pics[0].texture != null, "Bild geladen")
	var lines := Memories.wrap_text(Memories.place("muehle").text)
	for l in lines:
		assert_true(texts.has(l), "Zeile fehlt: " + l)
	b.queue_free()


func test_memory_text_stays_on_the_page() -> void:
	var b := _book()
	var limit: float = BookUI.PAPER_RIGHT - b._content.position.x
	for p in Memories.PLACES:
		b.memories = PackedStringArray([p.key])
		b._mem_page = 0
		b.mode = BookUI.Mode.MEMORIES
		b._apply_mode()
		for c in b._content.get_children():
			if c is Label and not c.is_queued_for_deletion():
				assert_true(c.position.x + c.get_minimum_size().x <= limit + 0.5, "%s: '%s'" % [p.key, c.text])
	b.queue_free()


func test_bookmark_shows_until_the_book_opens() -> void:
	var b := _book()
	b.mode = BookUI.Mode.CLOSED
	b._apply_mode()
	var seen := [false]
	b.bookmark_seen.connect(func(): seen[0] = true)
	b.set_bookmark(true)
	assert_true(b.has_bookmark())
	assert_true(b._mark.visible, "Band sichtbar am geschlossenen Buch")
	b.open_in_game()
	assert_false(b.has_bookmark())
	assert_false(b._mark.visible)
	assert_true(seen[0], "Signal kam")
	b.queue_free()


func test_new_page_while_book_is_open_is_there_next_time() -> void:
	var b := _book()
	b.open_in_game()
	b.memories.append("lager")
	b.set_bookmark(true)
	assert_true(b.has_bookmark(), "bleibt bis zum nächsten Öffnen")
	b.close()
	assert_true(b._mark.visible)
	b.open_in_game()
	assert_true(_texts(b).has("Erinnerungen"))
	assert_false(b.has_bookmark())
	b.queue_free()


func test_the_turned_stack_stays_within_the_drawn_sheets() -> void:
	# the page-turn shader draws at most 8 sheets lying back; deeper pages must not lift them further
	var b := _book()
	b._mem_page = 20
	assert_true(b._depth(BookUI.Mode.MEMORIES) <= 8, str(b._depth(BookUI.Mode.MEMORIES)))
	b.queue_free()
