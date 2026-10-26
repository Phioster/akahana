// Poppy heads sway in the same gusts as in the wallpaper, and part around the wanderer's feet. Behind him
// the parting opens into a V: narrow at his heels, wider and weaker further back, its edges frayed, until
// the flowers have slowly swung back. Whole-pixel shifts only.
shader_type canvas_item;

const int TRAIL = 24;
const float R0 = 4.0;                 // half width of the parting right at the feet
const float R1 = 12.0;                // ... at the far end of the wake
const float GAP = 3.0;                // half width of the empty lane right at the feet

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
	bool lane = false;
	float h = hash(p);
	float rw = mix(R1, R0, bk);                            // the V opens with age
	// frayed: each flower lets go at its own moment, on the edges and towards the end of the wake
	if (best > 0.25 * h && abs(bo) < rw * (1.0 - 0.35 * h)) {
		float push = bk * bk * (3.0 - 2.0 * bk);           // swings back slowly
		float gap = GAP * push;
		lane = abs(bo) < gap;
		float so = sign(bo) * clamp((abs(bo) - gap) * rw / max(rw - gap, 0.001), 0.0, rw);
		src = p - bn * (bo - so) * push;
	}
	vec4 c = texture(TEXTURE, (floor(src) - vec2(dx, 0.0) + 0.5) / tex_size);
	COLOR = lane ? vec4(0.0) : c;
}
