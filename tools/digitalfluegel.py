"""Berechneter Flügel: reine Teiltöne, keine Aufnahme, kein Hammer, keine Mechanik.

render(pm, sr) -> Stereo-Array. Liest Noten + Haltepedal (CC64) aus einem pretty_midi-Objekt.
Modell je Ton: Teiltöne mit Saiten-Inharmonizität, drei leicht verstimmte Saiten (Schwebung),
Anschlagsstelle 1/8 (Kammfilter im Spektrum), zweistufiges Abklingen (schnell, dann Nachklang),
Helligkeit wächst mit der Anschlagstärke, Dämpfer beim Loslassen ohne Pedal.
"""
import numpy as np

rng = np.random.default_rng(11)


def _pedal_kurve(pm):
    cc = sorted([c for i in pm.instruments for c in i.control_changes if c.number == 64], key=lambda c: c.time)
    return [(c.time, c.value >= 64) for c in cc]


def _loslassen(ende, kurve):
    """Wann der Dämpfer wirklich greift: Tastenende, oder später, wenn das Pedal da noch getreten ist."""
    unten = False
    for t, z in kurve:
        if t > ende:
            break
        unten = z
    if not unten:
        return ende
    for t, z in kurve:
        if t > ende and not z:
            return t
    return ende + 6.0


def ton(m, vel, dauer, sr, weich=0.004):
    f0 = 440.0 * 2 ** ((m - 69) / 12)
    v = vel / 127
    B = 0.00008 * 2 ** ((m - 40) / 14)                     # Inharmonizität: hohe Saiten steifer
    n_max = max(1, min(40, int(9000 / f0)))
    n = np.arange(1, n_max + 1)
    fn = n * f0 * np.sqrt(1 + B * n ** 2)
    hell = 1.6 - 0.9 * v                                   # leise = dunkel, laut = mehr Obertöne
    amp = n ** -hell * np.abs(np.sin(np.pi * n / 8 + 0.05)) # Anschlag bei 1/8 der Saite
    amp *= np.exp(-fn / (2500 + 5000 * v))
    amp /= amp.sum()
    # Abklingen: tiefe Töne klingen lange, hohe kurz; höhere Teiltöne schneller
    t60 = np.clip(18 * 2 ** (-(m - 21) / 22), 1.2, 18)
    tau1 = t60 / 6.9 * 0.25 / (1 + 0.04 * n)              # schneller Anfangsabfall
    tau2 = t60 / 6.9 / (1 + 0.02 * n)                      # Nachklang
    N = int(dauer * sr)
    t = np.arange(N) / sr
    y = np.zeros(N)
    saiten = 1 if m < 30 else (2 if m < 45 else 3)
    verstimm = [0.0, 0.9, -0.7][:saiten]                    # Cent: die Saiten schweben leicht gegeneinander
    for k in range(n_max):
        if fn[k] > sr * 0.45:
            break
        hull = 0.65 * np.exp(-t / tau1[k]) + 0.35 * np.exp(-t / tau2[k])
        for c in verstimm:
            f = fn[k] * 2 ** (c / 1200)
            y += amp[k] / saiten * hull * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    a = int(weich * sr)
    y[:a] *= np.sin(np.linspace(0, np.pi / 2, a)) ** 2     # weicher Einsatz, ohne Klick
    return y * (0.25 + 0.75 * v ** 1.6)


def render(pm, sr=44100):
    kurve = _pedal_kurve(pm)
    noten = [n for i in pm.instruments for n in i.notes]
    laenge = max(n.end for n in noten) + 8
    L = np.zeros(int(laenge * sr)); R = np.zeros_like(L)
    cache = {}
    for n in noten:
        los = _loslassen(n.end, kurve)
        dauer = min(los - n.start + 0.35, 14.0)
        key = (n.pitch, n.velocity, round(dauer, 1))
        if key not in cache:
            y = ton(n.pitch, n.velocity, round(dauer, 1), sr)
            d = int(0.3 * sr)                             # Dämpfer: 0,3 s Ausklingen
            y[-d:] *= np.linspace(1, 0, d) ** 2
            cache[key] = y
        y = cache[key]
        i = int(n.start * sr)
        k = min(len(y), len(L) - i)
        pan = np.clip((n.pitch - 21) / 87, 0, 1)            # tiefe Töne links, hohe rechts (Spielerperspektive)
        L[i:i + k] += y[:k] * (1.15 - 0.5 * pan)
        R[i:i + k] += y[:k] * (0.65 + 0.5 * pan)
    return np.stack([L, R], 1)
