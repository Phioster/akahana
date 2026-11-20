## The browser's picture (Philip 2026-11-20): the app's 180 x 400 on tall screens, wider on wider ones so an
## iPad or a phone with its address bar is filled, up to MAX_W (more would show three screens of world at once).
class_name WebFit
extends RefCounted

const BASE := Vector2(180, 400)
const MAX_W := 320                    # the dark beside the cave and greenhouse covers up to here (Cave.GAP)


static func fit(window: Vector2) -> Dictionary:
	if window.y <= 0.0 or window.x / window.y <= BASE.x / BASE.y:
		return {"size": Vector2i(BASE), "aspect": Window.CONTENT_SCALE_ASPECT_KEEP_WIDTH}
	var w := clampi(roundi(BASE.y * window.x / window.y), int(BASE.x), MAX_W)
	return {"size": Vector2i(w, int(BASE.y)), "aspect": Window.CONTENT_SCALE_ASPECT_KEEP}


## Browser only: follows the window as it turns or resizes.
static func follow(root: Window) -> void:
	var apply := func() -> void:
		var f := fit(Vector2(root.size))
		root.content_scale_size = f["size"]
		root.content_scale_aspect = f["aspect"]
	root.size_changed.connect(apply)
	apply.call()
