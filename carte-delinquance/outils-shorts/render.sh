# usage: sh render.sh <dossier> <nom-fichier>  → rend toutes les images (4 workers) puis encode
cd $1
N=$(python3 -c "import json;print(int(json.load(open('timeline.json'))['duration']*30))"); q=$((N/4+1))
for i in 0 1 2 3; do a=$((i*q)); b=$(( (i+1)*q < N ? (i+1)*q : N )); node snap.js frames $a $b > log_$a.txt 2>&1 & done; wait
python3 - <<'PY'
import os, numpy as np
from PIL import Image
bad = []
for f in sorted(os.listdir('frames')):
    try:
        im = Image.open('frames/' + f); im.load()
        if np.asarray(im.resize((54, 96))).mean() < 8: bad.append(f)
    except Exception: bad.append(f)
for f in bad: os.remove('frames/' + f)
print('bad', bad)
PY
for i in 0 1 2 3; do a=$((i*q)); b=$(( (i+1)*q < N ? (i+1)*q : N )); node snap.js frames $a $b > logb_$a.txt 2>&1 & done; wait
ffmpeg -y -loglevel error -framerate 30 -i frames/%05d.jpg -i mix.m4a -map 0:v -map 1:a -c:v libx264 -preset medium -crf 20 -maxrate 8M -bufsize 16M -pix_fmt yuv420p -c:a copy -shortest -movflags +faststart $2.mp4
ffmpeg -y -loglevel error -i $2.mp4 -vf scale=720:-2 -c:v libx264 -crf 26 -c:a aac -b:a 128k -movflags +faststart $2-apercu.mp4
echo DONE $1
