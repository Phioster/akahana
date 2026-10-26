## Two buses, one per slider: music and everything else (wind, water, steps, birds).
class_name AudioSetup
extends RefCounted

const MUSIC := "Musik"
const SOUNDS := "Geraeusche"


static func ensure_buses() -> void:
	for name in [MUSIC, SOUNDS]:
		if AudioServer.get_bus_index(name) < 0:
			AudioServer.add_bus()
			AudioServer.set_bus_name(AudioServer.bus_count - 1, name)
			AudioServer.set_bus_send(AudioServer.bus_count - 1, "Master")


static func to_db(v: float) -> float:
	return -80.0 if v <= 0.001 else linear_to_db(v)


static func apply(save: SaveData) -> void:
	ensure_buses()
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index(MUSIC), to_db(save.music))
	AudioServer.set_bus_volume_db(AudioServer.get_bus_index(SOUNDS), to_db(save.sounds))
	AudioServer.set_bus_mute(AudioServer.get_bus_index(MUSIC), save.music <= 0.001)
	AudioServer.set_bus_mute(AudioServer.get_bus_index(SOUNDS), save.sounds <= 0.001)
