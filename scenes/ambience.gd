## Everything you hear besides music and steps. A quiet bed of insects everywhere; the evening meadow in
## the south, wind getting stronger towards the mountains; the brook, the fire and the lanterns where they
## are; now and then a frog by the water or a far bell from the ruin.
class_name Ambience
extends Node2D

const RUIN := Vector2(1129, 1552)          # world coordinates (0.18: the west grew 900 on the left)
# Levels are set as (how loud it should arrive up close) minus (how loud the recording is, measured with
# ffmpeg volumedetect): music arrives at about -26 dB, steps at about -29.
const FIRE_DB := -4.0                # recording (rumble off, hiss tamed) -29 -> about -33, under the steps
const FIRE_REACH := 180.0
const BROOK_DB := {"bach_klein": -1.5, "bach_mittel": -1.0, "bach_gross": -7.0}   # recordings -27/-28/-22 -> -29
const BROOK_REACH := 130.0
const CANDLE_DB := -4.0              # recording -32 -> -36: you hear it when you stand at the lantern
# the last sounds (0.22): north waterfall, the mill in the west, the firs' wind, the woodcutter's hut creaking
const WATERFALL := Vector2(2152, 562)      # the fall under the Bergsee (north FALL_X 1252 + the west's 900)
const WATERFALL_DB := -7.0                 # recording -20 -> about -27 close by
const MILL_DB := -4.0                      # recording -20 -> about -24 at the wheel (0.22.1: Philip "zu leise")
const HUT := Vector2(1230, 860)            # the woodcutter's clearing (north HUT + 900)
const CREAK_DB := -12.0                    # recording -22 -> about -34
const FIR_DB := -14.0                      # 'tannenwind' -22 -> about -36, under the mountain wind
const STORM_DB := -12.0                    # 'schneesturm' -22 -> about -34 up high

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
var _wood := 0.0                      # smoothed: how deep in the dark wood the wanderer stands
var _silence := 0.0                   # 1 on the graves' clearing: the beds sink away
var _chime_in := 20.0
var _firs: Array[AudioStreamPlayer] = []
var _creak_in := 10.0
const DROPS_DB := -4.0                # recording -25.5 -> about -29.5 at the pond
const CHIME_DB := -10.5               # recording -20 -> about -30, like the far bell
const GRAVES_HUSH := 80.0             # px round the graves in which the beds sink
var _spots := Activator.new()         # place sounds exist only within earshot


func _ready() -> void:
	_bed = _flat("nacht", -15.0)
	_meadow = _flat("abendwiese", -14.0)
	_wind = _flat("wind_ruhig", -18.0)
	for n in ["bergwind_a", "bergwind_b"]:
		_mountain.append(_flat(n, -60.0))
	_firs = [_flat("tannenwind", -60.0), _flat("schneesturm", -60.0)]
	_spot("wasserfall", WATERFALL, WATERFALL_DB, 260.0)
	if world != null:
		if world.places.has("mill"):
			var ml: Array = world.places["mill"]
			_spot("muehle", Vector2(float(ml[0]), float(ml[1])), MILL_DB, 200.0)
		var sizes := ["bach_klein", "bach_mittel", "bach_gross"]
		for i in range(0, world.brook.size(), 2):
			var b: Dictionary = world.brook[i]
			var size: String = sizes[(i / 2) % 3]
			_spot(size, Vector2(float(b["x"]), float(b["y"])), BROOK_DB[size], BROOK_REACH)
		if world.places.has("pond"):
			var pd: Array = world.places["pond"]
			_spot("teich", Vector2(float(pd[0]), float(pd[1])), DROPS_DB, 110.0)
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
	_spots.add(Rect2(at, Vector2.ZERO), reach + 20.0, reach + 60.0, _make_spot.bind(name, at, db, reach),
			func(n: Node): n.queue_free())


func spot_nodes() -> int:
	return _spots.active_count()


func _make_spot(name: String, at: Vector2, db: float, reach: float) -> Node:
	var p := AudioStreamPlayer2D.new()
	p.stream = SoundBank.looped(name)
	p.position = at
	p.volume_db = db
	p.max_distance = reach
	p.attenuation = 1.0                       # an even fall-off: loud near, still there further away
	p.bus = AudioSetup.BACKDROP
	add_child(p)
	p.play(randf() * 8.0)
	return p


## 0 on the meadow .. 1 under the summit, from the height on the map
static func altitude(y: float) -> float:
	return clampf((SoundBank.NORTH + 560.0 - y) / 480.0, 0.0, 1.0)   # the whole north lies up high


func _process(delta: float) -> void:
	if player == null:
		return
	_spots.update(Rect2(player.position, Vector2.ZERO))
	var alt := altitude(player.position.y)
	if world != null:
		_wood = lerpf(_wood, world.wood_at(player.position), clampf(delta * 0.6, 0.0, 1.0))
		_silence = 0.0
		if world.places.has("graves"):
			var g: Array = world.places["graves"]
			_silence = clampf(1.0 - player.position.distance_to(Vector2(float(g[0]), float(g[1]))) / GRAVES_HUSH, 0.0, 1.0)
	_bed.volume_db = -15.0 - 14.0 * _silence
	_meadow.volume_db = lerpf(-14.0, -40.0, clampf(maxf(alt * 2.0, _wood * 1.5), 0.0, 1.0)) - 20.0 * _silence
	_wind.volume_db = lerpf(-18.0, -10.0, alt) - 3.0 * _wood - 12.0 * _silence   # only a breath in the needles
	# two mountain winds, slowly handing over to each other so it never repeats the same way
	_mountain_mix = clampf(_mountain_mix + _mountain_dir * delta / 40.0, 0.0, 1.0)
	if _mountain_mix <= 0.0 or _mountain_mix >= 1.0:
		_mountain_dir = -_mountain_dir
	var high := clampf((alt - 0.45) / 0.55, 0.0, 1.0)
	_mountain[0].volume_db = linear_to_db(maxf(high * (1.0 - _mountain_mix), 0.0001)) - 8.0
	_mountain[1].volume_db = linear_to_db(maxf(high * _mountain_mix, 0.0001)) - 8.0
	# the firs' wind in the north: the calm one at its foot turning into the snow storm where the snow falls fully
	var snow := Snowfall.density(player.position.y)
	var storm := clampf((snow - Snowfall.LIGHT) / (1.0 - Snowfall.LIGHT), 0.0, 1.0)
	var fir := clampf(snow / Snowfall.LIGHT, 0.0, 1.0) * (1.0 - _silence)
	_firs[0].volume_db = FIR_DB + linear_to_db(maxf(fir * sqrt(1.0 - storm), 0.0001))
	_firs[1].volume_db = STORM_DB + linear_to_db(maxf(fir * sqrt(storm), 0.0001))
	_creak_in -= delta
	if _creak_in <= 0.0:
		_creak_in = randf_range(14.0, 36.0)
		if player.position.distance_to(HUT) < 160.0:  # the hut's old wood, now and then, in the cold
			_play_once("knarzen_%02d" % (randi() % 4), HUT + Vector2(randf_range(-12, 12), -6), CREAK_DB, 160.0,
					randf_range(0.94, 1.04))
	_bell_in -= delta
	if _bell_in <= 0.0:
		_bell_in = randf_range(150.0, 260.0)
		_play_once("glocke", RUIN + Vector2(0, -40), -8.5, 700.0, 1.0, 2.0)   # steeper: soft from afar
	_chime_in -= delta
	if _chime_in <= 0.0:
		_chime_in = randf_range(70.0, 130.0)
		if world != null and world.places.has("ritual"):
			var rt: Array = world.places["ritual"]
			_play_once("glockchen", Vector2(float(rt[0]), float(rt[1])) + Vector2(randf_range(-30, 30), -10), CHIME_DB,
					220.0, randf_range(0.93, 1.06), 1.5)
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
