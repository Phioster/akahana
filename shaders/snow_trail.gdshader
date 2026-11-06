// The furrow in the snow (scenes/snow_trail.gd keeps the record, look approved 2026-11-06 from
// build/preview/spuren/furrow.py). Per pixel: R,G = when trodden (16 bit, in ticks), B = depth*2 + dent,
// A = 255 furrow / 128 snow beside it. Light falls from the upper left, as on the rest of the ground.
shader_type canvas_item;

uniform float now = 0.0;
uniform float fill = 960.0;          // ticks until the wind has filled it
uniform float wrap = 65536.0;
uniform vec2 origin;                 // world px of the picture's pixel 0 (padding included)
uniform sampler2D trail : filter_nearest;   // the record itself (TEXTURE is not readable in functions)

const vec3 IN_LIT = vec3(228.0, 224.0, 216.0) / 255.0;    // the snow's own warm greys, deeper
const vec3 IN_MID = vec3(190.0, 186.0, 182.0) / 255.0;
const vec3 IN_SHADE = vec3(162.0, 158.0, 157.0) / 255.0;
const vec3 WALL_DARK = vec3(120.0, 117.0, 119.0) / 255.0;
const vec3 DENT = vec3(132.0, 128.0, 129.0) / 255.0;
const vec3 PILE = vec3(250.0, 247.0, 240.0) / 255.0;
const vec3 PILE_SHADE = vec3(214.0, 210.0, 204.0) / 255.0;

// integer hash on whole pixels: sin() of large world coordinates turns to stripes on phone GPUs
float hash(vec2 p) {
	uvec2 v = uvec2(ivec2(floor(p)) + 65536);
	uint h = v.x * 1664525u + v.y * 1013904223u;
	h ^= h >> 16u; h *= 2246822519u; h ^= h >> 13u; h *= 3266489917u; h ^= h >> 16u;
	return float(h & 16777215u) / 16777216.0;
}

vec4 px(ivec2 q) {
	ivec2 s = textureSize(trail, 0);
	if (q.x < 0 || q.y < 0 || q.x >= s.x || q.y >= s.y) return vec4(0.0);
	return texelFetch(trail, q, 0);
}

// how far the wind has got here, 0..1
float filled(vec4 c) {
	float born = floor(c.r * 255.0 + 0.5) * 256.0 + floor(c.g * 255.0 + 0.5);
	return clamp(mod(now - born + wrap, wrap) / fill, 0.0, 1.0);
}

bool ring(vec4 c) { return c.a > 0.25; }

// still open: the walls fill first, then the middle, each pixel at its own moment
bool cut(ivec2 q) {
	vec4 c = px(q);
	if (c.a < 0.75) return false;
	float depth = floor(floor(c.b * 255.0 + 0.5) / 2.0);
	float key = 0.55 * depth / 4.0 + 0.45 * hash(origin + vec2(q));
	float f = filled(c);
	return f < 1.0 && key >= f;
}

bool rim(ivec2 q) {
	return ring(px(q)) && !cut(q) && (cut(q + ivec2(0, 1)) || cut(q + ivec2(0, -1)) || cut(q + ivec2(1, 0)) || cut(q + ivec2(-1, 0)));
}

float lump(ivec2 q) {
	vec2 w = origin + vec2(q);
	return hash(vec2(w.x, floor(w.y / 2.0)) + 17.0);
}

bool heap(ivec2 q) {
	if (!ring(px(q)) || cut(q)) return false;
	float f = filled(px(q));
	if (rim(q)) return lump(q) < 0.8 * (1.0 - f);
	return (rim(q - ivec2(0, 1)) || rim(q + ivec2(1, 0))) && lump(q) < 0.35 * (1.0 - f);   // bigger heaps here and there
}

void fragment() {
	ivec2 q = ivec2(floor(UV * vec2(textureSize(trail, 0))));
	vec4 c = px(q);
	COLOR = vec4(0.0);
	if (ring(c)) {
		vec2 w = origin + vec2(q);
		if (cut(q)) {
			float n = hash(floor(w / 2.0)) * 0.6 + hash(w + 5.0) * 0.4;   // churned clumps
			vec3 col = n < 0.33 ? IN_SHADE : (n < 0.75 ? IN_MID : IN_LIT);
			// the wall facing the light lies in its own shadow, the far one catches it
			bool dark = !cut(q - ivec2(0, 1)) || (!cut(q - ivec2(1, 0)) && lump(q) < 0.6);
			bool lit = !cut(q + ivec2(0, 1)) || !cut(q + ivec2(1, 0));
			if (dark) col = WALL_DARK;
			else if (lit) col = IN_LIT;
			int b = int(floor(c.b * 255.0 + 0.5));
			if (b % 2 == 1) col = DENT;
			else if (int(floor(px(q + ivec2(0, 1)).b * 255.0 + 0.5)) % 2 == 1 && cut(q + ivec2(0, 1))) col = IN_SHADE;   // the dent's back edge
			COLOR = vec4(col, 1.0);
		} else if (heap(q)) {
			COLOR = vec4(PILE, 1.0);
		} else if ((heap(q - ivec2(1, 1)) || heap(q - ivec2(0, 1))) && lump(q) > 0.45) {
			COLOR = vec4(PILE_SHADE, 1.0);           // the heap's shadow on the snow below it
		} else if (rim(q - ivec2(0, 1)) || rim(q + ivec2(0, 1)) || rim(q - ivec2(1, 0)) || rim(q + ivec2(1, 0))) {
			if (hash(w + 31.0) > 0.86 && filled(c) < 0.6) COLOR = vec4(PILE, 1.0);   // clumps kicked out beside it
		}
	}
}
