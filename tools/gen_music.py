#!/usr/bin/env python3
"""The poppy-field theme: calm, Japanese, with the lilt of "Golden Brown" (bars of 3+3+3+4 beats).

Real recordings, both CC0: a gayageum (Freesound, spt3125, ids 24551-24573) plays sparse plucks, some
pressed up after the pluck like a koto; a Kawai upright piano (FreePats "Upright Piano KW") carries
the melody. D miyako-bushi: D Eb G A Bb. Form: koto alone, theme, a still middle part with a steady
pulse, the theme an octave up, koto fading out (~88 s after the last pass: 15 % slower, a light
echo; the game puts long silences between plays).
Sources are read from ~/mohnweg-sounds (gayageum/*.ogg, piano/src/UprightPianoKW*/samples).
Writes assets/audio/musik.ogg.
"""
import os, glob, subprocess, numpy as np
from scipy import signal
SR = 44100
rng = np.random.default_rng(3)
HOME = os.path.expanduser('~/mohnweg-sounds')
NOTE = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}

def decode(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(float)

GAY = {}
for f in glob.glob(f'{HOME}/gayageum/kayageum1_*.ogg'):
    n = os.path.basename(f)[10:-4]; m = 12 * (int(n[1]) + 1) + NOTE[n[0]]
    x = decode(f); x = x[np.argmax(np.abs(x) > 0.02 * np.abs(x).max()):]; GAY[m] = x / np.abs(x).max()
PIANO = {}
PDIR = glob.glob(f'{HOME}/piano/src/UprightPianoKW*/samples')[0]
for f in glob.glob(f'{PDIR}/*vL.flac'):
    n = os.path.basename(f)[:-7]
    m = 12 * (int(n[-1]) + 1) + NOTE[n[0]] + (1 if '#' in n else 0)
    if 55 <= m <= 90:
        x = decode(f); PIANO[m] = x / 0.5
def repitch(x, ratio):
    """ratio may be an array over the output (bends); integrates the read position."""
    n_out = int(len(x) / (np.max(ratio) if np.ndim(ratio) else ratio)) if np.ndim(ratio) == 0 else len(ratio)
    r = np.full(n_out, ratio) if np.ndim(ratio) == 0 else ratio
    pos = np.cumsum(r); pos = pos[pos < len(x) - 1]
    return np.interp(pos, np.arange(len(x)), x)

def gay(m, dur=6.0, amp=0.5, bend=0.0, bend_at=0.5):
    root = min(GAY, key=lambda k: abs(k - m)); x = GAY[root]
    n = int(dur * SR); t = np.arange(n) / SR
    semis = (m - root) + bend * np.clip((t - bend_at) / 0.25, 0, 1) ** 0.7   # pressed up behind the bridge
    y = repitch(x, 2 ** (semis / 12))[:n]
    y = np.pad(y, (0, n - len(y)))
    return y * np.clip((dur - t) / 0.8, 0, 1) * amp

def piano(m, dur, amp=0.5, pedal=1.2):
    """Soft key, let ring for the note plus a little pedal, then the damper."""
    root = min(PIANO, key=lambda k: abs(k - m)); x = PIANO[root]
    y = repitch(x, 2 ** ((m - root) / 12))
    n = int((dur + pedal) * SR); y = np.pad(y[:n], (0, max(0, n - len(y))))
    t = np.arange(n) / SR
    return y * np.clip((dur + pedal - t) / pedal, 0, 1) * amp


BEAT = 0.62
CYCLE = [3, 3, 3, 4]
BARS = 32
bar_beats = [CYCLE[i % 4] for i in range(BARS)]
starts = np.concatenate([[0], np.cumsum(bar_beats)]) * BEAT
LEN = starts[-1] + 7
L = np.zeros(int(LEN * SR)); R = np.zeros(int(LEN * SR))
def add(x, t, pan=0.5, g=1.0):
    i = max(0, int(t * SR))
    for buf, gg, dt in ((L, 1.1 - pan * 0.6, 0), (R, 0.5 + pan * 0.6, int(0.006 * SR))):
        j = i + dt; k = min(len(x), len(buf) - j)
        if k > 0: buf[j:j + k] += x[:k] * gg * g

D2, D3, A2, G2, Bb2, Eb3 = 38, 50, 45, 43, 46, 51
# koto figure per bar of the cycle: (beat, midi, amp, bend) - few notes, the rest is silence
FIG = [
    [(0, D3, 0.55, 0), (1.5, 62, 0.3, 0), (2, 67, 0.28, 0)],
    [(0, A2, 0.45, 0), (1, 69, 0.3, 0), (2, 70, 0.25, 1)],            # Bb pressed up to B, then
    [(0, G2, 0.45, 0), (1.5, 62, 0.28, 0), (2, 63, 0.3, 0)],
    [(0, D3, 0.5, 0), (2, 69, 0.3, 0), (3, 67, 0.22, 2)],             # G pressed up a whole tone to A
]
THEME = [(0, 0, 2.5, 74), (1, 0, 1, 75), (1, 1, 2, 74), (2, 0, 3, 70), (3, 0, 4, 69),
         (5, 0, 1, 67), (5, 1, 2, 69), (6, 0, 3, 70), (7, 0, 2, 69), (7, 2, 2, 62)]
bar = 0
def koto_bar(fig, b, scale=1.0):
    for (be, m, a, bd) in fig:
        add(gay(m, 7.0, a * scale, bend=bd, bend_at=0.35 + rng.random() * 0.1), starts[b] + be * BEAT + rng.normal(0, 0.012), 0.35 + (m - 38) / 80)
for b in range(4): koto_bar(FIG[b], bar, 0.8); bar += 1                     # alone first
a0 = bar
for b in range(8): koto_bar(FIG[b % 4], bar); bar += 1
for (bo, be, d, m) in THEME: add(piano(m, d * BEAT, 0.42), starts[a0 + bo] + be * BEAT + rng.normal(0, 0.01), 0.6)
m0 = bar
# the middle part keeps a steady pulse: the left hand walks every beat, the koto marks each one,
# the melody lands on the ones (and a quiet pickup on the last beat) - no loose timing here
FIFTHS = [(50, 57), (46, 53), (43, 50), (45, 52)]
MID_MEL = [(0, 3, 69), (0, 2, 70), (2, 1, 69), (0, 3, 67), (0, 4, 69),
           (0, 3, 74), (0, 2, 75), (2, 1, 74), (0, 3, 70), (0, 4, 69)]
MID_BARS = [[0], [1, 2], [3], [4], [5], [6, 7], [8], [9]]
for b in range(8):
    lo, hi = FIFTHS[b % 4]; t0 = starts[bar]; nb = bar_beats[bar]
    walk = [lo + 12, hi + 12, lo + 24, hi + 12][:nb]
    for k, m in enumerate(walk):
        add(piano(m, BEAT * 0.95, 0.2 if k == 0 else 0.13, 0.9), t0 + k * BEAT, 0.4)
    add(gay(lo, 6.0, 0.35), t0, 0.35)
    for i in MID_BARS[b]:
        be, d, m = MID_MEL[i]
        add(piano(m, d * BEAT, 0.38 if be == 0 else 0.26, 1.0), t0 + be * BEAT, 0.6)
    bar += 1
r0 = bar                                          # the theme once more, an octave up, lighter
for b in range(8): koto_bar(FIG[b % 4], bar, 0.85); bar += 1
for (bo, be, d, m) in THEME: add(piano(m + 12, d * BEAT, 0.32), starts[r0 + bo] + be * BEAT + rng.normal(0, 0.01), 0.62)
for b in range(4): koto_bar(FIG[b], bar, 0.8 - 0.12 * b); bar += 1
add(gay(D3, 7.0, 0.4), starts[bar], 0.4)

ir_n = int(3.6 * SR)
ir = rng.normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 2.0)
ir = signal.lfilter(*signal.butter(2, 3500 / (SR / 2)), ir); ir /= np.abs(ir).sum() ** 0.5 * 26
L = L * 0.75 + signal.fftconvolve(L, ir)[:len(L)] * 0.65
R = R * 0.75 + signal.fftconvolve(R, ir)[:len(R)] * 0.65
n = len(L); fade = np.clip((n - np.arange(n)) / (4 * SR), 0, 1); L *= fade; R *= fade
rms = np.sqrt(((L ** 2 + R ** 2) / 2).mean()); g = 10 ** (-19 / 20) / rms   # even loudness, not one loud note
L, R = np.tanh(L * g / 0.8) * 0.8, np.tanh(R * g / 0.8) * 0.8                  # soft ceiling for the rare peak
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
out = os.path.join(ROOT, 'assets', 'audio', 'musik')
np.stack([L, R], 1).astype(np.float32).tofile(out + '.f32')
# last pass, the way every piece is finished: 15 % slower (and so lower), a light echo, a soft top
SLOW = 0.85
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', out + '.f32',
                '-af', f'apad=pad_dur=3,asetrate={SR}*{SLOW},aresample={SR},aecho=0.9:0.9:90|210:0.16|0.08,'
                       'lowpass=f=7000,volume=2dB,alimiter=limit=0.8,areverse,afade=t=in:d=4,areverse',
                '-c:a', 'libvorbis', '-q:a', '5', out + '.ogg'], check=True)
os.remove(out + '.f32')
print('ok', round((LEN + 3) / SLOW, 1), 's; Mittelteil ab', round(starts[m0] / SLOW, 1), '; Wiederkehr ab', round(starts[r0] / SLOW, 1))
