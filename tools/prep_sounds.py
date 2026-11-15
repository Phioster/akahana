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


def save(name, x, rms=0.1, soft=False):
    x = x * (rms / (np.sqrt(np.mean(x ** 2)) + 1e-9))
    peak = np.abs(x).max()
    if soft:                                             # spiky crackle: round the peaks off instead of
        x = 0.95 * np.tanh(x / 0.95)                     # turning everything down for them
    elif peak > 0.95:
        x *= 0.95 / peak
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-',
                    '-c:a', 'libvorbis', '-q:a', '3', os.path.join(OUT, name + '.ogg')],
                   input=x.astype(np.float32).tobytes(), check=True)


def loop(src, name, ss, length, rms, fade=2.0, highpass=0.0, lowpass=0.0, soft=None):
    x = load(src, ss, length + fade)
    if highpass:                                         # drop rumble phones and earbuds cannot play, so the
        from scipy import signal                         # level is set by what is actually heard
        x = signal.sosfiltfilt(signal.butter(4, highpass, 'high', fs=SR, output='sos'), x)
    if lowpass:                                          # tame the hiss and sharp spikes on top
        from scipy import signal
        x = signal.sosfiltfilt(signal.butter(2, lowpass, 'low', fs=SR, output='sos'), x)
    n, f = int(length * SR), int(fade * SR)
    if len(x) < n + f:                                   # short recording: use what is there
        n = len(x) - f
    out = x[:n].copy()
    ramp = np.linspace(0, 1, f)
    out[:f] = x[:f] * ramp + x[n:n + f] * (1 - ramp)     # the end flows into the start
    save(name, out, rms, soft=bool(highpass) if soft is None else soft)


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


def south():
    """The south's sounds (approved on the review page): the tall grass's rustle, the fireflies' hum."""
    import shutil
    sud = os.path.join(FS, 'sueden')
    for f in sorted(glob.glob(os.path.join(sud, 'hochgras', 'rascheln_*.ogg'))):   # cut from #559082 (CC0)
        shutil.copy(f, os.path.join(OUT, os.path.basename(f)))
    # fireflies: BBC "Several hovering" (NHU05086119, BBC licence: personal use only - replace before any
    # release) with the moth's flutter (#693457, CC0) far below it
    hum = load(os.path.join(SRC, 'bbc', 'NHU05086119.mp3'), 2, 22)
    fl = load(os.path.join(sud, '693457.ogg'), 0, 22)
    n = min(len(hum), len(fl))
    mix = hum[:n] / (np.sqrt(np.mean(hum[:n] ** 2)) + 1e-9) + 0.2 * fl[:n] / (np.sqrt(np.mean(fl[:n] ** 2)) + 1e-9)
    f = int(2.0 * SR)
    m = n - f
    out = mix[:m].copy()
    ramp = np.linspace(0, 1, f)
    out[:f] = mix[:f] * ramp + mix[m:m + f] * (1 - ramp)
    save('gluehwuermchen', out, 0.08)
    # wading at the lake rim: single splashes cut from #861369 (CC0), chosen over #612964
    from scipy import signal as sg
    x = load(f'{FS}/861369.ogg')
    env = sg.sosfiltfilt(sg.butter(2, 8, 'low', fs=SR, output='sos'), np.abs(x))
    peaks, _ = sg.find_peaks(env, distance=int(0.35 * SR), prominence=env.max() * 0.15)
    k = 0
    for p in peaks:
        a = max(0, p - int(0.08 * SR))
        st = x[a:a + int(0.5 * SR)].copy()
        if len(st) < int(0.5 * SR) or k >= 10:
            continue
        st[:400] *= np.linspace(0, 1, 400)
        st[-int(0.08 * SR):] *= np.linspace(1, 0, int(0.08 * SR))
        # a splash has nothing below ~200 Hz: two of the ten cuts were a dull thud there (0.8.1: "a heartbeat
        # knock by the water"). Filtered, and the loudness taken from what stays, not from the thud.
        st = sg.sosfiltfilt(sg.butter(4, 200, 'high', fs=SR, output='sos'), st)
        save(f'schritt_waten_{k:02d}', st, 0.09)
        k += 1


def east():
    """The Ostwald's sounds: the pond's night lake (#524287 Sheyvan, CC0), the ritual place's little bell (the far bell,
    #266525, an octave up and cut short)."""
    loop(f'{FS}/524287.ogg', 'teich', 5, 30, 0.08, highpass=120.0)
    b = load(f'{FS}/266525.ogg')[:int(5.0 * SR)]
    b = np.interp(np.arange(0, len(b) - 1, 1.335), np.arange(len(b)), b)         # a fourth up, still slow
    n = int(3.6 * SR)
    b = b[:n] * np.minimum(1, np.linspace(3.6, 0, n)[:len(b)] / 1.2)
    save('glockchen', b, 0.1)


def rain():
    """The rain (Philip's picks, 2026-11-15, all CC0, previews in ~/mohnweg-sounds/freesound/regen):
    meadow light #584268 SamsterBirdies -> full #160699 klangfabrik, wood light #523391 Anya_Media -> full
    #612960 sandralaughs, water #399281 Mjeno, greenhouse inside (tin roof) #521772 MrFossy, outside (house roof)
    #833924 bassimat, far thunder #616607 TRP and #574386 TRP. Each slice is the recording's calmest 40 s (fewest
    single loud drops); levels are evened out in scenes/rain_sounds.gd from the measured means."""
    R = os.path.join(FS, 'regen')
    loop(f'{R}/584268.ogg', 'regen_wiese_leicht', 69, 40, 0.08, highpass=90.0, soft=False)
    loop(f'{R}/160699.ogg', 'regen_wiese_voll', 15, 40, 0.1, highpass=90.0, soft=False)
    loop(f'{R}/523391.ogg', 'regen_wald_leicht', 9, 40, 0.06, highpass=150.0, lowpass=9000.0, soft=False)   # very quiet recording: no hiss boost
    loop(f'{R}/612960.ogg', 'regen_wald_voll', 18, 40, 0.1, highpass=90.0, soft=False)
    loop(f'{R}/399281.ogg', 'regen_wasser', 0, 30, 0.1, highpass=90.0, soft=False)
    loop(f'{R}/521772.ogg', 'regen_dach_innen', 28, 40, 0.1, highpass=90.0, soft=False)
    loop(f'{R}/833924.ogg', 'regen_dach_aussen', 690, 40, 0.1, highpass=90.0, soft=False)
    for src, name, ss, t in ((f'{R}/616607.ogg', 'donner_0', 140.0, 22.0), (f'{R}/574386.ogg', 'donner_1', 0.5, 26.0)):
        x = load(src, ss, t)
        n = len(x)
        x = x * np.minimum(1, np.minimum(np.arange(n) / (0.8 * SR), (n - np.arange(n)) / (4.0 * SR)))   # soft in, long fade out
        save(name, x, 0.1)


def shots(src, prefix, n, length, rms=0.1, lo=90.0):
    """The n loudest separate moments of a take as single one-shots (a creak, a chatter, a quack)."""
    from scipy import signal
    x = load(src)
    x = signal.sosfiltfilt(signal.butter(4, lo, 'high', fs=SR, output='sos'), x)
    e = np.convolve(x ** 2, np.ones(int(0.05 * SR)) / int(0.05 * SR), 'same')
    picks, taken = [], np.zeros(len(x), bool)
    for i in np.argsort(e)[::-1]:
        if len(picks) == n:
            break
        if taken[i]:
            continue
        a = max(0, i - int(0.25 * length * SR))
        b = min(len(x), a + int(length * SR))
        picks.append((a, b))
        taken[max(0, a - int(length * SR)):b + int(length * SR)] = True
    for k, (a, b) in enumerate(sorted(picks)):
        c = x[a:b].copy()
        f = int(0.01 * SR)
        c[:f] *= np.linspace(0, 1, f)
        g = int(0.25 * len(c))
        c[-g:] *= np.linspace(1, 0, g) ** 2
        save(f'{prefix}_{k:02d}', c, rms)


def last():
    """The last missing sounds (Philip's picks, 2026-11-15): north waterfall Nox 'Cascata do Limbo', wind in the
    firs Nox 'Wind Forest' turning into the snow storm #792516 higher up, creaking wood #414092 at the
    woodcutter's hut, the slowly turning wheel #715478 KVV_Audio, red squirrel #111393 philberts, fish splash #507091
    paulprit / #425140 gis_sweden, a duck #188376 calodas, ducks together #716942 ghosttropic (all CC0)."""
    sm = [d for d in os.listdir(NOX) if d.endswith('Miguel_Flows_NOX_SOUND')][0]
    N, T = os.path.join(FS, 'norden'), os.path.join(FS, 'tiere')
    loop(f'{NOX}/{sm}/Ambiance_Waterfall_Moihnos_Cascata_do_Limbo_Loop_Stereo.wav', 'wasserfall', 0, 30, 0.1)
    loop(first('Nature_Essentials_NOX_SOUND/Ambiance_Wind_Forest_Loop_Stereo.wav'), 'tannenwind', 0, 28, 0.08)
    loop(f'{N}/792516.ogg', 'schneesturm', 20, 40, 0.08)
    # the wheel only turns slowly now: a creaking wooden wheel, not the rushing mill race (0.22.3, Philip)
    loop(os.path.join(FS, 'muehle', '715478.ogg'), 'muehle', 8, 40, 0.1, highpass=80.0, soft=False)
    for k, (ss, t) in enumerate([(43.2, 3), (68.7, 3), (90.2, 3), (154.7, 3)]):
        c = load(f'{N}/414092.ogg', ss, t)
        f = int(0.3 * SR)
        c[-f:] *= np.linspace(1, 0, f)
        save(f'knarzen_{k:02d}', c, 0.1)
    shots(f'{T}/111393.ogg', 'eichhorn', 4, 2.4, lo=300.0)
    shots(f'{T}/507091.ogg', 'platsch_a', 1, 1.6)
    shots(f'{T}/425140.ogg', 'platsch_b', 1, 1.6)
    shots(f'{T}/188376.ogg', 'ente', 4, 1.2, lo=200.0)
    x = load(f'{T}/716942.ogg')
    cs = np.concatenate([[0], np.cumsum(x ** 2)])
    L = 8 * SR
    starts = np.arange(0, max(1, len(x) - L), SR // 4)
    a = int(starts[np.argmax(cs[np.minimum(starts + L, len(x))] - cs[starts])])
    c = x[a:a + L].copy()
    f = int(0.5 * SR)
    c[:f] *= np.linspace(0, 1, f)
    c[-f:] *= np.linspace(1, 0, f)
    save('enten', c, 0.1)


if __name__ == '__main__' and sys.argv[1:] == ['last']:
    os.makedirs(OUT, exist_ok=True)
    last()
    sys.exit(0)

if __name__ == '__main__' and sys.argv[1:] == ['rain']:
    os.makedirs(OUT, exist_ok=True)
    rain()
    sys.exit(0)

if __name__ == '__main__' and sys.argv[1:] == ['east']:
    os.makedirs(OUT, exist_ok=True)
    east()
    sys.exit(0)

if __name__ == '__main__' and sys.argv[1:] == ['south']:
    south()
    sys.exit(0)

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
    loop(f'{FS}/320231.ogg', 'feuer', 2, 24, 0.035, highpass=150.0, lowpass=3200.0)   # rumble off, hiss tamed
    loop(f'{FS}/680476.ogg', 'kerze', 5, 20, 0.1)
    loop(f'{FS}/181563.ogg', 'knistern', 2, 24, 0.1)
    w = load(f'{FS}/249809.ogg')                         # torch swing: one soft whoosh per breath of the wisp
    from scipy import signal
    w = signal.sosfiltfilt(signal.butter(2, 120, 'high', fs=SR, output='sos'), w)[:int(2.3 * SR)]
    save('fackel', w * np.minimum(1, np.linspace(2.3, 0, len(w)) / 0.3), 0.1)
    for i, sid in enumerate([484366, 484367, 507265]):
        save(f'vogel_{i}', load(f'{FS}/{sid}.ogg'), 0.12)
    save('fluegel_0', load(f'{FS}/414671.ogg'), 0.12)          # chosen over 389633
    save('glocke', load(f'{FS}/266525.ogg'), 0.1)
    save('frosch', load(f'{FS}/536759.ogg'), 0.12)
    for i, sid in enumerate([484933, 484941, 484949]):
        save(f'seite_{i}', load(f'{FS}/{sid}.ogg'), 0.1)
    save('buch_zu_0', load(f'{FS}/484886.ogg'), 0.1)           # chosen over 484884
    south()
    east()
    print('ok', len(glob.glob(os.path.join(OUT, '*.ogg'))), 'Dateien')
