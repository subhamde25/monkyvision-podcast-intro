# usage: python -I tools/locate_clips.py   (run from work/)
# Finds where each of the earlier session's picked clips (resilient-intro/assets/audio/*.wav) sits in the raw
# mic tracks by FFT cross-correlation at 4 kHz, so the cut list can be rebuilt from the raw footage.
import glob, json, os, subprocess
import numpy as np
from scipy.signal import fftconvolve

SR = 4000
RAW = '../Raw Footage'
TRACKS = {'g': f'{RAW}/6931f6c68fc841fc5136fc29-audio.wav', 'h': f'{RAW}/6931f6c93a63010f3d2c4fd4-audio.wav'}


def load(p):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


tracks = {k: load(p) for k, p in TRACKS.items()}
out = {}
for p in sorted(glob.glob('../resilient-intro/assets/audio/' + (os.environ.get('ONLY') or '*') + '.wav')):
    clip = load(p)
    best = None
    for k, x in tracks.items():
        c = fftconvolve(x, clip[::-1], mode='valid')
        e = np.sqrt(np.maximum(fftconvolve(x * x, np.ones(len(clip), np.float32), mode="valid"), 1e-4 * len(clip) * float(np.mean(x * x)))) * np.linalg.norm(clip)
        n = c / e
        j = int(np.argmax(n))
        if best is None or n[j] > best[1]:
            best = (k, float(n[j]), j / SR)
    name = os.path.splitext(os.path.basename(p))[0]
    out[name] = {'track': best[0], 'score': round(best[1], 3), 'in': round(best[2], 3), 'dur': round(len(clip) / SR, 3)}
    print(name, out[name], flush=True)
json.dump(out, open('clip_locations.json', 'w'), indent=1)
