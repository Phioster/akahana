// Sound in Safari on iPhone/iPad (Philip 2026-11-20: no sound on the iPad). Two things keep Web Audio quiet there:
// the silent mode (Web Audio counts as ringer sound unless the page says it plays media) and a context that
// stays suspended until a tap wakes it. Loaded before the engine, in every browser build.
(function () {
  try { if (navigator.audioSession) navigator.audioSession.type = 'playback'; } catch (e) { /* older Safari */ }
  const made = [];
  for (const name of ['AudioContext', 'webkitAudioContext']) {
    const Orig = window[name];
    if (!Orig) continue;
    const Wrapped = function (...a) { const c = new Orig(...a); made.push(c); return c; };
    Wrapped.prototype = Orig.prototype;
    Object.setPrototypeOf(Wrapped, Orig);
    window[name] = Wrapped;
  }
  function wake() {
    for (const c of made) {
      if (c.state !== 'running') c.resume().catch(() => {});
      try {                                   // a silent sound inside the tap: what unlocks iOS for good
        const s = c.createBufferSource();
        s.buffer = c.createBuffer(1, 1, 22050);
        s.connect(c.destination);
        s.start(0);
      } catch (e) { /* closed context */ }
    }
  }
  for (const ev of ['touchend', 'pointerup', 'click', 'keydown'])
    addEventListener(ev, wake, { capture: true, passive: true });
  document.addEventListener('visibilitychange', () => { if (!document.hidden) wake(); });
  window.akahanaAudio = () => made.map(c => c.state);   // for the probe: what the contexts are doing
})();
