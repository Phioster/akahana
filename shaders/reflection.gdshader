// The wanderer mirrored below his feet, only on open water (the approved reflect_anim look): dimmed, a
// little of the water's colour through it, his rows pulled sideways by the same two swells as the still
// reflections in water.gdshader, and broken by the same ripple rows further from his feet.
shader_type canvas_item;

const float LOOP = 8.0;
const float KEEP = 0.68;
const float DIM = 0.72;

uniform sampler2D open_water : filter_nearest;   // the whole world, 255 where open water lies
uniform vec2 world_size = vec2(900.0, 3600.0);
uniform float foot_y = 0.0;                      // world row of his feet, set every frame
uniform sampler2D puddles : filter_nearest;      // after the rain he shows in the puddles too (water.gdshader)
uniform float wet = 0.0;
const float POOL_FROM = 0.35;                   // the ground soaks first; only then the puddles fill (0.17.1)

// how far the puddles have filled: a hold of exactly 1 must still wait for the first of it (mobile floats
// made 127/127 a hair above 1, so the fire's hollow stood full the moment it rained, 0.17.3)
bool pooled(float h) {
	float fill = clamp((wet - POOL_FROM) / (1.0 - POOL_FROM), 0.0, 1.0);
	return fill > 0.001 && h > 1.0 - fill;
}
uniform float rain = 0.0;

bool puddle_at(vec2 p) {
	if (p.x < 0.0 || p.y < 0.0 || p.x >= world_size.x || p.y >= world_size.y) return false;
	float v = round(texelFetch(puddles, ivec2(clamp(p, vec2(0.0), world_size - 1.0)), 0).r * 255.0);
	float h = v < 0.5 ? 0.0 : (v < 127.5 ? (v - 1.0) / 126.0 : (v - 128.0) / 127.0);
	return wet > 0.001 && h > 0.0 && pooled(h);
}

varying vec2 world;

void vertex() {
	world = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
}

void fragment() {
	vec2 p = floor(world);
	float ph = 6.2831853 * mod(TIME, LOOP) / LOOP;
	float d = max(0.0, p.y - foot_y);
	float amp = min(2.0, 0.4 + d / 14.0);
	float sway = 0.65 * sin(p.y * 0.85 - ph + 0.03 * p.x) + 0.45 * sin(p.y * 0.31 + 3.0 * ph + 0.05 * p.x + 1.7);
	vec2 texel = 1.0 / vec2(textureSize(TEXTURE, 0));
	float w = texelFetch(open_water, ivec2(clamp(p, vec2(0.0), world_size - 1.0)), 0).r;
	bool pud = w < 0.5 && puddle_at(p);
	float shift = round(amp * sway);
	if (pud)                                     // a puddle lies still, the rain shakes it a little
		shift = round((0.3 + 0.45 * rain) * sin(mod(p.y, 628.3185) * 0.9 + mod(TIME, 2513.274) * 2.5));
	vec4 c = texture(TEXTURE, UV - vec2(shift * texel.x, 0.0));
	bool broken = !pud && d > 6.0 && sin(p.y * 1.7 + 2.0 * ph + sin(p.y * 0.23 - ph) * 3.0) > 1.0 - min(4.0, floor(d / 8.0)) / 4.5;
	if (c.a < 0.5 || (w < 0.5 && !pud) || broken)
		discard;
	float k = KEEP * max(0.35, 1.0 - d / 90.0);
	COLOR = vec4(c.rgb * DIM, k);
}
