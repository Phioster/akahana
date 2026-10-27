// Moving water on the ground (a port of tools/world/south/water_anim.py, the approved look): the brooks'
// streaks drift downstream, the lake ripples calmly. Each chunk's water map says per pixel where water is
// and how it moves: R flow direction, G depth, B distance along the stream (mod 256 px), A kind
// (1 old brook, 2 new brooks, 3 lake and pools). Bridges, stones, lily pads are not in it: they keep still.
shader_type canvas_item;

const float LOOP = 8.0;                 // like the lights: everything comes round together
const float K = 6.2831853 * 22.0 / 256.0;   // streaks along the stream: whole periods in the 256 px of B
const float W_FLOW = 6.2831853 * 5.0 / LOOP;
const float W_LAKE = 6.2831853 / LOOP;
const vec3 WATER[5] = {vec3(31.0, 42.0, 49.0), vec3(42.0, 58.0, 68.0), vec3(58.0, 79.0, 90.0),
		vec3(85.0, 112.0, 121.0), vec3(127.0, 152.0, 156.0)};
const vec3 OLD_WAT[6] = {vec3(60.0, 70.0, 80.0), vec3(78.0, 90.0, 101.0), vec3(100.0, 113.0, 124.0),
		vec3(127.0, 140.0, 150.0), vec3(163.0, 174.0, 182.0), vec3(214.0, 221.0, 225.0)};

uniform sampler2D water_tex : filter_nearest;
uniform vec2 origin;                    // world position of this chunk's top-left pixel

// The GPU computes in 32 bit: sin() of world coordinates in the thousands would make the noise stripy,
// so the coordinates are folded first (water_anim.hash2 does the same).
float hash2(vec2 p, float s) {
	vec2 q = mod(p, 289.0);
	return fract(sin(q.x * 12.9898 + q.y * 78.233 + s) * 43758.5453);
}

void fragment() {
	ivec2 px = ivec2(UV * vec2(textureSize(TEXTURE, 0)));
	vec4 base = texelFetch(TEXTURE, px, 0);
	vec4 w = texelFetch(water_tex, px, 0);
	int kind = int(round(w.a * 255.0));
	COLOR = base;
	if (kind > 0) {
		vec2 p = origin + vec2(px);
		float t = mod(TIME, LOOP);
		float ang = w.r * 255.0 / 256.0 * 6.2831853;
		float dep = w.g;
		float along = round(w.b * 255.0);
		vec2 f = vec2(cos(ang), sin(ang));
		float n = hash2(p, 0.0) * 2.0 - 1.0;
		float h2 = hash2(p, 1.7);
		float across = p.x * f.y - p.y * f.x;
		vec3 c;
		if (kind == 3) {                                          // the lake and the pools: calm ripples
			float v = 0.6 - 0.45 * dep + 0.05 * n;
			int idx = clamp(int(round(v * 4.0)), 0, 4);
			bool ripple = sin(p.x * 0.45 + 3.0 * sin(p.y * 0.35 + t * W_LAKE) + n + t * 2.0 * W_LAKE) > 0.93;
			if (ripple && mod(p.y, 3.0) < 0.5 && h2 < 0.6) idx = 4;
			c = WATER[idx];
		} else {
			float streak = sin(along * K - t * W_FLOW + 2.2 * sin(across * 0.9) + 0.8 * n);
			if (kind == 2) {                                      // the new brooks
				float v = 0.62 - 0.38 * dep + 0.06 * n;
				if (streak > 0.82) v += 0.28;
				if (streak > 0.97 && h2 < 0.5) v = 0.97;
				c = WATER[clamp(int(round(v * 4.0)), 0, 4)];
			} else {                                              // the old brook, in gen_world's colours
				int b = clamp(int((0.52 - 0.22 * dep + 0.06 * (h2 - 0.5)) * 6.0), 0, 3);
				int wi = streak > 0.82 ? min(b + 1, 3) : b;       // never the near-white steps: they glittered
				if (streak > 0.97 && h2 < 0.06) wi = 4;
				if (dep < 0.25 && h2 < 0.15) wi = 4;
				c = OLD_WAT[wi];
			}
		}
		COLOR = vec4(c / 255.0, base.a);
	}
}
