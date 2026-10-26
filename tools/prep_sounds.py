#!/usr/bin/env python3
"""Prepares the chosen recordings for the game (all CC0, see docs/CREDITS.md).

Sources live outside the repo (large): ~/mohnweg-sounds/nox (Nox Sound "Essentials", unzipped) and
~/mohnweg-sounds/freesound (<id>.ogg previews, fetched with the Freesound API). This script cuts them:
  loops     a slice of each recording whose end is cross-faded into its start, so it repeats without a seam
  steps     single footfalls, silence trimmed, levelled so no surface jumps out
  one-shots birds, wings, bell, frog, book
Out: assets/audio/*.ogg (mono, 44.1 kHz)
"""
import glob
import os
import subprocess
import sys

import numpy as np

SR = 44100
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'assets', 'audio')
SRC = os.path.expanduser(os.environ.get('MOHNWEG_SOUNDS', '~/mohnweg-sounds'))
NOX = os.path.join(SRC, 'nox', 'Essentials_Series_NOX_SOUND')
FS = os.path.join(SRC, 'freesound')


def load(path, ss=0.0, t=None):
    cmd = ['ffmpeg', '-loglevel', 'error', '-ss', str(ss), '-i', path] + (['-t', str(t)] if t else [])
    cmd += ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(float)


def save(name, x, rms=0.1):
    x = x * (rms / (np.sqrt(np.mean(x ** 2)) + 1e-9))
    peak = np.abs(x).max()
    if peak > 0.95:
        x *= 0.95 / peak
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-c:a', 'libvorbis', '-q:a', '3', os.path.join(OUT, name + '.ogg')],
                   input=x.astype(np.float32).tobytes(), check=True)


def loop(src, name, ss, length, rms, fade=2.0):
    x = load(src, ss, length + fade)
    n, f = int(length * SR), int(fade * SR)
    if len(x) < n + f:                                   # short recording: use what is there
        n = len(x) - f
    out = x[:n].copy()
    ramp = np.linspace(0, 1, f)
    out[:f] = x[:f] * ramp + x[n:n + f] * (1 - ramp)     # the end flows into the start
    save(name, out, rms)


def step(src, name, rms):
    x = load(src)
    i = int(np.argmax(np.abs(x) > 0.05 * np.abs(x).max()))
    x = x[max(0, i - 40):][:int(0.45 * SR)]
    x[-int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    save(name, x, rms)


def nox_walk(sub, pattern, name, n=12, rms=0.12):
    files = sorted(glob.glob(os.path.join(NOX, sub, pattern)))[:n]
    if not files:
        sys.exit('fehlt: ' + sub + '/' + pattern)
    for i, f in enumerate(files):
        step(f, f'{name}_{i:02d}', rms)


def first(pattern):
    hits = sorted(glob.glob(os.path.join(NOX, pattern)))
    if not hits:
        sys.exit('fehlt: ' + pattern)
    return hits[0]


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, '*.ogg')):
        if os.path.basename(f) != 'musik.ogg':
            os.remove(f)
    fw = 'Footsteps_Essentials_NOX_SOUND'
    isl = 'Iceland_Packs_NOX_SOUND/Iceland_Footsteps_Pack_NOX_SOUND/Footsteps_Iceland_Walk'
    nox_walk(f'{fw}/Footsteps_Grass/Footsteps_Grass_Walk', '*.wav', 'schritt_gras')
    nox_walk(f'{fw}/Footsteps_DirtyGround/Footsteps_DirtyGround_Walk', '*.wav', 'schritt_erde')
    nox_walk(f'{fw}/Footsteps_Rock/Footsteps_Rock_Walk', '*.wav', 'schritt_stein')
    nox_walk(f'{fw}/Footsteps_Wood/Footsteps_Wood_Walk', '*.wav', 'schritt_holz')
    nox_walk(isl, '*Snow_Short_Grass*.wav', 'schritt_schnee_wenig')
    nox_walk(isl, '*Walk_Snow_Grass*.wav', 'schritt_schnee')
    nox_walk(isl, '*Snow_Hard*.wav', 'schritt_schnee_hart')
    nox_walk(isl, '*Black_Pebble*.wav', 'schritt_nass')
    loop(first('Nature_Essentials_NOX_SOUND/Ambiance_Night_Loop_Stereo.wav'), 'nacht', 0, 27, 0.08)
    loop(first('Nature_Essentials_NOX_SOUND/Ambiance_Wind_Calm_Loop_Stereo.wav'), 'wind_ruhig', 0, 27, 0.08)
    loop(f'{FS}/434858.ogg', 'abendwiese', 5, 40, 0.08)
    loop(f'{FS}/165526.ogg', 'bergwind_a', 10, 40, 0.1)
    loop(f'{FS}/156045.ogg', 'bergwind_b', 10, 40, 0.1)
    loop(f'{FS}/692538.ogg', 'bach_klein', 2, 30, 0.1)
    loop(f'{FS}/615249.ogg', 'bach_mittel', 5, 30, 0.1)
    loop(f'{FS}/826443.ogg', 'bach_gross', 5, 30, 0.1)
    loop(f'{FS}/320231.ogg', 'feuer', 2, 24, 0.1)
    loop(f'{FS}/680476.ogg', 'kerze', 5, 20, 0.1)
    loop(f'{FS}/181563.ogg', 'knistern', 2, 24, 0.1)
    loop(f'{FS}/521883.ogg', 'schimmer', 0, 10, 0.1, fade=1.5)
    for i, sid in enumerate([484366, 484367, 507265]):
        save(f'vogel_{i}', load(f'{FS}/{sid}.ogg'), 0.12)
    for i, sid in enumerate([414671, 389633]):
        save(f'fluegel_{i}', load(f'{FS}/{sid}.ogg'), 0.12)
    save('glocke', load(f'{FS}/266525.ogg'), 0.1)
    save('frosch', load(f'{FS}/536759.ogg'), 0.12)
    for i, sid in enumerate([484933, 484941, 484949]):
        save(f'seite_{i}', load(f'{FS}/{sid}.ogg'), 0.1)
    for i, sid in enumerate([484886, 484884]):
        save(f'buch_zu_{i}', load(f'{FS}/{sid}.ogg'), 0.1)
    print('ok', len(glob.glob(os.path.join(OUT, '*.ogg'))), 'Dateien')
