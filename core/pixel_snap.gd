## Showing a smoothly moving thing on whole pixels without it shaking: plain rounding flips between two
## pixels when the true spot hovers round a pixel's middle. This keeps the shown pixel until the true spot
## is clearly (3/4 px) away from it; a steady drift still moves on one pixel at a time.
class_name PixelSnap
extends RefCounted

const KEEP := 0.75


static func sticky(shown: Vector2, at: Vector2) -> Vector2:
	var out := shown
	for k in 2:
		if absf(at[k] - shown[k]) >= KEEP:
			out[k] = roundf(at[k])
	return out


## For a thing that swims: both axes step together, once the true spot is a whole pixel away. Separate
## per-axis steps made a curve a zigzag (x and y ticked a frame apart, 17 ms to 230 ms between ticks, measured);
## together the ticks come evenly (133 to 250 ms at 6 px/s) and only half as many.
static func together(shown: Vector2, at: Vector2) -> Vector2:
	if (at - shown).length() >= 1.0:
		return at.round()
	return shown
