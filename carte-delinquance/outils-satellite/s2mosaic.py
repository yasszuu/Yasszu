"""Mosaïque Sentinel-2 (TCI, AWS sentinel-cogs) → texture équirectangulaire nette.
usage: s2mosaic.py out.npz lon0 lon1 lat0 lat1 pxdeg ovl TILE [TILE...]
médiane de plusieurs scènes peu nuageuses par tuile MGRS (enlève nuages / bandes vides)."""
import sys, os, json, re, urllib.request, numpy as np, concurrent.futures as cf
os.environ.setdefault('CURL_CA_BUNDLE', '/root/.ccr/ca-bundle.crt'); os.environ['GDAL_DISABLE_READDIR_ON_OPEN'] = 'EMPTY_DIR'
import rasterio
from rasterio.warp import reproject, Resampling
from rasterio.transform import from_origin
B = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
out, lon0, lon1, lat0, lat1, pxd, ovl = sys.argv[1], *map(float, sys.argv[2:7]), int(sys.argv[7]); tiles = sys.argv[8:]
NS = int(os.environ.get('NS', 5))
import time
def get(u):
    for k in range(5):
        try: return urllib.request.urlopen(u, timeout=60).read()
        except Exception:
            if k == 4: raise
            time.sleep(2**k)
def ls(prefix):
    x = get(f"{B}/?list-type=2&prefix={prefix}&delimiter=/").decode()
    return re.findall(r"<Prefix>([^<]+)</Prefix>", x)[1:]
def scenes(t):
    cf_ = f'scenes_{t}.json'
    if os.path.exists(cf_): return json.load(open(cf_))
    r = scenes_(t); json.dump(r, open(cf_, 'w')); return r
def scenes_(t):
    z, b, sq = t[:2], t[2], t[3:]; res = []
    months = [m for y in ("2021", "2022", "2023", "2024") for m in ls(f"sentinel-s2-l2a-cogs/{z}/{b}/{sq}/{y}/")]
    for m in months:
        for s in ls(m):
            sid = s.rstrip('/').split('/')[-1]
            try: p = json.loads(get(f"{B}/{s}{sid}.json"))['properties']
            except Exception: continue
            nd = p.get('s2:nodata_pixel_percentage', 0)
            if nd < 40: res.append((p.get('eo:cloud_cover', 100) + nd*0.05, s))
    res.sort(); return [s for c, s in res[:NS] if c < 15]
W, H = int(round((lon1 - lon0)*pxd)), int(round((lat1 - lat0)*pxd))
dst_t = from_origin(lon0, lat1, 1/pxd, 1/pxd)
def warp(s):
    with rasterio.open(f"{B}/{s}TCI.tif", overview_level=ovl) as src:
        a = src.read(); d = np.zeros((3, H, W), np.uint8)
        reproject(a, d, src_transform=src.transform, src_crs=src.crs, dst_transform=dst_t, dst_crs='EPSG:4326', resampling=Resampling.bilinear, src_nodata=0, dst_nodata=0)
    print('  ', s.split('/')[-2], flush=True); return d
with cf.ThreadPoolExecutor(8) as ex: lists = list(ex.map(scenes, tiles))
allS = [s for l in lists for s in l]; print(len(allS), 'scènes', flush=True)
with cf.ThreadPoolExecutor(6) as ex: stack = list(ex.map(warp, allS))
st = np.stack(stack); del stack                                           # uint8 (n, 3, H, W)
img = np.zeros((H, W, 3), np.uint8); ok = np.zeros((H, W), bool)
for r in range(0, H, 256):
    c = st[:, :, r:r+256].astype(np.float32); c[c == 0] = np.nan
    br = np.nanmean(c, 1); med = np.nanmedian(br, 0)
    c[np.broadcast_to((br > med + 25)[:, None], c.shape)] = np.nan       # nuages : bien plus clairs que la médiane
    m = np.nanmedian(c, 0); ok[r:r+256] = ~np.isnan(m[0]); img[r:r+256] = np.nan_to_num(m).transpose(1, 2, 0).astype(np.uint8)
np.savez_compressed(out, img=img, ok=ok, box=np.array([lon0, lon1, lat0, lat1, pxd]))
print('ok', W, H, ok.mean())
