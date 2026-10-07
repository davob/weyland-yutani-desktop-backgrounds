from PIL import Image, ImageFilter, ImageDraw
import numpy as np
from scipy.ndimage import map_coordinates, gaussian_filter1d as g1
from scipy.cluster.vq import kmeans2
im=Image.open('images/1.webp').convert('RGB').filter(ImageFilter.MedianFilter(3))
A=np.asarray(im).astype(np.float32); lum=A.max(2)
ph=np.load('work/phase.npy'); p0=19.9
u=np.arange(2000)/p0+ph/(2*np.pi)
prof=g1(lum.sum(1),2)
rows=[y for y in range(10,670) if prof[y]==prof[y-8:y+9].max() and prof[y]>prof.max()*0.08]
print('rows',rows)
Z=4; PW,PH=28,44  # patch size in source px, sampled at Z x
def patch(cx,cy):
    xs=cx+(np.arange(PW*Z)-PW*Z/2+0.5)/Z; ys=cy+(np.arange(PH*Z)-PH*Z/2+0.5)/Z
    X,Y=np.meshgrid(xs,ys); return map_coordinates(lum,[Y,X],order=1)
cells=[]
for r,y in enumerate(rows):
    for k in range(int(np.ceil(u[0])),int(u[-1])+1):
        x=np.interp(k,u,np.arange(2000))
        w=lum[int(y-17):int(y+18),int(x-9):int(x+10)]
        if w.size and w.max()>95: cells.append((r,k,x,y))
print('cells',len(cells))
P=np.stack([patch(x,y) for (_,_,x,y) in cells])
np.save('work/P.npy',P); np.save('work/cells.npy',np.array(cells)); np.save('work/rows.npy',np.array(rows))
# features: central cell region downsampled
c=P[:,(PH-38)*Z//2:(PH+38)*Z//2,(PW-20)*Z//2:(PW+20)*Z//2]
feat=c.reshape(len(c),38,Z,20,Z).mean((2,4)).reshape(len(c),-1)
feat=feat/np.maximum(feat.max(1,keepdims=True),1)
np.random.seed(0)
cent,lab=kmeans2(feat,36,minit='++',seed=1,iter=50)
np.save('work/lab.npy',lab)
# montage: each cluster row shows up to 12 members
K=lab.max()+1; th,tw=PH*2,PW*2
M=Image.new('L',(60+12*(tw+4),K*(th+4)),0); d=ImageDraw.Draw(M)
for kk in range(K):
    idx=np.where(lab==kk)[0]
    d.text((4,kk*(th+4)+th//2-6),f'{kk}:{len(idx)}',fill=255)
    for j,i in enumerate(idx[:12]):
        t=Image.fromarray(np.clip(P[i],0,255).astype(np.uint8)).resize((tw,th))
        M.paste(t,(60+j*(tw+4),kk*(th+4)))
M.save('work/clusters.png'); print('K',K)
