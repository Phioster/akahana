// Poppy heads sway in the same gusts as in the wallpaper: whole-pixel shifts, never smeared.
shader_type canvas_item;

uniform vec2 tex_size;

void fragment() {
	vec2 p = floor(UV * tex_size);
	float ph = 6.2831853 * TIME / 8.0;
	float g = max(sin(6.2831853 * (p.x * 0.6 + p.y) / 170.0 - 2.0 * ph), 0.0);
	float w = 1.4 * g * g + 0.4 * sin(3.0 * ph + p.x * 0.11 + p.y * 0.07);
	float dx = floor(w + 0.5);
	COLOR = texture(TEXTURE, (p - vec2(dx, 0.0) + 0.5) / tex_size);
}
