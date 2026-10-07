from PIL import Image, ImageFilter
import numpy as np
from scipy.ndimage import map_coordinates
raw=np.asarray(Image.open('images/1.webp').convert('RGB')).astype(np.float32)
A=np.asarray(Image.open('images/1.webp').convert('RGB').filter(ImageFilter.MedianFilter(3))).astype(np.float32); lum=A.max(2)
cells=np.load('work/cells.npy'); lab=np.load('work/lab.npy'); rows=np.load('work/rows.npy')
Z=4; CW,CH=20,38          # cell size in source px
def patch(cx,cy,w=CW+8,h=CH+6,img=lum):
    xs=cx+(np.arange(w*Z)-w*Z/2+0.5)/Z; ys=cy+(np.arange(h*Z)-h*Z/2+0.5)/Z
    X,Y=np.meshgrid(xs,ys); return map_coordinates(img,[Y,X],order=1)
names={}
for c in [3,8,11,13,14,15,20,21,25,28,31,33,35]: names[c]='M'
names.update({27:'N',5:'m',18:'h',24:'d',7:'y',26:'s',32:'/'})
# seed templates from confident clusters
def norm(p): p=p-p.mean(); return p/np.linalg.norm(p)
ART=np.array([rows[r] for r in range(1,12)],float); rr=np.arange(1,12)
b,a_=np.polyfit(rr,ART,1); print('row pitch',b)
def rowy(r): return a_+b*r if 1<=r<=12 else rows[r]
cells=np.array([(r,k,x,rowy(int(r))) for r,k,x,y in cells])
cellpos={(int(r),int(k)):(x,y) for r,k,x,y in cells}
def cellpatch(r,k): x,y=cellpos[(r,k)]; return patch(x,y)
T={}
for ch in set(names.values()):
    idx=[i for i,l in enumerate(lab) if names.get(l)==ch and 1<=cells[i,0]<=12]
    T[ch]=np.mean([patch(cells[i,2],cells[i,3]) for i in idx],0)
# punctuation seeds picked from known positions (row, k)
seeds={'o':[(3,7),(11,22),(12,24),(12,25),(12,26)],'.':[(1,58),(1,97),(2,79)],'-':[(1,62),(1,83),(2,62)],':':[(1,80),(2,19)],'+':[(1,43),(2,5),(2,22)]}
for ch,lst in seeds.items(): T[ch]=np.mean([cellpatch(r,k) for r,k in lst],0)
CHARS=list(T)
# classify every art cell by NCC over small shifts; refine x/y offset
def crop(p,dx,dy):  # dx,dy in Z-steps; central cell window
    ox=(p.shape[1]-CW*Z)//2+dx; oy=(p.shape[0]-CH*Z)//2+dy; return p[oy:oy+CH*Z,ox:ox+CW*Z]
TN={c:norm(crop(T[c],0,0)) for c in CHARS}
SH=[(dx,dy) for dx in range(-12,13,2) for dy in range(-8,9,2)]
def classify(p):
    best=(-2,None,0,0)
    for dx,dy in SH:
        q=crop(p,dx,dy)
        if q.max()<1: continue
        qn=norm(q)
        for c in CHARS:
            v=float((qn*TN[c]).sum())
            if v>best[0]: best=(v,c,dx,dy)
    return best
res={}
for it in range(2):
    res={}
    for r,k,x,y in cells:
        r,k=int(r),int(k)
        if not 1<=r<=12: continue
        res[(r,k)]=classify(patch(x,y))
    # rebuild templates from aligned members
    for c in CHARS:
        mem=[patch(cellpos[key][0]+v[2]/Z,cellpos[key][1]+v[3]/Z) for key,v in res.items() if v[1]==c and v[0]>0.6]
        if mem: T[c]=np.mean(mem,0)
    TN={c:norm(crop(T[c],0,0)) for c in CHARS}
import pickle; pickle.dump({'res':res,'T':T},open('work/classes.pkl','wb'))
for r in range(1,13):
    ks=sorted(k for (rr,k) in res if rr==r); line=''; prev=None
    for k in ks:
        v=res[(r,k)]
        if prev is not None: line+=' '*(k-prev-1)
        line+=v[1] if v[0]>0.5 else ' '; prev=k
    lo=min(res[(r,k)][0] for k in ks)
    print(f'{r:2d} {ks[0]:3d} |{line}|  minscore {lo:.2f}')

