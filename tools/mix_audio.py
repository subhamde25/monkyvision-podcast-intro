# usage: python -I tools/mix_audio.py   (run from work/)
# Bakes film/assets/audio/mix.wav: level-matched, compressed dialogue + the bar-edited score (auto-ducked under
# speech) + SFX, normalised to about -15 LUFS with a -1.5 dBTP ceiling.
import json, subprocess, os
import numpy as np
import soundfile as sf

SR = 48000
tl = json.load(open('build/timeline.json'))
END = tl['end']
N = int(round(END * SR))
LIB = {'gen': 'audio/sfx'}   # all SFX generated for this film (ElevenLabs sound-effects model via Runway), no third-party licences
LIB = {k: os.path.normpath(os.path.join(os.getcwd(), v)) for k, v in LIB.items()}


def dec(path, ch):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', str(ch), '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).copy()
    return x.reshape(-1, ch) if ch > 1 else x


def ffchain(x, af):
    p = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', '-af', af,
                        '-f', 'f32le', '-ac', '1', '-'], input=x.astype(np.float32).tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(p, np.float32).copy()[:len(x)]


# ---------- dialogue: match each shot's speech level, then one cleanup chain ----------
dlg = dec('build/dialog.wav', 1)[:N]
dlg = np.pad(dlg, (0, N - len(dlg)))
lv = []
for s in tl['segs']:
    a, b = int(s['start'] * SR), int(s['end'] * SR)
    seg = dlg[a:b]
    fr = seg[:len(seg) // 480 * 480].reshape(-1, 480)
    r = np.sqrt((fr ** 2).mean(1) + 1e-12)
    act = r[r > 10 ** (-42 / 20)]
    lv.append(20 * np.log10(np.sqrt((act ** 2).mean())) if len(act) > 10 else None)
ref = np.median([v for v in lv if v is not None])
gain = np.ones(N, np.float32)
for s, v in zip(tl['segs'], lv):
    if v is not None:
        g = 10 ** (np.clip(ref - v, -6, 6) / 20)
        gain[int(s['start'] * SR):int(s['end'] * SR)] = g
k = int(0.02 * SR)
gain = np.convolve(gain, np.ones(k) / k, mode='same')        # 20 ms ramps between shots
dlg = ffchain(dlg * gain, 'highpass=f=75,lowpass=f=15000,equalizer=f=3500:t=q:w=1.2:g=2,'
                          'acompressor=threshold=0.08:ratio=3.2:attack=8:release=140:makeup=1.6')

# ---------- score: bar-accurate edit of the generated bed (110 BPM, bar 2.18 s) ----------
mus = dec('audio/bgm_runway.mp3', 2)
PIECES = [  # (film_start, music_start, music_end)
    (0.000, 12.277, 21.860),     # tension pulse under the hook; near-silence lands on "16 steps" + the laugh
    (9.583, 21.860, 43.660),     # the drop on the title
    (31.383, 30.580, 56.697),    # 6 bars back: groove carries the barrage and R.E.A.L.
    (57.500, 56.697, 78.600),    # groove dies under the story, stab on "man's spot", lift lands on "WRONG"
    (79.400, 93.860, 99.000),    # last downbeat on the end card, ring-out
]
score = np.zeros((N, 2), np.float32)
XF = int(0.03 * SR)
for i, (fs, m0, m1) in enumerate(PIECES):
    a = int(round(fs * SR)); src = mus[int(round(m0 * SR)):int(round(m1 * SR))]
    nxt = int(round(PIECES[i + 1][0] * SR)) if i + 1 < len(PIECES) else N
    src = src[:nxt - a + XF].copy()
    src[:XF] *= np.sin(np.linspace(0, np.pi / 2, XF))[:, None] if i else 1
    if i + 1 < len(PIECES) and len(src) > nxt - a:
        tail = len(src) - (nxt - a)
        src[-tail:] *= np.cos(np.linspace(0, np.pi / 2, tail))[:, None]
    b = min(N, a + len(src))
    score[a:b] += src[:b - a]

# duck under speech: envelope of the dialogue, 60 ms attack / 350 ms release
fr = 240
e = np.sqrt(np.pad(dlg, (0, -len(dlg) % fr)).reshape(-1, fr).__pow__(2).mean(1))
speech = (20 * np.log10(e + 1e-9) > -38).astype(np.float32)
env = np.zeros_like(speech); up, dn = 1 - np.exp(-fr / (0.06 * SR)), 1 - np.exp(-fr / (0.35 * SR))
for i in range(len(speech)):
    p = env[i - 1] if i else 0
    env[i] = p + (speech[i] - p) * (up if speech[i] > p else dn)
LO, HI = 0.20, 0.42
mg = HI + (LO - HI) * np.repeat(env, fr)[:N]
t = np.arange(N) / SR
mg = np.where(t >= 79.40, 0.78, mg)                            # end card: the score takes over
mg = np.where((t >= 75.75) & (t < 79.40), np.maximum(mg, 0.27), mg)   # claim rides on the peak
fade = np.clip((END - t) / 0.7, 0, 1)
score *= (mg * fade)[:, None]

# ---------- SFX: (film time of the hit, file, volume). Peaks land one frame after the picture. ----------
SFX = [  # volumes are relative to files normalised to -16 dB (1.0 ~ just under the voice)
    (0.00, 'gen/soft-thump.mp3', 0.55),
    (2.28, 'gen/punch-swipe.mp3', 0.55), (4.20, 'gen/soft-pop.mp3', 0.6), (7.74, 'gen/bass-hit.mp3', 0.6),
    (9.40, 'gen/air-whoosh.mp3', 0.55), (9.583, 'gen/deep-impact.mp3', 0.95),
    (11.76, 'gen/title-slam.mp3', 0.55), (12.24, 'gen/air-whoosh.mp3', 0.4), (12.48, 'gen/soft-tick.mp3', 0.35),
    (13.00, 'gen/punch-swipe.mp3', 0.45),
    (15.583, 'gen/air-whoosh.mp3', 0.5),
    (15.72, 'gen/soft-tick.mp3', 0.28), (16.96, 'gen/soft-tick.mp3', 0.28), (17.52, 'gen/soft-tick.mp3', 0.28), (18.30, 'gen/soft-tick.mp3', 0.28),
    (23.40, 'gen/card-flick.mp3', 0.6), (24.10, 'gen/air-whoosh.mp3', 0.4),
    (29.07, 'gen/bass-hit.mp3', 0.5), (31.64, 'gen/punch-swipe.mp3', 0.45), (36.52, 'gen/soft-pop.mp3', 0.6),
    (39.32, 'gen/air-whoosh.mp3', 0.4),
    (41.90, 'gen/air-whoosh.mp3', 0.45), (42.38, 'gen/deep-impact.mp3', 0.75), (43.75, 'gen/card-flick.mp3', 0.5),
    (50.25, 'gen/air-whoosh.mp3', 0.55), (50.48, 'gen/title-slam.mp3', 0.45),
    (52.10, 'gen/soft-pop.mp3', 0.4), (53.23, 'gen/soft-tick.mp3', 0.3), (55.04, 'gen/soft-pop.mp3', 0.4), (56.52, 'gen/soft-tick.mp3', 0.3),
    (57.50, 'gen/soft-thump.mp3', 0.5),
    (64.62, 'gen/soft-tick.mp3', 0.22), (68.15, 'gen/soft-tick.mp3', 0.22),
    (71.21, 'gen/soft-pop.mp3', 0.4), (73.00, 'gen/air-whoosh.mp3', 0.4), (73.05, 'gen/shimmer.mp3', 0.45),
    (75.11, 'gen/title-slam.mp3', 0.6),
    (79.40, 'gen/deep-impact.mp3', 0.95), (79.45, 'gen/shimmer.mp3', 0.45),
]
fx = np.zeros((N, 2), np.float32)
cache = {}
for hit, f, vol in SFX:
    if f not in cache:
        lib, name = f.split('/')
        x = dec(os.path.join(LIB[lib], name), 2)
        r = np.sqrt(np.convolve((x ** 2).mean(1), np.ones(480) / 480, mode='same'))
        r100 = np.sqrt(np.convolve((x ** 2).mean(1), np.ones(4800) / 4800, mode='same')).max()
        x = x * (10 ** (-16 / 20) / (r100 + 1e-9))               # every file to -16 dB loudest 100 ms
        cache[f] = (x, int(np.argmax(r[:int(1.5 * SR)])))      # where the file hits
    x, pk = cache[f]
    a = int(round((hit + 1 / 24) * SR)) - pk
    s0 = max(0, -a); a = max(0, a); b = min(N, a + len(x) - s0)
    fx[a:b] += x[s0:s0 + b - a] * vol

mix = dlg[:, None] * np.array([[1.0, 1.0]], np.float32) + score + fx
sf.write('build/mix_raw.wav', mix, SR, subtype='FLOAT')

# ---------- loudness: two-pass loudnorm + true-peak ceiling ----------
m = subprocess.run(['ffmpeg', '-hide_banner', '-i', 'build/mix_raw.wav', '-af', 'loudnorm=I=-15:TP=-1.5:LRA=11:print_format=json',
                    '-f', 'null', '-'], capture_output=True, text=True).stderr
js = json.loads(m[m.rindex('{'):m.rindex('}') + 1])
af = (f"loudnorm=I=-15:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
      f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true,"
      f"aresample=192000,alimiter=limit=0.8:attack=2:release=60:level=disabled,aresample=48000,apad=whole_dur={END:.4f}")   # 4x oversampled = true-peak safe
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'build/mix_raw.wav', '-af', af, '-t', f'{END:.4f}', '-c:a', 'pcm_s16le',
                'film/assets/audio/mix.wav'], check=True)
# the limiter's look-ahead eats a few frames off the tail: pad back to the exact film length
out, _ = sf.read('film/assets/audio/mix.wav', dtype='int16')
sf.write('film/assets/audio/mix.wav', np.pad(out, ((0, max(0, N - len(out))), (0, 0)))[:N], SR, subtype='PCM_16')
print('input', js['input_i'], 'LUFS  tp', js['input_tp'])
