"""Sums up the browser test logs (<logs>/*.jsonl) as Markdown: per device the browser, WebGL, load time,
frame times per stage, the highest memory and the errors. Usage: python3 report.py <logs dir> [sizes file]"""
import glob
import json
import os
import sys


def probe(m):
    msg = m.get('msg', '')
    if m.get('type') == 'log' and msg.startswith('PROBE '):
        try:
            return json.loads(msg[6:])
        except ValueError:
            return None
    return None


def device(path):
    rows = []
    with open(path, encoding='utf-8') as f:
        for line in f:
            try:
                rows.append(json.loads(line))
            except ValueError:
                pass
    out = ['## ' + os.path.basename(path)[:-6], '']
    ua = next((r for r in rows if r.get('type') == 'ua'), {})
    gl = next((r for r in rows if r.get('type') == 'webgl'), {})
    out.append(f"- Browser: {ua.get('msg', '?')} (Bild {ua.get('w')}x{ua.get('h')} @ {ua.get('dpr')})")
    out.append(f"- WebGL2: {'ja' if gl.get('ok') else 'NEIN'} {gl.get('renderer', '')} max. Textur {gl.get('maxTex')}")
    probes = [p for p in (probe(r) for r in rows) if p]
    boot = next((r for r in rows if (probe(r) or {}).get('kind') == 'boot'), None)
    if boot:
        out.append(f"- Start bis Spiel läuft: {boot['t'] / 1000:.1f} s")
    done = any(p.get('kind') == 'done' for p in probes)
    out.append(f"- Rundgang: {'durch' if done else 'NICHT zu Ende'}")
    lost = [r for r in rows if r.get('type') == 'contextlost']
    if lost:
        out.append(f"- **Grafik weggenommen (WebGL context lost)** nach {lost[0].get('t', 0) / 1000:.1f} s")
    if any(r.get('type') == 'crash' for r in rows):
        out.append('- **Seite abgestürzt**')
    wasm = [r['wasm_mb'] for r in rows if r.get('type') == 'mem' and r.get('wasm_mb')]
    js = [r['js_mb'] for r in rows if r.get('type') == 'mem' and r.get('js_mb')]
    if wasm:
        out.append(f"- Spielspeicher (wasm): höchstens {max(wasm)} MB")
    if js:
        out.append(f"- JS-Speicher: höchstens {max(js)} MB")
    stages = [p for p in probes if p.get('kind') == 'stage']
    if stages:
        out += ['', '| Abschnitt | Bilder/s | 95 % unter ms | längstes ms | Ruckler | Texturen MB | Grafik MB | RAM MB |',
                '|---|---|---|---|---|---|---|---|']
        for s in stages:
            out.append(f"| {s['stage']} | {s.get('fps', '-')} | {s.get('p95_ms', '-')} | {s.get('max_ms', '-')} | "
                       f"{s.get('hitches', '-')} | {s.get('texture_mb')} | {s.get('video_mb')} | {s.get('static_mb')} |")
    errs = [r for r in rows if r.get('type') in ('error', 'pageerror', 'rejection', 'runner')]
    warns = [r for r in rows if r.get('type') == 'warn']
    out += ['', f"Fehler: {len(errs)}, Warnungen: {len(warns)}"]
    seen = set()
    for r in errs + warns:
        k = r.get('msg', '')[:160]
        if k not in seen and len(seen) < 15:
            seen.add(k)
            out.append(f"- `{r['type']}` {k}")
    return '\n'.join(out) + '\n'


def main():
    logs = sys.argv[1]
    parts = ['# Akahana im Browser: Testlauf', '']
    if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
        parts += ['```', open(sys.argv[2]).read().strip(), '```', '']
    for p in sorted(glob.glob(os.path.join(logs, '*.jsonl'))):
        parts.append(device(p))
    print('\n'.join(parts))


if __name__ == '__main__':
    main()
