## Two buses, one per slider: music and everything else (wind, water, steps, birds).
## In front of them two routes the Ducker can lower for a moment: the music track and the
## ambient backdrop (night, meadow, wind, brooks, fire). Events (steps, birds, book) skip them.
class_name AudioSetup
extends RefCounted

const MUSIC := "Musik"
const SOUNDS := "Geraeusche"
const MUSIC_TRACK := "Musikspur"
const BACKDROP := "Kulisse"


static func ensure_buses() -> void:
	for pair in [[MUSIC, "Master"], [SOUNDS, "Master"], [MUSIC_TRACK, MUSIC], [BACKDROP, SOUNDS]]:
		if AudioServer.get_bus_index(pair[0]) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count - 1, pair[0])
			AudioServer.set_bus_send(AudioServer.bus_count - 1, pair[1])


static func to_db(v: float) -> float:
	return -80.0 if v <= 0.001 else linear_to_db(v)


static func apply(save: SaveData) -> void:
	ensure_buses()
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index(MUSIC), to_db(save.music))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index(SOUNDS), to_db(save.sounds))
	AudioServer.set_bus_mute(AudioServer.get_bus_index(MUSIC), save.music <= 0.001)
	AudioServer.set_bus_mute(AudioServer.get_bus_index(SOUNDS), save.sounds <= 0.001)
