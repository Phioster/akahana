// The journal's page turn (approved 2026-11-06, build/preview/buch/turn.py round 5). The book is bound at the
// top: the bottom right corner curls up to the binding, goes over the stitched band and the sheet stays
// lying back above it. Nothing is bent or skewed; only the fold moves. Drawn over the live page:
// forward  - the old page (a picture taken on the tap) where it is not yet lifted, the live new page beneath
// backward - the page being covered (the picture) where it is lifted, the live page where it lies again
shader_type canvas_item;

uniform sampler2D sheet_tex : filter_nearest;    // assets/ui/buch_blatt.png: R paper, G sheet, B page alpha
uniform sampler2D old_tex : filter_nearest;      // the page as it looked when tapped
uniform float t = 0.0;                           // 0 flat .. 1 turned and lying back
uniform bool forward = true;
uniform bool has_old = false;
uniform vec2 margin = vec2(80.0, 40.0);          // room left of and above the page in this rect
uniform int stacked = 0;                         // sheets already lying back under the turning one (Philip: they stay)

const float W = 156.0;
const float H = 236.0;
const float HINGE = 3.0;                         // the top of the stitched band
const float PAPER_TOP = 15.0;
const float REST = 18.0;                         // what shows of the turned sheet above the band (Philip)
const vec2 CORNER = vec2(147.0, 228.0);
const vec3 BACK = vec3(206.0, 189.0, 152.0) / 255.0;
const vec3 BACK_DARK = vec3(182.0, 164.0, 128.0) / 255.0;
const vec3 BACK_EDGE = vec3(150.0, 130.0, 98.0) / 255.0;

vec4 sheet(vec2 q) {
	if (q.x < 0.0 || q.y < 0.0 || q.x >= W || q.y >= H) return vec4(0.0);
	return texelFetch(sheet_tex, ivec2(q), 0);
}

float ease(float x) { return x * x * (3.0 - 2.0 * x); }

void fold(out vec2 c, out vec2 n) {
	float e = ease(clamp(t, 0.0, 1.0));
	float a = radians(45.0 + 45.0 * e);          // from the corner's diagonal round to the binding's line
	n = vec2(cos(a), sin(a));
	c = CORNER + (vec2(CORNER.x, HINGE) - CORNER) * e;
}

float dist(vec2 q, vec2 c, vec2 n) { return dot(q + 0.5 - c, n); }

// the reflected sheet, before what is over the binding is laid back
bool reflected(vec2 q, vec2 c, vec2 n) {
	float d = dist(q, c, n);
	if (d >= 0.0) return false;
	vec2 s = floor(q + 0.5 - 2.0 * d * n);
	return sheet(s).g > 0.5;
}

// over the binding the sheet lies back at once, foreshortened like the resting sheet: it always hangs on the block
bool flap_only(vec2 q, vec2 c, vec2 n) {
	if (q.y < HINGE) {
		float sc = REST / (H - HINGE);
		float ry = floor(HINGE - (HINGE - (q.y + 0.5)) / sc);
		return reflected(vec2(q.x, ry), c, n);
	}
	return reflected(q, c, n);
}

// wherever it has gone over the binding it covers the band too: one piece of paper, no gap to the band
bool over(float x, vec2 c, vec2 n) {
	for (int i = 1; i <= 20; i++) {
		if (flap_only(vec2(x, HINGE - float(i)), c, n)) return true;
	}
	return false;
}

bool roll(vec2 q, vec2 c, vec2 n) {
	return q.y >= HINGE && q.y <= PAPER_TOP && sheet(q).g > 0.5 && over(q.x, c, n);
}

bool flap(vec2 q, vec2 c, vec2 n) { return flap_only(q, c, n) || roll(q, c, n); }

// the sheets turned before lie behind the newest, each older one a pixel higher, so their edges show as a stack
const int MAX_STACK = 8;
int stack_at(vec2 q) {
	if (q.y > PAPER_TOP || stacked <= 0) return -1;   // the stack only lies over the band and above it
	vec2 c1 = vec2(CORNER.x, HINGE);
	vec2 n1 = vec2(0.0, 1.0);
	int top = -1;
	for (int k = 0; k < MAX_STACK; k++) {
		if (k >= stacked) break;
		// only the part lying back steps up; over the band they all lie in one roll (a shifted roll left a
		// row of the band showing while the next sheet turned, Philip 0.15.1)
		float up = q.y < HINGE ? float(stacked - k) : 0.0;
		if (flap(q + vec2(0.0, up), c1, n1)) top = k;   // the newest in front
	}
	return top;
}

void fragment() {
	vec2 rect = vec2(W, H) + margin;
	vec2 q = floor(UV * rect) - margin;           // page pixel
	vec2 c; vec2 n;
	fold(c, n);
	float d = dist(q, c, n);
	vec4 s = sheet(q);
	bool on_page = s.b > 0.5;
	bool paper = s.r > 0.5;
	bool lifted = paper && d > 0.0;
	COLOR = vec4(0.0);
	if (flap(q, c, n)) {
		float shade;
		if (roll(q, c, n)) {
			float u = clamp((q.y + 0.5 - HINGE) / (PAPER_TOP - HINGE), 0.0, 1.0);
			shade = 0.55 + 0.45 * sin(3.14159 * (0.25 + 0.6 * u));
		} else if (q.y < HINGE) {
			shade = 1.0 - 0.6 * clamp((HINGE - (q.y + 0.5)) / REST, 0.0, 1.0);
		} else {
			shade = clamp(-d / 30.0, 0.0, 1.0);    // darker at the fold, lighter where it curls out
		}
		vec3 col = mix(BACK_DARK, BACK, shade);
		bool edge = !(flap(q + vec2(1, 0), c, n) && flap(q - vec2(1, 0), c, n) && flap(q + vec2(0, 1), c, n) && flap(q - vec2(0, 1), c, n));
		COLOR = vec4(edge ? BACK_EDGE : col, 1.0);
	} else if (stacked > 0 && stack_at(q) >= 0) {
		int k = stack_at(q);
		float rel = q.y < HINGE ? clamp((HINGE - (q.y + float(stacked - k) + 0.5)) / REST, 0.0, 1.0) : 0.0;
		vec3 col = mix(BACK_DARK, BACK, 1.0 - 0.6 * rel);
		bool edge = stack_at(q - vec2(0.0, 1.0)) < k || stack_at(q + vec2(1.0, 0.0)) < 0 || stack_at(q - vec2(1.0, 0.0)) < 0;
		COLOR = vec4(edge ? BACK_EDGE : col, 1.0);
	} else {
		float dark = 1.0;
		if (lifted && d < 5.0) dark *= 0.86;       // the sheet's shadow on the page under it, close to the fold
		if (q.y >= PAPER_TOP && q.y < PAPER_TOP + 4.0 && paper && t > 0.8) dark *= 0.9;   // the roll's shadow
		if (on_page && flap(q + vec2(2, -2), c, n)) dark *= 0.8;   // its own shadow, a little down-left
		// which part is the picture: the old page not yet lifted (forward), the covered page lifted (backward)
		bool pic = has_old && paper && (forward ? !lifted : lifted);
		if (pic) {
			vec3 o = texture(old_tex, (q + 0.5) / vec2(W, H)).rgb;
			COLOR = vec4(o * dark, 1.0);
		} else if (on_page && dark < 1.0) {
			COLOR = vec4(0.0, 0.0, 0.0, 1.0 - dark);
		}
	}
}
