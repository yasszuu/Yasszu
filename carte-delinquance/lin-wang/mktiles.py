"""Génère les tuiles 256 px (relief ombré + couleurs naturelles) listées dans plan.json → tiles/z/x/y.jpg"""
import json, math, os, numpy as np, concurrent.futures as cf
from PIL import Image
from scipy.ndimage import map_coordinates, uniform_filter
import sys; sys.path.insert(0, '../gombe'); from demlib import tile
Image.MAX_IMAGE_PIXELS = None
REG = np.array(Image.open('tex_region.jpg')).astype(np.float32)/255        # lon 90..126, lat 32..18, 120 px/°
WRL = np.array(Image.open('../lion/tex_world.jpg')).astype(np.float32)/255         # monde 8192×4096 (même étalonnage)
def color(lon, lat):
    return color0(lon, lat)
def color0(lon, lat):
    inR = (lon > 90.05) & (lon < 125.95) & (lat < 31.95) & (lat > 18.05)
    out = np.empty(lon.shape + (3,), np.float32)
    yr, xr = (32 - lat)*120, (lon - 90)*120; yw, xw = (90 - lat)/180*4096, (lon + 180)/360*8192
    for c in range(3):
        a = map_coordinates(REG[..., c], [yr, xr], order=1, mode='nearest'); w = map_coordinates(WRL[..., c], [yw, xw], order=1, mode='nearest')
        out[..., c] = np.where(inR, a, w)
    return out
import os as _os
from sat import Layer
SAT = []                                                                  # du plus large au plus fin, chacun calé sur le précédent
for p, fe in (('../s2/region_f.npz', 1.5), ('../s2/tw.npz', 0.15), ('../s2/tpe.npz', 0.03)):
    if _os.path.exists(p): SAT.append(Layer(p, (lambda L: (lambda lo, la: L.sample(lo, la, 1e9)[0]))(SAT[-1]) if SAT else color0, fe))
def padded(z, x, y):
    n = 2**z; rows = []
    for dy in (-1, 0, 1):
        row = []
        for dx in (-1, 0, 1):
            yy = min(max(y + dy, 0), n - 1); row.append(tile(z, (x + dx) % n, yy))
        rows.append(np.hstack(row))
    return np.vstack(rows)[255:513, 255:513]                                  # 258×258 (1 px de marge)
def make(key):
    z, x, y = map(int, key.split('/')); p = f'tiles/{z}/{x}/{y}.jpg'
    if os.path.exists(p): return
    h = padded(z, x, y)
    n = 2**z; px = (x*256 + np.arange(-1, 257) + 0.5)/(256*n); py = (y*256 + np.arange(-1, 257) + 0.5)/(256*n)
    lon = px*360 - 180; lat = np.degrees(np.arctan(np.sinh(math.pi*(1 - 2*py))))
    LON, LAT = np.meshgrid(lon, lat)
    m = 156543.03*np.cos(np.radians(LAT))/n                                   # mètres par pixel
    ex = 1.6*2**((13 - z)*0.38)
    e = np.maximum(h, 0)
    gx = (e[1:-1, 2:] - e[1:-1, :-2])/(2*m[1:-1, 1:-1])*ex; gy = (e[2:, 1:-1] - e[:-2, 1:-1])/(2*m[1:-1, 1:-1])*ex
    def shade(az, alt):
        az, alt = math.radians(az), math.radians(alt)
        lx, ly, lz = math.cos(alt)*math.sin(az), -math.cos(alt)*math.cos(az), math.sin(alt)
        nx, ny, nz = -gx, gy, np.ones_like(gx); nn = np.sqrt(nx**2 + ny**2 + 1)
        return np.clip((nx*lx + ny*ly + nz*lz)/nn, 0, 1)
    s = 0.65*shade(315, 40) + 0.35*shade(260, 50)
    flat = shade(315, 40)*0 + math.sin(math.radians(40))
    col = color(LON[1:-1, 1:-1], LAT[1:-1, 1:-1])
    land = h[1:-1, 1:-1] > 0.5
    need = 256*n/360*1.4; satA = np.zeros(land.shape, np.float32)
    for L in SAT:
        if z < 4 or LON.min() > L.lon1 or LON.max() < L.lon0 or LAT.min() > L.lat1 or LAT.max() < L.lat0: continue
        sc, sa = L.sample(LON[1:-1, 1:-1], LAT[1:-1, 1:-1], need); sa = (sa*land*(0.5 if z == 4 else 1))[..., None]
        col = col*(1 - sa) + sc*sa; satA = np.maximum(satA, sa[..., 0])
    mk = np.clip((-55 - LAT[1:-1, 1:-1])/6, 0, 1)[..., None]               # pas d'Antarctique : océan austral uni
    if mk.max() > 0:
        ocean = color(np.array([[85.0]]), np.array([[-48.0]]))[0, 0]
        col = col*(1 - mk) + ocean*mk; land = land & (mk[..., 0] < 0.5)
    # lacs (MNT parfaitement plat) aux grands zooms
    if z >= 8:
        slope = np.hypot(gx, gy); flatm = uniform_filter((slope < 1e-4).astype(np.float32), 5) > 0.9
        lake = flatm & land & (satA < 0.3)
        col[lake] = np.array([0.10, 0.36, 0.55]); land = land & ~lake
    f = np.clip(0.8 + 0.6*(s - 0.45), 0.5, 1.2)[..., None]       # relief déjà présent dans la texture : ombrage léger
    out = np.where(land[..., None], col*f, col)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    Image.fromarray((np.clip(out, 0, 1)*255).astype(np.uint8)).save(p, quality=90)
plan = json.load(open('plan.json'))
with cf.ThreadPoolExecutor(12) as ex: list(ex.map(make, plan))
print('ok', len(plan))
