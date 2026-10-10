"""Découpe la voix en répliques : silences candidats -> morceaux transcrits (Whisper) -> alignement DP sur le script."""
import numpy as np, subprocess, json, re, unicodedata, sherpa_onnx, soundfile as sf, difflib
from scipy.signal import resample_poly
SR = 44100
exec(open('audio_head.py').read())
raw = subprocess.run(["ffmpeg","-loglevel","error","-i","assets/voix.mp3","-ac","1","-ar",str(SR),"-f","f32le","-"],capture_output=True,check=True).stdout
x = np.frombuffer(raw, np.float32).copy()
hop = int(0.02*SR); rms = np.sqrt(np.convolve(x**2, np.ones(hop)/hop, "same"))[::hop]
sil = rms < max(0.004, np.percentile(rms, 95)*0.03)
runs, i = [], 0
while i < len(sil):
    if sil[i]:
        j = i
        while j < len(sil) and sil[j]: j += 1
        if i > 0 and j < len(sil) and (j - i)*0.02 >= 0.12: runs.append(((i + j)//2*hop, (j - i)*0.02))
        i = j
    else: i += 1
cuts = [0] + [c for c, _ in runs] + [len(x)]
d = 'sherpa-onnx-whisper-small'
r = sherpa_onnx.OfflineRecognizer.from_whisper(encoder=f'{d}/small-encoder.int8.onnx', decoder=f'{d}/small-decoder.int8.onnx', tokens=f'{d}/small-tokens.txt', language='fr', task='transcribe', num_threads=4)
chunks = []
for a, b in zip(cuts[:-1], cuts[1:]):
    seg = resample_poly(x[a:b], 16000, SR).astype('float32'); s = r.create_stream(); s.accept_waveform(16000, seg); r.decode_stream(s)
    chunks.append((a, b, s.result.text))
norm = lambda s: re.sub(r'[^a-z0-9 ]', ' ', unicodedata.normalize('NFKD', s.lower()).encode('ascii', 'ignore').decode()).split()
lines = [norm(c.replace('*', '')) for _, _, c in SCRIPT]
# DP : chaque réplique = suite contiguë de morceaux ; coût = 1 - similarité
n, m = len(chunks), len(lines); INF = 1e9
cost = lambda i, j, k: 1 - difflib.SequenceMatcher(None, ' '.join(sum((norm(chunks[q][2]) for q in range(i, j)), [])), ' '.join(lines[k])).ratio()
dp = [[INF]*(m + 1) for _ in range(n + 1)]; bk = {}; dp[0][0] = 0
for j in range(1, n + 1):
    for k in range(1, m + 1):
        for i in range(max(0, j - 6), j):
            v = dp[i][k-1] + cost(i, j, k - 1)
            if v < dp[j][k]: dp[j][k] = v; bk[(j, k)] = i
j, k, seg = n, m, []
while k > 0: i = bk[(j, k)]; seg.append((i, j)); j, k = i, k - 1
seg = seg[::-1]
bounds = [(chunks[i][0], chunks[j-1][1]) for i, j in seg]
for (a, b), (i, j), (sid, _, c) in zip(bounds, seg, SCRIPT):
    print(sid, round(a/SR, 2), round(b/SR, 2), '|', ' '.join(chunks[q][2] for q in range(i, j))[:90])
json.dump([[a, b] for a, b in bounds], open('vo_bounds.json', 'w'))
