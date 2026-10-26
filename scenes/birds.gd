## The small birds of the meadow: a few on each open spot. When a flock has flown, a new one lands there
## later, but only while you are far away and not looking.
class_name Birds
extends Node

const KINDS := ["spatz", "spatz", "spatz", "amsel", "rotkehl"]

var world: WorldData
var player: Node2D
var sorted: Node2D                          # the y-sorted layer the birds live in
var _flocks: Array = []                     # {spot, birds: Array[Bird], back_in}
var _call: AudioStreamPlayer2D
var _wings: AudioStreamPlayer2D
var _call_in := 6.0
var _area := Activator.new()                # a flock lands only once its spot comes near the view


func _ready() -> void:
	_call = AudioStreamPlayer2D.new()
	_wings = AudioStreamPlayer2D.new()
	for p in [_call, _wings]:
		p.bus = AudioSetup.SOUNDS
		p.max_distance = 140.0
		add_child(p)
	if world == null:
		return
	for b in world.birds:
		var f := {"spot": Vector2(float(b["x"]), float(b["y"])), "snow": bool(b.get("snow", false)),
				"birds": [], "back_in": 0.0, "on": false}
		_flocks.append(f)
		_area.add(Rect2(f["spot"], Vector2.ZERO), 60.0, 160.0, _arrive.bind(f), _leave.bind(f))


## Out of sight beyond the view's edge, so nobody sees them appear or vanish.
func update_area(view: Rect2) -> void:
	_area.update(view)


func flock_nodes() -> int:
	return _area.active_count()


func _arrive(f: Dictionary) -> Node:
	f["on"] = true
	f["back_in"] = 0.0
	_land(f)
	return Node.new()                       # a token for the activator; the birds live in `sorted`


func _leave(token: Node, f: Dictionary) -> void:
	for b in f["birds"]:
		b.queue_free()
	f["birds"] = []
	f["on"] = false
	token.free()


func _land(f: Dictionary) -> void:
	for b in f["birds"]:
		b.queue_free()
	f["birds"] = []
	var n := 1 if f["snow"] else randi_range(1, 3)
	var kind: String = "amsel" if f["snow"] else KINDS[randi() % KINDS.size()]
	for i in n:
		var b := Bird.new()
		b.setup(kind, randf())
		b.position = (f["spot"] + Vector2(randf_range(-10, 10), randf_range(-6, 6))).round()
		b.took_off.connect(_on_took_off)
		sorted.add_child(b)
		f["birds"].append(b)


func _on_took_off(b: Bird) -> void:
	_wings.stream = SoundBank.get_stream("fluegel_0")
	_wings.volume_db = -2.0                   # recording -22.5 -> arrives about -24, just over the steps
	Ducker.duck()
	_wings.position = b.position
	_wings.pitch_scale = randf_range(0.95, 1.1)
	_wings.play()
	if randf() < 0.4:
		_chirp(b.position)


func _chirp(at: Vector2) -> void:
	_call.stream = SoundBank.get_stream("vogel_%d" % (randi() % 3))
	_call.position = at
	_call.volume_db = -1.0                    # recording -26 -> about -27
	_call.pitch_scale = randf_range(0.95, 1.08)
	_call.play()


func _process(delta: float) -> void:
	if player == null:
		return
	var view := get_viewport().get_visible_rect().size
	for f in _flocks:
		if not f["on"]:
			continue
		var alive := false
		for b in f["birds"]:
			b.step(delta, player.position)
			if b.brain.state != BirdBrain.GONE:
				alive = true
		if not alive:
			if f["back_in"] <= 0.0:
				f["back_in"] = randf_range(25.0, 60.0)
			f["back_in"] -= delta
			var far: bool = f["spot"].distance_to(player.position) > maxf(view.x, view.y) * 0.6
			if f["back_in"] <= 0.0 and far:
				f["back_in"] = 0.0
				_land(f)
	_call_in -= delta
	if _call_in <= 0.0:                     # now and then one of the nearby birds calls
		_call_in = randf_range(6.0, 16.0)
		for f in _flocks:
			if f["spot"].distance_to(player.position) < 110.0 and not f["birds"].is_empty():
				var b: Bird = f["birds"][0]
				if b.brain.state != BirdBrain.GONE:
					_chirp(b.position)
					break
