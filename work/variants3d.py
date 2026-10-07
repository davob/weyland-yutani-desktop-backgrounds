from PIL import Image, ImageFilter, ImageDraw
import numpy as np, sys
rng=np.random.default_rng(11)
W,H=3840,2160; S=2; cx,cy=W/2,H/2; f=W*0.9
import os; OUT=os.environ.get('WY_OUT','wallpapers/')
# --- logo layer ---
logo=Image.open('work/logo_layer.png').convert('RGB')
L=np.zeros((H,W,3),np.float32); ox,oy=(W-logo.width)//2,(H-logo.height)//2
L[oy:oy+logo.height,ox:ox+logo.width]=np.asarray(logo)
# soft keep-out mask around glyphs so background lines never cross the lettering
m=Image.fromarray(((L.max(2)>20)*255).astype(np.uint8)).resize((W//8,H//8),Image.BOX)
m=m.point(lambda v:255 if v>0 else 0).filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(4)).resize((W,H),Image.BILINEAR)
KEEP=1-np.asarray(m).astype(np.float32)/255*0.92
yy,xx=np.mgrid[0:H,0:W].astype(np.float32)
r=np.sqrt(((xx-cx)/(W/2))**2+((yy-cy)/(H/2))**2)
def mix(c0,c1,t): t=np.clip(t,0,1)[...,None]; return np.array(c0,np.float32)*(1-t)+np.array(c1,np.float32)*t
def canvas(): img=Image.new('L',(W*S,H*S),0); return img,ImageDraw.Draw(img)
def resolve(img): return np.asarray(img.resize((W,H),Image.LANCZOS)).astype(np.float32)/255
def P(x,y): return (x*S,y*S)
def fog(z,zf): return float(np.exp(-z/zf))
def seg(d,pts_fn,z0,z1,zf,peak,n=48,w=3):
    zs=np.geomspace(z0,z1,n+1)
    for za,zb in zip(zs[:-1],zs[1:]):
        d.line([P(*pts_fn(za)),P(*pts_fn(zb))],fill=int(peak*fog((za+zb)/2,zf)),width=w)
def finish(bg,lines,col,name,amt=1.0,grain=1.4):
    bg=bg+(lines*KEEP)[...,None]*np.array(col,np.float32)*amt
    bg=bg+rng.normal(0,grain,(H,W))[...,None]
    bg=np.clip(bg,0,255); out=255-(255-bg)*(255-L)/255
    img=Image.fromarray(np.clip(out,0,255).astype(np.uint8)); img.save(OUT+f'wy-{name}.png',optimize=True)
    img.resize((960,540),Image.LANCZOS).save(f'work/p-{name}.png'); print('ok',name)
def stars(density,peak,keep=None):
    st=rng.random((H,W))>1-density; br=(rng.random((H,W))**4*peak+12)
    s=np.zeros((H,W),np.float32); s[st]=br[st]
    big=Image.fromarray(np.clip(s*(rng.random((H,W))>0.85),0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))
    sm=Image.fromarray(np.clip(s,0,255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    return (np.asarray(sm).astype(np.float32)*2.5+np.asarray(big).astype(np.float32)*4)*(KEEP if keep is None else keep)

def corridor():
    img,d=canvas(); w,h=1.75,1.0; zf=7; z0,z1=0.35,45
    rect=lambda z:(cx-f*w/z,cy-f*h/z,cx+f*w/z,cy+f*h/z)
    z=0.5
    while z<z1:
        x0,y0,x1,y1=rect(z); d.rectangle([P(x0,y0),P(x1,y1)],outline=int(255*fog(z,zf)),width=3); z+=0.9
    for u in np.linspace(-w,w,13):
        for yw in (-h,h): seg(d,lambda z,u=u,yw=yw:(cx+f*u/z,cy+f*yw/z),z0,z1,zf,255)
    for v in np.linspace(-h,h,8)[1:-1]:
        for xw in (-w,w): seg(d,lambda z,v=v,xw=xw:(cx+f*xw/z,cy+f*v/z),z0,z1,zf,255)
    bg=mix((24,32,44),(8,11,16),(r/1.3)**1.2)
    finish(bg,resolve(img),(60,85,110),'6-grid-corridor',0.55)

def horizon():
    img,d=canvas(); yh=cy+500; ch=1.0; zf=14
    for z in np.arange(0.4,60,0.8):
        y=yh+f*ch/z
        if y<H+10: d.line([P(0,y),P(W,y)],fill=int(255*fog(z,zf)),width=3)
    for u in np.arange(-40,40.1,0.8):
        seg(d,lambda z,u=u:(cx+f*u/z,yh+f*ch/z),0.25,80,zf,255)
    lines=resolve(img)
    sky=mix((7,12,16),(20,36,42),np.clip((yy-0)/(yh),0,1)**2.2)
    floor=mix((16,30,34),(6,10,12),np.clip((yy-yh)/(H-yh),0,1)**0.8)
    bg=np.where((yy<yh)[...,None],sky,floor)
    bg=bg+np.exp(-((yy-yh)/14)**2)[...,None]*np.array([10,22,26])*np.exp(-((xx-cx)/(W*0.45))**2)[...,None]
    bg=bg+(stars(0.0006,90)*np.clip((yh-80-yy)/600,0,1))[...,None]*np.array([0.8,0.95,1])
    finish(bg,lines,(55,110,115),'7-grid-horizon',0.6)

def terrain():
    img,d=canvas(); yh=cy+560; ch=1.0; zf=22
    nz,nx=90,260; xs=np.linspace(-30,30,nx); zs=np.geomspace(1.6,70,nz)
    noise=np.asarray(Image.fromarray((rng.random((12,40))*255).astype(np.uint8)).resize((nx,nz),Image.BICUBIC)).astype(np.float32)/255
    fine=np.asarray(Image.fromarray((rng.random((30,90))*255).astype(np.uint8)).resize((nx,nz),Image.BICUBIC)).astype(np.float32)/255
    valley=np.clip(np.abs(xs)/9,0,1)**1.6
    hgt=(noise*1.0+fine*0.35)*(0.15+1.9*valley)[None,:]*np.clip(zs/6,0.3,1)[:,None]
    for i in range(nz-1,-1,-1):
        z=zs[i]; pts=[(cx+f*x/z, yh+f*(ch-hh)/z) for x,hh in zip(xs,hgt[i])]
        poly=[P(*p) for p in pts]+[P(pts[-1][0],H+50),P(pts[0][0],H+50)]
        d.polygon(poly,fill=0)
        d.line([P(*p) for p in pts],fill=int(255*fog(z,zf)),width=3)
    lines=resolve(img)
    bg=mix((26,32,44),(8,10,15),np.clip(yy/H,0,1)**0.9)
    bg=bg+(stars(0.0005,80)*np.clip((yh-300-yy)/500,0,1))[...,None]*np.array([0.85,0.9,1])
    finish(bg,lines,(80,100,130),'8-wireframe-terrain',0.95)

def planet():
    R=5200; pcx,pcy=cx-500,H+R-560
    dd=np.sqrt((xx-pcx)**2+(yy-pcy)**2)
    space=mix((14,20,32),(4,6,10),(r/1.3)**1.1)
    inside=dd<R
    # lit from upper-right: terminator shading on the disc
    nx_=(xx-pcx)/R; ny_=(yy-pcy)/R
    lit=np.clip(0.35+0.65*(nx_*0.45-ny_*0.9),0,1)
    surf=mix((5,7,11),(18,26,38),lit**2)
    rim=np.exp(-np.clip(R-dd,0,None)/45)*inside
    atmo=np.exp(-np.clip(dd-R,0,None)/70)*(~inside)
    bg=np.where(inside[...,None],surf,space)
    rimw=np.clip(0.25+0.75*lit,0,1)
    bg=bg+(rim*rimw)[...,None]*np.array([40,62,85])+(atmo*rimw)[...,None]*np.array([22,36,55])
    # faint lat/long wireframe on the planet for depth
    img,d=canvas()
    for lat in np.radians(np.arange(-80,81,8)):
        pts=[]
        for lon in np.radians(np.linspace(-90,90,400)):
            X=np.cos(lat)*np.sin(lon); Y=np.sin(lat); Zc=np.cos(lat)*np.cos(lon)
            # tilt sphere toward viewer so the grid reads as a globe
            t_=np.radians(62); Y2=Y*np.cos(t_)-Zc*np.sin(t_); Z2=Y*np.sin(t_)+Zc*np.cos(t_)
            if Z2>0: pts.append(P(pcx+R*X,pcy+R*Y2))
            elif len(pts)>1: d.line(pts,fill=150,width=2); pts=[]
            else: pts=[]
        if len(pts)>1: d.line(pts,fill=150,width=2)
    for lon in np.radians(np.arange(-90,91,8)):
        pts=[]
        for lat in np.radians(np.linspace(-90,90,400)):
            X=np.cos(lat)*np.sin(lon); Y=np.sin(lat); Zc=np.cos(lat)*np.cos(lon)
            t_=np.radians(62); Y2=Y*np.cos(t_)-Zc*np.sin(t_); Z2=Y*np.sin(t_)+Zc*np.cos(t_)
            if Z2>0: pts.append(P(pcx+R*X,pcy+R*Y2))
            elif len(pts)>1: d.line(pts,fill=150,width=2); pts=[]
            else: pts=[]
        if len(pts)>1: d.line(pts,fill=150,width=2)
    lines=resolve(img)*np.clip((R-dd)/40,0,1)*(0.3+0.7*lit)
    bg=bg+(stars(0.0007,110)*(~inside))[...,None]*np.array([0.85,0.92,1])
    finish(bg,lines,(50,75,100),'9-planet-orbit',0.5)

def dotgrid():
    img,d=canvas(); sp=48
    for gy in np.arange(sp/2,H,sp):
        for gx in np.arange(sp/2,W,sp):
            big=(round((gx-sp/2)/sp)%5==0 and round((gy-sp/2)/sp)%5==0)
            rr=(3.2 if big else 1.9)*S; d.ellipse([gx*S-rr,gy*S-rr,gx*S+rr,gy*S+rr],fill=255 if big else 190)
    lines=resolve(img)*(0.45+0.55*np.clip(1-r/1.5,0,1))
    bg=mix((20,34,32),(6,11,11),(r/1.25)**1.2)
    finish(bg,lines,(55,95,85),'10-dot-grid',0.85)

if __name__=="__main__":
  for fn in sys.argv[1:] or ['corridor','horizon','terrain','planet','dotgrid']: globals()[fn]()
