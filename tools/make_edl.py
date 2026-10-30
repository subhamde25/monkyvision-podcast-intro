# usage: python -I tools/make_edl.py   (run from work/)
# The cut script. Each shot = (id, camera, mic, in, out, zoom). Times are raw-recording seconds (both cameras
# share one clock). mic: g / h / gh (both, for laughs) / none. Cut points that jump in time are snapped to the
# quietest 5 ms inside a small window so no word is clipped; contiguous shots keep their exact join.
import json, os, subprocess
import numpy as np

SHOTS = [
    # -- HOOK -- "Kilimanjaro... 16 steps in my house"
    ('hook-asked',   'g', 'g',  98.95, 101.00, 1.30),
    ('hook-kili',    'g', 'g', 101.00, 102.25, 1.00),
    ('hook-yes',     'g', 'g', 102.95, 104.25, 1.45),
    ('hook-climber', 'g', 'g', 105.55, 106.95, 1.00),
    ('hook-florida', 'g', 'g', 107.20, 108.02, 1.22),
    ('hook-16',      'g', 'g', 108.30, 109.62, 1.00),
    ('hook-laugh',   'h', 'gh', 109.62, 110.62, 1.10),
    # -- TITLE -- host VO under the title card
    ('title',        'h', 'h',    2.80,   6.30, 1.00),
    # -- INTRO --
    ('intro-simone', 'h', 'h',    6.66,   8.98, 1.00),
    ('intro-keynote','g', 'g',   37.10,  38.10, 1.00),
    ('intro-coach',  'g', 'g',   38.85,  39.40, 1.25),
    ('intro-author', 'g', 'g',   40.25,  40.80, 1.00),
    ('intro-host',   'g', 'g',   41.10,  42.10, 1.25),
    ('intro-notlife','g', 'g',   42.75,  45.75, 1.00),
    ('intro-acct',   'g', 'g',   45.75,  47.45, 1.38),
    # -- BARRAGE --
    ('selfish-q1',   'g', 'g',  288.70, 291.85, 1.00),
    ('selfish-q2',   'g', 'g',  291.85, 294.20, 1.25),
    ('selfish-a',    'g', 'g',  297.60, 300.35, 1.00),
    ('top-q',        'g', 'g',  328.75, 332.00, 1.20),
    ('top-half',     'g', 'g',  332.00, 332.92, 1.45),
    ('top-laugh',    'h', 'gh', 332.92, 334.10, 1.10),
    ('skill',        'g', 'g',  165.50, 167.75, 1.00),
    ('space',        'g', 'g', 1343.85, 1345.25, 1.00),
    ('whynot',       'g', 'g', 1345.60, 1346.45, 1.45),
    ('justq',        'g', 'g', 1276.45, 1277.60, 1.20),
    ('scroll-1',     'g', 'g', 2298.70, 2300.17, 1.00),
    ('scroll-2',     'g', 'g', 2300.59, 2301.45, 1.00),
    ('social',       'h', 'h', 2321.15, 2324.50, 1.00),
    # -- METHOD: R.E.A.L. --
    ('real-intro',   'g', 'g',  836.90, 838.65, 1.00),
    ('real-r',       'g', 'g',  838.65, 839.75, 1.20),
    ('real-e',       'g', 'g',  839.75, 841.55, 1.00),
    ('real-a',       'g', 'g',  841.55, 842.92, 1.20),
    ('real-l',       'g', 'g',  842.92, 843.95, 1.40),
    # -- DESCENT --
    ('dated',        'g', 'g', 1612.60, 1615.50, 1.00),
    ('dated-host',   'h', 'g', 1615.50, 1617.10, 1.00),
    ('stuffed',      'g', 'g', 1617.10, 1619.50, 1.28),
    ('mom-1',        'g', 'g', 1840.90, 1842.12, 1.00),
    ('mom-2',        'g', 'g', 1842.12, 1844.30, 1.30),
    # -- ASCENT --
    ('teacher',      'g', 'g', 1672.25, 1674.62, 1.00),
    ('writer',       'g', 'g', 1674.62, 1675.90, 1.35),
    ('published',    'g', 'g', 1682.45, 1684.55, 1.00),
    ('sowrong',      'g', 'g', 1684.55, 1686.15, 1.35),
    # -- CLAIM + END CARD --
    ('claim',        'g', 'g', 2880.35, 2883.70, 1.00),
    ('endcard',      'g', 'none', 2883.70, 2887.40, 1.00),
]

RAW = os.environ.get('RAW_DIR', '../Raw Footage')   # the folder holding the supplied 6931f6... videos and WAVs
MIC = {'g': f'{RAW}/6931f6c68fc841fc5136fc29-audio.wav', 'h': f'{RAW}/6931f6c93a63010f3d2c4fd4-audio.wav'}
SR = 8000


def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


env = {}
for k, p in MIC.items():
    x = load(p)
    n = len(x) // 40
    env[k] = np.sqrt((x[:n * 40].reshape(n, 40) ** 2).mean(1))   # 5 ms RMS


def quiet(mic, t, lo, hi):
    e = env['g' if mic in ('gh', 'none') else mic]
    a, b = int((t + lo) / 0.005), int((t + hi) / 0.005)
    return round((a + int(np.argmin(e[a:b]))) * 0.005, 3)


segs = []
for i, (sid, v, a, t0, t1, z) in enumerate(SHOTS):
    prev = SHOTS[i - 1] if i else None
    nxt = SHOTS[i + 1] if i + 1 < len(SHOTS) else None
    if not (prev and abs(prev[4] - t0) < 1e-6):
        t0 = quiet(a, t0, -0.12, 0.04)
    if not (nxt and abs(nxt[3] - t1) < 1e-6) and a != 'none':   # a silent shot ends exactly where it's told
        t1 = quiet(a, t1, -0.04, 0.15)
    segs.append({'id': sid, 'v': v, 'a': a, 'in': t0, 'out': t1, 'z': z})
json.dump({'segs': segs}, open('edl.json', 'w'), indent=1)
print(len(segs), 'shots', round(sum(s['out'] - s['in'] for s in segs), 2), 's')
