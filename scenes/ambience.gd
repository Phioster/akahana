## Everything you hear besides music and steps. A quiet bed of insects everywhere; the evening meadow in
## the south, wind getting stronger towards the mountains; the brook, the fire and the lanterns where they
## are; now and then a frog by the water or a far bell from the ruin.
class_name Ambience
extends Node2D

const RUIN := Vector2(229, 352)
# Levels are set as (how loud it should arrive up close) minus (how loud the recording is, measured with
# ffmpeg volumedetect): music arrives at about -26 dB, steps at about -29.
const FIRE_DB := -4.0                # recording (rumble off, hiss tamed) -29 -> about -33, under the steps
const FIRE_REACH := 180.0
const BROOK_DB := {"bach_klein": -1.5, "bach_mittel": -1.0, "bach_gross": -7.0}   # recordings -27/-28/-22 -> -29
const BROOK_REACH := 130.0
const CANDLE_DB := -4.0              # recording -32 -> -36: you hear it when you stand at the lantern

var world: WorldData
var player: Node2D
var _bed: AudioStreamPlayer
var _meadow: AudioStreamPlayer
var _wind: AudioStreamPlayer
var _mountain: Array[AudioStreamPlayer] = []
var _mountain_mix := 0.0
var _mountain_dir := 1.0
var _one: AudioStreamPlayer2D
var _bell_in := 0.0
var _frog_in := 0.0


func _ready() -> void:
	_bed = _flat("nacht", -15.0)
	_meadow = _flat("abendwiese", -14.0)
	_wind = _flat("wind_ruhig", -18.0)
	for n in ["bergwind_a", "bergwind_b"]:
		_mountain.append(_flat(n, -60.0))
	if world != null:
		var sizes := ["bach_klein", "bach_mittel", "bach_gross"]
		for i in range(0, world.brook.size(), 2):
			var b: Dictionary = world.brook[i]
			var size: String = sizes[(i / 2) % 3]
			_spot(size, Vector2(float(b["x"]), float(b["y"])), BROOK_DB[size], BROOK_REACH)
		if not world.fire.is_empty():
			_spot("feuer", Vector2(float(world.fire["x"]), float(world.fire["y"])), FIRE_DB, FIRE_REACH)
		for l in world.lights:
			if l["kind"] != "fire":
				_spot("kerze", Vector2(float(l["x"]), float(l["y"])), CANDLE_DB, 50.0)
	_one = AudioStreamPlayer2D.new()
	_one.bus = AudioSetup.SOUNDS
	add_child(_one)
	_bell_in = randf_range(60.0, 120.0)
	_frog_in = randf_range(8.0, 16.0)


func _flat(name: String, db: float) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.stream = SoundBank.looped(name)
	p.volume_db = db
	p.bus = AudioSetup.BACKDROP
	add_child(p)
	p.play(randf() * 10.0)
	return p


func _spot(name: String, at: Vector2, db: float, reach: float) -> void:
	var p := AudioStreamPlayer2D.new()
	p.stream = SoundBank.looped(name)
	p.position = at
	p.volume_db = db
	p.max_distance = reach
	p.attenuation = 1.0                       # an even fall-off: loud near, still there further away
	p.bus = AudioSetup.BACKDROP
	add_child(p)
	p.play(randf() * 8.0)


## 0 on the meadow .. 1 under the summit, from the height on the map
static func altitude(y: float) -> float:
	return clampf((560.0 - y) / 480.0, 0.0, 1.0)


func _process(delta: float) -> void:
	if player == null:
		return
	var alt := altitude(player.position.y)
	_meadow.volume_db = lerpf(-14.0, -40.0, clampf(alt * 2.0, 0.0, 1.0))
	_wind.volume_db = lerpf(-18.0, -10.0, alt)
	# two mountain winds, slowly handing over to each other so it never repeats the same way
	_mountain_mix = clampf(_mountain_mix + _mountain_dir * delta / 40.0, 0.0, 1.0)
	if _mountain_mix <= 0.0 or _mountain_mix >= 1.0:
		_mountain_dir = -_mountain_dir
	var high := clampf((alt - 0.45) / 0.55, 0.0, 1.0)
	_mountain[0].volume_db = linear_to_db(maxf(high * (1.0 - _mountain_mix), 0.0001)) - 8.0
	_mountain[1].volume_db = linear_to_db(maxf(high * _mountain_mix, 0.0001)) - 8.0
	_bell_in -= delta
	if _bell_in <= 0.0:
		_bell_in = randf_range(150.0, 260.0)
		_play_once("glocke", RUIN + Vector2(0, -40), -8.5, 700.0, 1.0, 2.0)   # steeper: soft from afar
	_frog_in -= delta
	if _frog_in <= 0.0:
		_frog_in = randf_range(7.0, 18.0)
		var near := _near_water(player.position, 120.0)
		if near != Vector2.INF:
			_play_once("frosch", near, -11.0, 120.0, randf_range(0.9, 1.08))


func _near_water(at: Vector2, within: float) -> Vector2:
	if world == null:
		return Vector2.INF
	var best := Vector2.INF
	for b in world.brook:
		var p := Vector2(float(b["x"]), float(b["y"])) + Vector2(randf_range(-10, 10), randf_range(-4, 4))
		if p.distance_to(at) < within and (best == Vector2.INF or randf() < 0.4):
			best = p
	return best


func _play_once(name: String, at: Vector2, db: float, reach: float, pitch: float, fall := 1.0) -> void:
	_one.stream = SoundBank.get_stream(name)
	_one.attenuation = fall
	_one.position = at
	_one.volume_db = db
	_one.max_distance = reach
	_one.pitch_scale = pitch
	_one.play()
