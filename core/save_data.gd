## What survives closing the game: where the wanderer stood and the two volume sliders.
class_name SaveData
extends RefCounted

const DEFAULT_PATH := "user://mohnweg.cfg"

var has_position := false
var position := Vector2.ZERO
var world_h := 3600                  # the world's height when the position was saved (before 0.11: 3600)
var music := 1.0
var sounds := 1.0


static func load_from(path: String = DEFAULT_PATH) -> SaveData:
	var s := SaveData.new()
	var c := ConfigFile.new()
	if c.load(path) != OK:
		return s
	s.has_position = c.has_section_key("weg", "position")
	if s.has_position:
		s.position = c.get_value("weg", "position", Vector2.ZERO)
		s.world_h = int(c.get_value("weg", "welthoehe", 3600))
	s.music = float(c.get_value("ton", "musik", 1.0))
	s.sounds = float(c.get_value("ton", "geraeusche", 1.0))
	return s


func save_to(path: String = DEFAULT_PATH) -> void:
	var c := ConfigFile.new()
	if has_position:
		c.set_value("weg", "position", position)
		c.set_value("weg", "welthoehe", world_h)
	c.set_value("ton", "musik", music)
	c.set_value("ton", "geraeusche", sounds)
	c.save(path)


func set_position(p: Vector2) -> void:
	position = p
	has_position = true


func forget_position() -> void:
	has_position = false


## The world grew on top (the north): a position saved in a lower world moves down with everything else.
func fit_to(height: int) -> void:
	if has_position and world_h != height:
		position.y += float(height - world_h)
		world_h = height
