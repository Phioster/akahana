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
// The still things by the water, mirrored (tools/world/south/reflect_map.py, the approved reflect_anim look):
// RGB the dimmed colour, A strength (high nibble) and distance below the foot / 6 (low nibble). It has the
// apron, so the ripples can pull a reflection across the chunk's edge.
uniform sampler2D refl_tex : filter_nearest;
uniform float apron = 8.0;
uniform vec2 lamps[4];                  // a lantern by the lake: where its light's path on the water starts
uniform int lamp_count = 0;
const vec3 LAMP = vec3(236.0, 190.0, 110.0);

// The wet ground after the rain (approved 2026-11-06, build/preview/regen/wet.py round 3; tools/world/gen_wet.py):
// darker and richer, puddles in the hollows that mirror the sky and the things by them, the lights drawn out
// into warm streaks, a glitter now and then, rings on the puddles while it rains.
uniform sampler2D puddles : filter_nearest;     // the world: 0 none, 1..127 meadow, 128..255 path; the rest: hold
uniform vec2 world_size = vec2(1800.0, 4800.0);
uniform float wet = 0.0;                        // Weather.wetness(): 0 dry .. 1 soaked
const float POOL_FROM = 0.35;                   // the ground soaks first; only then the puddles fill (0.17.1)

// how far the puddles have filled: a hold of exactly 1 must still wait for the first of it (mobile floats
// made 127/127 a hair above 1, so the fire's hollow stood full the moment it rained, 0.17.3)
bool pooled(float h) {
	float fill = clamp((wet - POOL_FROM) / (1.0 - POOL_FROM), 0.0, 1.0);
	return fill > 0.001 && h > 1.0 - fill;
}
uniform float rain = 0.0;                       // the shower now: its rings, and it shakes the mirror
uniform vec4 wlights[8];                        // lights on this chunk's ground: x, y, strength, 1 = a fire
uniform int wlight_count = 0;
const vec3 SKY = vec3(106.0, 118.0, 144.0);     // the evening sky in a puddle
const vec3 WARM = vec3(255.0, 180.0, 90.0);

// The GPU computes in 32 bit: sin() of world coordinates in the thousands would make the noise stripy,
// so the coordinates are folded first (water_anim.hash2 does the same).
float hash2(vec2 p, float s) {
	vec2 q = mod(p, 289.0);
	return fract(sin(q.x * 12.9898 + q.y * 78.233 + s) * 43758.5453);
}

// how early a puddle holds here (0 never) and what the ground is (0 none, 1 meadow, 2 path)
float hold_at(vec2 p, out int kind) {
	kind = 0;
	if (p.x < 0.0 || p.y < 0.0 || p.x >= world_size.x || p.y >= world_size.y) return 0.0;   // the cave lies beside
	float v = round(texelFetch(puddles, ivec2(p), 0).r * 255.0);
	kind = v < 0.5 ? 0 : (v < 127.5 ? 1 : 2);
	return kind == 0 ? 0.0 : (kind == 1 ? (v - 1.0) / 126.0 : (v - 128.0) / 127.0);
}

bool puddle_at(vec2 p) {
	int k;
	float h = hold_at(p, k);
	return h > 0.0 && pooled(h);
}

vec3 wet_ground(vec3 base_col, vec2 p, ivec2 px) {
	vec3 col = base_col;
	int kind;
	float h = hold_at(p, kind);
	if (kind == 0) return col;
	bool path = kind == 2;
	float t = TIME;
	float lum = (col.r + col.g + col.b) / 3.0;
	col = (col + (col - lum) * 0.25 * wet) * (1.0 - (path ? 0.30 : 0.16) * wet);
	bool pud = h > 0.0 && pooled(h);
	if (pud) {
		vec2 f = mod(p, 628.3185);                 // whole periods of every wave: no stripes at large coordinates
		float band = sin(f.y * 1.6 + f.x * 0.15 + t * 0.25) + 0.4 * sin(f.x * 0.7 - t * 0.4);
		vec3 m = SKY / 255.0 + (band > 1.05 ? vec3(34.0, 36.0, 40.0) / 255.0 : vec3(0.0));
		// what stands by it, mirrored (baked with the water's reflections), still once the rain stops
		float amp = 0.3 + 0.45 * rain;
		int sh = int(round(amp * sin(mod(p.y, 628.3185) * 0.9 + mod(t, 2513.274) * 2.5)));
		ivec2 rs = ivec2(textureSize(refl_tex, 0));
		vec4 r = texelFetch(refl_tex, clamp(px + ivec2(int(apron)) - ivec2(sh, 0), ivec2(0), rs - 1), 0);
		int a = int(round(r.a * 255.0));
		if (a > 0) {
			vec3 c = r.rgb;
			vec3 raw = c / 0.72;                    // reflect_map dims everything; a flame stays bright in water
			if (raw.r > 0.83 && raw.r - raw.b > 0.35) c = min(raw * 0.95, vec3(1.0));
			m = mix(m, c, min(1.0, float(a >> 4) / 15.0 * 1.1));
		}
		col = col * 0.08 + m * 0.92;
		if (!puddle_at(p - vec2(0.0, 1.0))) col = col * 0.5 + vec3(170.0, 178.0, 196.0) / 255.0 * 0.5;   // the far brim
		else if (!puddle_at(p + vec2(0.0, 1.0))) col *= 0.72;                                             // the bank
		// rings while it rains: one at a time in each 8-px cell, each half a second
		if (rain > 0.0) {
			vec2 cell = floor(p / 8.0);
			float hc = hash2(cell, 5.3);
			float tt = t / 0.5 + hc;
			float slot = floor(tt);
			if (hash2(cell, mod(slot, 97.0) * 0.71) < min(1.0, 1.9 * rain)) {
				vec2 o = p - (cell * 8.0 + 1.0 + floor(vec2(hash2(cell, 1.1 + slot), hash2(cell, 2.3 + slot)) * 6.0));
				float age = fract(tt) * 0.5;
				float R = round(age / 0.12);
				bool on = R < 0.5 ? (o.x == 0.0 && o.y == 0.0) : abs(round(length(vec2(o.x, o.y / 0.6))) - R) < 0.5;
				if (on) col = mix(col, vec3(200.0, 210.0, 222.0) / 255.0, (1.0 - age / 0.5) * 0.45);
			}
		}
	}
	// the lights drawn out downwards over the wet ground; in a puddle their own mirror does most of it
	float near = 0.0;
	for (int i = 0; i < 8; i++) {
		if (i >= wlight_count) break;
		vec4 l = wlights[i];
		bool fire = l.w > 0.5;
		vec2 d = p - l.xy;
		near = max(near, l.z * exp(-dot(d, d) / 900.0));
		if (d.y <= 2.0 || d.y >= (fire ? 60.0 : 34.0)) continue;
		float wx = (fire ? 2.5 : 1.5) + 0.04 * d.y;
		float wob = sin(mod(p.y, 628.3185) * 0.8 + mod(t, 1000.0) * (6.0 + 6.0 * rain)) * (0.5 + 0.8 * rain);
		float u = (d.x - wob) / wx;
		float k = exp(-u * u) * exp(-d.y / (fire ? 22.0 : 12.0));
		float fl = 0.85 + 0.15 * sin(mod(t, 1000.0) * (fire ? 13.0 : 5.0) + l.x);
		float gain = (pud ? 0.84 : (path ? 0.30 : 0.12)) * wet * l.z * fl;
		col += WARM / 255.0 * min(k * gain, 0.6);
	}
	// glitter: a pixel lights up for a moment, more on the path and by the lights
	float slot = floor(t / 0.15);
	if (hash2(p, mod(slot, 211.0) * 1.37) < 7.0e-4 * ((path ? 0.5 : 0.08) + near) * wet)
		col = col * 0.3 + vec3(235.0, 225.0, 200.0) / 255.0 * 0.6;
	return col;
}

void fragment() {
	ivec2 px = ivec2(UV * vec2(textureSize(TEXTURE, 0)));
	vec4 base = texelFetch(TEXTURE, px, 0);
	vec4 w = texelFetch(water_tex, px, 0);
	int kind = int(round(w.a * 255.0));
	COLOR = base;
	if (kind == 0 && wet > 0.001)
		COLOR = vec4(wet_ground(base.rgb, origin + vec2(px), px), base.a);
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
		vec3 col = c / 255.0;
		float ph = 6.2831853 * t / LOOP;
		// the reflection: rows swayed by two swells at their own pace, broken by ripple rows further out
		float sway = 0.65 * sin(p.y * 0.85 - ph + 0.03 * p.x) + 0.45 * sin(p.y * 0.31 + 3.0 * ph + 0.05 * p.x + 1.7);
		ivec2 rs = ivec2(textureSize(refl_tex, 0));
		ivec2 q = px + ivec2(int(apron));
		int a0 = int(round(texelFetch(refl_tex, q, 0).a * 255.0));
		float amp = a0 > 0 ? min(2.0, 0.4 + float(a0 & 15) * 6.0 / 14.0) : 1.4;   // further out, more sway
		vec4 r = texelFetch(refl_tex, clamp(q - ivec2(int(round(amp * sway)), 0), ivec2(0), rs - 1), 0);
		int a = int(round(r.a * 255.0));
		if (a > 0) {
			float d = float(a & 15) * 6.0;
			bool broken = d > 6.0 && sin(p.y * 1.7 + 2.0 * ph + sin(p.y * 0.23 - ph) * 3.0)
					> 1.0 - min(4.0, floor(d / 8.0)) / 4.5;
			if (!broken)
				col = mix(col, r.rgb, float(a >> 4) / 15.0);
		}
		// a lantern's light: glints in their own rhythm, swaying, thinning out downwards (lake only)
		if (kind == 3) {
			for (int i = 0; i < 4; i++) {
				if (i >= lamp_count) break;
				float dd = p.y - lamps[i].y;
				if (dd < 0.0 || dd >= 26.0) continue;
				float half = 1.0 + floor(dd / 9.0);
				float off = round(1.0 * sin(p.y * 0.9 - ph) + 0.7 * sin(p.y * 0.37 + 3.0 * ph + 1.3));
				if (abs(p.x - (lamps[i].x + off)) > half) continue;
				float hh = hash2(p, 3.1);
				float cyc = 1.0 + floor(hh * 5.0);           // whole cycles per loop: it still loops
				if (sin(cyc * ph + hh * 40.0) < 0.15) continue;
				col = mix(col, LAMP / 255.0, 0.68 * (1.0 - dd / 30.0) * 0.9);
			}
		}
		COLOR = vec4(col, base.a);
	}
}
