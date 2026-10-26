#!/usr/bin/env python3
"""A soft hum of a few small insects round a firefly swarm, made from scratch (every recording found had
birds in it): each insect a buzzing tone with wavering wingbeat, drifting near and away again.

    python3 tools/sounds/insect_hum.py out.wav [seconds] [seed]
"""
import sys
import wave

import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100


def insect(t, f0, rng):
    wob = 1 + 0.035 * np.sin(2 * np.pi * rng.uniform(0.2, 0.5) * t + rng.uniform(0, 6)) \
        + 0.012 * np.convolve(rng.normal(0, 1, len(t)), np.ones(800) / 800, 'same') * 20
    ph = 2 * np.pi * np.cumsum(f0 * wob) / SR
    tone = sum(np.sin(k * ph + rng.uniform(0, 6)) / k ** 1.3 for k in range(1, 9))   # wingbeat: buzzy, not a sine
    tone *= 1 + 0.25 * np.sin(ph * 0.5)                                           # the beat is a little uneven
    near = np.full(len(t), 0.18)                                                  # far off most of the time ...
    for c in rng.uniform(0, t[-1], 3):                                            # ... coming close now and then
        near += 0.9 * np.exp(-((t - c) / rng.uniform(0.6, 1.4)) ** 2)
    return tone * near


def hum(seconds=10.0, seed=3):
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * SR)) / SR
    left = np.zeros_like(t)
    right = np.zeros_like(t)
    for f0 in (196, 228, 251, 274):
        s = insect(t, f0 * rng.uniform(0.97, 1.03), rng)
        pan = rng.uniform(0.25, 0.75)
        left += s * (1 - pan)
        right += s * pan
    sos = butter(4, [140, 3200], 'bandpass', fs=SR, output='sos')                # soft: no whine on top
    out = np.stack([sosfilt(sos, left), sosfilt(sos, right)], 1)
    return out / np.abs(out).max() * 0.6


if __name__ == '__main__':
    sec = float(sys.argv[2]) if len(sys.argv) > 2 else 10.0
    a = (hum(sec, int(sys.argv[3]) if len(sys.argv) > 3 else 3) * 32767).astype(np.int16)
    with wave.open(sys.argv[1], 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(a.tobytes())
