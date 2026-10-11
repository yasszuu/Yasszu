"""Relief réel du Haut Atlas autour du Tizi n'Tichka (Terrarium z12) -> h.npy (m), grille métrique 25 m."""
import sys, math, numpy as np
sys.path.insert(0, '../gombe'); import demlib
from scipy.ndimage import map_coordinates
Z = 12; LON0, LAT0 = -7.40, 31.25
NX, NY, STEP = 720, 720, 25.0                     # 18 km × 18 km
xs = (np.arange(NX) - NX/2)*STEP; ys = (np.arange(NY) - NY/2)*STEP; X, Y = np.meshgrid(xs, ys)
lon = LON0 + X/(111320*math.cos(math.radians(LAT0))); lat = LAT0 + Y/110574
n = 2**Z; r = np.radians(lat); fx = (lon + 180)/360*n; fy = (1 - np.log(np.tan(r) + 1/np.cos(r))/np.pi)/2*n
tx0, ty0, tx1, ty1 = int(fx.min()), int(fy.min()), int(fx.max()), int(fy.max())
big = np.zeros(((ty1-ty0+1)*256, (tx1-tx0+1)*256), np.float32)
for ty in range(ty0, ty1+1):
    for tx in range(tx0, tx1+1): big[(ty-ty0)*256:(ty-ty0+1)*256, (tx-tx0)*256:(tx-tx0+1)*256] = demlib.tile(Z, tx, ty)
H = map_coordinates(big, [(fy-ty0)*256-0.5, (fx-tx0)*256-0.5], order=3, mode='nearest')
print('alt', H.min(), H.max()); np.save('h.npy', H.astype(np.float32))
iy, ix = np.unravel_index(np.argmax(H), H.shape); print('sommet', xs[ix], ys[iy], H[iy, ix])
