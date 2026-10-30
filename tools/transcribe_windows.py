# usage: python -I tools/transcribe_windows.py [pad]   (run from work/)
# Word-timestamped transcript of each located clip (clip_locations.json) plus `pad` seconds either side,
# on that clip's own mic track. Times are absolute source seconds. Writes words.json.
import json, subprocess, sys
import numpy as np
from faster_whisper import WhisperModel

PAD = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
RAW = '../Raw Footage'
TRACKS = {'g': f'{RAW}/6931f6c68fc841fc5136fc29-audio.wav', 'h': f'{RAW}/6931f6c93a63010f3d2c4fd4-audio.wav'}
loc = json.load(open('clip_locations.json'))
model = WhisperModel('small.en', device='cpu', compute_type='int8', cpu_threads=4)
out = {}
for name, c in loc.items():
    t0 = max(0.0, c['in'] - PAD)
    dur = c['dur'] + 2 * PAD
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-t', f'{dur:.3f}', '-i', TRACKS[c['track']],
                          '-ac', '1', '-ar', '16000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    segs, _ = model.transcribe(np.frombuffer(raw, np.float32), language='en', word_timestamps=True, beam_size=5)
    words = [[round(t0 + w.start, 2), round(t0 + w.end, 2), w.word.strip()] for s in segs for w in (s.words or [])]
    out[name] = {**c, 'words': words}
    print(name, ' '.join(w[2] for w in words), flush=True)
json.dump(out, open('words.json', 'w'), indent=1, ensure_ascii=False)
