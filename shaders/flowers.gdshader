// Poppy heads sway in the same gusts as in the wallpaper, and nod aside around the wanderer's feet. Each
// flower moves as a whole by a few pixels (never the picture under it: that squashes the blossoms and
// looks laid over the meadow). Behind him the nodding opens into a frayed V and swings back slowly.
shader_type canvas_item;

const int TRAIL = 24;
const float R0 = 8.0;                 // half width of the wake right at the feet: widest where he walks
const float R1 = 2.0;                 // ... at its far end: it closes behind him like a V
const float PUSH = 6.0;
const float REED_H = 9.0;               // from this height up a reed leans the whole way out of the wake               // most a flower nods aside, in whole pixels

const float BEND_H = 10.0;            // px above its foot from where a blade goes the whole way with the wind
const float CALM_B = 1.1;             // grass and reeds stir between the gusts too (poppies keep 0.5)

uniform sampler2D bend_tex : filter_nearest;   // per pixel: height above its plant's foot, 255 = sways whole
uniform vec2 tex_size;
uniform vec2 origin;                  // world position of this picture's top-left texel (chunk minus apron)
uniform sampler2D ground_tex : filter_nearest;   // the chunk's ground (no apron): the trail darkens it
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
// the bend map (tools/world/south/bendcode.py): height above the foot, + 128 for reeds; 255 = poppy head
float raw_at(vec2 w) { return round(texture(bend_tex, (floor(w) - origin + 0.5) / tex_size).r * 255.0); }
float height_at(vec2 w) { float b = raw_at(w); return b > 254.5 ? 255.0 : mod(b, 128.0); }
bool reed_at(vec2 w) { float b = raw_at(w); return b > 127.5 && b < 254.5; }

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
	float press = 0.0;                                     // in the trail's middle the blades lie pressed down
	bool lay_flat = false;
	// the trail through tall grass (approved B): pressed blades lie flat, the ground between them a little
	// darker, short stalks lying along the way; it rises again with the wake (tools/world/south/trail_video.py)
	{
		float e = bk * bk * (3.0 - 2.0 * bk);
		float rw0 = mix(R1, R0, bk);                       // wide at his feet, closing behind him (a V)
		press = best > 0.05 ? clamp(sqrt(e) * clamp(1.2 - abs(bo) / (rw0 * 0.8), 0.0, 1.0), 0.0, 1.0) : 0.0;
	}
	float h = hash(p);
	float lean = 0.0;                                      // reeds: how far their tops lean out of the way
	float rw = mix(R1, R0, bk);                            // the V closes with age
	if (best > 0.3 * h && abs(bo) < rw) {                  // frayed: each flower lets go at its own moment
		float ease = bk * bk * (3.0 - 2.0 * bk);           // swings back slowly
		float amt = PUSH * ease * clamp(1.0 - abs(bo) / rw, 0.0, 1.0) * 2.0;
		float off = floor(clamp(amt, 0.0, PUSH) + h * 0.6);
		trampled = abs(bo) < 1.0 && h < 0.5 * ease;        // here and there one bent under his feet
		src = p - bn * sign(bo) * off;
		lean = clamp(length(bn * off) * 2.6 * sign(abs(bn.x) > 0.2 ? -bn.x * sign(bo) : -sign(bo)), -8.0, 8.0);   // within the chunk's apron
	}
	// poppy heads (height 255) move whole, as they always did
	vec4 c = at(TEXTURE, src - vec2(dx, 0.0));
	if (!(c.a > 0.0 && height_at(src - vec2(dx, 0.0)) > 254.5)) {
		// grass and reeds bend: which blade pixel lands here (the highest wins where two do)
		c = vec4(0.0);
		float best = -1.0;
		bool reed = false;
		for (int k = -2; k <= 3; k++) {
			vec2 s = src - vec2(float(k), 0.0);
			vec4 cs = at(TEXTURE, s);
			float h = height_at(s);
			if (cs.a > 0.0 && h < 254.5 && h > best && bend_of(s, h) == float(k) && !(lean != 0.0 && reed_at(s))) {
				c = cs;
				best = h;
				reed = reed_at(s);
			}
		}
		// reeds in the wake bend from their foot like in a gust: the higher, the further they lean aside
		if (lean != 0.0) {
			for (int k = -11; k <= 11; k++) {
				vec2 s = p - vec2(float(k), 0.0);
				vec4 cs = at(TEXTURE, s);
				float h = height_at(s);
				if (cs.a > 0.0 && h < 254.5 && h > best && reed_at(s)
						&& bend_of(s, h) + round(lean * min(h / REED_H, 1.0)) == float(k)) {
					c = cs;
					best = h;
					reed = true;
				}
			}
		}
		// at a gust's front one blade goes and its neighbour not yet: fill that 1-px gap, never ground
		if (c.a > 0.0 && press > 0.15 && best > 1.0 && !reed) {   // reeds only step aside
			c = vec4(0.0);                                 // pressed flat (the lane below fills it with ground)
			lay_flat = true;
		}
		else if (c.a == 0.0 && press < 0.15 && at(TEXTURE, src).a > 0.0 && height_at(src) < 254.5) {
			vec4 f = at(TEXTURE, src - vec2(bend_of(src, height_at(src)), 0.0));
			c = f.a > 0.0 ? f : at(TEXTURE, src);
		}
	}
	if (press > 0.15) {
		vec2 gs = vec2(textureSize(ground_tex, 0));
		vec2 g = p - origin - (tex_size - gs) * 0.5;      // the ground has no apron
		vec3 ground = texelFetch(ground_tex, ivec2(clamp(g, vec2(0.0), gs - 1.0)), 0).rgb;
		vec4 lane = c.a > 0.0 ? c : vec4(ground * (lay_flat ? 1.0 - 0.45 * press : 1.0), 1.0);
		if (hash(vec2(p.x, floor(p.y / 3.0))) < 0.18 && press > 0.3 && (c.a == 0.0 || lay_flat))   // a stalk lying along the way
			lane.rgb = lane.rgb * 0.5 + vec3(150.0, 150.0, 116.0) / 255.0 * 0.5;
		COLOR = lane;
	} else {
		COLOR = trampled ? vec4(0.0) : c;
	}
}
