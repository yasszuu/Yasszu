"""Après les plans 3D et la carte : rend les images qui contiennent un plan 3D, puis assemble la vidéo (+ aperçu)."""
import json, os, math, subprocess, time
TL = json.load(open('timeline.json'))
while not (os.path.exists('../../gombe3d/r3d.done') and os.path.exists('frames.done')): time.sleep(30)
rng = [(int(math.floor(c['a']*30)) - 1, int(math.ceil(c['b']*30)) + 2) for c in TL['clips']]
procs = [subprocess.Popen(['node', 'snap.js', 'frames', str(a), str(b)]) for a, b in rng]
for p in procs: p.wait()
n = int(TL['duration']*30)
missing = [i for i in range(n) if not os.path.exists(f'frames/{i:05d}.jpg')]
if missing: subprocess.run(['node', 'snap.js', 'frames', str(min(missing)), str(max(missing) + 1)])
subprocess.run('ffmpeg -loglevel error -y -framerate 30 -i frames/%05d.jpg -i mix.m4a -c:v libx264 -preset slow -crf 20 -maxrate 8M -bufsize 16M '
               '-pix_fmt yuv420p -c:a copy -shortest -movflags +faststart la-guerre-des-chimpanzes.mp4', shell=True, check=True)
subprocess.run('ffmpeg -loglevel error -y -i la-guerre-des-chimpanzes.mp4 -vf scale=720:1280 -c:v libx264 -crf 25 -preset medium -c:a aac -b:a 128k '
               '-movflags +faststart la-guerre-des-chimpanzes-apercu.mp4', shell=True, check=True)
open('finish.done', 'w').write('ok')
