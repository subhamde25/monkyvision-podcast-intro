# usage: python -I tools/remux_audio.py <rendered.mp4> <out.mp4>   (run from work/)
# Swaps film/assets/audio/mix.wav into a finished render without touching the picture (-c:v copy), so an
# audio-only change (a new SFX, a level tweak) never needs a 50-minute 4K re-render. AAC 320k, 48 kHz.
import subprocess, sys

src, dst = sys.argv[1], sys.argv[2]
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-i', 'film/assets/audio/mix.wav', '-map', '0:v:0', '-map', '1:a:0',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '320k', '-ar', '48000', '-movflags', '+faststart', dst], check=True)
print('wrote', dst)
