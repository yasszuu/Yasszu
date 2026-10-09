"""MNT Terrarium (AWS) -> couleur « satellite » + normales + hauteurs pour un patch du terrain 3D."""
import numpy as np, math, glob, sys
from PIL import Image
from scipy.ndimage import gaussian_filter, zoom
Image.MAX_IMAGE_PIXELS=None
def mosaic(d, Z, L, R, B, T, rx, ry):
    N=2**Z; tiles={}
    for f in glob.glob(d+'/*.png'):
        x,y=f.split('/')[-1][:-4].split('_')[-2:]
        a=np.array(Image.open(f).convert('RGB')).astype(np.float32); tiles[(int(x),int(y))]=a[...,0]*256+a[...,1]+a[...,2]/256-32768
    W=int(round((R-L)/rx)); H=int(round((T-B)/ry))
    lon=L+(np.arange(W)+0.5)*rx; lat=T-(np.arange(H)+0.5)*ry; LON,LAT=np.meshgrid(lon,lat)
    fx=(LON+180)/360*N; r=np.radians(LAT); fy=(1-np.log(np.tan(r)+1/np.cos(r))/np.pi)/2*N
    ix=np.floor(fx).astype(int); iy=np.floor(fy).astype(int)
    px=np.clip(((fx-ix)*256).astype(int),0,255); py=np.clip(((fy-iy)*256).astype(int),0,255)
    h=np.zeros((H,W),np.float32)
    for (x,y),a in tiles.items():
        m=(ix==x)&(iy==y)
        if m.any(): h[m]=a[py[m],px[m]]
    return h, LAT
def build(name, h, LAT, rx, ry, L, R, B, T, geo):
    # NE : masque glace (blanc) pour les glaciers
    ne=Image.open('../lion/NE1_HR_LC_SR_W_DR.tif')
    box=(int((L+180)*60),int((90-T)*60),int((R+180)*60),int((90-B)*60))
    n=np.array(ne.crop(box).convert('RGB').resize((h.shape[1],h.shape[0]),Image.BILINEAR)).astype(np.float32)/255
    icem=np.clip((n.mean(-1)-0.88)/0.06,0,1)*np.clip((np.maximum(h,0)-200)/300,0,1)
    land=gaussian_filter((h>0.5).astype(np.float32),0.8)
    hs=gaussian_filter(h,1.0)
    dx=rx*111320*np.cos(np.radians(LAT)); dy=ry*111320
    gx=np.gradient(hs,axis=1)/dx; gy=-np.gradient(hs,axis=0)/dy; slope=np.sqrt(gx**2+gy**2)
    e=np.maximum(h,0)
    tundra=np.array([0.36,0.35,0.25]); rock=np.array([0.33,0.30,0.27]); rock2=np.array([0.48,0.43,0.37])
    base=tundra*np.clip(1-e/500,0,1)[...,None]+rock*np.clip(e/500,0,1)[...,None]
    base=base*(1-np.clip(slope*1.5,0,1)[...,None])+rock2*np.clip(slope*1.5,0,1)[...,None]
    snow=np.clip((e-1700)/500,0,1)*np.clip(1-slope*2.0,0,1)
    ice=np.maximum(np.maximum(icem*np.clip(1-slope*1.5,0.25,1), np.clip((e-2000)/500,0,1)), snow)[...,None]
    icecol=np.array([0.90,0.94,0.98])
    col=base*(1-ice)+icecol*ice
    dep=np.clip(-h/400,0,1)[...,None]
    sea=np.array([0.10,0.42,0.55])*(1-dep)+np.array([0.03,0.13,0.30])*dep
    out=col*land[...,None]+sea*(1-land[...,None])
    Image.fromarray((np.clip(out,0,1)*255).astype(np.uint8)).save(f'{name}_color.jpg',quality=92)
    hl=e*2.2
    gx=np.gradient(gaussian_filter(hl,0.6),axis=1)/dx; gy=-np.gradient(gaussian_filter(hl,0.6),axis=0)/dy
    nn=np.stack([-gx,-gy,np.ones_like(gx)],-1); nn/=np.linalg.norm(nn,axis=-1,keepdims=True)
    Image.fromarray(((nn*0.5+0.5)*255).astype(np.uint8)).save(f'{name}_normal.png')
    Image.fromarray(np.clip(e/4000*255,0,255).astype(np.uint8)).resize(geo,Image.BILINEAR).save(f'{name}_height.png')
    print(name, h.shape)
if __name__=='__main__':
    L,R,B,T=-62,-10,58,81; h,LAT=mosaic('dem',7,L,R,B,T,0.012,0.008); build('coarse',h,LAT,0.012,0.008,L,R,B,T,(1100,700))
    L,R,B,T=-34,-15,66,75; h,LAT=mosaic('dem9',9,L,R,B,T,0.006,0.0025); build('fine',h,LAT,0.006,0.0025,L,R,B,T,(1100,1000))
