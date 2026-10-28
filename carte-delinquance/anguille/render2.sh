#!/bin/sh
cd "$(dirname "$0")"
for S in sargasses abysse; do SHOT=$S ../bl/bin/python eel.py clips/$S 0 138 16 50 > r_$S.log 2>&1; done
for S in sargasses riviere abysse; do ffmpeg -loglevel error -y -framerate 30 -i clips/$S/%04d.jpg -vf "scale=1080:1920:flags=lanczos" -c:v libx264 -crf 20 -pix_fmt yuv420p $S.mp4; done
ffmpeg -loglevel error -y -f concat -safe 0 -i l.txt -vf scale=720:1280 -c:v libx264 -crf 24 -pix_fmt yuv420p -movflags +faststart plans-3d-anguille.mp4
echo done > r2.done
