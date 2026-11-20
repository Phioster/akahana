// Browser test run (only with ?probe): sends the console, errors, WebGL facts and the wasm memory to /log,
// where tools/web/probe_server.py writes them per device. The game's own numbers come as "PROBE {...}" lines.
(function () {
  if (!location.search.includes('probe')) return;
  const dev = new URLSearchParams(location.search).get('dev') || 'unbekannt';
  const t0 = performance.now();
  const dpr = new URLSearchParams(location.search).get('dpr');   // test: draw at fewer pixels than the screen has
  if (dpr) Object.defineProperty(window, 'devicePixelRatio', { get: () => Number(dpr) });
  const local = ['localhost', '127.0.0.1'].includes(location.hostname);   // the test server collects; Pages does not
  let box = null;                       // elsewhere the findings stay on screen for a screenshot
  function show(line) {
    if (local) return;
    if (!box) {
      if (!document.body) { addEventListener('DOMContentLoaded', () => show(line)); return; }
      box = document.createElement('pre');
      box.style.cssText = 'position:fixed;left:0;right:0;bottom:0;max-height:45vh;overflow:auto;margin:0;padding:6px 8px;' +
        'font:11px/1.35 ui-monospace,monospace;color:#f3ead8;background:rgba(20,16,12,.82);z-index:9;white-space:pre-wrap';
      document.body.appendChild(box);
    }
    box.textContent += line + '\n';
    box.scrollTop = box.scrollHeight;
  }
  function note(o) {
    const s = (o.t / 1000).toFixed(1) + 's ';
    if (o.type === 'log' && o.msg.startsWith('PROBE ')) {
      let p; try { p = JSON.parse(o.msg.slice(6)); } catch (e) { return; }
      if (p.kind === 'boot') show(s + 'Spiel laeuft (' + p.window + ')');
      else if (p.kind === 'stage') show(s + p.stage + ': ' + p.fps + ' B/s, laengstes ' + p.max_ms + ' ms, Ruckler ' + p.hitches + ', Grafik ' + p.video_mb + ' MB');
      else if (p.kind === 'done') show(s + 'FERTIG - Rundgang durch');
    } else if (o.type === 'error' && /ERROR|TypeError/.test(o.msg)) show(s + 'Fehler: ' + o.msg.slice(0, 120));
    else if (['pageerror', 'rejection', 'contextlost', 'webgl', 'ua'].includes(o.type))
      show(s + o.type + ': ' + (o.msg || o.renderer || (o.ok === false ? 'WebGL2 fehlt' : '')).slice(0, 160));
  }
  function send(o) {
    o.dev = dev;
    o.t = Math.round(performance.now() - t0);
    note(o);
    if (!local) return;
    try { fetch('/log', { method: 'POST', body: JSON.stringify(o), keepalive: true }); } catch (e) { /* page leaving */ }
  }
  for (const k of ['log', 'warn', 'error']) {
    const f = console[k].bind(console);
    console[k] = function (...a) { send({ type: k, msg: a.map(String).join(' ').slice(0, 2000) }); f(...a); };
  }
  addEventListener('error', e => send({ type: 'pageerror', msg: String(e.message) + ' @' + e.filename + ':' + e.lineno }));
  // Safari takes the GPU away from a page that uses too much: every shader after that fails
  document.addEventListener('webglcontextlost', e => send({ type: 'contextlost', msg: String(e.statusMessage || '') }), true);
  document.addEventListener('webglcontextrestored', () => send({ type: 'contextrestored' }), true);
  addEventListener('pagehide', () => send({ type: 'pagehide' }));
  addEventListener('unhandledrejection', e => send({ type: 'rejection', msg: String(e.reason) }));

  let mem = null;                       // the engine's memory: Safari kills a tab that grows too big
  function look(x) {
    if (!x || typeof x !== 'object') return;
    for (const k in x) {
      const v = x[k];
      if (v instanceof WebAssembly.Memory) mem = v;
      else if (v && typeof v === 'object' && !(v instanceof WebAssembly.Module)) {
        for (const j in v) if (v[j] instanceof WebAssembly.Memory) mem = v[j];
      }
    }
  }
  for (const name of ['instantiate', 'instantiateStreaming']) {
    const orig = WebAssembly[name];
    if (!orig) continue;
    WebAssembly[name] = async function (...a) {
      look(a[1]);
      const r = await orig.apply(this, a);
      try { look((r.instance || r).exports); } catch (e) { /* not an instance */ }
      return r;
    };
  }

  try {
    const g = document.createElement('canvas').getContext('webgl2');
    if (!g) send({ type: 'webgl', ok: false });
    else {
      const d = g.getExtension('WEBGL_debug_renderer_info');
      send({ type: 'webgl', ok: true, renderer: d ? g.getParameter(d.UNMASKED_RENDERER_WEBGL) : g.getParameter(g.RENDERER),
        maxTex: g.getParameter(g.MAX_TEXTURE_SIZE), ext: g.getSupportedExtensions().filter(x => /compressed/.test(x)) });
    }
  } catch (e) { send({ type: 'webgl', ok: false, msg: String(e) }); }
  send({ type: 'ua', msg: navigator.userAgent, dpr: devicePixelRatio, w: innerWidth, h: innerHeight,
    cores: navigator.hardwareConcurrency || null });
  addEventListener('load', () => {
    const n = performance.getEntriesByType('resource').map(r => [r.name.split('/').pop(), Math.round(r.duration)]);
    send({ type: 'load', resources: n });
  });
  setInterval(() => send({ type: 'mem', wasm_mb: mem ? Math.round(mem.buffer.byteLength / 1048576) : null,
    js_mb: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : null }), 5000);
})();
