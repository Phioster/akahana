## What survives closing the game: where the wanderer stood, the two volume sliders and the memories
## (pages found in the order found, regions whose name scroll was shown, the bookmark on the book).
class_name SaveData
extends RefCounted

const DEFAULT_PATH := "user://mohnweg.cfg"

var has_position := false
var position := Vector2.ZERO
var world_h := 3600                  # the world's height when the position was saved (before 0.11: 3600)
var world_w := 1800                  # ... and its width (before the west, 0.18: 1800)
var music := 1.0
var sounds := 1.0
var found := PackedStringArray()
var regions_seen := PackedStringArray()
var bookmark := false


static func load_from(path: String = DEFAULT_PATH) -> SaveData:
	var s := SaveData.new()
	var c := ConfigFile.new()
	if c.load(path) != OK:
		return s
	s.has_position = c.has_section_key("weg", "position")
	if s.has_position:
		s.position = c.get_value("weg", "position", Vector2.ZERO)
		s.world_h = int(c.get_value("weg", "welthoehe", 3600))
		s.world_w = int(c.get_value("weg", "weltbreite", 1800))
	s.music = float(c.get_value("ton", "musik", 1.0))
	s.sounds = float(c.get_value("ton", "geraeusche", 1.0))
	s.found = PackedStringArray(c.get_value("erinnerungen", "orte", PackedStringArray()))
	s.regions_seen = PackedStringArray(c.get_value("erinnerungen", "gebiete", PackedStringArray()))
	s.bookmark = bool(c.get_value("erinnerungen", "lesezeichen", false))
	return s


func save_to(path: String = DEFAULT_PATH) -> void:
	var c := ConfigFile.new()
	if has_position:
		c.set_value("weg", "position", position)
		c.set_value("weg", "welthoehe", world_h)
		c.set_value("weg", "weltbreite", world_w)
	c.set_value("ton", "musik", music)
	c.set_value("ton", "geraeusche", sounds)
	c.set_value("erinnerungen", "orte", found)
	c.set_value("erinnerungen", "gebiete", regions_seen)
	c.set_value("erinnerungen", "lesezeichen", bookmark)
	c.save(path)


func set_position(p: Vector2) -> void:
	position = p
	has_position = true


func forget_position() -> void:
	has_position = false


## The world grew on top (the north) and to the left (the west): a position saved in a smaller world moves
## down and right with everything else.
func fit_to(height: int, width: int = 1800) -> void:
	if has_position and world_h != height:
		position.y += float(height - world_h)
		world_h = height
	if has_position and world_w != width:
		position.x += float(width - world_w)
		world_w = width
