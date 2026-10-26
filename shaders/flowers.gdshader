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

float hash2(vec2 i) {
	return fract(sin(i.x * 127.1 + i.y * 311.7) * 43758.5453);
}

float vnoise(vec2 q) {
	vec2 i = floor(q);
	vec2 f = q - i;
	vec2 u = f * f * (3.0 - 2.0 * f);
	float a = hash2(i), b = hash2(i + vec2(1.0, 0.0)), c = hash2(i + vec2(0.0, 1.0)), d = hash2(i + vec2(1.0, 1.0));
	return a + (b - a) * u.x + (c - a) * u.y + (a - b - c + d) * u.x * u.y;
}

void fragment() {
	vec2 p = floor(UV * tex_size);
	float ph = 6.2831853 * TIME / 8.0;
	// gusts are drifting patches of noise, not bands: straight waves read as lines laid over the field
	vec2 q = vec2(p.x / 70.0 - 0.035 * TIME, p.y / 45.0 - 0.06 * TIME);
	float n = vnoise(q) * 0.65 + vnoise(q * 2.3 + vec2(17.0, 5.0)) * 0.35;
	float g = smoothstep(0.5, 0.85, n);
	float w = 1.6 * g + 0.35 * sin(3.0 * ph + 6.2832 * vnoise(p / 23.0 + vec2(3.1, 8.7)));
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
