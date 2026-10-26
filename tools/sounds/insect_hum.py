#!/usr/bin/env python3
"""A soft hum of a few small insects round a firefly swarm, made from scratch (every recording found had
birds in it). Modelled on a real hoverfly recording (Freesound #34111): several insects between 150 and
300 Hz, mostly fundamental and octave, the loudest one changing every few tenths of a second, quick
darts close by (up to four times as loud), pitch rising as one comes and dropping as it leaves.

    python3 tools/sounds/insect_hum.py out.wav [seconds] [seed]
"""
import sys
import wave

import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import butter, sosfilt

SR = 44100


CTRL = 200                          # slow movements are worked out at 200 values a second, then stretched


def wander(n, rng, sigma_s, amount):
    """Slow random drift (a random walk, smoothed), about +-amount."""
    m = n * CTRL // SR + 2
    w = gaussian_filter1d(np.cumsum(rng.normal(0, 1, m)), max(sigma_s * CTRL, 0.5))
    w -= w.mean()
    w = w / (np.abs(w).max() + 1e-9) * amount
    return np.interp(np.arange(n) / SR, np.arange(m) / CTRL, w)


def darts(t, rng, rate):
    """How near the insect is: mostly off a little way, now and then a quick dart in and a slower drift
    away; sometimes gone for a while."""
    near = np.full(len(t), 0.12) + wander(len(t), rng, 0.8, 0.08)
    c = rng.uniform(-1, 1)
    while c < t[-1]:
        c += rng.exponential(1 / rate)
        up, down, a = rng.uniform(0.04, 0.16), rng.uniform(0.12, 0.45), rng.uniform(0.4, 2.8)   # quick, as measured
        d = t - c
        near += a * np.where(d < 0, np.exp(-(d / up) ** 2), np.exp(-(d / down) ** 2))
    gone = gaussian_filter1d((rng.random(len(t) // 4410 + 2) < 0.18).astype(float), 1.2)
    near *= 1 - 0.9 * np.clip(np.interp(t, np.arange(len(gone)) * 0.1, gone) * 2, 0, 1)
    return np.clip(near, 0, None)


def insect(t, f0, rng):
    n = len(t)
    near = darts(t, rng, rng.uniform(0.8, 1.8))
    nc = near[::SR // CTRL]
    dc = np.gradient(gaussian_filter1d(nc, 0.03 * CTRL)) * CTRL * 0.025          # coming: higher, going: lower
    doppler = np.interp(t, np.arange(len(nc)) / CTRL, dc)
    pitch = f0 * (1 + wander(n, rng, 0.12, 0.03) + np.clip(doppler, -0.08, 0.08))
    jitter = gaussian_filter1d(rng.normal(0, 1, n), 0.004 * SR) * 0.6            # every wingbeat a little off
    ph = 2 * np.pi * np.cumsum(pitch * (1 + 0.04 * jitter)) / SR
    tone = np.zeros(n)
    for k, a in enumerate([1.0, 0.6, 0.22, 0.1, 0.05], 1):                         # fundamental and octave lead
        colour = 1 + wander(n, rng, 0.25, 0.35)                                      # the timbre turns as it flies
        tone += a * colour * np.sin(k * ph + rng.uniform(0, 6))
    air = gaussian_filter1d(rng.normal(0, 1, n), 2) * (0.5 + 0.5 * np.abs(np.sin(ph / 2)))   # the rasp of wings
    return (tone + 0.35 * air) * near


def hum(seconds=10.0, seed=3):
    rng = np.random.default_rng(seed)
    t = np.arange(int(seconds * SR)) / SR
    left = np.zeros_like(t)
    right = np.zeros_like(t)
    for f0 in rng.choice([152, 168, 178, 190, 208, 262, 278, 290], size=int(rng.integers(4, 7)), replace=False):
        s = insect(t, f0 * rng.uniform(0.96, 1.04), rng)
        pan = np.clip(0.5 + wander(len(t), rng, 1.0, 0.35), 0.05, 0.95)              # drifting left and right
        left += s * (1 - pan)
        right += s * pan
    sos = butter(3, [120, 2600], 'bandpass', fs=SR, output='sos')
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
