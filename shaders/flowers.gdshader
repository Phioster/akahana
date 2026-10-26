// Poppy heads sway in the same gusts as in the wallpaper, and nod aside around the wanderer's feet. Each
// flower moves as a whole by a few pixels (never the picture under it: that squashes the blossoms and
// looks laid over the meadow). Behind him the nodding opens into a frayed V and swings back slowly.
shader_type canvas_item;

const int TRAIL = 24;
const float R0 = 5.0;                 // half width of the wake right at the feet
const float R1 = 13.0;                // ... at its far end
const float PUSH = 4.0;               // most a flower nods aside, in whole pixels

uniform vec2 tex_size;
uniform vec4 trail[24];               // x, y, walking direction x, y
uniform float trail_k[24];            // 1 just stepped .. 0 swung back (linear in time)

float hash(vec2 p) {
	return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void fragment() {
	vec2 p = floor(UV * tex_size);
	float ph = 6.2831853 * TIME / 8.0;
	float g = max(sin(6.2831853 * (p.x * 0.6 + p.y) / 170.0 - 2.0 * ph), 0.0);
	float w = 1.4 * g * g + 0.4 * sin(3.0 * ph + p.x * 0.11 + p.y * 0.07);
	float dx = floor(w + 0.5);

	float best = 0.0;
	float bo = 0.0;
	float bk = 0.0;
	vec2 bn = vec2(0.0);
	for (int i = 0; i < TRAIL; i++) {
		float k = trail_k[i];
		if (k <= 0.0) continue;
		vec2 d = trail[i].zw;
		vec2 n = vec2(-d.y, d.x);
		vec2 r = p + 0.5 - vec2(trail[i].x, trail[i].y - 2.0);
		float s = k * clamp(1.0 - abs(dot(r, d)) / 4.0, 0.0, 1.0);
		if (s > best) {
			best = s;
			bo = dot(r, n);
			bn = n;
			bk = k;
		}
	}
	vec2 src = p;
	bool trampled = false;
	float h = hash(p);
	float rw = mix(R1, R0, bk);                            // the V opens with age
	if (best > 0.3 * h && abs(bo) < rw) {                  // frayed: each flower lets go at its own moment
		float ease = bk * bk * (3.0 - 2.0 * bk);           // swings back slowly
		float amt = PUSH * ease * clamp(1.0 - abs(bo) / rw, 0.0, 1.0) * 1.6;
		float off = floor(clamp(amt, 0.0, PUSH) + h * 0.6);
		trampled = abs(bo) < 1.0 && h < 0.5 * ease;        // here and there one bent under his feet
		src = p - bn * sign(bo) * off;
	}
	vec4 c = texture(TEXTURE, (floor(src) - vec2(dx, 0.0) + 0.5) / tex_size);
	COLOR = trampled ? vec4(0.0) : c;
}
