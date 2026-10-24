"""Couches satellite Sentinel-2 (s2mosaic.py) étalonnées sur la texture régionale → couleur nette aux grands zooms."""
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, binary_erosion, distance_transform_edt
class Layer:
    def __init__(self, path, ref, feather):
        d = np.load(path); img = d['img'].astype(np.float32)/255; ok = d['ok']
        self.lon0, self.lon1, self.lat0, self.lat1, pxd = d['box']
        # étalonnage : moyenne / écart-type par canal calés sur la texture de référence (terres valides)
        H, W = ok.shape; yy, xx = np.mgrid[0:H:8, 0:W:8]; lon = self.lon0 + (xx + 0.5)/pxd; lat = self.lat1 - (yy + 0.5)/pxd
        r = ref(lon, lat); s = img[::8, ::8]; m = ok[::8, ::8] & (s.mean(-1) > 0.04)
        lr, ls_ = r[m].mean(), (s[m]**0.85).mean(); self.a = np.full(3, lr/ls_, np.float32); self.b = np.zeros(3, np.float32)   # gain de luminosité seul : teintes naturelles
        # fondu sur les bords de la zone couverte
        f = distance_transform_edt(np.pad(ok, 1))[1:-1, 1:-1]; self.levels = []
        for k in range(5):
            q = 2**k; im = np.asarray(Image.fromarray((img*255).astype(np.uint8)).resize((W//q, H//q), Image.LANCZOS), np.float32)/255
            al = np.asarray(Image.fromarray(np.clip(f/(feather*pxd), 0, 1).astype(np.float32)).resize((W//q, H//q), Image.BILINEAR))
            self.levels.append((pxd/q, im, al))
    def sample(self, lon, lat, need):
        """need = px/° demandé par la tuile ; renvoie (couleur, alpha)"""
        pxd, im, al = next((l for l in reversed(self.levels) if l[0] >= need), self.levels[0])
        y, x = (self.lat1 - lat)*pxd - 0.5, (lon - self.lon0)*pxd - 0.5
        c = np.stack([map_coordinates(im[..., i], [y, x], order=1, mode='constant', cval=0) for i in range(3)], -1)
        a = map_coordinates(al, [y, x], order=1, mode='constant', cval=0)
        c = np.clip(c**0.85*self.a + self.b, 0, 1)
        g = c.mean(-1, keepdims=True); c = np.clip(g + (c - g)*1.1, 0, 1)          # un peu plus de saturation
        return c, a
