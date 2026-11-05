## Plays a footfall whenever a foot of the wanderer touches the ground, from the set that fits the ground.
class_name Footsteps
extends Node

var player: Player
var store: ChunkStore
var cave: Cave                       # its floor is earth and gravel
var _sets := {}
var _last := -1
var _out: AudioStreamPlayer
var _rustle: AudioStreamPlayer
var _steps := 0
const TALL_GRASS_Y := 1800.0         # from zone 2 on the grass stands tall (tools/world/south/zone2_draft.py)


## Whether a footfall here brushes through tall grass.
static func rustles(mat: int, y: float) -> bool:
	return mat == GroundMat.GRASS and y >= TALL_GRASS_Y


## Counts the step; true on every second one in tall grass (each one rustling was too busy).
func next_rustles(mat: int, y: float) -> bool:
	_steps += 1
	return rustles(mat, y) and _steps % 2 == 0


func _ready() -> void:
	_out = AudioStreamPlayer.new()
	_out.bus = AudioSetup.SOUNDS
	add_child(_out)
	_rustle = AudioStreamPlayer.new()
	_rustle.bus = AudioSetup.SOUNDS
	add_child(_rustle)
	if player != null:
		player.stepped.connect(_on_step)


const SET_DB := {"schritt_holz": 2.0}   # boards a touch louder: the bridge should be heard


func ground_at(p: Vector2) -> int:
	if cave != null and cave.contains(p):
		return GroundMat.EARTH
	return store.material_at(p) if store != null else GroundMat.GRASS


func _on_step() -> void:
	var mat := ground_at(player.position)
	if next_rustles(mat, player.position.y):
		if not _sets.has("rascheln"):
			_sets["rascheln"] = SoundBank.variants("rascheln")
		var r: Array = _sets["rascheln"]
		if not r.is_empty():                           # the blades pushed aside, a little under the footfall
			_rustle.stream = r[randi() % r.size()]
			_rustle.pitch_scale = randf_range(0.95, 1.05)
			_rustle.volume_db = randf_range(-13.0, -11.0)
			_rustle.play()
	var name := SoundBank.step_set(mat, player.position.y)
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
	_out.volume_db = randf_range(-10.5, -7.5) + SET_DB.get(name, 0.0)   # steps sit just under the meadow
	_out.play()
