## What the rain sounds like where the wanderer stands. Each place has a light and a full recording and the
## shower turns from one to the other as it swells (meadow, wood); water and the greenhouse's roof come in by
## nearness; inside the greenhouse its tin roof drums over everything. Now and then thunder rolls far off,
## one of two recordings at random. Above the snow line there is no rain, so nothing here either.
class_name RainSounds
extends Node

# Levels as in Ambience: how loud it should arrive at the full shower minus how loud the recording is
# (ffmpeg volumedetect mean of the prepared file, tools/prep_sounds.py rain).
const MEAN_DB := {"regen_wiese_leicht": -31.5, "regen_wiese_voll": -20.2, "regen_wald_leicht": -24.6,
		"regen_wald_voll": -28.9, "regen_wasser": -21.0, "regen_dach_innen": -24.7, "regen_dach_aussen": -21.2}
const ARRIVE_DB := {"regen_wiese_leicht": -35.0, "regen_wiese_voll": -31.0, "regen_wald_leicht": -36.0,
		"regen_wald_voll": -32.0, "regen_wasser": -33.0, "regen_dach_innen": -28.0, "regen_dach_aussen": -37.0}
const THUNDER := ["donner_0", "donner_1"]
const THUNDER_MEAN_DB := [-21.6, -25.8]
const THUNDER_ARRIVE_DB := -40.0      # far off: under the rain, felt more than heard
const THUNDER_FROM := 0.45            # only in a real shower
const THUNDER_GAP := Vector2(30.0, 80.0)
const FULL_FROM := 0.35               # shower strength where the full recording starts taking over ..
const FULL_AT := 0.85                 # .. and where it has
const MUFFLED := 0.15                 # the outside rain heard through the greenhouse's glass
const ROOF_NEAR := 40.0               # the greenhouse's roof from outside: full this close to its door ..
const ROOF_FAR := 220.0               # .. gone this far
const WATER_NEAR := 120.0
const WATER_FAR := 380.0
const SILENT_DB := -80.0
const SMOOTH := 2.0                   # per second: walking in or out turns the sound over about half a second

var world: WorldData
var player: Node2D
var weather: Weather
var glashaus: Cave                    # for its door outside
var room: Cave                        # the room the wanderer is in, null outside (set by Main)
var _p := {}
var _gain := {}                       # smoothed linear gain per recording
var _thunder: AudioStreamPlayer
var _thunder_in := 20.0
var _playing := false


## Linear gain per recording (0..1) for a shower strength r (already 0 above the snow) and the place:
## how deep in the wood, how near water, how near the greenhouse's roof, and where: "" outside,
## "glashaus" inside the greenhouse, "cave" in the cave.
static func mix(r: float, wood: float, water: float, roof: float, where: String) -> Dictionary:
	var s := smoothstep(FULL_FROM, FULL_AT, r)
	var light := r * (1.0 - s)
	var full := r * s
	var w := clampf(wood, 0.0, 1.0)
	var out := {
		"regen_wiese_leicht": light * (1.0 - w), "regen_wiese_voll": full * (1.0 - w),
		"regen_wald_leicht": light * w, "regen_wald_voll": full * w,
		"regen_wasser": r * clampf(water, 0.0, 1.0), "regen_dach_aussen": r * clampf(roof, 0.0, 1.0),
		"regen_dach_innen": 0.0,
	}
	if where == "cave":
		for k in out:
			out[k] = 0.0
	elif where == "glashaus":
		for k in out:
			out[k] *= MUFFLED
		out["regen_dach_aussen"] = 0.0
		out["regen_dach_innen"] = r
	return out


static func _near(p: Vector2, spots: Array, near: float, far: float) -> float:
	var best := 0.0
	for s in spots:
		best = maxf(best, clampf((far - p.distance_to(s)) / (far - near), 0.0, 1.0))
	return best


func _ready() -> void:
	for k in MEAN_DB:
		var p := AudioStreamPlayer.new()
		p.stream = SoundBank.looped(k)
		p.volume_db = SILENT_DB
		p.bus = AudioSetup.BACKDROP
		add_child(p)
		_p[k] = p
		_gain[k] = 0.0
	_thunder = AudioStreamPlayer.new()
	_thunder.bus = AudioSetup.BACKDROP
	add_child(_thunder)


func _where() -> String:
	if room == null:
		return ""
	return "glashaus" if room == glashaus else "cave"


func _target() -> Dictionary:
	var where := _where()
	var r := weather.intensity() if weather != null else 0.0
	if player == null:
		return mix(0.0, 0.0, 0.0, 0.0, "")
	if where != "":                                  # inside: the greenhouse lies low in the west, it rains there
		return mix(r, 0.0, 0.0, 0.0, where)
	var at := player.position
	r *= Rain.reach(at.y)
	var water := _near(at, Music.LAKES, WATER_NEAR, WATER_FAR)
	if world != null and world.places.has("pond"):
		var pd: Array = world.places["pond"]
		water = maxf(water, _near(at, [Vector2(float(pd[0]), float(pd[1]))], 40.0, 160.0))
	var roof := 0.0
	if glashaus != null:
		roof = _near(at, [glashaus.out], ROOF_NEAR, ROOF_FAR)
	return mix(r, world.wood_at(at) if world != null else 0.0, water, roof, "")


func _process(delta: float) -> void:
	var goal := _target()
	var a := clampf(delta * SMOOTH, 0.0, 1.0)
	var any := false
	for k in _p:
		_gain[k] = lerpf(_gain[k], goal[k], a)
		any = any or _gain[k] > 0.001
	if any and not _playing:                          # the decoders run only while it rains
		for k in _p:
			_p[k].play(randf() * 20.0)
		_playing = true
	elif not any and _playing:
		for k in _p:
			_p[k].stop()
		_playing = false
	for k in _p:
		var g: float = _gain[k]
		_p[k].volume_db = SILENT_DB if g <= 0.001 else ARRIVE_DB[k] - MEAN_DB[k] + linear_to_db(g)
	_step_thunder(delta)


func _step_thunder(delta: float) -> void:
	var r := weather.intensity() if weather != null else 0.0
	var where := _where()
	if where == "" and player != null:
		r *= Rain.reach(player.position.y)
	if r < THUNDER_FROM or where == "cave":
		_thunder_in = maxf(_thunder_in, 15.0)         # the first roll comes a while into the shower
		return
	_thunder_in -= delta
	if _thunder_in > 0.0 or _thunder.playing:
		return
	var i := randi() % THUNDER.size()
	_thunder.stream = SoundBank.get_stream(THUNDER[i])
	_thunder.volume_db = THUNDER_ARRIVE_DB - THUNDER_MEAN_DB[i] + randf_range(-5.0, 0.0) - (4.0 if where == "glashaus" else 0.0)
	_thunder.pitch_scale = randf_range(0.92, 1.04)    # never quite the same roll twice
	_thunder.play()
	_thunder_in = randf_range(THUNDER_GAP.x, THUNDER_GAP.y)
