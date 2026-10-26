## The music: one calm piece, then a long pause where only nature is heard, then again.
class_name Music
extends Node

const PATH := "res://assets/audio/musik.ogg"
const PAUSE_MIN := 45.0
const PAUSE_MAX := 90.0

var _p: AudioStreamPlayer
var _wait := 0.0


func _ready() -> void:
	var stream: AudioStream = null
	if ResourceLoader.exists(PATH):
		stream = load(PATH)
	else:
		stream = AudioStreamOggVorbis.load_from_file(ProjectSettings.globalize_path(PATH))
	if stream is AudioStreamOggVorbis:
		stream.loop = false
	_p = AudioStreamPlayer.new()
	_p.stream = stream
	_p.volume_db = -9.0                  # under the meadow, not on top of it
	_p.bus = AudioSetup.MUSIC
	add_child(_p)
	_p.finished.connect(func(): _wait = randf_range(PAUSE_MIN, PAUSE_MAX))
	_p.play()


func _process(delta: float) -> void:
	if _wait > 0.0:
		_wait -= delta
		if _wait <= 0.0:
			_p.play()
