# Production: pipeline, commands, versions, gotchas

The repo sits next to the supplied footage: the scripts read `../Raw Footage/` (the two videos and two
WAVs) and write intermediates to `build/` and `build4k/`, which are not in the repo. Run every tool from the
repo root.

## Pipeline

| Step | Command | In → out |
|---|---|---|
| 1. Locate the picks | `python -I tools/locate_clips.py` | 25 picked clip WAVs from the earlier pass → `clip_locations.json` (one-off; needs that pass's `../resilient-intro/assets/audio/`) |
| 2. Word timings | `python -I tools/transcribe_windows.py 2.5` | each pick ±2.5 s, on its own mic → `words.json` |
| 3. Cut script | `python -I tools/make_edl.py` | the `SHOTS` list (44 cuts, camera, mic, in/out, punch-in) → `edl.json`, cut points snapped to the quietest 5 ms |
| 4. A-roll + dialogue | `python -I tools/build_aroll.py` · `RES=4k python -I tools/build_aroll.py` | → `build[4k]/aroll.mp4`, `build/dialog.wav`, `build/timeline.json`. Face-framed punch-ins (YuNet), per-camera grade, 24 fps. Arguments = shot indexes to rebuild only those |
| 5. Finishing pass | `python -I tools/finish_aroll.py` · `python -I tools/finish_aroll.py 4k` | vignette, bottom falloff and the 57.5–68.1 s descent grade → `film/assets/video/aroll[4k].mp4` |
| 6. Words on the film clock | `python -I tools/make_words.py` | → `film/assets/film-words.json` |
| 7. Captions | `python -I tools/make_captions.py` | the `G` list (text, style, side, accent) → `film/compositions/caps.html`. Never edit the HTML by hand |
| 8. Mix | `python -I tools/mix_audio.py` | dialogue levelled per shot and compressed, the score cut on bars and ducked, SFX by peak → `film/assets/audio/mix.wav` (−15 LUFS, −1.8 dBTP) |
| 9. Check | `cd film && npx --yes hyperframes@0.8.216 check` | 0 errors expected; the remaining craft warnings are the deliberately short title-sting holds |
| 10. Render | see below | → `renders/` |
| 11. Audio-only changes | `python -I tools/remux_audio.py renders/in.mp4 renders/out.mp4` | swaps in a new `mix.wav` with `-c:v copy`, so there's no re-render |

### Render (7.4 GB RAM machine)

One long capture crashes Chrome after about 900–1,600 frames. Short segments, a fresh browser per
segment and `--resume` make it reliable:

```sh
cd film
# 4K 60 fps (the delivered master): ~51 min, 4,976 frames
HF_SEGMENTED_CAPTURE=true HF_SEGMENT_FRAMES=360 HF_SEGMENT_BROWSER_RECYCLE=1 \
  npx --yes hyperframes@0.8.216 render --fps 60 --resolution 4k --quality delivery --workers 1 \
  --low-memory-mode --protocol-timeout 900000 --resume --keep-segments -o ../renders/out_4k60.mp4
# 1080p 24 fps: ~12 min (set the <video> src in index.html back to aroll.mp4 first)
HF_SEGMENTED_CAPTURE=true HF_SEGMENT_FRAMES=240 HF_SEGMENT_BROWSER_RECYCLE=1 \
  npx --yes hyperframes@0.8.216 render --fps 24 --quality delivery --workers 1 \
  --low-memory-mode --protocol-timeout 900000 --resume --keep-segments -o ../renders/out_1080p.mp4
```

`--resolution 4k` renders the 1920×1080 composition at device-pixel-ratio 2, so the type is natively
sharp. The footage stays 24p inside the 60 fps output (each frame is repeated), while every animation
and camera move draws a new frame at 60. Frame interpolation was left out on purpose because it smears
hands and mouths.

Needs Python 3.12 with numpy, scipy, opencv-python (5.x, for YuNet), soundfile, librosa and
faster-whisper, plus ffmpeg and Node.js. Close heavy browsers before rendering.

## Versions

| Version | Change |
|---|---|
| v1 | First full render (1080p24). Review found the "I started off as an" caption printing over the white ACCOUNTANT card |
| v2 | `COVERS` in `make_captions.py`: captions paint above the scenes, so any group overlapping a full-frame card is clamped to the card's start |
| v3 | Every SFX regenerated (no attribution or unknown licences left); audio remuxed onto v2's picture |
| **4K60** | A-roll rebuilt at 3840×2160 (host native, guest upscaled), rendered at 60 fps in 4K. **Delivered** |

## Gotchas

- **Full-length transcription** of a 49-minute track ran out of memory and crawled on this CPU. Transcribing only the windows around each pick took minutes.
- **FFT matching on near-silent audio** divides by almost zero, which gave bogus scores of 10⁶. The energy floor in `locate_clips.py` fixes it.
- **Word dedupe:** overlapping windows hear the same word twice. Keying on a rounded start time silently dropped different words that started close together, so dedupe on text plus a 0.3 s window.
- **Caption groups** need `inset: 0`. A zero-height box parks the bottom-anchored text above the frame.
- **GSAP:** `letterSpacing` tweens snap under frame-by-frame capture. The PODCAST spread animates each letter's `x` instead.
- **Limiter look-ahead** trims a few frames off the tail, so the mix is padded back to the exact film length.
- **4K ffmpeg encodes** occasionally die with `0xC000012D` (commit limit). `build_aroll.py` retries and caps x264 threads.
