"""Speak every line with kokoro TTS and lay out the timeline -> out/timing.json + out/voice/*.wav.
Lines are cached by (voice, speed, text), so editing one line only re-speaks that line."""
import hashlib
import json
import os
import numpy as np
import soundfile as sf

FPS = 30
MODELS = os.environ.get('STORY_MODELS', os.path.join(os.path.dirname(__file__), '..', 'models'))
DEFAULT_VOICES = {'host': {'voice': 'am_puck', 'speed': 1.05}, 'narrator': {'voice': 'bm_george', 'speed': 0.95}}
_K = None


def kokoro():
    global _K
    if _K is None:
        from kokoro_onnx import Kokoro
        _K = Kokoro(os.path.join(MODELS, 'kokoro-v1.0.onnx'), os.path.join(MODELS, 'voices-v1.0.bin'))
    return _K


def trim(x, sr, thr=0.012):
    idx = np.where(np.abs(x) > thr)[0]
    if not len(idx):
        return x
    return x[max(0, idx[0] - int(.02 * sr)):min(len(x), idx[-1] + int(.07 * sr))]


def envelope(x, sr):
    """Mouth openness per video frame, 0..1."""
    hop = sr // FPS
    n = int(np.ceil(len(x) / hop))
    rms = np.array([np.sqrt(np.mean(x[i * hop:(i + 1) * hop] ** 2) + 1e-9) for i in range(n)])
    if rms.max() > 0:
        rms = rms / np.percentile(rms, 95)
    return [round(float(min(1, max(0, v - 0.12) * 1.3)), 2) for v in rms]


def words(text, dur):
    """Rough per-word timing (by letters) for karaoke captions."""
    ws = text.split()
    wt = [len(w.strip('.,!?…')) + 2 for w in ws]
    tot = sum(wt) or 1
    t, out = 0.0, []
    for w, k in zip(ws, wt):
        d = dur * k / tot
        out.append([w, round(t, 3), round(t + d, 3)])
        t += d
    return out


def speak(story, out):
    voices = dict(DEFAULT_VOICES)
    voices.update(story.get('voices', {}))
    vdir = os.path.join(out, 'voice')
    os.makedirs(vdir, exist_ok=True)
    timing, T = {'fps': FPS, 'scenes': []}, 0.0
    for sc in story['scenes']:
        t, lines = sc.get('lead', 0.25), []
        for i, ln in enumerate(sc.get('lines', [])):
            v = dict(voices.get(ln.get('by', 'host'), voices['host']))
            if 'voice' in ln:
                v['voice'] = ln['voice']
            speed = v.get('speed', 1.0) * ln.get('speed', 1.0)
            text = ln['text']
            h = hashlib.md5(f"{v['voice']}|{speed:.3f}|{text}".encode()).hexdigest()[:12]
            wav = os.path.join(vdir, f'{h}.wav')
            if not os.path.exists(wav):
                s, sr = kokoro().create(text, voice=v['voice'], speed=speed, lang=v.get('lang', 'en-us'))
                sf.write(wav, trim(np.asarray(s, dtype=np.float32), sr), sr)
            x, sr = sf.read(wav, dtype='float32')
            t += ln.get('gap', 0.25 if i else 0.0)
            d = len(x) / sr
            cap = ln.get('caption', text)
            lines.append(dict(id=ln.get('id', f'l{i}'), by=ln.get('by', 'host'), file=os.path.relpath(wav, out),
                              start=round(t, 3), end=round(t + d, 3), caption=cap, words=words(cap, d),
                              mouth=envelope(x, sr) if ln.get('by', 'host') == 'host' else None))
            t += d
        dur = round(max(t + sc.get('tail', 0.5), sc.get('min_dur', 0)), 3)
        timing['scenes'].append(dict(id=sc['id'], start=round(T, 3), dur=dur, lines=lines))
        T += dur
    timing['total'] = round(T, 3)
    json.dump(timing, open(os.path.join(out, 'timing.json'), 'w'), indent=1)
    return timing
