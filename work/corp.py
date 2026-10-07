import sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__))+'/..')
sys.path.insert(0,'work')
from variants3d import *
from PIL import ImageFont
FR='C:/Windows/Fonts/consola.ttf'; FB='C:/Windows/Fonts/consolab.ttf'
def font(sz,b=False): return ImageFont.truetype(FB if b else FR,sz)

def terrain_lines(yh,zf=22,seed=11):
    g=np.random.default_rng(seed); img,d=canvas(); ch=1.0
    nz,nx=90,260; xs=np.linspace(-30,30,nx); zs=np.geomspace(1.6,70,nz)
    noise=np.asarray(Image.fromarray((g.random((12,40))*255).astype(np.uint8)).resize((nx,nz),Image.BICUBIC)).astype(np.float32)/255
    fine=np.asarray(Image.fromarray((g.random((30,90))*255).astype(np.uint8)).resize((nx,nz),Image.BICUBIC)).astype(np.float32)/255
    valley=np.clip(np.abs(xs)/9,0,1)**1.6
    hgt=(noise+fine*0.35)*(0.15+1.9*valley)[None,:]*np.clip(zs/6,0.3,1)[:,None]
    for i in range(nz-1,-1,-1):
        z=zs[i]; pts=[(cx+f*x/z, yh+f*(ch-hh)/z) for x,hh in zip(xs,hgt[i])]
        d.polygon([P(*p) for p in pts]+[P(pts[-1][0],H+50),P(pts[0][0],H+50)],fill=0)
        d.line([P(*p) for p in pts],fill=int(255*fog(z,zf)),width=3)
    return resolve(img), img

def dot_lines(sp=48, ymax=None):
    img,d=canvas()
    for gy in np.arange(sp/2,H if ymax is None else ymax,sp):
        for gx in np.arange(sp/2,W,sp):
            big=(round((gx-sp/2)/sp)%5==0 and round((gy-sp/2)/sp)%5==0)
            rr=(3.2 if big else 1.9)*S; d.ellipse([gx*S-rr,gy*S-rr,gx*S+rr,gy*S+rr],fill=255 if big else 190)
    return resolve(img)

class HUD:
    """Thin interface chrome drawn as an additive light layer."""
    def __init__(s): s.img=Image.new('L',(W,H),0); s.d=ImageDraw.Draw(s.img); s.rects=[]
    def text(s,x,y,t,sz=30,v=150,anchor='la',track=4,b=False):
        sz=int(round(sz*1.2)); fnt=font(sz,b); w=sum(fnt.getlength(c)+track for c in t)-track
        if anchor[0]=='r': x-=w
        if anchor[0]=='m': x-=w/2
        s.rects.append((x,y,x+w,y+sz*1.25))
        for c in t: s.d.text((x,y),c,font=fnt,fill=v); x+=fnt.getlength(c)+track
        return w
    def corners(s,m=110,l=70,v=120,w=2):
        for (x,y,dx,dy) in [(m,m,1,1),(W-m,m,-1,1),(m,H-m-60,1,-1),(W-m,H-m-60,-1,-1)]:
            s.d.line([(x,y),(x+dx*l,y)],fill=v,width=w); s.d.line([(x,y),(x,y+dy*l)],fill=v,width=w)
    def rule(s,x0,x1,y,v=70,w=2): s.d.line([(x0,y),(x1,y)],fill=v,width=w)
    def ticks(s,x0,x1,y,n,h=10,v=90):
        for x in np.linspace(x0,x1,n): s.d.line([(x,y),(x,y-h)],fill=v,width=2)
    def arr(s): return np.asarray(s.img).astype(np.float32)/255
    def clear(s, pad=30):
        # solid padded box behind every text block so background linework never crosses lettering
        m=Image.new('L',(W,H),0); md=ImageDraw.Draw(m)
        for x0,y0,x1,y1 in s.rects: md.rectangle([x0-pad,y0-pad,x1+pad,y1+pad],fill=255)
        m=m.filter(ImageFilter.GaussianBlur(12))
        return 1-np.asarray(m).astype(np.float32)/255*0.95

def render(bg,layers,name,hud=None,logo=None):
    LL=L if logo is None else logo
    c=hud.clear() if hud is not None else 1
    for i,(arr,col) in enumerate(layers):
        if hud is not None and i<len(layers)-1: arr=arr*c
        bg=bg+arr[...,None]*np.array(col,np.float32)
    bg=bg+rng.normal(0,1.3,(H,W))[...,None]
    bg=np.clip(bg,0,255); out=255-(255-bg)*(255-LL)/255
    img=Image.fromarray(np.clip(out,0,255).astype(np.uint8)); img.save(OUT+f'wy-{name}.png',optimize=True)
    img.resize((960,540),Image.LANCZOS).save(f'work/p-{name}.png'); print('ok',name)

TOP=120; BOT=H-230   # stay clear of desktop icons column (left) and taskbar (bottom)

def survey():
    yh=cy+560; lines,_=terrain_lines(yh)
    bg=mix((26,32,44),(8,10,15),np.clip(yy/H,0,1)**0.9)
    h=HUD(); h.corners()
    R=W-200
    h.text(R,TOP+40,'WEYLAND-YUTANI CORPORATION',34,170,'ra',6,True)
    h.text(R,TOP+92,'TERRAFORMING DIVISION  //  ATMOSPHERIC SURVEY',26,115,'ra',4)
    h.rule(R-760,R,TOP+140,60)
    h.text(R,TOP+158,'SURVEY GRID  ACH-07     STATUS  NOMINAL',24,95,'ra',4)
    # bottom-right survey readout, above the taskbar
    y=BOT-120
    for i,t in enumerate(['LV-426  //  ACHERON','ZETA2 RETICULI SYSTEM','LAT -32.17   LONG 118.40   ELEV 2,310 M']):
        h.text(R,y+i*40,t,26 if i else 30,130 if i==0 else 95,'ra',4,i==0)
    # scale bar bottom-centre
    sx=cx-250; sy=BOT+10
    h.rule(sx,sx+500,sy,110); h.ticks(sx,sx+500,sy,6,12,110)
    h.text(sx,sy+14,'0',22,95,'ma',2); h.text(sx+500,sy+14,'10 KM',22,95,'ma',2)
    render(bg,[(lines*KEEP,(80,100,130)),(h.arr()*KEEP,(150,175,195))],'11-corporate-survey',h)

def place(path):
    a=np.zeros((H,W),np.float32); m=np.asarray(Image.open(path)).astype(np.float32)/255
    a[oy:oy+m.shape[0],ox:ox+m.shape[1]]=m; return a
MATTE=place('work/logo_matte.png'); TEXTM=place('work/logo_matte_text.png')
GREEN_HI=np.array([150,222,186],np.float32); GREEN_LO=np.array([105,170,150],np.float32)
def green_logo():
    # keep the original's two-tone structure (yellow vs blue words) as two shades of phosphor green
    blu=np.clip((L[...,2]-L[...,0])/np.maximum(L.max(2),1)*2.2+0.35,0,1)
    blu=np.asarray(Image.fromarray((blu*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))).astype(np.float32)/255
    tint=GREEN_HI*(1-blu[...,None])+GREEN_LO*blu[...,None]
    return MATTE[...,None]*tint
def dot_logo(sp=48, coloured=False, base=10, grow=28, bright=1.0):
    art=np.clip(MATTE-TEXTM,0,1)
    img=Image.new('RGB',(W*S,H*S),(0,0,0)); d=ImageDraw.Draw(img)
    gx=np.arange(sp/2,W,sp); gy=np.arange(sp/2,H,sp)
    cov=np.zeros((len(gy),len(gx)))
    for j,y in enumerate(gy):
        for i,x in enumerate(gx):
            cov[j,i]=art[int(y-sp/2):int(y+sp/2),int(x-sp/2):int(x+sp/2)].mean()
    cov=np.clip(cov/np.percentile(cov[cov>0.02],90),0,1)
    for j,y in enumerate(gy):
        for i,x in enumerate(gx):
            c=cov[j,i]
            if c<0.14: continue
            side=base+grow*c**0.8; v=(0.55+0.45*c)*bright
            if coloured:
                cell=L[int(y-sp/2):int(y+sp/2),int(x-sp/2):int(x+sp/2)].reshape(-1,3); lum=cell.max(1)
                col=cell[lum>0.5*lum.max()].mean(0); col=col/col.max()*235
            else: col=GREEN_HI
            hs=side*S/2; d.rectangle([x*S-hs,y*S-hs,x*S+hs,y*S+hs],fill=tuple(int(t) for t in col*v))
    sq=np.asarray(img.resize((W,H),Image.LANCZOS)).astype(np.float32)
    text=TEXTM[...,None]*(L if coloured else GREEN_HI*np.ones(3)) if coloured else TEXTM[...,None]*GREEN_LO*1.25
    if coloured: text=L*(TEXTM[...,None]>0.02)
    return np.maximum(sq,text)

def workstation(style='orig'):
    dots=dot_lines()*(0.45+0.55*np.clip(1-r/1.5,0,1))
    bg=mix((20,34,32),(6,11,11),(r/1.25)**1.2)
    h=HUD(); sp=48
    for k,gx in enumerate(np.arange(sp/2,W,sp*5)):
        if gx>W*0.35: h.text(gx,sp/2+14,f'{k*5:03d}',18,80,'ma',2)
    for k,gy in enumerate(np.arange(sp/2,H,sp*5)):
        if 0<k and gy<BOT-60: h.text(W-sp/2-14,gy-9,f'{k*5:03d}',18,80,'ra',2)
    R=W-170
    h.text(R,TOP+40,'WY-NET  SECURE WORKSTATION',34,170,'ra',6,True)
    h.text(R,TOP+92,'NODE 7F3A-0C  //  CLEARANCE LEVEL 2',26,115,'ra',4)
    y=BOT-60
    h.rule(R-1500,R,y-30,55)
    h.text(R,y,'THIS TERMINAL IS PROPERTY OF WEYLAND-YUTANI CORP.  ALL ACTIVITY IS MONITORED AND RECORDED.',22,95,'ra',3)
    h.text(R,y+36,'(C) 2122 WEYLAND-YUTANI CORP.  BUILDING BETTER WORLDS',22,80,'ra',3)
    logo={'orig':None,'green':green_logo(),'dots':dot_logo(base=8,grow=16,bright=0.9),'dots-colour':dot_logo(coloured=True,base=8,grow=16,bright=0.9),'dots-bold':dot_logo(bright=0.85)}[style]
    keep=KEEP if style in ('orig','green') else np.minimum(KEEP*0+1, 1-0.9*np.asarray(Image.fromarray(((logo.max(2)>8)*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(4))).astype(np.float32)/255)
    name={'orig':'12-corporate-workstation','green':'12b-workstation-green','dots':'12c-workstation-dot-logo','dots-colour':'12d-workstation-dot-logo-colour','dots-bold':'12e-workstation-dot-logo-bold'}[style]
    render(bg,[(dots*keep,(55,95,85)*np.array(0.85)),(h.arr()*KEEP,(130,185,170))],name,h,logo)
def workstation_all():
    for st in ('orig','green','dots','dots-colour','dots-bold'): workstation(st)

def orbital():
    yh=cy+560; lines,timg=terrain_lines(yh,seed=23)
    # dots only in the sky, hidden behind the ridgeline
    sky=np.asarray(timg.resize((W,H),Image.BILINEAR)).astype(np.float32)
    dots=dot_lines(ymax=yh+200)
    # mask: anything below the far ridge silhouette — approximate with horizon minus peaks via fill
    m=Image.new('L',(W,H),0); md=ImageDraw.Draw(m)
    ridge=np.full(W,H,np.float32)
    ys,xs_=np.nonzero(lines>0.02)
    np.minimum.at(ridge,xs_,ys.astype(np.float32))
    ridge=np.asarray(Image.fromarray(ridge[None,:]).filter(ImageFilter.MinFilter(1)) if False else ridge)
    above=(yy<ridge[None,:]-6).astype(np.float32)
    dots=dots*above*(0.35+0.65*np.clip(1-r/1.5,0,1))
    bg=mix((22,30,40),(7,9,13),np.clip(yy/H,0,1)**0.9)
    h=HUD(); h.corners(v=100)
    R=W-200
    h.text(R,TOP+40,'WEYLAND-YUTANI CORPORATION',34,170,'ra',6,True)
    h.text(R,TOP+92,'COLONIAL ADMINISTRATION  //  ORBITAL SURVEY',26,115,'ra',4)
    # compass rose-ish heading tape, top centre
    tx0,tx1,ty=cx-600,cx+600,TOP+30
    h.rule(tx0,tx1,ty,70); h.ticks(tx0,tx1,ty+12,25,12,80)
    for i,lab in enumerate(['W','NW','N','NE','E']): h.text(tx0+i*300,ty+22,lab,22,110,'ma',2)
    h.text(R,BOT-40,'HADLEY\'S HOPE  //  POP. 158  //  PROCESSOR ONLINE',24,100,'ra',4)
    render(bg,[(dots*KEEP,(70,90,115)),(lines*KEEP,(80,100,130)),(h.arr()*KEEP,(150,175,195))],'13-corporate-orbital',h)

def executive():
    dots=dot_lines(sp=40)*(0.5+0.5*np.clip(1-r/1.5,0,1))
    bg=mix((30,32,36),(10,11,13),(r/1.25)**1.2)
    h=HUD()
    for y in (TOP+10,BOT+20): h.rule(W*0.38,W-170,y,70)
    h.text(W-170,TOP+28,'WEYLAND-YUTANI CORPORATION  //  EXECUTIVE NETWORK',26,135,'ra',6)
    h.text(W-170,BOT+38,'EST. 2099  //  HEADQUARTERS: TOKYO  .  LONDON  .  SAN FRANCISCO',22,95,'ra',4)
    render(bg,[(dots*KEEP,(70,74,82)),(h.arr()*KEEP,(170,175,185))],'14-corporate-executive',h)

if __name__=='__main__':
  # args are function names; "workstation:<style>" renders a single workstation style
  for fn in sys.argv[1:] or ['survey','workstation_all','orbital','executive']:
      name,_,arg=fn.partition(':')
      globals()[name](arg) if arg else globals()[name]()
