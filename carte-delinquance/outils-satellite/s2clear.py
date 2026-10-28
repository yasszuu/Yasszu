"""Mosaïque sans nuages pour une petite zone très nuageuse : masque SCL (classification Sentinel-2) par scène,
médiane des pixels clairs sur beaucoup de scènes.  usage: s2clear.py out.npz lon0 lon1 lat0 lat1 pxdeg NSCENES"""
import sys, os, json, re, time, threading, numpy as np, concurrent.futures as cf, requests, mgrs
os.environ.setdefault('CURL_CA_BUNDLE', '/root/.ccr/ca-bundle.crt'); os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
B = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
out, lon0, lon1, lat0, lat1, pxd = sys.argv[1], *map(float, sys.argv[2:7]); NS = int(sys.argv[7])
TLS = threading.local()
def get(u):
    if not hasattr(TLS, 's'): TLS.s = requests.Session(); TLS.s.verify = '/root/.ccr/ca-bundle.crt'
    for k in range(5):
        try: r = TLS.s.get(u, timeout=60); r.raise_for_status(); return r.content
        except Exception:
            if k == 4: raise
            time.sleep(2**k)
def ls(prefix): return re.findall(r"<Prefix>([^<]+)</Prefix>", get(f"{B}/?list-type=2&prefix={prefix}&delimiter=/").decode())[1:]
m = mgrs.MGRS(); tiles = sorted({m.toMGRS(la, lo, MGRSPrecision=0) for la in np.linspace(lat0, lat1, 6) for lo in np.linspace(lon0, lon1, 6)})
def scenes(t):
    z, b, sq = t[:2], t[2], t[3:]; res = []
    def one(s):
        sid = s.rstrip('/').split('/')[-1]
        try: p = json.loads(get(f"{B}/{s}{sid}.json"))['properties']
        except Exception: return None
        return (p.get('eo:cloud_cover', 100), p.get('s2:nodata_pixel_percentage', 0), s)
    months = [mm for y in ("2021", "2022", "2023", "2024") for mm in ls(f"sentinel-s2-l2a-cogs/{z}/{b}/{sq}/{y}/")]
    with cf.ThreadPoolExecutor(16) as ex: ss = [s for l in ex.map(ls, months) for s in l]
    with cf.ThreadPoolExecutor(32) as ex: res = [r for r in ex.map(one, ss) if r and r[1] < 30 and r[0] < 60]
    res.sort(); return [s for c, n, s in res[:NS]]
allS = [s for t in tiles for s in scenes(t)]; print(len(tiles), 'tuiles', len(allS), 'scènes', flush=True)
W, H = int(round((lon1 - lon0)*pxd)), int(round((lat1 - lat0)*pxd)); dt = from_origin(lon0, lat1, 1/pxd, 1/pxd)
ovl = None if pxd > 7000 else (0 if pxd > 3000 else 1)
def warp(s):
    try:
        d = np.zeros((3, H, W), np.uint8); c = np.zeros((1, H, W), np.uint8)
        with rasterio.open(f"{B}/{s}TCI.tif", overview_level=ovl) as src:
            reproject(src.read(), d, src_transform=src.transform, src_crs=src.crs, dst_transform=dt, dst_crs='EPSG:4326', resampling=Resampling.bilinear, src_nodata=0, dst_nodata=0)
        with rasterio.open(f"{B}/{s}SCL.tif", overview_level=(ovl - 1 if ovl else None)) as src:
            reproject(src.read(), c, src_transform=src.transform, src_crs=src.crs, dst_transform=dt, dst_crs='EPSG:4326', resampling=Resampling.nearest, src_nodata=0, dst_nodata=0)
        ok = np.isin(c[0], [2, 4, 5, 6, 7, 11]) & (d.sum(0) > 0)          # sol, végétation, sol nu, eau, bâti… (pas nuage/ombre/cirrus)
        print('  ', s.split('/')[-2], round(ok.mean(), 2), flush=True); return d, ok
    except Exception as e: print('ERR', s, e, flush=True); return None
with cf.ThreadPoolExecutor(8) as ex: R = [r for r in ex.map(warp, allS) if r]
st = np.stack([r[0] for r in R]); okm = np.stack([r[1] for r in R]); del R
img = np.zeros((3, H, W), np.float32); good = np.zeros((H, W), bool)
for r0 in range(0, H, 128):
    c = st[:, :, r0:r0+128].astype(np.float32); m = okm[:, r0:r0+128]
    c2 = c.copy(); c2[c2 == 0] = np.nan; c[~np.broadcast_to(m[:, None], c.shape)] = np.nan
    with np.errstate(all='ignore'): a_ = np.nanmedian(c, 0); fb = np.nanmedian(c2, 0)
    g = ~np.isnan(a_[0]); good[r0:r0+128] = g; img[:, r0:r0+128] = np.where(g[None], a_, fb)
print('couverture claire', good.mean()); okk = ~np.isnan(img[0])
np.savez(out, img=np.nan_to_num(img).transpose(1, 2, 0).astype(np.uint8), ok=okk, box=np.array([lon0, lon1, lat0, lat1, pxd]))
print('ok', W, H)
