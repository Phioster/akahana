## The music: one calm piece, then a long pause where only nature is heard, then again.
## The piece exists twice in the same length (tools/gen_music.py): the meadow's and a darker one for the Ostwald
## (melody an octave down, a drone under it, a longer room). Both always play together and are crossfaded by how
## deep in the wood the wanderer stands, so the song changes softly with the region and never restarts.
class_name Music
extends Node

const PATH := "res://assets/audio/musik.ogg"
const PATH_DARK := "res://assets/audio/musik_dunkel.ogg"
const PAUSE_MIN := 45.0
const PAUSE_MAX := 90.0
const LEVEL_DB := -9.0               # under the meadow, not on top of it
const OFF_DB := -60.0

var world: WorldData
var player: Node2D
var _p: AudioStreamPlayer
var _dark: AudioStreamPlayer
var _wait := 0.0
var _wood := 0.0                     # smoothed depth in the wood, 0..1


static func _stream(path: String) -> AudioStream:
	var stream: AudioStream = null
	if ResourceLoader.exists(path):
		stream = load(path)
	else:
		stream = AudioStreamOggVorbis.load_from_file(ProjectSettings.globalize_path(path))
	if stream is AudioStreamOggVorbis:
		stream.loop = false
	return stream


## Volumes (dB) of the meadow's and the dark version at a wood depth: equal-power crossfade.
static func mix_db(wood: float) -> Vector2:
	var w := clampf(wood, 0.0, 1.0)
	return Vector2(LEVEL_DB + linear_to_db(maxf(cos(w * PI * 0.5), 0.0001)),
			LEVEL_DB + linear_to_db(maxf(sin(w * PI * 0.5), 0.0001)))


func _ready() -> void:
	_p = _make(PATH)
	_dark = _make(PATH_DARK)
	_p.finished.connect(func(): _wait = randf_range(PAUSE_MIN, PAUSE_MAX))
	_apply()
	_p.play()
	_dark.play()


func _make(path: String) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.stream = _stream(path)
	p.volume_db = LEVEL_DB
	p.bus = AudioSetup.MUSIC_TRACK
	add_child(p)
	return p


func _apply() -> void:
	var m := mix_db(_wood)
	_p.volume_db = maxf(m.x, OFF_DB)
	_dark.volume_db = maxf(m.y, OFF_DB)


func _process(delta: float) -> void:
	if world != null and player != null:
		_wood = lerpf(_wood, world.wood_at(player.position), clampf(delta * 0.15, 0.0, 1.0))   # a slow turn, over seconds
		_apply()
	if _wait > 0.0:
		_wait -= delta
		if _wait <= 0.0:
			_p.play()
			_dark.play()
