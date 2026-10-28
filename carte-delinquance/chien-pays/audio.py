"""Le chien dans chaque pays : aboiement (intro seulement) + voix décalée de 0,9 s + musique 128 BPM + bruitages."""
import json, subprocess, numpy as np, soundfile as sf
from scipy.signal import resample_poly, butter, sosfilt
SR = 44100; DUR = 25.2; N = int(DUR*SR); rng = np.random.default_rng(5); OFFS = 0.9
L = json.load(open('lines.json'))
def read(p, ss=None, t=None):
    cmd = ["ffmpeg", "-loglevel", "error"] + (["-ss", str(ss), "-t", str(t)] if ss is not None else []) + ["-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()
vo = np.zeros(N, np.float32); v = read('assets/voix.mp3'); i0 = int(OFFS*SR); vo[i0:i0+len(v)] = v[:N-i0]; sf.write('vo.wav', vo, SR)
fx = np.zeros(N, np.float32)
bark = read('assets/aboiement.mp3', 0.0, 0.95); bark *= np.clip((0.95 - np.arange(len(bark))/SR)/0.12, 0, 1); bark = bark/np.abs(bark).max()*0.9
fx[:len(bark)] += bark
def load(p):
    x, sr = sf.read(p, dtype='float32'); x = x.mean(1) if x.ndim > 1 else x
    if sr != SR: x = resample_poly(x, SR, sr).astype(np.float32)
    return x/(np.abs(x).max() + 1e-9)*0.8
B = {k: load(f'../sterne/ep/assets/s_{k}.wav') for k in ('pop', 'woosh', 'impact')}
def add(k, t, g):
    x = B[k]*g; i = int(t*SR); fx[i:i+len(x)] += x[:max(0, N-i)]
ON = [l['on'] for l in L]
def ANI(i):
    g = L[i]['gaps']; return max(g, key=lambda a: a[1]-a[0])[1] if g else L[i]['on']
for i in range(6): add('pop', ON[0] + 0.2 + i*0.14, 0.3)
for i in range(1, 9):
    add('woosh', ON[i] + 0.12 - 0.5, 0.65); add('pop', ANI(i) - 0.03, 0.5); add('pop', ANI(i) + 0.29, 0.4)
add('impact', ANI(8) - 0.03, 0.5); add('woosh', ON[9] - 0.2, 0.6); add('pop', ANI(9) - 0.1, 0.5)
sf.write('sfx.wav', fx, SR)
lp = lambda x, f: sosfilt(butter(2, f, 'lowpass', fs=SR, output='sos'), x)
hp = lambda x, f: sosfilt(butter(2, f, 'highpass', fs=SR, output='sos'), x)
bpm = 128; beat = 60/bpm; bar = 4*beat; A = 55.0*2**(2/12)
PROG = [(0, [0, 4, 7]), (7, [0, 4, 7]), (9, [0, 3, 7]), (5, [0, 4, 7])]          # B majeur, ambiance légère
mus = np.zeros(N)
for b in range(int(DUR/bar) + 2):
    t0 = b*bar; i0 = int(t0*SR); root, iv = PROG[b % 4]; n = int(bar*SR) + int(0.4*SR); tl = np.arange(n)/SR
    f0 = A*2**(root/12); env = np.clip(tl/0.05, 0, 1)*np.clip((bar + 0.4 - tl)/0.4, 0, 1)
    seg = lp(sum(sum(np.sin(2*np.pi*f0*4*2**(s/12)*h*tl)/h for h in range(1, 5)) for s in iv)/3, 2500)*env*0.045
    for k in range(8):
        st = int(k*beat/2*SR); tn = np.arange(int(beat/2*SR))/SR; f = f0*8*2**(iv[k % 3]/12)
        pl = sum(np.sin(2*np.pi*f*h*tn)/h*np.exp(-tn*(10 + 4*h)) for h in range(1, 4))*0.05; e = min(len(pl), n - st); seg[st:st+e] += pl[:e]
        bs = lp(np.sign(np.sin(2*np.pi*f0*2*tn)), 600)*np.exp(-tn*6)*0.09; seg[st:st+e] += bs[:e]
    for k in range(4):
        st = int(k*beat*SR); tn = np.arange(int(0.35*SR))/SR
        kk = np.sin(2*np.pi*np.cumsum(50 + 120*np.exp(-tn*35))/SR)*np.exp(-tn*9)*0.33; seg[st:st+len(kk)] += kk
        sh = int((k + 0.5)*beat*SR); hh = hp(rng.standard_normal(int(0.08*SR)), 7000)*np.exp(-np.arange(int(0.08*SR))/SR*60)*0.06; seg[sh:sh+len(hh)] += hh
        if k in (1, 3): sn = hp(rng.standard_normal(len(tn)), 1500)*np.exp(-tn*22)*0.11; seg[st:st+len(sn)] += sn
    e = min(n, N - i0)
    if e > 0: mus[i0:i0+e] += seg[:e]
t = np.arange(N)/SR; mus *= np.clip((t - 0.6)/0.4, 0, 1)*np.clip((DUR - t)/1.0, 0, 1)          # la musique démarre après l'aboiement
sf.write('music.wav', (mus/np.abs(mus).max()*0.6).astype(np.float32), SR)
print('ok')
