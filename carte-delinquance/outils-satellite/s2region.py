"""Mosaïque Sentinel-2 d'une grande région : pour chaque tuile MGRS, médiane de quelques scènes claires (saison sèche),
lue en aperçu basse résolution, puis reprojetée et fondue dans une texture équirectangulaire.
usage: s2region.py out.npz lon0 lon1 lat0 lat1 pxdeg ovl"""
import sys, os, json, re, time, threading, urllib.request, numpy as np, concurrent.futures as cf
os.environ.setdefault('CURL_CA_BUNDLE', '/root/.ccr/ca-bundle.crt'); os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'
import rasterio, mgrs
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
from scipy.ndimage import distance_transform_edt
B = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
out, lon0, lon1, lat0, lat1, pxd, ovl = sys.argv[1], *map(float, sys.argv[2:7]), int(sys.argv[7])
NS = int(os.environ.get('NS', 3)); CMAX = float(os.environ.get('CMAX', 25)); USE_SCL = os.environ.get('SCL') == '1'; os.makedirs('cache', exist_ok=True)
import requests
TLS = threading.local()
def get(u):
    if not hasattr(TLS, 's'): TLS.s = requests.Session(); TLS.s.verify = '/root/.ccr/ca-bundle.crt'
    for k in range(5):
        try:
            r = TLS.s.get(u, timeout=60); r.raise_for_status(); return r.content
        except Exception:
            if k == 4: raise
            time.sleep(2**k)
def ls(prefix): return re.findall(r"<Prefix>([^<]+)</Prefix>", get(f"{B}/?list-type=2&prefix={prefix}&delimiter=/").decode())[1:]
def scenes(t):
    cfn = f'cache/{t}_{os.environ.get("MONTHS", "")}_{NS}_{CMAX}.json'
    if os.path.exists(cfn): return json.load(open(cfn))
    z, b, sq = t[:2], t[2], t[3:]; res = []
    for y in ("2023", "2024"):
        for mo in os.environ.get("MONTHS", "1,2,3,11,12").split(","):
            for s in ls(f"sentinel-s2-l2a-cogs/{z}/{b}/{sq}/{y}/{mo}/"):
                sid = s.rstrip('/').split('/')[-1]
                try: p = json.loads(get(f"{B}/{s}{sid}.json"))['properties']
                except Exception: continue
                nd = p.get('s2:nodata_pixel_percentage', 0)
                if nd < 40: res.append((p.get('eo:cloud_cover', 100) + nd*0.05, s))
    res.sort(); r = [s for c, s in res[:NS] if c < CMAX]; json.dump(r, open(cfn, 'w')); return r
m = mgrs.MGRS(); tiles = sorted({m.toMGRS(la, lo, MGRSPrecision=0) for la in np.arange(lat0 + 0.1, lat1, 0.2) for lo in np.arange(lon0 + 0.1, lon1, 0.2)})
exist = set()
for zb in sorted({t[:3] for t in tiles}): exist |= {zb + p.rstrip("/").split("/")[-1] for p in ls(f"sentinel-s2-l2a-cogs/{zb[:2]}/{zb[2]}/")}
tiles = [t for t in tiles if t in exist]
print(len(tiles), 'tuiles MGRS candidates', flush=True)
W, H = int(round((lon1 - lon0)*pxd)), int(round((lat1 - lat0)*pxd)); dst_t = from_origin(lon0, lat1, 1/pxd, 1/pxd)
ACC = np.zeros((H, W, 3), np.float32); WT = np.zeros((H, W), np.float32); lock = threading.Lock(); done = [0]
def work(t):
    ss = scenes(t)
    if not ss: return
    arrs = []
    for s in ss:
        try:
            with rasterio.open(f"{B}/{s}TCI.tif", overview_level=ovl) as src: a = src.read(); tr, crs = src.transform, src.crs
            if USE_SCL:
                with rasterio.open(f"{B}/{s}SCL.tif", overview_level=ovl - 1) as src: c = src.read(1)
                if c.shape != a.shape[1:]: c = np.asarray(__import__('PIL.Image').Image.fromarray(c).resize(a.shape[:0:-1], 0))
                a = a*np.isin(c, [2, 4, 5, 6, 7, 11])[None]
            arrs.append(a)
        except Exception: pass
    if not arrs: return
    st = np.stack(arrs).astype(np.float32); st[st == 0] = np.nan
    if len(arrs) >= 3 and not USE_SCL:
        br = np.nanmean(st, 1); med = np.nanmedian(br, 0); st[np.broadcast_to((br > med + 25)[:, None], st.shape)] = np.nan
    with np.errstate(all='ignore'): img = np.nanmedian(st, 0)
    ok = ~np.isnan(img[0]); img = np.nan_to_num(img)
    w = np.clip(distance_transform_edt(ok)/40, 0, 1).astype(np.float32)          # fondu aux bords de la tuile
    # fenêtre de destination
    from rasterio.warp import transform_bounds
    b = transform_bounds(crs, 'EPSG:4326', tr.c, tr.f + tr.e*img.shape[1], tr.c + tr.a*img.shape[2], tr.f)
    x0, x1 = max(0, int((b[0] - lon0)*pxd) - 2), min(W, int((b[2] - lon0)*pxd) + 2); y0, y1 = max(0, int((lat1 - b[3])*pxd) - 2), min(H, int((lat1 - b[1])*pxd) + 2)
    if x1 <= x0 or y1 <= y0: return
    wt = from_origin(lon0 + x0/pxd, lat1 - y0/pxd, 1/pxd, 1/pxd)
    d = np.zeros((4, y1 - y0, x1 - x0), np.float32)
    reproject(np.concatenate([img, w[None]*255]).astype(np.float32), d, src_transform=tr, src_crs=crs, dst_transform=wt, dst_crs='EPSG:4326', resampling=Resampling.bilinear, src_nodata=None)
    a = d[3]/255
    with lock:
        ACC[y0:y1, x0:x1] += d[:3].transpose(1, 2, 0)*a[..., None]; WT[y0:y1, x0:x1] += a; done[0] += 1
        if done[0] % 20 == 0: print(done[0], 'tuiles', flush=True)
with cf.ThreadPoolExecutor(48) as ex: list(ex.map(work, tiles))
ok = WT > 0.05; img = np.where(ok[..., None], ACC/np.maximum(WT, 1e-6)[..., None], 0).astype(np.uint8)
np.savez(out, img=img, ok=ok, box=np.array([lon0, lon1, lat0, lat1, pxd]))
print('ok', W, H, ok.mean())
