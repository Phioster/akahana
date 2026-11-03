## A swarm of fireflies hovering low over the grass and the water: each fly drifts on its own slow loop
## and glows up and down in its own rhythm (tools/world/south/fireflies.py, the approved look; the
## generator writes every fly's loop into world.json). Each glowing fly lends the post shader a tiny light.
class_name Fireflies
extends Node2D

const GLOW := [Color8(224, 178, 84), Color8(248, 214, 120), Color8(255, 242, 176)]   # dim .. bright
const COOL := [Color8(150, 214, 178), Color8(190, 240, 214), Color8(226, 255, 240)]   # the wood's flies: moon-green
const LIGHT_R := 7.0
const COOL_R := 13.0                 # the wood's flies light a wider pool: the floor there is dark
const LIGHT_K := 0.27

var home := Vector2.ZERO
var flies: Array = []
var cool := false                    # the wood's swarms glow cool (a negative strength for the post shader)
var _t := randf() * 100.0


const HUM_DB := -8.0                 # recording -23 -> about -31 near it, as soft as the wisp's crackle
const HUM_RANGE := 70.0               # heard walking through or beside a swarm (at -18 / 50 px: inaudible)


func setup(d: Dictionary) -> void:
	home = Vector2(float(d["x"]), float(d["y"]))
	flies = d["flies"]
	cool = bool(d.get("cool", false))
	add_to_group("fireflies")
	var hum := AudioStreamPlayer2D.new()
	hum.name = "Summen"
	hum.stream = SoundBank.looped("gluehwuermchen")
	hum.bus = AudioSetup.SOUNDS
	hum.volume_db = HUM_DB
	hum.max_distance = HUM_RANGE
	hum.position = home
	hum.autoplay = true
	add_child(hum)


## Every fly at time t (seconds): x, y in the world and its glow 0..1.
func state(t: float) -> Array[Vector3]:
	var out: Array[Vector3] = []
	for f in flies:
		var a: float = f["ph"] + t * f["sp"]
		var x: float = home.x + f["ax"] + f["rx"] * sin(a) + 0.6 * f["rx"] * sin(2.3 * a + 1.0)
		var y: float = home.y + f["ay"] + f["ry"] * sin(1.7 * a + 2.0)
		var b := 0.2 + 0.8 * pow(maxf(0.0, sin(f["bph"] + t * f["blink"] * 2.4)), 1.2)   # a glimmer, then a glow
		out.append(Vector3(x, y, b))
	return out


## Small lights for the post shader: x, y, radius, strength.
func lights() -> Array[Vector4]:
	var out: Array[Vector4] = []
	for p in state(_t):
		if p.z > 0.05:
			out.append(Vector4(p.x + 0.5, p.y + 0.5, COOL_R if cool else LIGHT_R, LIGHT_K * p.z * (-1.0 if cool else 1.0)))
	return out


func _process(delta: float) -> void:
	_t += delta
	queue_redraw()


func _draw() -> void:
	var glow: Array = COOL if cool else GLOW
	for p in state(_t):
		if p.z < 0.12:
			continue
		var at := Vector2(roundf(p.x), roundf(p.y)) - position
		draw_rect(Rect2(at, Vector2.ONE), glow[mini(2, int(p.z * 3.0))])
		if p.z > 0.45:                                   # glowing up: a small cross of light round it
			var c: Color = glow[1 if p.z > 0.8 else 0]
			for d in [Vector2.RIGHT, Vector2.LEFT, Vector2.DOWN, Vector2.UP]:
				draw_rect(Rect2(at + d, Vector2.ONE), c)
