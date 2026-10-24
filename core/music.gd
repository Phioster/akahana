## Background music: one calm loop, started once, quietly.
class_name Music
extends RefCounted

const PATH := "res://assets/audio/musik.ogg"


static func start(parent: Node) -> AudioStreamPlayer:
	var stream: AudioStream = null
	if ResourceLoader.exists(PATH):
		stream = load(PATH)
	else:
		stream = AudioStreamOggVorbis.load_from_file(ProjectSettings.globalize_path(PATH))
	if stream == null:
		return null
	if stream is AudioStreamOggVorbis:
		stream.loop = true
	var p := AudioStreamPlayer.new()
	p.stream = stream
	p.volume_db = -6.0
	parent.add_child(p)
	p.play()
	return p
