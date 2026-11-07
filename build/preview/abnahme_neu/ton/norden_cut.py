"""Listening samples for step 55 (north sounds): same loudness, soft in and out, as mp3 for the page."""
import os
import subprocess
import sys

import numpy as np

SR = 44100
OUT = os.path.dirname(os.path.abspath(__file__))
FS = os.path.expanduser('~/mohnweg-sounds/freesound')
NOX = os.path.expanduser('~/mohnweg-sounds/nox/Essentials_Series_NOX_SOUND')
SM = [d for d in os.listdir(NOX) if d.endswith('Miguel_Flows_NOX_SOUND')][0]

# name: (source, start s, length s, target rms)
PICKS = {
    'fall_a': (f'{NOX}/Nature_Essentials_NOX_SOUND/Ambiance_Waterfall_Calm_Loop_Stereo.wav', 0, 25, 0.1),
    'fall_b': (f'{FS}/norden/727804.ogg', 10, 25, 0.1),
    'fall_c': (f'{NOX}/{SM}/Ambiance_Waterfall_Moihnos_Cascata_do_Limbo_Loop_Stereo.wav', 0, 20, 0.1),
    'wald_a': (f'{FS}/670307.ogg', 270, 30, 0.08),
    'wald_b': (f'{FS}/norden/792516.ogg', 20, 30, 0.08),
    'wald_c': (f'{NOX}/Nature_Essentials_NOX_SOUND/Ambiance_Wind_Forest_Loop_Stereo.wav', 0, 28, 0.08),
}


def load(path, ss=0.0, t=None):
    cmd = ['ffmpeg', '-loglevel', 'error', '-ss', str(ss), '-i', path] + (['-t', str(t)] if t else [])
    cmd += ['-ac', '1', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).astype(float)


def save(name, x, rms):
    x = x * (rms / (np.sqrt(np.mean(x ** 2)) + 1e-9))
    f = int(0.6 * SR)
    x[:f] *= np.linspace(0, 1, f)
    x[-f:] *= np.linspace(1, 0, f)
    x = np.clip(x, -0.95, 0.95)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-c:a', 'libmp3lame', '-q:a', '4', os.path.join(OUT, name + '.mp3')],
                   input=x.astype(np.float32).tobytes(), check=True)


def creaks(src, name, spans, rms=0.1, gap=2.5):
    """A few single creaks from a longer take, with quiet between them, as they would come in the game."""
    parts = []
    for ss, t in spans:
        c = load(src, ss, t)
        c = c * (rms / (np.sqrt(np.mean(c ** 2)) + 1e-9))
        parts += [c, np.zeros(int(gap * SR))]
    x = np.concatenate(parts)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-c:a', 'libmp3lame', '-q:a', '4', os.path.join(OUT, name + '.mp3')],
                   input=np.clip(x, -0.95, 0.95).astype(np.float32).tobytes(), check=True)


if __name__ == '__main__':
    only = sys.argv[1:]
    for n, (src, ss, t, rms) in PICKS.items():
        if (not only or n in only) and os.path.exists(src):
            save(n, load(src, ss, t), rms)
            print('ok', n)
    N = f'{FS}/norden'
    if not only or 'knarz' in only:
        creaks(f'{N}/414092.ogg', 'knarz_a', [(43.2, 3), (68.7, 3), (90.2, 3), (154.7, 3)])
        creaks(f'{N}/345311.ogg', 'knarz_b', [(6.4, 2.2), (11.6, 2.2), (15.8, 2.4), (20.6, 2.4)])
        creaks(f'{N}/527838.ogg', 'knarz_c', [(10.0, 3), (39.0, 3)])
        print('ok knarz')
