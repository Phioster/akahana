// Poppy heads sway in the same gusts as in the wallpaper, and nod aside around the wanderer's feet. Each
// flower moves as a whole by a few pixels (never the picture under it: that squashes the blossoms and
// looks laid over the meadow). Behind him the nodding opens into a frayed V and swings back slowly.
shader_type canvas_item;

const int TRAIL = 24;
const float R0 = 5.0;                 // half width of the wake right at the feet
const float R1 = 13.0;                // ... at its far end
const float PUSH = 4.0;               // most a flower nods aside, in whole pixels

const float BEND_H = 10.0;            // px above its foot from where a blade goes the whole way with the wind
const float CALM_B = 1.1;             // grass and reeds stir between the gusts too (poppies keep 0.5)

uniform sampler2D bend_tex : filter_nearest;   // per pixel: height above its plant's foot, 255 = sways whole
uniform vec2 tex_size;
uniform vec2 origin;                  // world position of this picture's top-left texel (chunk minus apron)
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

// The gust's whole-pixel push at world pixel p: drifting patches of noise, not bands (straight waves read
// as lines laid over the field), plus a gentle sway of strength calm in each spot's own rhythm.
float wind(vec2 p, float calm) {
	float ph = 6.2831853 * TIME / 8.0;
	vec2 q = vec2(p.x / 70.0 - 0.0455 * TIME, p.y / 45.0 - 0.078 * TIME);
	float n = vnoise(q) * 0.65 + vnoise(q * 2.3 + vec2(17.0, 5.0)) * 0.35;
	float g = smoothstep(0.42, 0.8, n);
	return floor(2.6 * g + calm * sin(3.0 * ph + 6.2832 * vnoise(p / 23.0 + vec2(3.1, 8.7))) + 0.5);
}

// How far a blade pixel at world p with height h is pushed: its foot stays, its top goes with the gust,
// each stalk kinking at its own height (else a clump breaks along one row and shows a line).
float bend_of(vec2 p, float h) {
	float kink = 0.55 + 0.9 * hash2(vec2(p.x, 7.0));
	return floor(wind(p, CALM_B) * min(h * kink / BEND_H, 1.0) + 0.5);
}

vec4 at(sampler2D t, vec2 w) { return texture(t, (floor(w) - origin + 0.5) / tex_size); }
float height_at(vec2 w) { return texture(bend_tex, (floor(w) - origin + 0.5) / tex_size).r * 255.0; }

void fragment() {
	vec2 p = origin + floor(UV * tex_size);              // world pixel: wind and trail line up across chunks
	float dx = wind(p, 0.5);

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
	// poppy heads (height 255) move whole, as they always did
	vec4 c = at(TEXTURE, src - vec2(dx, 0.0));
	if (!(c.a > 0.0 && height_at(src - vec2(dx, 0.0)) > 254.5)) {
		// grass and reeds bend: which blade pixel lands here (the highest wins where two do)
		c = vec4(0.0);
		float best = -1.0;
		for (int k = -2; k <= 3; k++) {
			vec2 s = src - vec2(float(k), 0.0);
			vec4 cs = at(TEXTURE, s);
			float h = height_at(s);
			if (cs.a > 0.0 && h < 254.5 && h > best && bend_of(s, h) == float(k)) {
				c = cs;
				best = h;
			}
		}
		// at a gust's front one blade goes and its neighbour not yet: fill that 1-px gap, never show ground
		if (c.a == 0.0 && at(TEXTURE, src).a > 0.0 && height_at(src) < 254.5) {
			vec4 f = at(TEXTURE, src - vec2(bend_of(src, height_at(src)), 0.0));
			c = f.a > 0.0 ? f : at(TEXTURE, src);
		}
	}
	COLOR = trampled ? vec4(0.0) : c;
}
