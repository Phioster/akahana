## Plays a footfall whenever a foot of the wanderer touches the ground, from the set that fits the ground.
class_name Footsteps
extends Node

var player: Player
var ground: GroundMat
var _sets := {}
var _last := -1
var _out: AudioStreamPlayer


func _ready() -> void:
	_out = AudioStreamPlayer.new()
	_out.bus = AudioSetup.SOUNDS
	add_child(_out)
	if player != null:
		player.stepped.connect(_on_step)


func _on_step() -> void:
	var name := SoundBank.step_set(ground.at(player.position) if ground != null else GroundMat.GRASS, player.position.y)
	if not _sets.has(name):
		_sets[name] = SoundBank.variants(name)
	var v: Array = _sets[name]
	if v.is_empty():
		return
	var i := randi() % v.size()
	if i == _last and v.size() > 1:                  # never the same recording twice in a row
		i = (i + 1) % v.size()
	_last = i
	_out.stream = v[i]
	_out.pitch_scale = randf_range(0.95, 1.05)
	_out.volume_db = randf_range(-10.5, -7.5)       # steps sit just under the meadow
	_out.play()
