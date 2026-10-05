#!/bin/sh
# voix compressée + bruitages + musique (ducking sous la voix), normalisé à -14 LUFS
ffmpeg -loglevel error -y -i vo.wav -i sfx.wav -i music.wav -filter_complex "
[0]highpass=f=90,acompressor=threshold=-20dB:ratio=2:attack=10:release=120:makeup=2dB,equalizer=f=3500:t=q:w=1:g=1,asplit=2[v][sc];
[2]volume=0.275[m];[m][sc]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=300[md];
[1]volume=0.4[s];
[v][s][md]amix=inputs=3:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[out]" -map "[out]" -ar 44100 -ac 2 mix.wav
ffmpeg -loglevel error -y -i mix.wav -c:a aac -b:a 160k mix.m4a
# 2e passe : remonte exactement à -14 LUFS avec limiteur
I=$(ffmpeg -i mix.wav -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1 | awk '{print $2}')
G=$(python3 -c "print(-14-($I))")
ffmpeg -loglevel error -y -i mix.wav -af "volume=${G}dB,alimiter=limit=0.89:level=false" -ar 44100 mix2.wav && mv mix2.wav mix.wav
ffmpeg -loglevel error -y -i mix.wav -c:a aac -b:a 160k mix.m4a
