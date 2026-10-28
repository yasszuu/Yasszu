"""Construit une vidéo « carte + drapeaux » à partir de cfg.json : alignement voix, géographie, drapeaux, page, audio.
Usage (depuis le dossier de la vidéo) : python3 ../tpl/make.py [align|geo|page|audio]"""
import json, sys, subprocess, os, numpy as np
SR = 44100; CFG = json.load(open('cfg.json')); OFFS = CFG['offset']
step = sys.argv[1]
if step == 'align':
    open('audio_head.py', 'w').write('SR = 44100\nSCRIPT = ' + repr([(f"s{i:02d}", "", l) for i, l in enumerate(CFG['script'])]) + '\n')
    if not os.path.exists('sherpa-onnx-whisper-small'): os.symlink('../sterne/ep/sherpa-onnx-whisper-small', 'sherpa-onnx-whisper-small')
    subprocess.run(['python3', '../animal/align.py'], check=True)
    raw = subprocess.run(["ffmpeg","-loglevel","error","-i","assets/voix.mp3","-ac","1","-ar",str(SR),"-f","f32le","-"],capture_output=True,check=True).stdout
    x = np.frombuffer(raw, np.float32); hop = int(0.01*SR); rms = np.sqrt(np.convolve(x**2, np.ones(hop)/hop, "same"))[::hop]
    sil = rms < max(0.004, np.percentile(rms, 95)*0.04); out = []
    for a, b in json.load(open('vo_bounds.json')):
        a0, b0 = a//hop, b//hop; seg = sil[a0:b0]; nz = np.where(~seg)[0]; runs = []; i = 0
        while i < len(seg):
            if seg[i]:
                j = i
                while j < len(seg) and seg[j]: j += 1
                if 0 < i and j < len(seg) and (j - i) >= 6: runs.append([round((a0+i)*0.01 + OFFS, 2), round((a0+j)*0.01 + OFFS, 2)])
                i = j
            else: i += 1
        out.append({"on": round((a0+nz[0])*0.01 + OFFS, 2), "off": round((a0+nz[-1])*0.01 + OFFS, 2), "gaps": runs})
    json.dump(out, open('lines.json', 'w')); [print(o) for o in out]
elif step == 'geo':
    import shapefile
    r = shapefile.Reader('../animal/ne/ne_10m_admin_0_map_units.shp'); f = [x[0] for x in r.fields[1:]]
    rows = [(dict(zip(f, s.record)), s.shape) for s in r.iterShapeRecords()]
    def parts(sh):
        p = sh.points; idx = list(sh.parts) + [len(p)]; return [p[idx[i]:idx[i+1]] for i in range(len(idx) - 1)]
    def area(q): return abs(sum(q[i][0]*q[i+1][1] - q[i+1][0]*q[i][1] for i in range(len(q) - 1)))/2
    def rings(sh, minA, lonmin=-180, lonmax=180):
        o = []
        for q in parts(sh):
            xs = [p[0] for p in q]
            if max(xs) - min(xs) > 180 or min(xs) < lonmin or max(xs) > lonmax or area(q) < minA: continue
            o.append([[round(a, 3), round(b, 3)] for a, b in q])
        return o
    U = {d['GEOUNIT']: s for d, s in rows}
    G = {c['id']: rings(U[c['unit']], c.get('minA', 0.003), *c.get('lonr', [-180, 180])) for c in CFG['countries']}
    B = []
    for d, s in rows: B += rings(s, 0.08)
    json.dump({'c': G, 'b': B}, open('geo.json', 'w'), separators=(',', ':'))
    os.makedirs('flags', exist_ok=True)
    for c in CFG['countries']: subprocess.run(['cp', f"../animal/pkg/package/flags/4x3/{c['flag']}.svg", 'flags/'], check=True)
    print({k: len(v) for k, v in G.items()}, len(B))
elif step == 'page':
    L = json.load(open('lines.json')); page = {k: v for k, v in CFG.items() if k not in ('script',)}
    open('page.html', 'w').write(open('../tpl/page.html').read().replace('__LINES__', json.dumps(L)).replace('__CFG__', json.dumps(page, ensure_ascii=False)))
    s = open('../animal/snap.js').read().replace('/animal/page.html', '/' + os.path.basename(os.getcwd()) + '/page.html'); open('snap.js', 'w').write(s)
    if not os.path.exists('mktiles.py'): subprocess.run(['cp', '../animal/mktiles.py', '.'], check=True)
elif step == 'audio':
    from scipy.signal import resample_poly, butter, sosfilt
    import soundfile as sf
    DUR = CFG['dur']; N = int(DUR*SR); rng = np.random.default_rng(5); L = json.load(open('lines.json'))
    def read(p, ss=None, t=None):
        cmd = ["ffmpeg", "-loglevel", "error"] + (["-ss", str(ss), "-t", str(t)] if ss is not None else []) + ["-i", p, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"]
        return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).copy()
    vo = np.zeros(N, np.float32); v = read('assets/voix.mp3'); i0 = int(OFFS*SR); vo[i0:i0+len(v)] = v[:N-i0]; sf.write('vo.wav', vo, SR)
    fx = np.zeros(N, np.float32)
    if CFG.get('cry'):
        c = CFG['cry']; x = read(c['file'], c['ss'], c['t']); x *= np.clip((c['t'] - np.arange(len(x))/SR)/0.12, 0, 1); fx[:len(x)] += x/np.abs(x).max()*0.9
    def load(p):
        x, sr = sf.read(p, dtype='float32'); x = x.mean(1) if x.ndim > 1 else x
        if sr != SR: x = resample_poly(x, SR, sr).astype(np.float32)
        return x/(np.abs(x).max() + 1e-9)*0.8
    B = {k: load(f'../sterne/ep/assets/s_{k}.wav') for k in ('pop', 'woosh', 'impact')}
    def add(k, t, g):
        x = B[k]*g; i = int(t*SR); fx[i:i+len(x)] += x[:max(0, N-i)]
    ON = [l['on'] for l in L]; NC = len(CFG['countries'])
    def ANI(i):
        g = L[i]['gaps']; return max(g, key=lambda a: a[1]-a[0])[1] if g else L[i]['on']
    if not CFG.get('cry'): add('impact', 0.05, 0.6); add('woosh', 0.0, 0.5)
    for i in range(1, NC + 1): add('woosh', ON[i] + 0.12 - 0.5, 0.65); add('pop', ANI(i) - 0.03, 0.55)
    add('impact', ANI(NC) - 0.03, 0.5); add('woosh', ON[NC + 1] - 0.2, 0.6); add('pop', ANI(NC + 1) - 0.1, 0.5)
    sf.write('sfx.wav', fx, SR)
    lp = lambda x, f: sosfilt(butter(2, f, 'lowpass', fs=SR, output='sos'), x)
    hp = lambda x, f: sosfilt(butter(2, f, 'highpass', fs=SR, output='sos'), x)
    bpm = 124; beat = 60/bpm; bar = 4*beat; A = 55.0*2**(CFG.get('key', 2)/12)
    PROG = [(0, [0, 4, 7]), (7, [0, 4, 7]), (9, [0, 3, 7]), (5, [0, 4, 7])]
    mus = np.zeros(N)
    for b in range(int(DUR/bar) + 2):
        t0 = b*bar; j0 = int(t0*SR); root, iv = PROG[b % 4]; n = int(bar*SR) + int(0.4*SR); tl = np.arange(n)/SR
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
        e = min(n, N - j0)
        if e > 0: mus[j0:j0+e] += seg[:e]
    t = np.arange(N)/SR; mus *= np.clip((t - CFG.get('music_in', 0.0))/0.4, 0, 1)*np.clip((DUR - t)/1.0, 0, 1)
    sf.write('music.wav', (mus/np.abs(mus).max()*0.6).astype(np.float32), SR)
    subprocess.run(['sh', '../animal/mix.sh'], check=True); print('audio ok')
