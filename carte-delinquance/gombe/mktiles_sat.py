"""Génère les tuiles 256 px (relief ombré + couleurs naturelles) listées dans plan.json → tiles/z/x/y.jpg"""
import json, math, os, numpy as np, concurrent.futures as cf
from PIL import Image
from scipy.ndimage import map_coordinates, uniform_filter
from demlib import tile
Image.MAX_IMAGE_PIXELS = None
AFR = np.array(Image.open('color_africa.png')).astype(np.float32)/255          # lon -20..55, lat 38..-36, 60 px/°
WRL = np.array(Image.open('../lapin/tex_world.jpg')).astype(np.float32)/255    # monde 8192×4096
def color0(lon, lat):
    inA = (lon > -19.9) & (lon < 54.9) & (lat < 37.9) & (lat > -35.9)
    out = np.empty(lon.shape + (3,), np.float32)
    ys, xs = (38 - lat)*60, (lon + 20)*60
    yw, xw = (90 - lat)/180*4096, (lon + 180)/360*8192
    for c in range(3):
        a = map_coordinates(AFR[..., c], [ys, xs], order=1, mode='nearest'); w = map_coordinates(WRL[..., c], [yw, xw], order=1, mode='nearest')
        out[..., c] = np.where(inA, a, w)
    return out
import os as _os
from sat import Layer
SAT = []                                                                  # couches satellite Sentinel-2, de la plus large à la plus fine
for p, fe, zm in json.load(open('layers.json')):
    if _os.path.exists(p): SAT.append(Layer(p, (lambda L: (lambda lo, la: L.sample(lo, la, 1e9)[0]))(SAT[-1]) if SAT else color0, fe)); SAT[-1].zmin = zm
color = color0
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
    # lac Tanganyika (MNT plat) : eau uniforme, sans les raccords entre scènes satellite
    if z >= 6:
        slope0 = np.hypot(gx, gy); lk = uniform_filter((slope0 < 2e-4).astype(np.float32), 7) > 0.85
        lk = lk & land & (h[1:-1, 1:-1] < 800) & (h[1:-1, 1:-1] > 760)
        lkf = uniform_filter(lk.astype(np.float32), 5)
    else: lkf = np.zeros(land.shape, np.float32)
    for L in SAT:
        if z < L.zmin or LON.min() > L.lon1 or LON.max() < L.lon0 or LAT.min() > L.lat1 or LAT.max() < L.lat0: continue
        sc, sa = L.sample(LON[1:-1, 1:-1], LAT[1:-1, 1:-1], need); sa = (sa*land*(0.5 if z == L.zmin else 1))[..., None]
        sa = sa*(1 - lkf[..., None]); col = col*(1 - sa) + sc*sa; satA = np.maximum(satA, sa[..., 0])
    if lkf.max() > 0:
        water = np.array([0.075, 0.13, 0.22], np.float32)*(1 + 0.04*np.sin(LON[1:-1, 1:-1]*40)[..., None])
        col = col*(1 - lkf[..., None]) + water*lkf[..., None]; satA = np.maximum(satA, lkf)
    # lacs (MNT parfaitement plat) aux grands zooms
    if z >= 8:
        slope = np.hypot(gx, gy); flatm = uniform_filter((slope < 1e-4).astype(np.float32), 5) > 0.9
        lake = flatm & land & (satA < 0.3)
        col[lake] = np.array([0.10, 0.36, 0.55]); land = land & ~lake
    f = (np.clip(0.55 + 1.05*(s - 0.45), 0.25, 1.35)*(1 - satA) + np.clip(0.8 + 0.6*(s - 0.45), 0.5, 1.2)*satA)[..., None]   # relief déjà dans l'image satellite : ombrage léger
    out = np.where(land[..., None], col*f, col)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    Image.fromarray((np.clip(out, 0, 1)*255).astype(np.uint8)).save(p, quality=90)
plan = json.load(open('plan.json'))
with cf.ThreadPoolExecutor(12) as ex: list(ex.map(make, plan))
print('ok', len(plan))
