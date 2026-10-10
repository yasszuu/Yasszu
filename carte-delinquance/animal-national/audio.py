"""Animal national : voix + musique énergique (128 BPM) + bruitages (whoosh aux balayages, pop aux révélations, carillon licorne)."""
import json, subprocess, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt, fftconvolve
SR = 44100; DUR = 21.6; N = int(DUR*SR); rng = np.random.default_rng(3)
L = json.load(open('lines.json'))
def read(p):
    raw = subprocess.run(["ffmpeg","-loglevel","error","-i",p,"-ac","1","-ar",str(SR),"-f","f32le","-"],capture_output=True,check=True).stdout
    return np.frombuffer(raw, np.float32).copy()
vo = np.zeros(N, np.float32); v = read('assets/voix.mp3'); vo[:len(v)] = v[:N]; sf.write('vo.wav', vo, SR)
def load(p):
    x, sr = sf.read(p, dtype='float32'); x = x.mean(1) if x.ndim > 1 else x
    if sr != SR: x = resample_poly(x, SR, sr).astype(np.float32)
    return x/(np.abs(x).max() + 1e-9)*0.8
B = {k: load(f'../sterne/ep/assets/s_{k}.wav') for k in ('pop', 'woosh', 'impact')}
tt = np.arange(int(1.6*SR))/SR
B['chime'] = sum(np.sin(2*np.pi*f*tt)*np.exp(-tt*(3 + i)) for i, f in enumerate([1568, 2093, 2637, 3136, 4186]))*0.25
fx = np.zeros(N, np.float32)
def add(k, t, g):
    x = B[k]*g; i = int(t*SR); fx[i:i+len(x)] += x[:max(0, N-i)]
ON = [l['on'] for l in L]
def ANI(i):
    g = L[i]['gaps']; return max(g, key=lambda a: a[1]-a[0])[1] if g else L[i]['on']
add('impact', 0.02, 0.6); add('woosh', 0.0, 0.6)
for i in range(6): add('pop', 0.25 + i*0.14, 0.35)
for i in range(1, 8):
    add('woosh', ON[i] + 0.12 - 0.5, 0.7); add('pop', ANI(i) - 0.03, 0.55)
add('chime', ANI(7) - 0.05, 0.9); add('woosh', ON[8] - 0.2, 0.6); add('pop', ANI(8) - 0.1, 0.5)
sf.write('sfx.wav', fx, SR)
lp = lambda x, f: sosfilt(butter(2, f, 'lowpass', fs=SR, output='sos'), x)
hp = lambda x, f: sosfilt(butter(2, f, 'highpass', fs=SR, output='sos'), x)
bpm = 128; beat = 60/bpm; bar = 4*beat; A = 55.0
PROG = [(0, [0, 3, 7]), (8, [0, 4, 7]), (3, [0, 4, 7]), (10, [0, 4, 7])]
mus = np.zeros(N)
for b in range(int(DUR/bar) + 2):
    t0 = b*bar; i0 = int(t0*SR); root, iv = PROG[b % 4]; n = int(bar*SR) + int(0.4*SR); tl = np.arange(n)/SR
    f0 = A*2**(root/12); env = np.clip(tl/0.05, 0, 1)*np.clip((bar + 0.4 - tl)/0.4, 0, 1)
    seg = lp(sum(sum(np.sin(2*np.pi*f0*4*2**(s/12)*h*tl)/h for h in range(1, 5)) for s in iv)/3, 2500)*env*0.05
    for k in range(8):                                         # basse en croches
        st = int(k*beat/2*SR); tn = np.arange(int(beat/2*SR))/SR
        bs = lp(np.sign(np.sin(2*np.pi*f0*2*tn)), 600)*np.exp(-tn*6)*0.10; e = min(len(bs), n - st); seg[st:st+e] += bs[:e]
    for k in range(4):                                         # kick 4/4 + hi-hat
        st = int(k*beat*SR); tn = np.arange(int(0.35*SR))/SR
        kk = np.sin(2*np.pi*np.cumsum(50 + 120*np.exp(-tn*35))/SR)*np.exp(-tn*9)*0.35; seg[st:st+len(kk)] += kk
        sh = int((k + 0.5)*beat*SR); hh = hp(rng.standard_normal(int(0.08*SR)), 7000)*np.exp(-np.arange(int(0.08*SR))/SR*60)*0.06; seg[sh:sh+len(hh)] += hh
        if k in (1, 3): sn = hp(rng.standard_normal(len(tn)), 1500)*np.exp(-tn*22)*0.12; seg[st:st+len(sn)] += sn
    e = min(n, N - i0)
    if e > 0: mus[i0:i0+e] += seg[:e]
t = np.arange(N)/SR; mus *= np.clip(t/0.3, 0, 1)*np.clip((DUR - t)/1.0, 0, 1)
sf.write('music.wav', (mus/np.abs(mus).max()*0.6).astype(np.float32), SR)
print('ok')
