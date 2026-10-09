"""Après les plans 3D : recalcule les images de carte qui contiennent un plan 3D, puis assemble la vidéo."""
import json, os, math, subprocess, time
TL = json.load(open('timeline.json'))
while not os.path.exists('../r3d.done'): time.sleep(20)
rng = []
for c in TL['clips']:
    a, b = int(math.floor(c['a']*30)) - 1, int(math.ceil(c['b']*30)) + 1
    for f in range(a, b + 1):
        p = f'frames/{f:05d}.jpg'
        if os.path.exists(p): os.remove(p)
    rng.append((a, b + 1))
procs = [subprocess.Popen(['node', 'render_par.js', str(a), str(b)]) for a, b in rng]
for p in procs: p.wait()
subprocess.run('ffmpeg -loglevel error -y -framerate 30 -i frames/%05d.jpg -i mix.m4a -c:v libx264 -preset medium -crf 21 -maxrate 7M -bufsize 14M '
               '-pix_fmt yuv420p -c:a copy -shortest -movflags +faststart la-sterne-arctique.mp4', shell=True, check=True)
subprocess.run('ffmpeg -loglevel error -y -i la-sterne-arctique.mp4 -vf scale=720:1280 -c:v libx264 -crf 26 -preset medium -c:a aac -b:a 128k '
               '-movflags +faststart la-sterne-arctique-apercu.mp4', shell=True, check=True)
open('finish.done', 'w').write('ok')
