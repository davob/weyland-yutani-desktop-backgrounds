import pickle, numpy as np
from PIL import Image, ImageFilter
from scipy.ndimage import map_coordinates, gaussian_filter
exec(open('work/crisp.py').read().split('CHARS=list(T)')[0])   # reuse helpers/positions (no reclassify)
D=pickle.load(open('work/classes.pkl','rb')); res,T=D['res'],D['T']
def cellmask(shape,cw=CW+0.6):
    h,w=shape; xx=np.abs(np.arange(w)-w/2+0.5)/Z; m=np.clip((cw/2-xx)*2+0.5,0,1)
    return np.tile(m,(h,1))
def crispen(t,lo=0.45,hi=0.6,mask=True):
    t=t+1.6*(t-gaussian_filter(t,3.0))           # recover detail lost to camera blur
    t=gaussian_filter(t,0.6); t=t/np.percentile(t,99.5)
    x=np.clip((t-lo)/(hi-lo),0,1); x=x*x*(3-2*x)
    return x*cellmask(t.shape) if mask else x
TC={c:crispen(T[c]) for c in T}
# lowercase m: too few clean samples, so rebuild it from measured geometry (bbox + stem width from 'h')
def build_m():
    base=crispen(T['m'],0.55,0.7)>0.5
    ys,xs=np.nonzero(base[:, int(base.shape[1]*0.2):int(base.shape[1]*0.8)]); xs=xs+int(base.shape[1]*0.2)
    hb=TC['h']>0.5; row=hb[int(hb.shape[0]*0.75)]; runs=np.diff(np.concatenate([[0],row.astype(int),[0]]))
    st=np.nonzero(runs==1)[0]; en=np.nonzero(runs==-1)[0]; sw=int(np.median(en-st))
    hcols=np.nonzero(hb.any(0))[0]; x0,x1=hcols.min(),hcols.max()+1   # same advance/width as h
    top=int(np.percentile(ys,2)); bot=int(np.nonzero(hb.any(1))[0].max())+1
    gap=int(np.median(st[1:]-en[:-1])) if len(st)>1 else 8      # h's counter width
    gap=max(4,int(gap*0.5)); stem=(x1-x0-2*gap)/3; bar=int(round(sw*0.75))
    m=np.zeros(base.shape,np.float32); m[top:top+bar,x0:x1]=1
    for i in range(3):
        a=int(round(x0+i*(stem+gap))); m[top:bot,a:int(round(a+stem))]=1
    return gaussian_filter(m,0.7)
TC['m']=build_m()
# snap art cells to a straight grid
ks=[];xs=[]
for (r,k),v in res.items():
    if v[0]>0.5 and v[1]=='M': ks.append(k); xs.append(cellpos[(r,k)][0]+v[2]/Z)
c1,c0=np.polyfit(ks,xs,1); print('pitch',c1)
placements=[]   # (cx, cy, tile, colour)
def colour(x,y):
    w=raw[int(y-CH/2):int(y+CH/2),int(x-CW/2):int(x+CW/2)].reshape(-1,3); l=w.max(1)
    core=w[l>0.65*l.max()]; return core.mean(0)
cols={key:colour(*cellpos[key]) for key,v in res.items() if v[0]>0.5}
for (r,k),v in res.items():
    if v[0]<=0.5: continue
    run=[k]
    for d in (-1,1):
        kk=k+d
        while (r,kk) in cols and abs(kk-k)<=3: run.append(kk); kk+=d
    wts=np.array([np.exp(-((kk-k)/1.8)**2) for kk in run])
    col=(np.array([cols[(r,kk)] for kk in run])*wts[:,None]).sum(0)/wts.sum()
    mu=col.mean(); col=np.clip((mu+(col-mu)*1.25)*1.12,0,255)   # restore the original's saturation/brightness
    x=c0+c1*k; y=rowy(r); placements.append((x,y,TC[v[1]],col,'art'))
# title & tagline: each letter keeps its own (cleaned) shape from the photo
for r,txt in [(0,'W E Y L A N D - Y U T A N I   C O R P'),(13,'B U I L D I N G   B E T T E R   W O R L D S')]:
    k0=min(int(k) for rr,k,_,_ in cells if rr==r)
    if r==13: k0+=1
    for i,ch in enumerate(txt):
        if ch==' ': continue
        k=k0+i; x,y=cellpos.get((r,k),(c0+c1*k,rows[r]))
        p=patch(c0+c1*k,rows[r]); 
        # recentre on the glyph's own mass so photo wobble is removed
        m=np.clip(p-60,0,None); cxm=(m.sum(0)*np.arange(m.shape[1])).sum()/m.sum()
        shift=(cxm-m.shape[1]/2)/Z
        if ch in 'LP': shift-= 1.5   # asymmetric letters: keep their natural offset
        p=patch(c0+c1*k+shift,rows[r])
        col=colour(c0+c1*k+shift,rows[r]); mu=col.mean(); col=np.clip((mu+(col-mu)*1.2)*1.12,0,255)
        placements.append((c0+c1*k,rows[r],crispen(p,0.45,0.6),col,'text'))
S=4; Wc,Hc=2000*S,682*S
matte=np.zeros((Hc,Wc),np.float32); rgb=np.zeros((Hc,Wc,3),np.float32); tm=np.zeros((Hc,Wc),np.float32)
for x,y,t,col,kind in placements:
    h,w=t.shape; X=int(round(x*S-w/2)); Y=int(round(y*S-h/2))
    sl=(slice(Y,Y+h),slice(X,X+w))
    matte[sl]=np.maximum(matte[sl],t); rgb[sl]=np.maximum(rgb[sl],t[...,None]*col)
    if kind=='text': tm[sl]=np.maximum(tm[sl],t)
OW,OH=2500,852
Image.fromarray(np.clip(rgb,0,255).astype(np.uint8)).resize((OW,OH),Image.LANCZOS).save('work/logo_layer.png')
Image.fromarray((np.clip(matte,0,1)*255).astype(np.uint8)).resize((OW,OH),Image.LANCZOS).save('work/logo_matte.png')
print('rendered',len(placements))
Image.fromarray((np.clip(tm,0,1)*255).astype(np.uint8)).resize((OW,OH),Image.LANCZOS).save('work/logo_matte_text.png')
import json; json.dump({'row_pitch':float(b),'row1_y':float(a_+b),'nrows':12},open('work/logo_grid.json','w'))
# export per-cell layout for re-typesetting
out=[]
for (r,k),v in res.items():
    if v[0]<=0.5: continue
    col=colour(*cellpos[(r,k)]); blue=float(np.clip((col[2]-col[0])/max(col.max(),1)*2.2+0.35,0,1))
    out.append({'r':int(r),'k':int(k),'ch':v[1],'x':float(c0+c1*k),'y':float(rowy(r)),'blue':blue})
json.dump({'cells':out,'pitch':float(c1),'row_pitch':float(b),'title_y':float(rows[0]),'tag_y':float(rows[13]),
           'title_x':[float(c0+c1*(min(int(k) for rr,k,_,_ in cells if rr==0))),float(c0+c1*(min(int(k) for rr,k,_,_ in cells if rr==0)+36))]},
          open('work/layout.json','w'))
print('layout exported',len(out))
