"""Soundtrack for "Mission 8: Black Friday" (GTA-style SpendSense reel).

Timeline (s): hook 0-2.4 | spree 2.4-8.4 | WASTED 8.4-11.4 | rewind 11.4-12.6 |
Sense 12.6-19.2 | MISSION PASSED 19.2-22.2 | end 22.2-25.2
Instrument music is MIDI rendered with the GM soundfont; effects are made in numpy.
usage: python3 audio.py <workdir>
"""
import subprocess, sys, wave, os
import numpy as np
import mido

WORK = sys.argv[1]
SR = 48000
BPM = 100; B = 60 / BPM; TPB = 480
DUR = 25.4
PICKUPS = [3.0, 4.2, 5.4, 6.6]          # purchase moments
SENSE_HITS = [13.6, 16.4]               # Sense answers

def midi_render(events, name, programs, vols):
    mid = mido.MidiFile(ticks_per_beat=TPB); tr = mido.MidiTrack(); mid.tracks.append(tr)
    tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)))
    ev = []
    for ch, p in programs.items():
        ev.append((0, mido.Message('program_change', channel=ch, program=p)))
    for ch, v in vols.items():
        ev.append((0, mido.Message('control_change', channel=ch, control=7, value=v)))
        ev.append((0, mido.Message('control_change', channel=ch, control=91, value=40)))
    for ch, n, t, d, vel in events:
        s = int(t / B * TPB); e = int((t + d) / B * TPB)
        ev.append((s, mido.Message('note_on', channel=ch, note=n, velocity=vel)))
        ev.append((e, mido.Message('note_off', channel=ch, note=n, velocity=0)))
    ev.sort(key=lambda x: (x[0], 0 if x[1].type == 'note_off' else 1))
    last = 0
    for t, m in ev:
        tr.append(m.copy(time=t - last)); last = t
    mp = os.path.join(WORK, name + '.mid'); wp = os.path.join(WORK, name + '.wav')
    mid.save(mp)
    subprocess.run(['fluidsynth', '-ni', '-g', '0.8', '-r', str(SR), '-F', wp,
                    '/usr/share/sounds/sf2/default-GM.sf2', mp], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return load(wp)

def load(p):
    with wave.open(p) as w:
        a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
        a = a.reshape(-1, w.getnchannels())
    return a if a.shape[1] == 2 else np.repeat(a, 2, axis=1)

# ---------------- music (MIDI) ----------------
# channels: 0 e-piano, 1 slap bass, 2 brass, 3 strings, 4 bells, 9 drums
ev = []
def n(ch, note, t, d, v): ev.append((ch, note, t, d, v))

# Am - F - C - G groove, one chord per 2 beats (1.2 s)
CH = {'Am': ([57, 60, 64], 33), 'F': ([53, 57, 60], 29), 'C': ([55, 60, 64], 36), 'G': ([55, 59, 62], 31),
      'Dm': ([57, 62, 65], 26), 'E': ([56, 59, 64], 28)}
PROG = ['Am', 'F', 'C', 'G']

def groove(t0, t1, full=True, vel=1.0):
    t, i = t0, 0
    while t < t1 - 0.01:
        c = PROG[i % 4]; notes, root = CH[c]
        for k in (0, 0.75, 1.5):              # e-piano stabs
            for x in notes: n(0, x, t + k * B, 0.3 * B, int(62 * vel))
        n(1, root, t, 0.6 * B, int(96 * vel)); n(1, root + 12, t + 0.75 * B, 0.2 * B, int(80 * vel))
        n(1, root, t + 1.5 * B, 0.4 * B, int(88 * vel))
        # drums: kick, snare on 2, hats eighths
        n(9, 36, t, 0.2, int(100 * vel)); n(9, 36, t + 1.25 * B, 0.2, int(80 * vel))
        if full: n(9, 38, t + B, 0.2, int(92 * vel))
        else: n(9, 37, t + B, 0.2, int(70 * vel))
        for h in range(4): n(9, 42, t + h * 0.5 * B, 0.1, int((70 if h % 2 == 0 else 50) * vel))
        if full and i % 2 == 1: n(2, notes[-1] + 12, t + 1.5 * B, 0.35 * B, int(78 * vel))  # brass hit
        t += 2 * B; i += 1

groove(0.0, 8.4, full=True)
n(9, 49, 2.4, 1.0, 90)                                   # crash as the spree starts
# WASTED: sad held strings + low piano
n(3, 45, 8.9, 2.4, 70); n(3, 52, 8.9, 2.4, 60); n(3, 57, 8.9, 2.4, 55)
n(0, 33, 8.9, 2.0, 70)
# Sense section: lighter groove
groove(12.6, 19.2, full=False, vel=0.85)
for t in SENSE_HITS:
    n(4, 84, t, 0.4, 70); n(4, 91, t + 0.12, 0.5, 60)    # soft "answer" chime
# MISSION PASSED fanfare (brass + strings)
fan = [(19.2, [60, 64, 67], 0.3), (19.5, [60, 64, 67], 0.15), (19.7, [62, 65, 69], 0.3),
       (20.0, [64, 67, 72], 1.6)]
for t, chord, d in fan:
    for x in chord: n(2, x + 12, t, d, 100); n(3, x, t, d + 0.4, 70)
n(1, 36, 20.0, 1.6, 100); n(9, 49, 20.0, 1.5, 100); n(9, 36, 20.0, 0.2, 110)
# end: warm resolve
for x in [48, 55, 60, 64, 67]: n(0, x, 22.2, 2.8, 60); n(3, x, 22.2, 3.0, 50)
n(1, 36, 22.2, 2.4, 80); n(4, 84, 22.3, 1.2, 55); n(4, 88, 22.5, 1.2, 50)

music = midi_render(ev, 'bf_music', {0: 4, 1: 36, 2: 61, 3: 48, 4: 9}, {0: 92, 1: 100, 2: 90, 3: 80, 4: 70, 9: 92})

N = int(DUR * SR)
mix = np.zeros((N, 2), np.float32)
def put(sig, t, gain=1.0):
    s = int(t * SR); e = min(N, s + len(sig))
    if e > s: mix[s:e] += sig[:e - s] * gain

music = music[:N]
put(music, 0)

# ---------------- effects ----------------
rng = np.random.default_rng(7)
def tt(d): return np.arange(int(d * SR)) / SR
def st(x): return np.stack([x, x], axis=1).astype(np.float32)

# tape stop into WASTED: take 7.6-8.4 of the groove and slow it to a stop
seg = music[int(7.8 * SR):int(8.4 * SR)].copy()
L = len(seg); pos = np.cumsum(np.linspace(1.0, 0.05, int(L * 1.5)))
pos = pos[pos < L - 1]
tape = np.stack([np.interp(pos, np.arange(L), seg[:, c]) for c in (0, 1)], axis=1)
tape *= np.linspace(1, 0, len(tape))[:, None]
mix[int(7.8 * SR):int(8.4 * SR)] = 0
put(tape, 7.8, 1.0)

# WASTED impact: sub boom + noise burst
t = tt(2.2)
boom = np.sin(2 * np.pi * (55 * np.exp(-t * 1.2)) * t) * np.exp(-t * 2.2)
noise = rng.standard_normal(len(t)) * np.exp(-t * 9) * 0.35
put(st(boom * 0.9 + noise), 8.45, 0.9)

# rewind: the spree played backwards, 5x fast, with a warble
spree = music[int(2.4 * SR):int(8.4 * SR)][::-1]
idx = np.arange(0, len(spree), 5.0)
rew = np.stack([np.interp(idx, np.arange(len(spree)), spree[:, c]) for c in (0, 1)], axis=1)
rew = rew[:int(1.2 * SR)] * (0.8 + 0.2 * np.sin(np.arange(min(len(rew), int(1.2 * SR)))[:, None] / SR * 2 * np.pi * 9))
put(rew.astype(np.float32), 11.4, 0.8)

# cash pickup "cha-ching": noise click + two bright bells
def chaching():
    t = tt(0.7)
    click = rng.standard_normal(len(t)) * np.exp(-t * 60) * 0.5
    b1 = (np.sin(2 * np.pi * 2093 * t) + 0.5 * np.sin(2 * np.pi * 4186 * t)) * np.exp(-t * 8)
    t2 = np.clip(t - 0.09, 0, None)
    b2 = (np.sin(2 * np.pi * 2637 * t2) + 0.5 * np.sin(2 * np.pi * 5274 * t2)) * np.exp(-t2 * 6) * (t > 0.09)
    return st(click + 0.35 * b1 + 0.35 * b2)
for p in PICKUPS:
    put(chaching(), p, 0.55)

# wanted-star alarm: short two-tone siren whoop
def whoop(d=0.45):
    t = tt(d); f = 700 + 500 * np.sin(np.pi * t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return st(np.sign(np.sin(ph)) * 0.18 * np.exp(-t * 3) + np.sin(ph) * 0.2)
for k, p in enumerate(PICKUPS):
    put(whoop(), p + 0.25, 0.25 + 0.08 * k)

# whoosh into each scene
def whoosh(d=0.5):
    t = tt(d); x = rng.standard_normal(len(t))
    x = np.convolve(x, np.ones(30) / 30, mode='same') * np.sin(np.pi * t / d) ** 2
    return st(x * 0.9)
for t0 in [2.3, 12.5, 19.1, 22.1]:
    put(whoosh(), t0 - 0.2, 0.5)

# master
peak = np.abs(mix).max()
mix = np.tanh(mix / peak * 1.6) * 0.9
fade = int(1.0 * SR); mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
out = os.path.join(WORK, 'bf_audio.wav')
with wave.open(out, 'w') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((mix * 32767).astype(np.int16).tobytes())
print('ok', out)
