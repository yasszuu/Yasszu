"""Bouche les trous (jonctions de zones UTM) par push-pull pyramidal."""
import sys, numpy as np
from PIL import Image
d = np.load(sys.argv[1]); img = d['img'].astype(np.float32); ok = d['ok'].astype(np.float32)
def pp(c, w):
    if min(c.shape[:2]) < 4: return c/np.maximum(w, 1e-6)[..., None]
    H, W = w.shape; h2, w2 = (H + 1)//2, (W + 1)//2
    cp = np.zeros((h2*2, w2*2, 3), np.float32); wp = np.zeros((h2*2, w2*2), np.float32); cp[:H, :W] = c; wp[:H, :W] = w
    cs = cp.reshape(h2, 2, w2, 2, 3).sum((1, 3)); ws = wp.reshape(h2, 2, w2, 2).sum((1, 3))
    lo = pp(cs, ws); up = np.repeat(np.repeat(lo, 2, 0), 2, 1)[:H, :W]
    up = np.asarray(Image.fromarray(np.clip(up, 0, 255).astype(np.uint8)).filter(__import__('PIL.ImageFilter').ImageFilter.GaussianBlur(1)), np.float32)
    k = np.clip(w, 0, 1)[..., None]; return (c/np.maximum(w, 1e-6)[..., None])*k + up*(1 - k)
out = pp(img*ok[..., None], ok)
np.savez(sys.argv[2], img=np.clip(out, 0, 255).astype(np.uint8), ok=np.ones_like(d['ok']), box=d['box'])
Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).resize((1440, 560)).save('region_fill_small.jpg')
