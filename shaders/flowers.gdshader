// Poppy heads sway in the same gusts as in the wallpaper, and part around the wanderer's feet: pushed
// aside across the walking direction, a lane left behind that closes again. Whole-pixel shifts only.
shader_type canvas_item;

const int TRAIL = 14;
const float R = 9.0;                  // how far to the side the poppies are pushed
const float GAP = 3.0;                // half width of the lane right at the feet

uniform vec2 tex_size;
uniform vec4 trail[14];               // x, y, walking direction x, y
uniform float trail_k[14];            // strength 1 (just stepped) .. 0 (closed again)

void fragment() {
	vec2 p = floor(UV * tex_size);
	float ph = 6.2831853 * TIME / 8.0;
	float g = max(sin(6.2831853 * (p.x * 0.6 + p.y) / 170.0 - 2.0 * ph), 0.0);
	float w = 1.4 * g * g + 0.4 * sin(3.0 * ph + p.x * 0.11 + p.y * 0.07);
	float dx = floor(w + 0.5);

	float best = 0.0;
	float bo = 0.0;
	vec2 bn = vec2(0.0);
	for (int i = 0; i < TRAIL; i++) {
		float st = trail_k[i];
		if (st <= 0.0) continue;
		vec2 d = trail[i].zw;
		vec2 n = vec2(-d.y, d.x);
		vec2 r = p + 0.5 - vec2(trail[i].x, trail[i].y - 2.0);
		float s = st * clamp(1.0 - abs(dot(r, d)) / 4.0, 0.0, 1.0);
		if (s > best) {
			best = s;
			bo = dot(r, n);
			bn = n;
		}
	}
	vec2 src = p;
	bool lane = false;                                     // right at the feet: no poppy at all
	if (best > 0.05 && abs(bo) < R) {
		float gap = GAP * best;
		lane = abs(bo) < gap;
		float so = sign(bo) * clamp((abs(bo) - gap) * R / max(R - gap, 0.001), 0.0, R);
		src = p - bn * (bo - so);
	}
	vec4 c = texture(TEXTURE, (floor(src) - vec2(dx, 0.0) + 0.5) / tex_size);
	COLOR = lane ? vec4(0.0) : c;
}
