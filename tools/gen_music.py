#!/usr/bin/env python3
"""A calm lofi loop with a medieval touch, made from scratch (no samples, no foreign rights).

D dorian at 72 BPM, 32 bars (~107 s) that loop seamlessly:
  plucked lute arpeggios (Karplus-Strong), a recorder melody with breath and vibrato,
  a hurdy-gurdy drone, soft swung lofi drums, vinyl crackle, a little tape wobble and reverb.
Writes assets/audio/musik.ogg.
"""
import os
import subprocess

import numpy as np
from scipy import signal

SR = 44100
BPM = 72
BEAT = 60 / BPM
BAR = 4 * BEAT
BARS = 32
LEN = int(BARS * BAR * SR)
rng = np.random.default_rng(7)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def hz(m): return 440.0 * 2 ** ((m - 69) / 12)


def add(buf, x, t):
    i = int(t * SR) % LEN                                  # wrap around: the loop has no seam
    n = len(x)
    if i + n <= LEN:
        buf[i:i + n] += x
    else:
        k = LEN - i
        buf[i:] += x[:k]
        buf[:n - k] += x[k:]


def pluck(m, dur=2.2, bright=0.5, amp=0.3):
    """Karplus-Strong string: a burst of noise in a delay line that loses its highs every round."""
    f = hz(m)
    N = int(SR / f)
    n = int(dur * SR)
    burst = np.zeros(n)
    exc = rng.uniform(-1, 1, N)
    exc = signal.lfilter([1 - bright], [1, -bright], exc)   # softer pluck: fingers, not a pick
    burst[:N] = exc
    d = 0.996
    a = np.zeros(N + 2)
    a[0] = 1
    a[N] = -d * 0.5
    a[N + 1] = -d * 0.5
    y = signal.lfilter([1], a, burst)
    y *= np.minimum(1, np.linspace(0, dur, n)[::-1] / 0.08)  # tiny fade at the end
    body = signal.lfilter(*signal.butter(2, [180 / (SR / 2), 3200 / (SR / 2)], 'band'), y)   # wooden body
    return (0.7 * y + 0.5 * body) * amp


def recorder(m, dur, amp=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz(m)
    vib = 1 + 0.004 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.25) / 0.3, 0, 1)   # vibrato after the attack
    ph = 2 * np.pi * np.cumsum(f * vib) / SR
    tone = np.sin(ph) + 0.18 * np.sin(2 * ph) + 0.06 * np.sin(3 * ph)
    breath = signal.lfilter(*signal.butter(2, [f * 0.8 / (SR / 2), min(0.99, f * 3 / (SR / 2))], 'band'),
                            rng.normal(0, 1, n)) * 0.12
    env = np.clip(t / 0.06, 0, 1) * np.clip((dur - t) / 0.12, 0, 1)
    return (tone + breath) * env * amp


def kick():
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = 55 + 70 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9) * 0.35


def brush():
    n = int(0.25 * SR)
    t = np.arange(n) / SR
    x = signal.lfilter(*signal.butter(2, [1500 / (SR / 2), 7000 / (SR / 2)], 'band'), rng.normal(0, 1, n))
    return x * np.exp(-t * 14) * 0.09


def shaker():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    x = signal.lfilter(*signal.butter(2, 5000 / (SR / 2), 'high'), rng.normal(0, 1, n))
    return x * np.exp(-t * 45) * np.clip(t / 0.01, 0, 1) * 0.035


CHORDS = [(50, 'm'), (50, 'm'), (48, 'M'), (48, 'M'), (43, 'M'), (43, 'M'), (45, 'm'), (45, 'm')]   # Dm C G Am
def chord_tones(root, q):
    third = 3 if q == 'm' else 4
    return [root, root + 7, root + 12, root + 12 + third, root + 19, root + 24]

MEL_A = [  # (bar, beat, beats, midi)
    (0, 0, 1.5, 69), (0, 1.5, 0.5, 72), (0, 2, 2, 74),
    (1, 0, 1, 72), (1, 1, 1, 69), (1, 2, 1.5, 67),
    (2, 0, 2, 76), (2, 2, 1, 74), (2, 3, 1, 72),
    (3, 0, 3, 67),
    (4, 0, 1, 71), (4, 1, 1, 74), (4, 2, 2, 74),
    (5, 0, 1.5, 71), (5, 1.5, 0.5, 69), (5, 2, 2, 67),
    (6, 0, 1, 69), (6, 1, 1, 72), (6, 2, 1, 76), (6, 3, 1, 74),
    (7, 0, 3, 69)]
MEL_B = [  # the answer: same contour, ornamented, ending lower
    (0, 0, 1, 74), (0, 1, 0.5, 76), (0, 1.5, 0.5, 74), (0, 2, 2, 72),
    (1, 0, 1, 69), (1, 1, 1, 67), (1, 2, 2, 65),
    (2, 0, 1.5, 67), (2, 1.5, 0.5, 69), (2, 2, 2, 72),
    (3, 0, 1, 71), (3, 1, 2, 67),
    (4, 0, 2, 74), (4, 2, 1, 71), (4, 3, 1, 74),
    (5, 0, 3, 74),
    (6, 0, 1, 72), (6, 1, 1, 69), (6, 2, 1, 67), (6, 3, 1, 65),
    (7, 0, 3, 62)]

L = np.zeros(LEN)
R = np.zeros(LEN)
SWING = 0.07 * BEAT                                       # late offbeats: lazy, lofi
for bar in range(BARS):
    root, q = CHORDS[bar % 8]
    tones = chord_tones(root, q)
    cyc = bar // 8
    t0 = bar * BAR
    # lute: 8 eighths, root low, a different arpeggio shape every other bar
    pattern = [0, 1, 2, 3, 4, 3, 2, 1] if bar % 2 == 0 else [0, 2, 1, 3, 2, 4, 3, 2]
    for k, idx in enumerate(pattern):
        if cyc == 3 and k % 2 == 1 and rng.random() < 0.5:
            continue                                      # last round thins out before the loop restarts
        t = t0 + k * BEAT / 2 + (SWING if k % 2 else 0) + rng.normal(0, 0.006)
        p = pluck(tones[idx], 2.0, bright=0.45 + 0.1 * rng.random(), amp=0.22 if k else 0.3)
        pan = 0.35 + 0.3 * (idx / 4)
        add(L, p * (1 - pan * 0.6), t)
        add(R, p * (0.4 + pan * 0.6), t)
    # drums from the second round on, softer in the last
    if cyc >= 1:
        dv = 0.7 if cyc == 3 else 1.0
        for b in (0, 2.5):
            add(L, kick() * dv, t0 + b * BEAT); add(R, kick() * dv, t0 + b * BEAT)
        for b in (1, 3):
            add(L, brush() * dv * 0.9, t0 + b * BEAT); add(R, brush() * dv, t0 + b * BEAT + 0.004)
        for k in range(8):
            t = t0 + k * BEAT / 2 + (SWING if k % 2 else 0)
            add(L, shaker() * (0.6 if k % 2 else 1.0), t); add(R, shaker() * (1.0 if k % 2 else 0.6), t + 0.003)
# drone: D and A, slowly breathing, like a hurdy-gurdy far away
t = np.arange(LEN) / SR
drone = np.zeros(LEN)
for m, a in ((38, 0.05), (45, 0.035), (50, 0.02)):
    f = hz(m)
    ph = 2 * np.pi * f * t
    drone += a * (np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.2 * np.sin(3 * ph))
drone *= 0.75 + 0.25 * np.sin(2 * np.pi * t / (BAR * 4))  # 4-bar swell, whole cycles: loops cleanly
drone = signal.lfilter(*signal.butter(2, 900 / (SR / 2)), drone)
L += drone; R += drone
# melody: A in round 2, B in round 3, a fragment of A in round 4
for cyc, mel in ((1, MEL_A), (2, MEL_B), (3, MEL_A[:7])):
    for (b, beat, dur, m) in mel:
        tt = (cyc * 8 + b) * BAR + beat * BEAT + rng.normal(0, 0.01)
        x = recorder(m, dur * BEAT * 0.95)
        add(L, x * 0.8, tt); add(R, x, tt + 0.008)
# reverb: a soft room tail, folded around so the loop start already carries the end's echo
ir_n = int(2.2 * SR)
ir = rng.normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 3.2)
ir = signal.lfilter(*signal.butter(2, 4000 / (SR / 2)), ir)
ir /= np.abs(ir).sum() ** 0.5 * 30
def verb(x):
    """Circular convolution: the tail running past the end lands on the start, so the loop has no seam."""
    y = signal.fftconvolve(x, ir)
    out = y[:LEN].copy()
    out[:len(y) - LEN] += y[LEN:]
    return out
wetL, wetR = verb(L), verb(R)
L = L * 0.82 + wetL * 0.5
R = R * 0.82 + wetR * 0.5
# lofi: gentle top cut, a little tape wobble, vinyl crackle and hiss
lp = signal.butter(2, 5200 / (SR / 2))
L = signal.filtfilt(*lp, L); R = signal.filtfilt(*lp, R)
wob = 0.0016 * np.sin(2 * np.pi * t / (BAR * 2)) * SR    # +-1.6 ms, whole cycles over the loop
idx = np.arange(LEN) + wob
L = np.interp(idx % LEN, np.arange(LEN), L, period=LEN); R = np.interp(idx % LEN, np.arange(LEN), R, period=LEN)
crack = np.zeros(LEN)
pos = rng.integers(0, LEN, 900)
crack[pos] = rng.uniform(-1, 1, 900) * rng.uniform(0.2, 1, 900)
crack = signal.lfilter(*signal.butter(2, [800 / (SR / 2), 6000 / (SR / 2)], 'band'), crack) * 0.05
hiss = signal.lfilter(*signal.butter(1, 3000 / (SR / 2)), rng.normal(0, 1, LEN)) * 0.0025
L += crack + hiss; R += crack * 0.9 + hiss
peak = max(np.abs(L).max(), np.abs(R).max())
L, R = L / peak * 0.7, R / peak * 0.7
out_dir = os.path.join(ROOT, 'assets', 'audio')
os.makedirs(out_dir, exist_ok=True)
raw = np.stack([L, R], 1).astype(np.float32)
wav = os.path.join(out_dir, 'musik_tmp.f32')
raw.tofile(wav)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', wav,
                '-c:a', 'libvorbis', '-q:a', '4', os.path.join(out_dir, 'musik.ogg')], check=True)
os.remove(wav)
print('ok', round(LEN / SR, 1), 's, rms', round(float(np.sqrt((L ** 2).mean())), 3))
