#!/bin/bash
# Joins the tower clips with their SFX and the cute music bed (ducked under the effects).
set -e
cd "$(dirname "$0")"
PY=../venv/bin/python
: > concat_v.txt; : > concat_a.txt
for n in 1 3 5 10 20 30 50; do
  d=clips/t$n
  ffmpeg -loglevel error -y -framerate 30 -i $d/frames/%04d.png \
    -vf "scale=1080:1920:flags=lanczos" -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p $d/video.mp4
  echo "file '$d/video.mp4'" >> concat_v.txt
  echo "file '$d/sfx.wav'" >> concat_a.txt
done
ffmpeg -loglevel error -y -f concat -safe 0 -i concat_v.txt -c copy all_video.mp4
ffmpeg -loglevel error -y -f concat -safe 0 -i concat_a.txt -c pcm_s16le all_sfx.wav
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 all_video.mp4)
$PY music_cute.py "$DUR" music.wav
ffmpeg -loglevel error -y -i all_sfx.wav -i music.wav -filter_complex \
  "[1:a]volume=0.32[m];[0:a]asplit[s1][s2];[m][s1]sidechaincompress=threshold=0.06:ratio=3:attack=5:release=300[md];\
   [s2][md]amix=inputs=2:normalize=0,alimiter=limit=0.8[a]" -map "[a]" -c:a pcm_s16le mix.wav
ffmpeg -loglevel error -y -i all_video.mp4 -i mix.wav -c:v copy -af volume=-1.5dB -c:a aac -b:a 192k \
  -shortest -movflags +faststart gummy_tower.mp4
ffmpeg -loglevel error -y -i gummy_tower.mp4 -c:v libx264 -preset slow -crf 23 -maxrate 3.2M -bufsize 6M \
  -pix_fmt yuv420p -c:a copy -movflags +faststart gummy_tower_light.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 gummy_tower.mp4
