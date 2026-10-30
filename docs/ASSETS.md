# Assets: where every piece comes from

| Asset | Source | Licence / rights | Treatment | Where it lands |
|---|---|---|---|---|
| Guest video + mic | Supplied raw footage, `6931f6c68…` (1080p24) | Client's, supplied for this test | Face-framed crops, warm S-curve, light vibrance and sharpen; upscaled to 4K with Lanczos | All guest shots |
| Host video + mic | Supplied raw footage, `6931f6c93…` (4K24) | Client's, supplied for this test | Haze pulled out of the window, shadows warmed, contrast and saturation up; native 4K crops | Welcome, intro, laugh and listening cutaways, social-media line |
| Shot picks | An earlier pass's 25 picked moments, located in the raw tracks by FFT cross-correlation (`clip_locations.json`, every match scored 1.000) | — | Re-cut from the raw files; cut points snapped to the quietest 5 ms | `tools/make_edl.py` |
| Word timings | faster-whisper `small.en`, clip windows only (`tools/transcribe_windows.py`) | — | Deduped and mapped onto the film clock | Captions, scene timings |
| Music bed | Original, generated for this film with Runway (ElevenLabs music model): "instrumental cinematic podcast intro… 110 BPM", 99 s | Generated for the user; no third-party licence | Cut on bars: 12.3–21.9 s, 21.9–43.7 s, a 6-bar loop back to 30.6 s, 56.7–78.6 s, 93.9 s to the end. Ducked under speech | `audio/bgm_runway.mp3` → mix |
| 10 SFX | Original, generated with Runway's sound-effects model (ElevenLabs): deep impact, title slam, bass hit, soft thump, air whoosh, punch swipe, card flick, soft pop, soft tick, shimmer | Generated for the user; no credit needed | Normalised per file, placed by measured peak | `audio/sfx/` → mix |
| Book card | Crop of the real book on her shelf (guest camera, 28:03), 10-frame temporal denoise, 2× Lanczos | Part of the supplied footage | Rounded card with a shadow, tilted −4° | `film/assets/img/book.png` |
| Fonts | League Gothic, Playfair Display, Inter, Space Mono, bundled with HyperFrames | SIL OFL | — | All type |
| Watermark | SD mark (`SD_watermark_white.png`) | The editor's own | 92 px, 62% opacity, soft shadow, top-right | `film/assets/img/sd.png` |
| Face detector | OpenCV YuNet (`tools/yunet.onnx`) | MIT | — | Punch-in framing |

Earlier versions (v1, v2) used a CC BY impact ("Deep Cinematic Impact" by MeijstroAudio) and library
whooshes. v3 replaced every effect with the generated set, so the final needs no attribution.
