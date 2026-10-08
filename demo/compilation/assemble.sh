#!/bin/bash
# Joins all rendered clips, their SFX, and the ducked music bed into the final compilation.
set -e
cd "$(dirname "$0")"
CLIPS="1 2 3 4 5 10 20 30 50 100"
: > concat_v.txt; : > concat_a.txt
for n in $CLIPS; do
  d=clips/c$n
  ffmpeg -loglevel error -y -framerate 30 -i $d/frames/%04d.png \
    -vf "scale=1080:1920:flags=lanczos" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p $d/video.mp4
  echo "file '$d/video.mp4'" >> concat_v.txt
  echo "file '$d/sfx.wav'" >> concat_a.txt
done
ffmpeg -loglevel error -y -f concat -safe 0 -i concat_v.txt -c copy all_video.mp4
ffmpeg -loglevel error -y -f concat -safe 0 -i concat_a.txt -c pcm_s16le all_sfx.wav
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 all_video.mp4)
./venv/bin/python music.py "$DUR" music.wav
# music sits under the SFX and ducks a little whenever the effects hit
ffmpeg -loglevel error -y -i all_sfx.wav -i music.wav -filter_complex \
  "[1:a]volume=0.4[m];[0:a]asplit[s1][s2];[m][s1]sidechaincompress=threshold=0.06:ratio=3:attack=5:release=300[md];\
   [s2][md]amix=inputs=2:normalize=0,alimiter=limit=0.8[a]" -map "[a]" -c:a pcm_s16le mix.wav
ffmpeg -loglevel error -y -i all_video.mp4 -i mix.wav -c:v copy -af volume=-1.5dB -c:a aac -b:a 192k -shortest -movflags +faststart pasteque_compilation.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 pasteque_compilation.mp4
