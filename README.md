# Monkyvision: "Resilient Mind Podcast" high-energy intro

An 83-second 16:9 YouTube intro cut from a 49-minute remote interview (host and guest on separate
cameras and mics), made for the **Monkyvision** video-editor assignment. Cut, framed, graded and mixed
with Python and ffmpeg; motion graphics in [HyperFrames](https://hyperframes.heygen.com) (HTML + GSAP);
rendered to 3840×2160 at 60 fps.

| | |
|---|---|
| **Final cut** | [`deliverables/ResilientMind_PodcastIntro_SD_4K60.mp4`](deliverables/) (3840×2160, 60 fps, 82.9 s, −15.1 LUFS, −1.8 dBTP, Git LFS) |
| **Source** | Guest Simone Knego (1080p24) and the host (4K24), separate video and audio per person, one shared clock |
| **Story** | Kilimanjaro hook ("16 steps in my house") → title on the host's own welcome → who she is → a barrage of her sharpest lines → her R.E.A.L. framework → the descent (an abusive relationship, her mother's 1961 med school) → the comeback ("she was so wrong") → "When you change the way you see yourself, the world around you changes." |
| **Style** | Raj Shamani's keyword slams and name card, The Diary Of A CEO's story arc and the score dropping out for the hard part, Somrat Dutta's white word card. See [`BRIEF.md`](BRIEF.md) |
| **Type** | League Gothic keywords, Playfair Display italic emphasis, Inter captions, Space Mono context chips |
| **Look** | Ink #0A0A0C, teal #22D1C1 (from her book cover), amber only on "16 STEPS". Per-camera grade, soft vignette, the descent 40% desaturated |
| **Sound** | Original generated 110 BPM score cut on bars so the drop, the stab, the lift and the last hit land on the title, "man's spot", "WRONG" and the end card. Auto-ducked under speech. 10 generated SFX across 39 cues |
| **Watermark** | SD mark, top-right |

> The beat sheet, the full 44-shot list and the sound cues are in [`BREAKDOWN.md`](BREAKDOWN.md).
> Every source and its licence is in [`docs/ASSETS.md`](docs/ASSETS.md); the pipeline, render settings,
> versions and gotchas are in [`docs/PRODUCTION.md`](docs/PRODUCTION.md).

## The edit in one glance

| Time | Beat |
|---|---|
| 0–9.6 s | **Hook:** cold open on "I was asked to climb **KILIMANJARO**… I have **16 STEPS** in my house", cut to the host laughing |
| 9.6–13.1 s | **Title:** RESILIENT MIND PODCAST slams in on the host's own "Welcome to another episode…" |
| 13.1–24.0 s | **The guest:** SIMONE KNEGO name card in a split layout, her roles as she says them, the white **ACCOUNTANT.** card |
| 24.0–50.3 s | **Barrage:** SELFISH? → NEVER SELFISH → HALFWAY (host laughs) → *skill* → **WHY NOT YOU?** → drop the ~~JUST~~ → the host's social-media joke |
| 50.3–57.5 s | **R.E.A.L.:** her framework builds row by row |
| 57.5–68.1 s | **Descent:** desaturated; high school, her mother at Pittsburgh Medical School, 1961 |
| 68.1–75.8 s | **Comeback:** "not a GOOD WRITER" → her first book → "she was **SO WRONG.**" |
| 75.8–82.9 s | **Thesis** line built word by word, then the show ident: "the full conversation starts now" |

## Project layout

```
.
├── tools/                     # the pipeline, in run order (docs/PRODUCTION.md)
│   ├── locate_clips.py        # find the picked moments in the raw mic tracks (FFT cross-correlation)
│   ├── transcribe_windows.py  # word timings for each pick (faster-whisper)
│   ├── make_edl.py            # THE CUT SCRIPT: 44 shots, camera, mic, in/out, punch-in, energy-snapped cuts
│   ├── build_aroll.py         # cut + face-framed punch-ins + per-camera grade → A-roll, dialogue, timeline
│   ├── finish_aroll.py        # vignette + descent grade → film/assets/video/
│   ├── make_words.py          # word timings on the film clock
│   ├── make_captions.py       # caption groups → film/compositions/caps.html
│   ├── mix_audio.py           # dialogue + bar-cut score + ducking + SFX → mix.wav (−15 LUFS)
│   ├── remux_audio.py         # swap a new mix into a render without re-rendering
│   └── yunet.onnx             # face detector
├── film/                      # the HyperFrames project
│   ├── index.html             # A-roll, camera moves (split layouts, kicks, push), scene hosts, audio
│   ├── compositions/          # title · intro · barrage · method · story · claim · endcard · caps · wm
│   ├── assets/img/            # book card, SD watermark; assets/video + mix.wav are built   [not in repo]
│   └── SPEC.md                # look, beats and sound as numbers
├── audio/                     # generated score (bgm_runway.mp3) and the 10 generated SFX
├── edl.json · words.json · clip_locations.json    # generated inputs the later steps read
├── deliverables/              # final 4K60 master                                           [Git LFS]
├── docs/  ASSETS.md · PRODUCTION.md
├── BRIEF.md · BREAKDOWN.md
└── build/ · build4k/ · renders/ · frames/        # intermediates, drafts, review sheets       [not in repo]
```

## Rebuild

With the supplied footage in `../Raw Footage/`:

```sh
python -I tools/make_edl.py
RES=4k python -I tools/build_aroll.py && python -I tools/finish_aroll.py 4k
python -I tools/build_aroll.py          # 1080p pass also writes build/dialog.wav + timeline.json
python -I tools/make_words.py && python -I tools/make_captions.py && python -I tools/mix_audio.py
cd film && npx --yes hyperframes@0.8.216 check
HF_SEGMENTED_CAPTURE=true HF_SEGMENT_FRAMES=360 HF_SEGMENT_BROWSER_RECYCLE=1 npx --yes hyperframes@0.8.216 render \
  --fps 60 --resolution 4k --quality delivery --workers 1 --low-memory-mode --resume --keep-segments -o ../renders/out.mp4
```

Needs Python 3.12 (numpy, scipy, opencv-python 5.x, soundfile, librosa, faster-whisper), ffmpeg and Node.js.

## Rights

The interview footage belongs to its owners and was supplied for this test only. It is not committed,
but the final cut in `deliverables/` contains it, so don't republish it outside a portfolio or test
context. The score and all sound effects were generated for this film; the fonts are SIL OFL.
