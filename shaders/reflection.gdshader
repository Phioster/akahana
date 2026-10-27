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
	vec4 c = texture(TEXTURE, UV - vec2(round(amp * sway) * texel.x, 0.0));
	float w = texelFetch(open_water, ivec2(clamp(p, vec2(0.0), world_size - 1.0)), 0).r;
	bool broken = d > 6.0 && sin(p.y * 1.7 + 2.0 * ph + sin(p.y * 0.23 - ph) * 3.0) > 1.0 - min(4.0, floor(d / 8.0)) / 4.5;
	if (c.a < 0.5 || w < 0.5 || broken)
		discard;
	float k = KEEP * max(0.35, 1.0 - d / 90.0);
	COLOR = vec4(c.rgb * DIM, k);
}
