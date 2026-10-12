"""Composite NE1 (terres, couleurs d'occupation du sol) + HYP (fonds marins) et étalonnage « satellite vif »."""
import numpy as np, sys
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

def grade(ne, hy):
    ne = ne.astype(np.float32)/255; hy = hy.astype(np.float32)/255
    r, g, b = ne[...,0], ne[...,1], ne[...,2]
    water = ((b - r) > 0.12) & ((b - g) > -0.02) & (b > 0.55)
    # ---- terres : classification douce désert / cultures / forêt à partir des teintes NE1
    R, G, Bc = r*255, g*255, b*255
    lum = (0.3*r + 0.59*g + 0.11*b)
    warm, yel = R - G, G - Bc
    sig = lambda x: 1/(1 + np.exp(-x))
    desert = sig((warm + 24 - yel)/5) * np.clip((lum - 0.55)/0.15, 0, 1)
    forest = np.clip((G - R + 4)/24, 0, 1)
    snow = np.clip((Bc - 238)/10, 0, 1) * np.clip(1 - (R - Bc)/12, 0, 1)
    shade = np.clip(lum/0.93, 0, 1.15)[...,None]**1.4                  # relief ombré conservé
    sandA = np.array([0.92, 0.75, 0.49]); sandB = np.array([0.80, 0.55, 0.30])   # sable clair / ocre
    sand = sandA*(1 - np.clip(warm/18, 0, 1))[...,None] + sandB*np.clip(warm/18, 0, 1)[...,None]
    olive = np.array([0.50, 0.58, 0.26]); deep = np.array([0.16, 0.36, 0.15])
    veg = olive*(1 - forest[...,None]) + deep*forest[...,None]
    land = (sand*desert[...,None] + veg*(1 - desert[...,None]))*shade
    land = land*(1 - snow[...,None]) + np.array([0.95, 0.96, 0.98])*snow[...,None]
    land = np.clip(land, 0, 1)
    # ---- océans : bathymétrie HYP recolorée (bleu nuit profond, plateaux turquoise)
    hl = (0.3*hy[...,0] + 0.59*hy[...,1] + 0.11*hy[...,2])
    t = np.clip((hl - 0.45)/0.4, 0, 1)[...,None]                       # 0 = profond, 1 = plateau
    deep = np.array([0.04, 0.16, 0.36]); shelf = np.array([0.10, 0.55, 0.68])
    ocean = deep*(1 - t) + shelf*t
    ocean *= (0.85 + 0.3*(hl[...,None] - hl.mean()))                   # garde le relief sous-marin
    out = np.where(water[...,None], ocean, land)
    return (np.clip(out, 0, 1)*255).astype(np.uint8)

if __name__ == "__main__":
    ne = Image.open("NE1_HR_LC_SR_W_DR.tif"); hy = Image.open("../v2/HYP_HR_SR_OB_DR.tif")
    mode = sys.argv[1]
    if mode == "test":
        L, R, T, B = -25, 70, 62, 0
        box = (int((L+180)*60), int((90-T)*60), int((R+180)*60), int((90-B)*60))
        a = np.array(ne.crop(box).reduce(3)); h = np.array(hy.convert("RGB").crop(box).reduce(3))
        Image.fromarray(grade(a, h)).save("grade_test.jpg", quality=88)
    else:
        out = np.zeros((10800, 21600, 3), np.uint8)
        for y0 in range(0, 10800, 1350):
            box = (0, y0, 21600, y0 + 1350)
            out[y0:y0+1350] = grade(np.array(ne.crop(box)), np.array(hy.convert("RGB").crop(box)))
        full = Image.fromarray(out)
        full.resize((8192, 4096), Image.LANCZOS).save("tex_world.jpg", quality=90)
        L, R, T, B = -20, 40, 52, 18                                      # = REG_BOX dans src.html
        reg = full.crop((int((L+180)*60), int((90-T)*60), int((R+180)*60), int((90-B)*60)))
        reg.resize((reg.width*2, reg.height*2), Image.LANCZOS).save("tex_region.jpg", quality=90)
        print(reg.size)
