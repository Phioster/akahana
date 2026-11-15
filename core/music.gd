## The music: the Akahana theme on the grand piano, then a long pause where only nature is heard, then again.
## The theme exists six times in exactly the same timing (tools/gen_thema_midi.py): meadow, wood, mountains,
## lake, village and rain differ only in their echoes, density, colour and room. All six always play together;
## where the wanderer stands and whether it rains decide how loud each one is, so the song turns softly with
## the land and the weather and never restarts.
class_name Music
extends Node

const REGIONS := ["mohnfeld", "wald", "berge", "see", "dorf", "regen"]
const DIR := "res://assets/audio/thema_%s.ogg"
const PAUSE_MIN := 45.0
const PAUSE_MAX := 90.0
const LEVEL_DB := -7.0               # under the meadow, not on top of it (Philip 0.20: "minimal lauter")
const OFF_DB := -60.0
const TURN := 0.15                   # how fast the mix follows the wanderer (per second): a slow turn, over seconds

# Where the lakes and the village lie (world coordinates, see TestTravel.PLACES); full inside NEAR, gone at FAR.
const LAKES := [Vector2(1474, 4145), Vector2(1670, 4520), Vector2(596, 4050), Vector2(850, 4030), Vector2(1990, 680)]
const LAKE_NEAR := 160.0
const LAKE_FAR := 420.0
const VILLAGE := [Vector2(536, 2344), Vector2(680, 2630), Vector2(560, 3340)]
const VILLAGE_NEAR := 220.0
const VILLAGE_FAR := 520.0

var world: WorldData
var player: Node2D
var weather: Weather
var _players := {}
var _mix := {}                       # smoothed weight per region, 0..1, summing to 1
var _wait := 0.0


static func _stream(path: String) -> AudioStream:
	var stream: AudioStream = null
	if ResourceLoader.exists(path):
		stream = load(path)
	else:
		stream = AudioStreamOggVorbis.load_from_file(ProjectSettings.globalize_path(path))
	if stream is AudioStreamOggVorbis:
		stream.loop = false
	return stream


static func _near(p: Vector2, spots: Array, near: float, far: float) -> float:
	var best := 0.0
	for s in spots:
		best = maxf(best, clampf((far - p.distance_to(s)) / (far - near), 0.0, 1.0))
	return best


## How much each version belongs to this spot and this weather (0..1 each, summing to 1).
## The places claim their share first (wood, mountains, lake, village); the meadow takes what is left;
## rain then lays itself over all of them by its strength.
static func weights(w: WorldData, p: Vector2, rain: float) -> Dictionary:
	var land := {
		"wald": w.wood_at(p) if w != null else 0.0,
		"berge": Ambience.altitude(p.y),
		"see": _near(p, LAKES, LAKE_NEAR, LAKE_FAR),
		"dorf": _near(p, VILLAGE, VILLAGE_NEAR, VILLAGE_FAR),
	}
	var sum := 0.0
	for k in land:
		sum += land[k]
	var out := {"mohnfeld": maxf(0.0, 1.0 - sum)}
	var scale := 1.0 / maxf(sum, 1.0)
	for k in land:
		out[k] = land[k] * scale
	var r := clampf(rain, 0.0, 1.0)
	for k in out:
		out[k] *= 1.0 - r
	out["regen"] = r
	return out


## Volume (dB) of one version at its weight: equal power, so the sum never swells or dips while turning.
static func level_db(weight: float) -> float:
	return maxf(LEVEL_DB + linear_to_db(maxf(sqrt(clampf(weight, 0.0, 1.0)), 0.0001)), OFF_DB)


func _ready() -> void:
	for k in REGIONS:
		var p := AudioStreamPlayer.new()
		p.stream = _stream(DIR % k)
		p.bus = AudioSetup.MUSIC_TRACK
		add_child(p)
		_players[k] = p
		_mix[k] = 0.0
	_mix = _target()                 # start right where the wanderer stands, no slow turn at the beginning
	_apply()
	_players["mohnfeld"].finished.connect(func(): _wait = randf_range(PAUSE_MIN, PAUSE_MAX))
	_play_all()


func _target() -> Dictionary:
	if player == null:
		return weights(null, Vector2(-99999, 99999), 0.0)
	return weights(world, player.position, weather.intensity() if weather != null else 0.0)


func _play_all() -> void:
	for k in REGIONS:
		_players[k].play()


func _apply() -> void:
	for k in REGIONS:
		_players[k].volume_db = level_db(_mix[k])


func _process(delta: float) -> void:
	var goal := _target()
	var a := clampf(delta * TURN, 0.0, 1.0)
	for k in REGIONS:
		_mix[k] = lerpf(_mix[k], goal[k], a)
	_apply()
	if _wait > 0.0:
		_wait -= delta
		if _wait <= 0.0:
			_play_all()
