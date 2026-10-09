"""Accès aux tuiles d'altitude Terrarium (AWS) avec cache disque."""
import math, os, urllib.request, numpy as np
from PIL import Image
CACHE = os.path.join(os.path.dirname(__file__), 'dem')
def tile(z, x, y):
    p = os.path.join(CACHE, f'{z}_{x}_{y}.png')
    import threading
    for k in range(5):
        if not os.path.exists(p):
            tmp = f'{p}.{threading.get_ident()}.tmp'
            try: urllib.request.urlretrieve(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png', tmp); os.replace(tmp, p)
            except Exception: continue
        try: a = np.array(Image.open(p).convert('RGB')).astype(np.float32); break
        except OSError: os.remove(p)
    return a[..., 0]*256 + a[..., 1] + a[..., 2]/256 - 32768
def lonlat_to_tile(lon, lat, z):
    n = 2**z; r = math.radians(lat)
    return (lon + 180)/360*n, (1 - math.log(math.tan(r) + 1/math.cos(r))/math.pi)/2*n
def elev(lon, lat, z=13):
    fx, fy = lonlat_to_tile(lon, lat, z); x, y = int(fx), int(fy)
    t = tile(z, x, y); return t[min(255, int((fy - y)*256)), min(255, int((fx - x)*256))]
