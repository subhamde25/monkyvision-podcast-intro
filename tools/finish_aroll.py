# usage: python -I tools/finish_aroll.py [4k]   (run from work/)
# Bakes the finishing pass into the A-roll the composition plays: a soft vignette with a darker bottom
# (so captions read over her white tee) and the desaturated, cooler "descent" grade from 57.5 to 68.125 s.
#   1080p: build/aroll.mp4   -> film/assets/video/aroll.mp4
#   4k:    build4k/aroll.mp4 -> film/assets/video/aroll4k.mp4   (index.html plays this one)
import subprocess, sys
import numpy as np, cv2

K4 = len(sys.argv) > 1 and sys.argv[1] == '4k'
W, H = (3840, 2160) if K4 else (1920, 1080)
SRC, DST = ('build4k/aroll.mp4', 'film/assets/video/aroll4k.mp4') if K4 else ('build/aroll.mp4', 'film/assets/video/aroll.mp4')
DESCENT = (57.5, 68.125)

y, x = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H * 0.45) / (H * 0.62)) ** 2)
vig = np.clip((r - 0.55) / 0.6, 0, 1) ** 1.6 * 0.42
bot = np.clip((y - H * 0.556) / (H * 0.444), 0, 1) ** 1.5 * 0.5
a = 1 - (1 - vig) * (1 - bot)
img = np.zeros((H, W, 4), np.uint8)
img[..., 3] = (a * 255).astype(np.uint8)
png = f'build/vignette{"4k" if K4 else ""}.png'
cv2.imwrite(png, img)

on = f"enable='between(t,{DESCENT[0]},{DESCENT[1]})'"
fc = (f"[0:v]eq=saturation=0.6:brightness=-0.03:contrast=1.05:{on},colorbalance=bs=0.03:bm=0.015:rs=-0.02:{on}[v];"
      "[v][1:v]overlay=0:0:shortest=1,format=yuv420p[o]")
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', SRC, '-loop', '1', '-i', png, '-filter_complex', fc, '-map', '[o]', '-an',
                '-c:v', 'libx264', '-crf', '16' if K4 else '15', '-preset', 'medium', '-threads', '4', '-g', '24', '-bf', '0',
                '-r', '24', DST], check=True)
print('wrote', DST)
