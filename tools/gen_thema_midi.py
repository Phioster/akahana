#!/usr/bin/env python3
"""Akahana-Thema als echtes Klavierstück: Partitur -> MIDI (Anschlag, Pedal, Rubato) -> sfizz/Splendid -> Raum.

    python3 gen_thema_midi.py out.m4a        Hörprobe: Vorspiel + A + A' (17 Takte)
Melodie und Harmoniefolge wie gen_thema.py; neu sind Griffe, Begleitung, Phrasierung und sparsame Echos.
"""
import os, subprocess, sys, tempfile
import numpy as np
import pretty_midi
from scipy import signal

SR = 44100
BPM = 74
SFZ = os.environ.get('SFZ', os.path.expanduser('~/klavier-samples/neu/SplendidGrandPiano/Splendid gleich.sfz'))   # 15 ms Einsatz, gleiche Farbe aller Stufen
SFIZZ = os.path.expanduser('~/klavier-samples/sfizz_render')
rng = np.random.default_rng(7)

# Griffe wie ein Pianist: linke Hand weit (Grundton, Quinte, Dezime), Reibungen nur ab C4 aufwärts
# name: (Grundton, Quinte, Dezime, [Mittelstimmen])
V = {
    'Dm9': (38, 45, 53, [57, 60]), 'Bbmaj7': (34, 41, 50, [57, 62]), 'C': (36, 43, 52, [55, 62]),
    'Am': (33, 40, 48, [55, 60]), 'Gm9': (31, 38, 46, [62, 65]), 'Dm7': (38, 45, 53, [57, 60]),
    'F': (29, 36, 45, [60, 65]), 'Asus': (33, 40, 50, [57, 64]), 'A': (33, 40, 49, [57, 64]),
    'C/E': (40, 48, 55, [60, 64]), 'Dm/C': (36, 45, 53, [57, 62]), 'Bb6': (34, 41, 50, [55, 62]),
}

# Melodie unverändert aus gen_thema.py (Schlag, Dauer, Ton)
A = [('Dm9', [(0, 1, 69), (1, 1, 74), (2, 2, 76)]),
     ('Bbmaj7', [(0, 1.5, 77), (1.5, .5, 76), (2, 2, 74)]),
     ('C', [(0, 1, 76), (1, 1, 72), (2, 2, 67)]),
     ('Am', [(0, 3, 69), (3, 1, 72)]),
     ('Gm9', [(0, 1, 70), (1, 1, 74), (2, 2, 79)]),
     ('Dm7', [(0, 1.5, 77), (1.5, .5, 76), (2, 1, 74), (3, 1, 72)]),
     ('F', [(0, 2, 74), (2, 1, 69), (3, 1, 72)]),
     ('Asus', [(0, 2, 71), (2, 2, 69)])]

B = [('F', [(0, 2, 72), (2, 1, 69), (3, 1, 72)]),
     ('C/E', [(0, 2, 76), (2, 1, 74), (3, 1, 72)]),
     ('Dm/C', [(0, 3, 74), (3, 1, 69)]),
     ('Bb6', [(0, 4, 77)]),
     ('Gm9', [(0, 1, 70), (1, 1, 74), (2, 2, 79)]),
     ('C', [(0, 1.5, 76), (1.5, .5, 74), (2, 2, 72)]),
     ('F', [(0, 1, 69), (1, 1, 72), (2, 2, 77)]),
     ('A', [(0, 4, 76)])]
END = [('Dm9', [(0, 1, 69), (1, 1, 74), (2, 2, 76)]),
       ('Bbmaj7', [(0, 1.5, 77), (1.5, .5, 76), (2, 2, 74)]),
       ('Gm9', [(0, 2, 70), (2, 2, 69)]),
       ('Dm9', [(0, 4, 74)])]

# Ganzes Stück: Vorspiel, A, A' (voller, Halbschluss), B (Höhepunkt), Wiederkehr in Oktaven, Schluss
TEIL = os.environ.get('TEIL', 'ganz')
if TEIL == 'probe':
    FORM = ([('Dm9', [], 'ruhig'), ('Bbmaj7', [(3, .5, 65), (3.5, .5, 67)], 'ruhig')]
            + [(c, m, 'leicht') for c, m in A]
            + [(c, m, 'fliessend') for c, m in A[:5]]
            + [('Asus', [(0, 3, 74), (3, 1, 76)], 'fliessend'), ('A', [(0, 2, 73), (2, 2, 76)], 'fliessend'),
               ('Dm9', [(0, 4, 74)], 'schluss')])   # Vorhalt D->Cis erst über A-Dur, nie über Asus
else:
    FORM = ([('Dm9', [], 'ruhig'), ('Bbmaj7', [(3, .5, 65), (3.5, .5, 67)], 'ruhig')]
            + [(c, m, 'leicht') for c, m in A]
            + [(c, m, 'fliessend') for c, m in A[:7]] + [('A', [(0, 4, 69)], 'fliessend')]
            + [(c, m, 'hoehepunkt') for c, m in B]
            + [(c, m, 'wiederkehr') for c, m in A[:4]]
            + [(c, m, 'leicht') for c, m in END[:3]] + [('Dm9', [(0, 4, 74)], 'schluss')])


# Gegenden: gleiche Noten und gleicher Zeitablauf, nur Echo, Dichte, Farbe und Raum ändern sich -> das Spiel kann jederzeit überblenden
GEGEND = {
    'mohnfeld': dict(echo=0.75, echos=(0.5, 0.28), bis='ton', hell=4800, raum=3.4),
    # mystisch: späte, unregelmäßige Echos von weit her, tiefer Bass, ab und zu ein heller Einzelton
    'wald': dict(echo=1.25, echos=(0.5, 0.32, 0.18), bis='takt', hell=3600, raum=5.0, tiefbass=True, funkeln=True, vel=-3),
    # karg: kaum Begleitung, jeder lange Ton mit genau einem späten Echo
    'berge': dict(echo=2.0, echos=(0.45,), bis='takt', hell=4000, raum=4.6, karg=True, tiefbass=True),
    # lebhaft: von Anfang an fließende Achtel, dichte schnelle Echos, hell
    'see': dict(echo=0.5, echos=(0.5, 0.3, 0.18), bis='takt', hell=6000, raum=3.0, dicht=True),
    'dorf': dict(echo=0.5, echos=(0.45, 0.25), bis='takt', hell=5600, raum=2.4, dicht=True),
    # Regen: keine Echos, keine Verzierungen, gedämpft, leiser - die Melodie trägt allein
    'regen': dict(echo=0.75, echos=(), bis='ton', hell=2600, raum=3.8, karg=True, tiefbass=True, perlen=False, vel=-6, gain_db=-7),
}


def zj(sd, *key):
    """Feste kleine Zeitschwankung je Ton: in allen Gegenden gleich, egal welche Töne dazukommen."""
    return float(np.random.default_rng([abs(int(k * 1000)) for k in key] + [17]).normal(0, sd))


def begleitung(art, r, q, x, inner):
    """Begleitfiguren (Schlag, Ton, Stärke); entwickelt sich: ruhig -> Viertel -> fließende Achtel."""
    if art == 'ruhig':
        return [(0, r, 46), (0.5, q, 34), (1, x, 36), (1.5, inner[0], 32), (2, q, 34), (2.5, x, 34), (3, inner[0], 32), (3.5, x, 32)]
    if art in ('leicht', 'wiederkehr'):
        return [(0, r, 48), (0.5, q, 34), (1, x, 36), (1.5, inner[0], 30), (2, q, 33), (2.5, x, 34),
                (3, inner[0], 30), (3.5, x, 31)]
    if art in ('fliessend', 'hoehepunkt'):              # voller: Bass in Oktaven, Achtel weiter gespannt
        tief = r - 12 if r - 12 >= 24 else r
        return [(0, tief, 44), (0, r, 46), (0.5, q, 36), (1, x, 38), (1.5, inner[0], 32), (2, inner[1], 32),
                (2.5, inner[0], 30), (3, x, 34), (3.5, q, 31)]
    return [(0, r, 44), (0, q, 34), (0.5, x, 34), (1, inner[0], 30), (1.5, inner[1], 28)]  # Schluss: einmal aufgefächert


def build(g):
    p = GEGEND[g]
    pm = pretty_midi.PrettyMIDI(initial_tempo=BPM)
    ins = pretty_midi.Instrument(0)
    beat0 = 60 / BPM
    n = len(FORM)
    # Verzierung wie im alten Thema (abgenommen): nach jedem 3. langen hohen Melodieton vier helle Akkordtöne aufwärts
    hoch = [(bi, k) for bi, (ch, mel, art) in enumerate(FORM) for k, (be, d, m) in enumerate(mel)
            if m >= 76 and d >= 2 and be + d <= 4 and art != 'schluss']
    perlen = set(hoch[1::3]) if p.get('perlen', True) else set()
    t = 0.5
    for bi, (ch, mel, art) in enumerate(FORM):
        r, q, x, inner = V[ch]
        pos = bi % 4                                     # Stelle in der 4-Takt-Phrase
        # Rubato: Phrasenende breiter, Schluss deutlich langsamer
        dehn = 1.0 + (0.09 if pos == 3 else 0.0) + (0.25 if art == 'schluss' else 0.0) + max(0, bi - (n - 3)) * 0.05
        b = beat0 * dehn
        bogen = [0.0, 4.0, 7.0, 2.0][pos]                # Lautstärkebogen über die Phrase
        lauter = {'fliessend': 5, 'hoehepunkt': 9, 'wiederkehr': -4}.get(art, 0)   # Wiederholung voller, Mittelteil am vollsten, Wiederkehr leise

        # Pedal: kurz nach dem neuen Bass loslassen und wieder treten (legato, ohne Matsch)
        ins.control_changes += [pretty_midi.ControlChange(64, 0, t + 0.04), pretty_midi.ControlChange(64, 127, t + 0.12)]

        muster = begleitung('fliessend' if p.get('dicht') and art in ('ruhig', 'leicht') else art, r, q, x, inner)
        if p.get('karg') and art != 'schluss':
            muster = [e for e in muster if e[0] in (0, 2.5) and not (e[0] == 0 and e[1] < r)]
        if p.get('tiefbass') and r - 12 >= 24 and not any(e[1] == r - 12 for e in muster):
            muster = muster + [(0, r - 12, 30)]
        for be, m, v in muster:
            st = t + be * b + zj(0.006, bi, be, m)
            ins.notes.append(pretty_midi.Note(int(v + bogen * 0.6 + lauter * 0.6 + p.get('vel', 0)), m, st, t + 4 * b))
        if p.get('funkeln') and bi % 3 == 1:           # Wald: ein heller Ton aus dem Akkord, weit weg, lang nachhallend
            melpc = [mm % 12 for _, _, mm in mel]
            kand = [c % 12 for c in (q, x, *inner) if all((c - z) % 12 not in (1, 11) for z in melpc)]
            if kand:
                hi = 84 + kand[bi % len(kand)]
                hb = (1.5, 2.5, 3.5)[bi % 3]
                for k, f in enumerate((1.0, 0.6, 0.36, 0.2)):
                    et = t + (hb + k * 1.5) * b
                    if et < t + 3.8 * b:
                        ins.notes.append(pretty_midi.Note(int(24 * f), hi, et, et + 1.2 * b))

        for be, d, m in mel:
            st = t + be * b - 0.012 + zj(0.005, bi, be, m)   # Melodie kommt einen Hauch vor der Begleitung (wie beim Pianisten)
            v = 41 + bogen * 0.6 + lauter * 0.6 + (2 if d >= 2 else 0) + p.get('vel', 0) * 0.5   # Melodie nur knapp über der Begleitung: sonst springt jeder hohe Ton 7-13 dB heraus   # sanfter: über 40 nimmt Splendid die ungefilterte Stufe, harter Hammer
            if art == 'schluss':
                v = 50
            ins.notes.append(pretty_midi.Note(int(v), m, st, st + d * b * 0.95))
            if art == 'wiederkehr':                      # Wiederkehr: Melodie zusätzlich eine Oktave höher, leise darüber
                ins.notes.append(pretty_midi.Note(int(v - 8), m + 12, st + 0.008, st + d * b * 0.95))
            if art in ('fliessend', 'hoehepunkt') and d >= 1:            # in der Wiederholung: Terz/Sexte darunter aus dem Akkord
                tief = [k for k in (m - 3, m - 4, m - 8, m - 9) if k % 12 in {p % 12 for p in (r, q, x, *inner)}
                        and all((k - p) % 12 != 1 for p in (r, q, x, *inner))]   # nur Terz/Sexte, nie kleine None über der Begleitung
                if tief:
                    ins.notes.append(pretty_midi.Note(int(v - 14), tief[0], st + 0.01, st + d * b * 0.95))
            if (bi, mel.index((be, d, m))) in perlen:
                oben = m + (12 if art == 'wiederkehr' else 0)
                toene = sorted({p % 12 + 12 * o for p in (r, q, x, *inner) for o in range(5, 9)})
                naechst = [mm for _, _, mm in FORM[bi + 1][1][:1]] if bi + 1 < len(FORM) else []
                toene = [k for k in toene if oben < k <= 96                # nie einen Halbton neben Melodie, ihrem Echo oder dem nächsten Melodieton
                         and all((k - z) % 12 not in (1, 11) for z in (m, *naechst))][:4]
                t0 = t + (be + 1) * b
                for j, k in enumerate(toene):
                    ins.notes.append(pretty_midi.Note(int(34 - 3 * j), k, t0 + j * 0.13 + zj(0.006, bi, j, k), min(t0 + j * 0.13 + 0.9 * b, t + 4 * b - 0.05)))
            # Echo nur auf langen hohen Melodietönen, nur innerhalb des Takts: der Flügel spielt den Ton leise nach
            if d >= 2 and m >= 72 and art not in ('schluss', 'wiederkehr'):
                mel_pc = [(bb, dd, mm) for bb, dd, mm in mel]
                for k, f in enumerate(p['echos'], 1):
                    et = st + k * p['echo'] * b
                    grenze = t + (be + d) * b if p['bis'] == 'ton' else t + 4 * b
                    klingt = [mm for bb, dd, mm in mel_pc if t + bb * b <= et < t + (bb + dd) * b]
                    if any((m - mm) % 12 in (1, 11) for mm in klingt):
                        break                              # Echo würde mit dem gerade klingenden Melodieton reiben
                    if et + 0.25 * b < grenze:
                        ins.notes.append(pretty_midi.Note(int(v * f), m, et, min(et + 0.6 * b, t + 4 * b - 0.03)))   # nie in den nächsten Akkord hinein
        t += 4 * b

    ins.control_changes.append(pretty_midi.ControlChange(64, 0, t + 3.0))
    pm.instruments.append(ins)
    with tempfile.TemporaryDirectory() as tmp:
        pm.write(f'{tmp}/t.mid')
        if os.environ.get('MIDI_AUCH'):
            pm.write(os.path.splitext(OUT)[0] + f'_{g}.mid')
        if os.environ.get('FLUEGEL') == 'digital':      # berechneter Flügel (digitalfluegel.py) statt Aufnahmen
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import digitalfluegel
            y = digitalfluegel.render(pm, SR)
        else:
            subprocess.run([SFIZZ, '--sfz', SFZ, '--midi', f'{tmp}/t.mid', '--wav', f'{tmp}/t.wav', '-s', str(SR)],
                           capture_output=True, check=True)
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f'{tmp}/t.wav', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
                                 capture_output=True, check=True).stdout
            y = np.frombuffer(raw, np.float32).astype(float).reshape(-1, 2)
    n_soll = int((t + 6) * SR)                          # alle Gegenden exakt gleich lang (sfizz hört bei leisen früher auf)
    y = np.pad(y[:n_soll], ((0, max(0, n_soll - len(y))), (0, 0)))
    # Raum wie in gen_thema.py (Mohnfeld): weicher, dunkler Nachhall
    rr = np.random.default_rng(7)
    ir_n = int(p['raum'] * SR)
    ir = rr.normal(0, 1, ir_n) * np.exp(-np.arange(ir_n) / SR * 1.9)
    ir = signal.lfilter(*signal.butter(2, 3200 / (SR / 2)), ir)
    ir /= np.abs(ir).sum() ** 0.5 * 24
    for c in range(2):
        y[:, c] = y[:, c] * 0.8 + signal.fftconvolve(y[:, c], ir)[:len(y)] * 0.5
    y = signal.lfilter(*signal.butter(2, p['hell'] / (SR / 2)), y, axis=0)   # dunkle Kette wie im alten Thema (Variante B): nimmt dem Anschlag die Spitze
    tief_db = float(os.environ.get('ANSCHLAG_DB', '7'))
    if tief_db > 0:                                      # Transientenformer: nur der Anschlag wird leiser, der Ton bleibt
        mono = np.abs(y).mean(1)
        def folger(x, auf, ab):
            a1, a2 = np.exp(-1 / (auf * SR)), np.exp(-1 / (ab * SR))
            e = np.empty_like(x); z = 0.0
            for i, v in enumerate(x):
                z = a1 * z + (1 - a1) * v if v > z else a2 * z + (1 - a2) * v
                e[i] = z
            return e
        schnell = folger(mono, 0.001, 0.060) + 1e-6
        langsam = folger(mono, 0.045, 0.060) + 1e-6
        g = np.clip(langsam / schnell, 10 ** (-tief_db / 20), 1.0)
        g = signal.filtfilt(*signal.butter(1, 60 / (SR / 2)), g)   # Verstärkung glatt: kein Knistern
        y = y * g[:, None]
    y[-int(4 * SR):] *= np.linspace(1, 0, int(4 * SR))[:, None]
    y *= 0.5 / np.abs(y).max() * 10 ** (p.get('gain_db', 0) / 20)   # Spitzen -6 dB (Regen leiser)
    return y, t


def main(out):
    global OUT
    OUT = out
    g = os.environ.get('GEGEND', 'mohnfeld')
    if g == 'wanderung':                               # Hörprobe: alle Gegenden nacheinander, gleichleistend überblendet
        order = ['mohnfeld', 'see', 'dorf', 'wald', 'berge', 'regen']
        teile = [build(x)[0] for x in order]
        n = min(len(x) for x in teile)
        tt = np.arange(n) / SR
        seg, xf = (n / SR - 6) / len(order), 8.0
        y = np.zeros((n, 2))
        for i, x in enumerate(teile):
            c = (i + 0.5) * seg
            w = np.clip((seg / 2 + xf / 2 - np.abs(tt - c)) / xf, 0, 1)
            if i == 0: w[tt < c] = 1
            if i == len(order) - 1: w[tt > c] = 1
            y += x[:n] * np.sin(w * np.pi / 2)[:, None]
        print('Wechsel bei', [round((i + 1) * seg) for i in range(len(order) - 1)], 's')
        t = n / SR
    else:
        y, t = build(g)
    with tempfile.TemporaryDirectory() as tmp:
        y.astype(np.float32).tofile(f'{tmp}/y.f32')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '2', '-i', f'{tmp}/y.f32',
                        '-b:a', '256k', out], check=True)
    print('ok', round(t, 1), 's')


if __name__ == '__main__':
    main(sys.argv[1])
