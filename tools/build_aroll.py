# usage: python -I tools/build_aroll.py [seg ...]   (run from work/; RES=4k builds a 3840x2160 copy into build4k/)
# Cuts edl.json into the 1920x1080 24fps A-roll (build/aroll.mp4) and the joined dialogue (build/dialog.wav).
# Each segment shows camera v ("g" guest / "h" host) and plays mic a (default = v) — so a host reaction shot
# can sit under the guest's line. Punch-ins (z) are framed on the face found by YuNet inside that segment.
# Writes build/timeline.json (segment times on the output clock) for the motion-graphics layer.
import json, subprocess, os, statistics, sys
import cv2

FPS = 24
W, H = (3840, 2160) if os.environ.get('RES') == '4k' else (1920, 1080)
B = 'build4k' if W == 3840 else 'build'
RAW = os.environ.get('RAW_DIR', '../Raw Footage')   # the folder holding the supplied 6931f6... videos and WAVs
SRC = {
    'g': {'v': f'{RAW}/6931f6c68fc841fc5136fc29-video.mp4', 'a': f'{RAW}/6931f6c68fc841fc5136fc29-audio.wav', 'w': 1920, 'h': 1080},
    'h': {'v': f'{RAW}/6931f6c93a63010f3d2c4fd4-video.mp4', 'a': f'{RAW}/6931f6c93a63010f3d2c4fd4-audio.wav', 'w': 3840, 'h': 2160},
}
# guest: warm library — gentle S-curve, protect the white tee. host: hazy window — pull the veil, warm the skin.
GRADE = {
    'g': ('curves=all=0/0.02 0.25/0.225 0.5/0.5 0.78/0.8 1/0.97,'
          'colorbalance=rs=0.01:bs=-0.012:rh=-0.006:bh=0.006,eq=contrast=1.05:saturation=1.04,'
          'vibrance=intensity=0.08,unsharp=5:5:0.45:3:3:0'),
    'h': ('curves=all=0/0 0.12/0.06 0.35/0.3 0.6/0.6 0.85/0.86 1/0.97,'
          'colorbalance=rs=0.035:gs=0.004:bs=-0.03:rm=0.02:bm=-0.02:rh=0.0:bh=0.01,'
          'eq=contrast=1.1:saturation=1.12:gamma=0.97,vibrance=intensity=0.12,unsharp=5:5:0.5:3:3:0'),
}
det = cv2.FaceDetectorYN_create(os.path.join(os.path.dirname(__file__), 'yunet.onnx'), '', (0, 0), 0.6)


def face(src, t0, t1):
    cap = cv2.VideoCapture(src['v'])
    pts, S = [], 480 / src['w']
    for k in range(5):
        cap.set(cv2.CAP_PROP_POS_MSEC, (t0 + (t1 - t0) * (k + 0.5) / 5) * 1000)
        ok, fr = cap.read()
        if not ok:
            continue
        im = cv2.resize(fr, None, fx=S, fy=S)
        det.setInputSize((im.shape[1], im.shape[0]))
        _, fs = det.detect(im)
        if fs is not None and len(fs):
            x, y, w, h = max(fs, key=lambda f: f[2])[:4]
            pts.append(((x + w / 2) / S, (y + h / 2) / S))
    if not pts:
        return src['w'] / 2, src['h'] * 0.38
    return statistics.median(p[0] for p in pts), statistics.median(p[1] for p in pts)


def run(cmd):
    # 4K decodes occasionally crash ffmpeg on this low-RAM machine; a retry clears it
    for k in range(3):
        if subprocess.run(cmd).returncode == 0:
            return
    raise RuntimeError(' '.join(cmd))


edl = json.load(open('edl.json'))
os.makedirs(f'{B}/segs', exist_ok=True)
only = set(sys.argv[1:])
tl, frame = [], 0
for i, s in enumerate(edl['segs']):
    v = SRC[s['v']]; mic = s.get('a', s['v'])
    nf = round((frame / FPS + s['out'] - s['in']) * FPS) - frame
    dur = nf / FPS
    z = s.get('z', 1.0)
    cx, cy = face(v, s['in'], s['in'] + dur)
    cw, ch = v['w'] / z, v['h'] / z
    x0 = min(max(cx - cw / 2 + s.get('dx', 0) * v['w'], 0), v['w'] - cw)
    y0 = min(max(cy - ch * 0.40, 0), v['h'] - ch)       # eyes on the upper third on punch-ins
    vf = (f"crop={cw:.1f}:{ch:.1f}:{x0:.1f}:{y0:.1f},scale={W}:{H}:flags=lanczos,{GRADE[s['v']]},"
          f"fps={FPS},setsar=1,format=yuv420p")
    out = f'{B}/segs/{i:02d}.mp4'
    if not only or str(i) in only or not os.path.exists(out):
        run(['ffmpeg', '-v', 'error', '-y', '-ss', f"{s['in']:.3f}", '-i', v['v'], '-frames:v', str(nf),
             '-vf', vf, '-an', '-c:v', 'libx264', '-crf', '15', '-preset', 'medium', '-threads', '4', '-g', '24', '-bf', '0', out])
        # fades only where the sound jumps in time, so continuous lines split across shots stay seamless
        segs = edl['segs']
        cont_in = i > 0 and segs[i - 1].get('a', segs[i - 1]['v']) == mic and abs(segs[i - 1]['out'] - s['in']) < 0.002
        cont_out = i + 1 < len(segs) and segs[i + 1].get('a', segs[i + 1]['v']) == mic and abs(segs[i + 1]['in'] - s['out']) < 0.002
        fades = ([] if cont_in else ['afade=t=in:d=0.012']) + ([] if cont_out else [f'afade=t=out:st={dur - 0.015:.4f}:d=0.015'])
        tail = ','.join(['aresample=48000'] + fades + [f'apad=whole_dur={dur:.4f}', f'atrim=0:{dur:.4f}'])
        seek = ['-ss', f"{s['in']:.3f}", '-t', f'{dur:.4f}']
        if mic == 'none':
            cmd = ['-f', 'lavfi', '-t', f'{dur:.4f}', '-i', 'anullsrc=r=48000:cl=mono', '-af', tail]
        elif mic == 'gh':
            cmd = seek + ['-i', SRC['g']['a']] + seek + ['-i', SRC['h']['a'], '-filter_complex',
                  f'[0:a][1:a]amix=inputs=2:normalize=0,{tail}']
        else:
            cmd = seek + ['-i', SRC[mic]['a'], '-af', tail]
        run(['ffmpeg', '-v', 'error', '-y'] + cmd + ['-vn', '-ac', '1', '-c:a', 'pcm_s16le', f'{B}/segs/{i:02d}.wav'])
    tl.append({'i': i, 'id': s.get('id', str(i)), 'v': s['v'], 'a': s.get('a', s['v']), 'start': round(frame / FPS, 4),
               'end': round((frame + nf) / FPS, 4), 'in': s['in'], 'z': z})
    frame += nf

with open(f'{B}/segs/list.txt', 'w') as f:
    f.writelines(f"file '{i:02d}.mp4'\n" for i in range(len(tl)))
with open(f'{B}/segs/alist.txt', 'w') as f:
    f.writelines(f"file '{i:02d}.wav'\n" for i in range(len(tl)))
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{B}/segs/list.txt', '-c', 'copy', f'{B}/aroll.mp4'])
run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', f'{B}/segs/alist.txt', '-c', 'copy', f'{B}/dialog.wav'])
json.dump({'fps': FPS, 'end': frame / FPS, 'segs': tl}, open(f'{B}/timeline.json', 'w'), indent=1)
print(f'{len(tl)} segments, {frame} frames = {frame / FPS:.3f}s')
