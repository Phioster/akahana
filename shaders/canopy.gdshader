// Whatever stands in front of the wanderer (y-sort: its foot lies below his) opens over him in a 4x4 Bayer
// screen, so he stays visible among the trees. The pattern is fixed to the world pixel: it never shimmers.
shader_type canvas_item;

uniform vec2 wanderer = vec2(-1000.0);  // his feet in world pixels
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
		vec2 d = max(abs(world - (wanderer - vec2(0.0, 8.0))) - HALF, vec2(0.0));
		float share = open_share * (1.0 - smoothstep(0.0, RAMP, length(d)));
		if (bayer4(ivec2(floor(world))) < share) {
			discard;
		}
	}
}
