"""Heightfield réel de Gombe (Terrarium z13) rééchantillonné en grille métrique locale -> h.npy (m), meta."""
import sys, math, numpy as np
sys.path.insert(0, '../gombe'); import demlib
from scipy.ndimage import map_coordinates, gaussian_filter
Z = 13; LON0, LAT0 = 29.635, -4.66           # centre
NX, NY, STEP = 640, 800, 15.0                # 9.6 km (E-O) x 12 km (N-S), 15 m
xs = (np.arange(NX) - NX/2)*STEP; ys = (np.arange(NY) - NY/2)*STEP
X, Y = np.meshgrid(xs, ys)
lon = LON0 + X/(111320*math.cos(math.radians(LAT0))); lat = LAT0 + Y/110574
n = 2**Z; r = np.radians(lat); fx = (lon+180)/360*n; fy = (1-np.log(np.tan(r)+1/np.cos(r))/np.pi)/2*n
tx0, ty0 = int(fx.min()), int(fy.min()); tx1, ty1 = int(fx.max()), int(fy.max())
big = np.zeros(((ty1-ty0+1)*256, (tx1-tx0+1)*256), np.float32)
for ty in range(ty0, ty1+1):
    for tx in range(tx0, tx1+1):
        big[(ty-ty0)*256:(ty-ty0+1)*256, (tx-tx0)*256:(tx-tx0+1)*256] = demlib.tile(Z, tx, ty)
H = map_coordinates(big, [(fy-ty0)*256-0.5, (fx-tx0)*256-0.5], order=3, mode='nearest')
print('min max', H.min(), H.max())
np.save('h.npy', H.astype(np.float32))
from PIL import Image
im = (np.clip((H-760)/(1600-760), 0, 1)*255).astype(np.uint8); Image.fromarray(im[::-1]).save('h_prev.png')
