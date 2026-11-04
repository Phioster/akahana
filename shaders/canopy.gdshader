// Whatever stands in front of the wanderer (y-sort: its foot lies below his) leaves his outline open and
// opens around him in a 4x4 Bayer screen, so he stays visible among the trees. The pattern is fixed to the world pixel: it never shimmers.
shader_type canvas_item;

uniform vec2 wanderer = vec2(-1000.0);  // his feet in world pixels
uniform sampler2D monk_tex : filter_nearest;   // his current sheet: what stands in front keeps his outline open
uniform vec4 monk_rect = vec4(-1000.0, -1000.0, 1.0, 1.0);   // his frame in world px: top-left, size
uniform vec4 monk_uv = vec4(0.0, 0.0, 1.0, 1.0);              // that frame in the sheet: uv origin, uv size
uniform vec4 lamp_rect = vec4(-1000.0, -1000.0, 0.0, 0.0);   // the lantern on his staff (drawn apart from the sheet)
uniform float open_share = 0.8;         // share of a crown's pixels left out right over him
const vec2 HALF = vec2(7.0, 9.0);       // his body around (feet.x, feet.y - 8)
const float RAMP = 5.0;                 // px over which the screen closes again around him

varying vec2 world;
varying float foot;

void vertex() {
	world = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
	foot = MODEL_MATRIX[3].y;
}

float bayer4(ivec2 p) {
	const float M[16] = float[16](0.0, 8.0, 2.0, 10.0, 12.0, 4.0, 14.0, 6.0, 3.0, 11.0, 1.0, 9.0, 15.0, 7.0, 13.0, 5.0);
	return (M[(p.y & 3) * 4 + (p.x & 3)] + 0.5) / 16.0;
}

void fragment() {
	if (foot > wanderer.y) {
		vec2 cell = floor(world);
		vec2 m = cell - monk_rect.xy;
		if (all(greaterThanEqual(m, vec2(0.0))) && all(lessThan(m, monk_rect.zw))
				&& texture(monk_tex, monk_uv.xy + (m + 0.5) / monk_rect.zw * monk_uv.zw).a > 0.5) {
			discard;                           // he himself shows whole, the screen only around him
		}
		vec2 l = cell - lamp_rect.xy;
		if (all(greaterThanEqual(l, vec2(0.0))) && all(lessThan(l, lamp_rect.zw))) {
			discard;
		}
		vec2 d = max(abs(world - (wanderer - vec2(0.0, 8.0))) - HALF, vec2(0.0));
		float share = open_share * (1.0 - smoothstep(0.0, RAMP, length(d)));
		if (bayer4(ivec2(floor(world))) < share) {
			discard;
		}
	}
}
