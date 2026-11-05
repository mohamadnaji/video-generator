"""Procedural music beds + sound effects, mixed under the voices with ducking -> out/mix.wav.
Music moods: calm, upbeat, hype, tense, sad, dread, mystery, happy, none.
Add a new SFX by adding a function to SFX (returns a mono float array at SR)."""
import json
import os
import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 44100
rng = np.random.default_rng(3)


def tt(d):
    return np.arange(int(d * SR)) / SR


def env(n, a=0.01, r=0.1):
    e = np.ones(n)
    na, nr = min(n, int(a * SR)), min(n, int(r * SR))
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def lp(x, f):
    return sosfilt(butter(4, f, 'low', fs=SR, output='sos'), x)


def bp(x, lo, hi):
    return sosfilt(butter(2, [lo, hi], 'band', fs=SR, output='sos'), x)


def tone(f, d, kind='sine', a=0.01, r=0.15, vib=0.0):
    t = tt(d)
    f = np.broadcast_to(np.asarray(f, dtype=float), t.shape) if np.ndim(f) else np.full(t.shape, f, dtype=float)
    ph = 2 * np.pi * np.cumsum(f * (1 + vib * np.sin(2 * np.pi * 5.5 * t))) / SR
    if kind == 'sine':
        s = np.sin(ph)
    elif kind == 'square':
        s = np.tanh(3 * np.sin(ph))
    elif kind == 'saw':
        s = sum(np.sin(k * ph) / k for k in range(1, 9))
    else:  # pluck
        s = np.sin(ph) * np.exp(-t * 6) + 0.3 * np.sin(2 * ph) * np.exp(-t * 9)
    return s * env(len(t), a, r)


def noise(d):
    return rng.standard_normal(int(d * SR))


def kick():
    t = tt(0.25)
    return np.sin(2 * np.pi * np.cumsum(50 + 120 * np.exp(-t * 30)) / SR) * np.exp(-t * 14)


def snare():
    t = tt(0.18)
    return (bp(noise(0.18), 1500, 7000) * 0.6 + np.sin(2 * np.pi * 190 * t) * 0.5) * np.exp(-t * 22)


def hat():
    return bp(noise(0.05), 6000, 12000) * np.exp(-tt(0.05) * 80) * 0.5


def place(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf) or i + len(sig) <= 0:
        return
    if i < 0:
        sig, i = sig[-i:], 0
    n = min(len(sig), len(buf) - i)
    buf[i:i + n] += sig[:n] * gain


def midi(n):
    return 440 * 2 ** ((n - 69) / 12)


# ------------------------------------------------------------------ music beds
MOODS = {  # bpm, chord roots (midi), chord type, pad level, drums, lead
    'calm': (84, [57, 53, 48, 55], 'maj', 0.10, 'soft', 'pluck'),
    'upbeat': (112, [60, 55, 57, 53], 'maj', 0.07, 'pop', 'pluck'),
    'hype': (128, [62, 58, 60, 57], 'min', 0.07, 'four', 'square'),
    'happy': (118, [60, 65, 67, 60], 'maj', 0.07, 'pop', 'pluck'),
    'tense': (96, [50, 50, 51, 50], 'min', 0.11, 'pulse', None),
    'mystery': (80, [57, 53, 56, 52], 'min', 0.10, 'soft', 'pluck'),
    'sad': (66, [57, 53, 48, 52], 'min', 0.12, None, 'sine'),
    'dread': (60, [45, 45, 46, 45], 'min', 0.14, 'heart', None),
}


def bed(mood, dur):
    out = np.zeros(int(dur * SR) + SR)
    if mood not in MOODS:
        return out[:int(dur * SR)]
    bpm, roots, kind, padg, drums, lead = MOODS[mood]
    beat = 60 / bpm
    bar = beat * 4
    third = 4 if kind == 'maj' else 3
    t, i = 0.0, 0
    lead_rng = np.random.default_rng(len(mood))
    while t < dur:
        r = roots[i % len(roots)]
        chord = [midi(r - 12), midi(r), midi(r + third), midi(r + 7)]
        pad = sum(tone(f, bar + 0.3, 'saw', 0.3, 0.4) for f in chord)
        place(out, lp(pad, 1100) * padg, t)
        if lead:
            scale = [0, 2, third, 7, 9 if kind == 'maj' else 8, 12]
            for k in range(8):
                if lead_rng.random() < 0.55:
                    n = r + 12 + scale[lead_rng.integers(len(scale))]
                    place(out, tone(midi(n), beat * 0.45, lead, 0.005, 0.12) * 0.05, t + k * beat / 2)
        for b in range(4):
            tb = t + b * beat
            if drums == 'four':
                place(out, kick() * 0.5, tb)
                place(out, hat() * 0.5, tb + beat / 2)
                if b % 2:
                    place(out, snare() * 0.35, tb)
            elif drums == 'pop':
                if b in (0, 2):
                    place(out, kick() * 0.4, tb)
                if b in (1, 3):
                    place(out, snare() * 0.25, tb)
                place(out, hat() * 0.35, tb + beat / 2)
            elif drums == 'soft':
                if b == 0:
                    place(out, kick() * 0.25, tb)
                place(out, hat() * 0.15, tb + beat / 2)
            elif drums == 'pulse':
                place(out, tone(midi(r - 24), beat * 0.4, 'saw', 0.005, 0.1) * 0.06, tb)
                place(out, tone(midi(r - 24), beat * 0.3, 'saw', 0.005, 0.1) * 0.05, tb + beat / 2)
            elif drums == 'heart' and b in (0, 2):
                place(out, kick() * 0.4, tb)
                place(out, kick() * 0.28, tb + 0.18)
        t += bar
        i += 1
    return out[:int(dur * SR)]


# ------------------------------------------------------------------ sound effects
def _whoosh(d=0.4):
    n = noise(d)
    return bp(n, 600, 3500) * np.sin(np.linspace(0, np.pi, len(n))) ** 2 * 0.5


def _boom():
    t = tt(2.2)
    b = lp(noise(2.2), 1800) * np.exp(-t * 2.2) * 1.2
    b += np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 1.2) + 25) / SR) * np.exp(-t * 1.6) * 0.9
    return np.tanh(b * 1.5) * 0.9


def _pop():
    t = tt(0.12)
    return np.sin(2 * np.pi * np.cumsum(300 + 900 * np.exp(-t * 40)) / SR) * np.exp(-t * 35) * 0.5


def _ding():
    return (tone(1318, 1.0, 'sine', 0.002, 0.9) + tone(2637, 0.6, 'sine', 0.002, 0.5) * 0.3) * 0.35


def _fanfare():
    out = np.zeros(int(1.6 * SR))
    for k, f in enumerate([523, 659, 784, 1047]):
        place(out, tone(f, 0.3 if k < 3 else 0.9, 'square', 0.01, 0.3) * 0.18, k * 0.13)
    return out


def _trombone():
    out = np.zeros(int(2.4 * SR))
    for k, (f, d) in enumerate([(311, 0.4), (293.7, 0.4), (277.2, 0.4), (261.6, 1.1)]):
        place(out, lp(tone(f, d, 'saw', 0.04, 0.15, vib=0.012 if k == 3 else 0.004), 1400) * 0.3, k * 0.42)
    return out


def _dtmf(digits='911'):
    keys = {'1': (697, 1209), '9': (852, 1477), '0': (941, 1336), '2': (697, 1336)}
    out = np.zeros(int((len(digits) * 0.25 + 0.2) * SR))
    for i, d in enumerate(digits):
        lo, hi = keys.get(d, (770, 1336))
        place(out, (tone(lo, 0.16, 'sine', .003, .02) + tone(hi, 0.16, 'sine', .003, .02)) * 0.2, i * 0.25)
    return out


def _ring():
    out = np.zeros(int(1.6 * SR))
    for k in range(2):
        place(out, (tone(440, 0.55, 'sine', .01, .05) + tone(480, 0.55, 'sine', .01, .05)) * 0.15, k * 0.75)
    return out


def _steps(n=6):
    out = np.zeros(int(n * 0.22 * SR + SR // 4))
    for k in range(n):
        place(out, lp(noise(0.06), 900) * np.exp(-tt(0.06) * 50) * 0.6, k * 0.22)
    return out


def _drumroll():
    out = np.zeros(int(1.6 * SR))
    for k in range(40):
        place(out, snare() * (0.1 + k / 40 * 0.3), k * 0.035)
    place(out, kick() * 0.8 + 0, 1.42)
    return out


def _scratch():
    n = int(0.3 * SR)
    return bp(noise(0.3), 300, 2500) * np.linspace(1, 0, n) * 0.5


def _heartbeat():
    out = np.zeros(int(1.0 * SR))
    place(out, kick() * 0.7, 0)
    place(out, kick() * 0.5, 0.18)
    return out


def _rise():
    t = tt(1.2)
    return np.sin(2 * np.pi * np.cumsum(200 + 900 * (t / 1.2) ** 2) / SR) * env(len(t), 0.05, 0.05) * 0.15 + \
        bp(noise(1.2), 2000, 8000) * (t / 1.2) * 0.15


def _deflate():
    t = tt(1.0)
    return np.sin(2 * np.pi * np.cumsum(400 * np.exp(-t * 1.6)) / SR) * env(len(t), 0.01, 0.3) * 0.25


def _crowd():
    return lp(noise(2.0), 2500) * env(int(2.0 * SR), 0.2, 0.8) * 0.12


def _rain():
    return lp(noise(4.0), 3000) * 0.06


SFX = {'whoosh': _whoosh, 'boom': _boom, 'pop': _pop, 'ding': _ding, 'fanfare': _fanfare, 'trombone': _trombone,
       'dial': _dtmf, 'ring': _ring, 'steps': _steps, 'drumroll': _drumroll, 'scratch': _scratch,
       'heartbeat': _heartbeat, 'rise': _rise, 'deflate': _deflate, 'crowd': _crowd, 'rain': _rain}


def mix(story, timing, events, out):
    """events: list of (global_time, sfx_name, gain)."""
    total = timing['total']
    n = int(total * SR) + SR
    voice, music, fx = np.zeros(n), np.zeros(n), np.zeros(n)
    for sc, st in zip(story['scenes'], timing['scenes']):
        mood = sc.get('music', story.get('music', 'calm'))
        b = bed(mood, st['dur'] + 0.3)
        b[:int(0.08 * SR)] *= np.linspace(0, 1, int(0.08 * SR))
        place(music, b, st['start'])
        for ln in st['lines']:
            x, sr = sf.read(os.path.join(out, ln['file']), dtype='float64')
            if sr != SR:
                x = np.interp(np.arange(0, len(x), sr / SR), np.arange(len(x)), x)
            place(voice, x, st['start'] + ln['start'])
    for t, name, g in events:
        if name in SFX:
            place(fx, SFX[name](), t, g)
    # duck music under speech
    hop = SR // 50
    lvl = np.array([np.abs(voice[i:i + hop]).max() for i in range(0, n, hop)])
    duck = np.where(lvl > 0.02, 0.35, 1.0)
    k = 12
    duck = np.convolve(np.pad(duck, k, mode='edge'), np.ones(k) / k, mode='same')[k:-k]
    music *= np.repeat(duck, hop)[:n]
    m = voice * 1.0 + music * story.get('music_level', 0.9) + fx * 0.8
    m = m[:int(total * SR)]
    m /= max(1e-6, np.abs(m).max()) / 0.9
    sf.write(os.path.join(out, 'mix.wav'), np.stack([m, m], 1).astype(np.float32), SR)
