// The wallpaper's atmosphere() + dither(), ported 1:1 so the game looks like the video:
// overcast morning grade, warm flickering light from lamps and fire, drifting mist, bloom,
// and the 4x4 Bayer raster only where mist and light show.
shader_type canvas_item;
render_mode unshaded;

uniform sampler2D screen_tex : hint_screen_texture, filter_nearest;
uniform sampler2D mist1 : repeat_enable, filter_linear;
uniform sampler2D mist2 : repeat_enable, filter_linear;
uniform vec2 view_world = vec2(180.0, 400.0);   // visible area in art pixels
uniform vec2 cam_pos;                 // world position (art px, fractional) of the screen's top-left corner
uniform int light_count = 0;
uniform vec4 lights[16];              // x, y, radius, strength
uniform vec4 light_info[16];          // kind, x seed, y seed, glowing pixel count

const float LOOP = 8.0;               // the wallpaper loops every 8 s; flicker uses the same phase
const vec3 LCOL = vec3(1.0, 0.62, 0.30);
const vec3 WCOL = vec3(0.55, 0.95, 0.85);    // the will-o'-the-wisp: a cold, pale green light
const vec3 MIST = vec3(214.0, 214.0, 212.0);

float flick(float kind, float ph, vec2 s) {
	if (kind < 0.5) return 0.80 + 0.12 * sin(ph * 11.0) + 0.08 * sin(ph * 23.0 + 1.3);                 // fire
	if (kind < 1.5) return 0.9 + 0.06 * sin(ph * 13.0 + sin(ph * 7.0));                                 // stone lantern
	if (kind < 2.5) return 0.75 + 0.25 * (0.5 + 0.35 * sin(ph * 11.0 + s.x) + 0.15 * sin(ph * 31.0 + s.y)); // wood lantern
	if (kind < 3.5) return 0.8 + 0.2 * sin(ph * 13.0 + sin(ph * 7.0));                                // candles
	return 1.0;                                                                                       // wisp: its own node pulses
}

float bayer4(vec2 p) {
	int i = int(mod(p.y, 4.0)) * 4 + int(mod(p.x, 4.0));
	float v = 0.0;
	if (i == 0) v = 0.0;  else if (i == 1) v = 8.0;  else if (i == 2) v = 2.0;  else if (i == 3) v = 10.0;
	else if (i == 4) v = 12.0; else if (i == 5) v = 4.0;  else if (i == 6) v = 14.0; else if (i == 7) v = 6.0;
	else if (i == 8) v = 3.0;  else if (i == 9) v = 11.0; else if (i == 10) v = 1.0; else if (i == 11) v = 9.0;
	else if (i == 12) v = 15.0; else if (i == 13) v = 7.0; else if (i == 14) v = 13.0; else v = 5.0;
	return (v + 0.5) / 16.0;
}

vec3 grade(vec3 c) {
	float lum = (c.r + c.g + c.b) / 3.0;
	return (c * 0.78 + lum * 0.22) * vec3(0.74, 0.76, 0.80);
}

void fragment() {
	// everything is worked out per ART pixel of the world, so the raster, mist and light sit on the
	// ground and glide with it instead of crawling over it while the camera moves
	vec2 px = floor(cam_pos + SCREEN_UV * view_world);
	vec2 world = px + 0.5;
	vec2 uv = (world - cam_pos) / view_world;              // centre of this art pixel on screen
	vec3 src = texture(screen_tex, uv).rgb * 255.0;
	bool em = src.r > 190.0 && src.g > 110.0 && src.b < 140.0 && src.r - src.b > 90.0;
	vec3 a = grade(src);

	float ph = 6.2831853 * TIME / LOOP;
	float L = 0.0;
	float Lw = 0.0;
	vec3 bloom = vec3(0.0);
	vec3 bloomw = vec3(0.0);
	for (int i = 0; i < 16; i++) {
		if (i >= light_count) break;
		vec4 l = lights[i];
		vec4 info = light_info[i];
		float fl = flick(info.x, ph, info.yz);
		vec2 dv = world - l.xy;
		float d = length(dv * vec2(1.0, 1.35)) / l.z;          // ground seen at an angle: pool wider than tall
		float li = l.w * fl / (1.0 + 4.0 * d * d) * sqrt(clamp(1.0 - d, 0.0, 1.0));
		float r2 = dot(dv, dv);                                // bloom = blurred glowing pixels, as three gaussians
		float g = 0.0875 * exp(-r2 / 8.0) + 0.0221 * exp(-r2 / 72.0) + 0.00568 * exp(-r2 / 392.0);
		if (info.x > 3.5) {
			Lw += li;
			bloomw += vec3(150.0, 240.0, 215.0) * info.w * g;
		} else {
			L += li;
			bloom += vec3(250.0, 190.0, 90.0) * info.w * fl * g;
		}
	}
	bloom *= vec3(1.0, 0.80, 0.55);
	a *= 1.0 + L * LCOL * 1.4 + Lw * WCOL * 1.2;

	vec2 m1 = (world - vec2(3.5 * TIME, 0.0)) / vec2(256.0);      // mist drifts right, two layers at two speeds
	vec2 m2 = (world - vec2(6.0 * TIME, 0.0)) / vec2(256.0);
	float f = 0.55 * (texture(mist1, m1).r - 0.5) * 6.0 + 0.45 * (texture(mist2, m2).r - 0.5) * 6.0;
	float dens = clamp((f - 0.2) * 0.36, 0.0, 0.32);

	vec2 t = 1.0 / view_world;                                     // softness only where the mist is thick
	vec3 nb = texture(screen_tex, uv + vec2(t.x, 0.0)).rgb + texture(screen_tex, uv - vec2(t.x, 0.0)).rgb
		+ texture(screen_tex, uv + vec2(0.0, t.y)).rgb + texture(screen_tex, uv - vec2(0.0, t.y)).rgb;
	vec3 soft = grade((nb * 0.25 * 0.55 + src / 255.0 * 0.45) * 255.0) * (1.0 + L * LCOL * 1.4);
	a = mix(a, soft, clamp(dens * 2.2, 0.0, 1.0));
	a = a * (1.0 - dens) + MIST * 0.8 * (1.0 + L * LCOL * 1.6) * dens;   // mist glows near the lights

	a += bloom + bloomw;
	if (em) a = max(a, src * 1.05);

	float eff = em ? 0.0 : clamp(dens * 7.0 + (L + Lw) * 2.5 + (bloom.r + bloom.g + bloom.b + bloomw.g) / 90.0, 0.0, 1.0);
	float bay = bayer4(px);
	if (eff > bay * 0.8 + 0.1) {                                   // raster only on mist and light
		float l2 = (a.r + a.g + a.b) / 3.0 + 0.001;
		float q = floor(l2 / 22.0 + bay) * 22.0;
		a = a * (q / l2);
	}
	COLOR = vec4(clamp(a / 255.0, 0.0, 1.0), 1.0);
}
