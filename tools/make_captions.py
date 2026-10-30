# usage: python -I tools/make_captions.py   (run from work/)
# Builds film/compositions/caps.html from GROUPS + film/assets/film-words.json. Edit GROUPS, never the HTML.
#   text: "lead words | KEY | tail words"  (lead/tail pop word by word; KEY slams on its first spoken word)
#   *word* = accent colour. styles: cap (sentence), stack (gothic key), serif (italic key), quote, strike.
import json, re, html

WORDS = json.load(open('film/assets/film-words.json'))
G = [  # (segments, text, style, side, accent)
    ('hook-asked hook-kili', 'I was asked to climb Mount | KILIMANJARO', 'stack', 'L', 'w'),
    ('hook-yes', 'I said | YES.', 'stack', 'R', 'a'),
    ('hook-climber', 'I am not a | climber.', 'serif', 'L', 'w'),
    ('hook-florida', 'I live in *Florida.*', 'cap', '', ''),
    ('hook-16 hook-laugh', 'I have | 16 STEPS | in my house.', 'stack', 'L', 'amber'),
    ('intro-simone', "Today I'm excited to be", 'cap', '', ''),
    ('intro-simone', 'joined by *Simone*', 'cap', '', ''),
    ('intro-notlife', 'And this is *not*', 'cap', '', ''),
    ('intro-notlife', 'how I started my life.', 'cap', '', ''),
    ('intro-acct', 'I started off as an', 'cap', '', ''),
    ('selfish-q1', "“You're really gonna leave", 'quote', '', ''),
    ('selfish-q1', 'your *family* at home', 'quote', '', ''),
    ('selfish-q1 selfish-q2', 'and go climb a mountain?', 'quote', '', ''),
    ('selfish-q2', "Don't you think that's | SELFISH?”", 'stack', 'L', 'a'),
    ('selfish-a', 'But my response was no,', 'cap', '', ''),
    ('selfish-a', 'self-care is | NEVER SELFISH.', 'stack', 'L', 'w'),
    ('top-q', "Do you really think you're", 'cap', '', ''),
    ('top-q', 'going to make it to the *top?*', 'cap', '', ''),
    ('top-q top-half', "No, I think I'm going to make it | HALFWAY.", 'stack', 'L', 'a'),
    ('top-laugh', "That's why I'm doing it.", 'cap', '', ''),
    ('skill', 'Confidence is a | skill', 'serif', 'L', 'a'),
    ('skill', 'that you *build.*', 'cap', '', ''),
    ('space', 'What would happen if you', 'cap', '', ''),
    ('space', 'took up space?', 'cap', '', ''),
    ('justq', 'We need to drop the | JUST.', 'strike', 'L', 'w'),
    ('scroll-1', 'How much time are you', 'cap', '', ''),
    ('scroll-1 scroll-2', 'spending *scrolling* on your phone?', 'cap', '', ''),
    ('social', "I don't want to know", 'cap', '', ''),
    ('social', 'how much time I spend', 'cap', '', ''),
    ('social', 'on *social media.*', 'cap', '', ''),
    ('dated', 'So I dated a guy', 'cap', '', ''),
    ('dated dated-host', 'in high school who was abusive', 'cap', '', ''),
    ('stuffed', 'and I stuffed it down | for years.', 'serif', 'L', 'w'),
    ('mom-1', 'The male students say,', 'cap', '', ''),
    ('mom-2', "“You took a man's spot.", 'quote', '', ''),
    ('mom-2', "You don't deserve to be here.”", 'quote', '', ''),
    ('teacher', 'A teacher who told me that', 'cap', '', ''),
    ('writer', 'I was not a | GOOD WRITER.', 'stack', 'L', 'w'),
    ('published', 'And when I published', 'cap', '', ''),
    ('published', 'my first *book,*', 'cap', '', ''),
    ('sowrong', 'I was like, oh, she was | SO WRONG.', 'stack', 'L', 'a'),
]


def norm(s):
    return re.sub(r"[^a-z0-9]", '', s.lower().replace('gonna', 'going'))


tl = json.load(open('build/timeline.json'))
seg_end = {s['id']: s['end'] for s in tl['segs']}
used = set()


def time_tokens(segs, toks):
    """Match display tokens to spoken words in order; unmatched tokens borrow the previous word's time."""
    pool = [w for w in WORDS if w['seg'] in segs and w['id'] not in used]
    out, j = [], 0
    for t in toks:
        n = norm(t)
        hit = None
        span = 1
        for k in range(j, min(j + 4, len(pool))):
            p = norm(pool[k]['text'])
            if n and p == n:
                hit = k
                break
            if k + 1 < len(pool) and n == p + norm(pool[k + 1]['text']):   # "self-care" heard as "self" "-care"
                hit, span = k, 2
                break
        if hit is not None:
            out.append((pool[hit]['start'], pool[hit + span - 1]['end']))
            for k in range(hit, hit + span):
                used.add(pool[k]['id'])
            j = hit + span
        else:
            out.append(None)
    for i, v in enumerate(out):        # fill gaps from neighbours
        if v is None:
            prev = next((out[k] for k in range(i - 1, -1, -1) if out[k]), None)
            nxt = next((out[k] for k in range(i + 1, len(out)) if out[k]), None)
            base = prev[1] if prev else (nxt[0] - 0.12 if nxt else 0)
            out[i] = (base, base + 0.12)
    return out


groups = []
for segs, text, style, side, acc in G:
    segs = segs.split()
    parts = [p.strip() for p in text.split('|')]
    lead, key, tail = (parts + ['', ''])[:3] if len(parts) > 1 else (parts[0], '', '')
    toks = [('lead', t) for t in lead.split()] + [('key', t) for t in key.split()] + [('tail', t) for t in tail.split()]
    times = time_tokens(segs, [t for _, t in toks])
    groups.append({'segs': segs, 'style': style, 'side': side, 'acc': acc, 'toks': toks, 'times': times})

COVERS = [(23.413, 24.103)]   # film-time windows of full-frame cards that sit under the caption layer (ACCOUNTANT)
for i, g in enumerate(groups):
    g['start'] = max(0.0, g['times'][0][0] - 0.06)
for i, g in enumerate(groups):
    last = g['times'][-1][1]
    hard = min(seg_end[g['segs'][-1]] + 0.0, last + 0.9)
    nxt = groups[i + 1]['start'] if i + 1 < len(groups) else 1e9
    g['end'] = round(min(hard, nxt - 0.02), 3)
    if g['end'] - g['start'] < 0.35:
        g['end'] = round(min(g['start'] + 0.35, nxt - 0.02), 3)
    for a, b in COVERS:                 # captions paint above the scenes: never over a full-frame card
        if g['start'] < a < g['end']:
            g['end'] = round(a, 3)

ACC = {'a': 'var(--accent)', 'w': '#FFFFFF', 'amber': 'var(--amber)', '': 'var(--accent)'}
html_groups, js = [], []
for i, g in enumerate(groups):
    gid = f'cg{i:02d}'
    st, sd = g['start'], g['end'] - g['start']
    cls = f"cg {g['style']} {'side-' + g['side'] if g['side'] else ''}"
    rows = {'lead': [], 'key': [], 'tail': []}
    for n, ((part, tok), (ws, we)) in enumerate(zip(g['toks'], g['times'])):
        hi = tok.startswith('*') and tok.endswith('*')
        word = html.escape(tok.strip('*'))
        rows[part].append(f'<span class="w{" hi" if hi else ""}" data-t="{ws - st:.3f}">{word}</span>')
    inner = ''
    if rows['lead']:
        inner += f'<div class="lead">{" ".join(rows["lead"])}</div>'
    if rows['key']:
        inner += f'<div class="key" style="color:{ACC[g["acc"]]}" data-t="{g["times"][len(rows["lead"])][0] - st:.3f}">{" ".join(rows["key"])}' \
                 + ('<i class="bar"></i>' if g['style'] == 'strike' else '') + '</div>'
    if rows['tail']:
        inner += f'<div class="tail">{" ".join(rows["tail"])}</div>'
    html_groups.append(f'      <div id="{gid}" class="clip {cls}" data-layout-allow-overflow data-start="{st:.3f}" data-duration="{sd:.3f}"><div class="in">{inner}</div></div>')

doc = '''<!DOCTYPE html>
<html>
  <template>
    <style>
      #root { position: absolute; inset: 0; overflow: visible; }
      .cg { position: absolute; inset: 0; overflow: visible; }
      .cg .in { position: absolute; }
      .w { display: inline-block; opacity: 0; }
      /* sentence captions: bottom centre */
      .cap .in, .quote .in { left: 0; right: 0; bottom: 92px; text-align: center; }
      .cap .lead { font-family: Inter, sans-serif; font-weight: 800; font-size: 54px; letter-spacing: -0.015em; color: #fff;
                   text-shadow: 0 2px 4px rgba(0,0,0,.55), 0 6px 26px rgba(0,0,0,.55); }
      .cap .w.hi { color: var(--accent); text-shadow: 0 0 2px rgba(0,0,0,.9), 0 2px 8px rgba(0,0,0,.85), 0 6px 26px rgba(0,0,0,.6); }
      .quote .lead { font-family: 'Playfair Display', serif; font-style: italic; font-weight: 700; font-size: 60px; color: #fff;
                     text-shadow: 0 2px 4px rgba(0,0,0,.55), 0 6px 26px rgba(0,0,0,.6); }
      .quote .w.hi { color: var(--accent); }
      /* stacked: small lead line + one big word, beside the speaker */
      .stack .in, .serif .in, .strike .in { bottom: 96px; max-width: 900px; }
      .side-L .in { left: 120px; text-align: left; }
      .side-R .in { right: 120px; text-align: right; }
      .stack .lead, .serif .lead, .strike .lead, .tail { font-family: Inter, sans-serif; font-weight: 700; font-size: 40px; color: #fff;
                    letter-spacing: -0.01em; text-shadow: 0 2px 4px rgba(0,0,0,.6), 0 6px 22px rgba(0,0,0,.5); margin-bottom: 6px; }
      .tail { margin-top: 10px; margin-bottom: 0; }
      .key { position: relative; display: inline-block; opacity: 0; transform-origin: 0% 85%; white-space: nowrap; }
      .side-R .key { transform-origin: 100% 85%; }
      .stack .key, .strike .key { font-family: 'League Gothic', sans-serif; font-size: 232px; line-height: .84; text-transform: uppercase;
                    letter-spacing: .005em; text-shadow: 0 8px 40px rgba(0,0,0,.45); }
      .serif .key { font-family: 'Playfair Display', serif; font-style: italic; font-weight: 800; font-size: 150px; line-height: .95;
                    text-shadow: 0 8px 40px rgba(0,0,0,.5); }
      .key .w { opacity: 1; }
      .bar { position: absolute; left: -2%; top: 52%; height: 22px; width: 104%; background: var(--accent);
             transform: scaleX(0); transform-origin: 0 50%; border-radius: 2px; }
    </style>
    <div id="root" data-composition-id="caps" data-width="1920" data-height="1080">
''' + '\n'.join(html_groups) + '''
    </div>
    <script>
      (function () {
        const tl = gsap.timeline({ paused: true });
        document.querySelectorAll('#root .cg').forEach((g) => {
          const st = parseFloat(g.dataset.start), dur = parseFloat(g.dataset.duration);
          g.querySelectorAll('.lead .w, .tail .w').forEach((w) => {
            tl.fromTo(w, { opacity: 0, filter: 'blur(6px)' }, { opacity: 1, filter: 'blur(0px)', duration: 0.13, ease: 'power2.out' }, st + parseFloat(w.dataset.t));
          });
          const key = g.querySelector('.key');
          if (key) {
            const kt = st + parseFloat(key.dataset.t);
            tl.fromTo(key, { opacity: 0, scale: 1.22, filter: 'blur(12px)' }, { opacity: 1, scale: 1, filter: 'blur(0px)', duration: 0.2, ease: 'expo.out' }, kt);
            const bar = key.querySelector('.bar');
            if (bar) tl.fromTo(bar, { scaleX: 0 }, { scaleX: 1, duration: 0.22, ease: 'power3.inOut' }, kt + 0.12);
          }
          const inner = g.querySelector('.in');
          tl.fromTo(inner, { opacity: 1 }, { opacity: 0, filter: 'blur(6px)', duration: 0.12, ease: 'power2.in', immediateRender: false }, st + dur - 0.12);
        });
        window.__timelines['caps'] = tl;
      })();
    </script>
  </template>
</html>
'''
open('film/compositions/caps.html', 'w', encoding='utf-8').write(doc)
for g in groups:
    print(f"{g['start']:6.2f}-{g['end']:6.2f} {g['style']:6s} {' '.join(t for _, t in g['toks'])}")
