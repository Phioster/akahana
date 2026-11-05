## Loads the prepared recordings (tools/prep_sounds.py) once and hands them out by name.
class_name SoundBank
extends RefCounted

const DIR := "res://assets/audio/"

const NORTH := 1200.0                # the north (0.11) above the old map: every older height moves down by it
const SOUTH_Y := NORTH + 1200.0      # below the old map: the lake's shallow rim and the pools
const PASS_Y := 300.0                # the pass up north: wind-packed snow

static var _cache := {}


static func get_stream(name: String) -> AudioStream:
	if _cache.has(name):
		return _cache[name]
	var path := DIR + name + ".ogg"
	var s: AudioStream = null
	if ResourceLoader.exists(path):
		s = load(path)
	elif FileAccess.file_exists(path):
		s = AudioStreamOggVorbis.load_from_file(ProjectSettings.globalize_path(path))   # dev device: no import cache
	_cache[name] = s
	return s


static func looped(name: String) -> AudioStream:
	var s := get_stream(name)
	if s is AudioStreamOggVorbis:
		s.loop = true
	return s


## All numbered variants of a sound: schritt_gras_00, _01, ...
static func variants(prefix: String) -> Array[AudioStream]:
	var out: Array[AudioStream] = []
	for i in 32:
		var s := get_stream("%s_%02d" % [prefix, i])
		if s == null:
			break
		out.append(s)
	return out


## Which footstep set fits where the wanderer stands. Snow gets deeper the higher up (smaller y) you go.
static func step_set(mat: int, y: float) -> String:
	match mat:
		GroundMat.EARTH: return "schritt_erde"
		GroundMat.STONE: return "schritt_stein"
		GroundMat.WOOD: return "schritt_holz"
		GroundMat.WET: return "schritt_waten" if y >= SOUTH_Y else "schritt_nass"   # lake rim / the old ford
		GroundMat.SNOW:
			if y < PASS_Y or (y >= NORTH and y < NORTH + 150.0):   # the pass, the old summit
				return "schritt_schnee_hart"
			if y < NORTH + 330.0:
				return "schritt_schnee"
			return "schritt_schnee_wenig"
	return "schritt_gras"
