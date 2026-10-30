# usage: python -I tools/make_words.py   (run from work/)
# Maps the per-clip word timings (words.json, raw-recording seconds) through the cut list (build/timeline.json)
# onto the film clock. Writes film/assets/film-words.json: [{id, seg, text, start, end}] in film seconds.
import json

clips = json.load(open('words.json'))
tl = json.load(open('build/timeline.json'))
raw = {'g': [], 'h': []}
for c in clips.values():
    raw[c['track']] += [tuple(w) for w in c['words']]
pool = {}
for k, ws in raw.items():                     # overlapping windows hear the same word twice: keep the first
    kept = []
    for s, e, w in sorted(ws):
        norm = w.lower().strip('.,?!"')
        if any(abs(s - ks) < 0.3 and norm == kw.lower().strip('.,?!"') for ks, ke, kw in kept[-6:]):
            continue
        kept.append((s, e, w))
    pool[k] = kept

out = []
for seg in tl['segs']:
    mic = {'gh': 'g', 'none': None}.get(seg['a'], seg['a'])
    if not mic:
        continue
    t_in, t_out = seg['in'], seg['in'] + (seg['end'] - seg['start'])
    for s, e, w in pool[mic]:
        mid = (s + e) / 2
        if t_in <= mid < t_out:
            fs = seg['start'] + max(s, t_in) - t_in
            fe = seg['start'] + min(e, t_out) - t_in
            out.append({'id': f'w{len(out)}', 'seg': seg['id'], 'text': w, 'start': round(fs, 3), 'end': round(fe, 3)})
json.dump(out, open('film/assets/film-words.json', 'w'), indent=1, ensure_ascii=False)
cur = None
for w in out:
    if w['seg'] != cur:
        cur = w['seg']; print(f"\n[{cur}]", end=' ')
    print(f"{w['text']}@{w['start']:.2f}", end=' ')
print()
