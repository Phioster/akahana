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
