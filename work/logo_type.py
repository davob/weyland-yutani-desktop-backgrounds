import sys, os, json
os.chdir(os.path.dirname(os.path.abspath(__file__))+'/..'); sys.path.insert(0,'work')
import corp
from corp import *
from scipy.ndimage import gaussian_filter
LY=json.load(open('work/layout.json')); SC=1.25
CW0=LY['pitch']*SC; CH0=LY['row_pitch']*SC
def to4k(x,y): return ox+x*SC, oy+y*SC
# --- wing silhouette + tone maps on the 4K canvas ---
occ=np.zeros((H,W),np.float32); tone=np.zeros((H,W),np.float32); cnt=np.zeros((H,W),np.float32)
for c in LY['cells']:
    X,Y=to4k(c['x'],c['y']); x0,x1=int(X-CW0/2),int(X+CW0/2); y0,y1=int(Y-CH0/2),int(Y+CH0/2)
    occ[y0:y1,x0:x1]=1; tone[y0:y1,x0:x1]+=c['blue']; cnt[y0:y1,x0:x1]+=1
tone=np.where(cnt>0,tone/np.maximum(cnt,1),0)
# vector silhouette: trace each word's edges row to row and join them into clean slanted polygons
PUNCT=set('.:-+/')
rowsd={}
for c in LY['cells']: rowsd.setdefault(c['r'],[]).append(c)
RUNS={}
for r,cs in rowsd.items():
    cs=sorted(cs,key=lambda c:c['k']); runs=[]; cur=[cs[0]]
    for c in cs[1:]:
        if c['k']==cur[-1]['k']+1: cur.append(c)
        else: runs.append(cur); cur=[c]
    runs.append(cur)
    out=[]
    for ru in runs:
        L_=to4k(ru[0]['x'],0)[0]-CW0/2+(CW0*0.5 if ru[0]['ch'] in PUNCT else 0)
        R_=to4k(ru[-1]['x'],0)[0]+CW0/2-(CW0*0.5 if ru[-1]['ch'] in PUNCT else 0)
        if R_-L_>CW0*0.6: out.append((L_,R_))
    RUNS[r]=(to4k(0,cs[0]['y'])[1],out)
SS2=2; vm=Image.new('L',(W*SS2,H*SS2),0); vd=ImageDraw.Draw(vm)
def P2(x,y): return (x*SS2,y*SS2)
POLYS=[]
rk=sorted(RUNS)
for a,b in zip(rk[:-1],rk[1:]):
    ya,ra=RUNS[a]; yb,rb=RUNS[b]
    def ov(p,q): return min(p[1],q[1])-max(p[0],q[0])
    pairs=set()
    for i,p in enumerate(ra):
        j=max(range(len(rb)),key=lambda j:ov(p,rb[j]))
        if ov(p,rb[j])>-CW0*0.5: pairs.add((i,j))
    for j,q in enumerate(rb):
        i=max(range(len(ra)),key=lambda i:ov(ra[i],q))
        if ov(ra[i],q)>-CW0*0.5: pairs.add((i,j))
    for i,j in pairs:
        p,q=ra[i],rb[j]; POLYS.append([(p[0],ya),(p[1],ya),(q[1],yb),(q[0],yb)])
# half-row caps on the top and bottom rows, continuing the slant
for r,sgn in ((rk[0],-1),(rk[-1],1)):
    y,rs=RUNS[r]
    for p in rs: POLYS.append([(p[0],y),(p[1],y),(p[1],y+sgn*CH0*0.45),(p[0],y+sgn*CH0*0.45)])
for poly in POLYS: vd.polygon([P2(*pt) for pt in poly],fill=255)
SMOOTH=np.asarray(vm.resize((W,H),Image.LANCZOS).filter(ImageFilter.GaussianBlur(2.5))).astype(np.float32)/255  # soften tiny jags
TONE=gaussian_filter(tone,(4,8))/np.maximum(gaussian_filter(occ,(4,8)),1e-3)
II=np.pad(SMOOTH,((1,0),(1,0))).cumsum(0).cumsum(1)
def cov(x0,y0,x1,y1):
    x0,y0,x1,y1=[int(round(v)) for v in (max(x0,0),max(y0,0),min(x1,W),min(y1,H))]
    return (II[y1,x1]-II[y0,x1]-II[y1,x0]+II[y0,x0])/max((x1-x0)*(y1-y0),1)
GHI=np.array([150,222,186],np.float32); GLO=np.array([100,165,145],np.float32)
def gcol(t,v,pal=None):
    hi,lo=pal if pal is not None else (GHI,GLO)
    return tuple(int(c) for c in (hi*(1-t)+lo*t)*v)
# stronger two-tone: yellow pieces -> warm phosphor green, blue pieces -> cool teal
PAL2=(np.array([178,226,140],np.float32),np.array([105,190,198],np.float32))
F='C:/Windows/Fonts/'
def typeset(style,dens=1,size=None,fontfile='consola.ttf',seed=5,base=0.72,pal=None):
    g=np.random.default_rng(seed); img=Image.new('RGB',(W,H),(0,0,0)); d=ImageDraw.Draw(img)
    cw,ch=CW0/dens,CH0/dens; fs=size or int(round(ch*0.92)); fnt=ImageFont.truetype(F+fontfile,fs)
    # grid aligned to the original character grid
    gx0=to4k(LY['cells'][0]['x'],0)[0]; gy0=to4k(0,LY['cells'][0]['y'])[1]
    xs=gx0+cw*np.arange(-int((gx0-ox)/cw)-2,int((ox+2500-gx0)/cw)+3)
    ys=gy0+ch*np.arange(-int((gy0-oy)/ch)-2,int((oy+852-gy0)/ch)+3)
    C=np.array([[cov(x-cw/2,y-ch/2,x+cw/2,y+ch/2) for x in xs] for y in ys])
    for j,y in enumerate(ys):
        for i,x in enumerate(xs):
            c=C[j,i]
            if c<0.12: continue
            nb=[C[jj,ii] if 0<=jj<len(ys) and 0<=ii<len(xs) else 0 for jj,ii in ((j-1,i),(j+1,i),(j,i-1),(j,i+1))]
            ch_,v=style(c,nb,i,j,g)
            if not ch_: continue
            t=float(TONE[int(min(y,H-1)),int(min(x,W-1))])
            d.text((x,y),ch_,font=fnt,fill=gcol(t,v*base,pal),anchor='mm')
    return np.asarray(img).astype(np.float32)
def edge_char(c):   # partially covered edge cells: drop them so the silhouette stays clean
    return '' if c<0.55 else None
# ---------------- styles ----------------
ORIG={(c['r'],c['k']):c for c in LY['cells']}
def s_ascii():
    img=Image.new('RGB',(W,H),(0,0,0)); d=ImageDraw.Draw(img); fnt=ImageFont.truetype(F+'consola.ttf',44)
    for c in LY['cells']:
        X,Y=to4k(c['x'],c['y']); d.text((X,Y),c['ch'],font=fnt,fill=gcol(c['blue'],0.78),anchor='mm')
    return np.asarray(img).astype(np.float32)
RAMP='MNmdhyso+/:-.'
def st_ramp(c,nb,i,j,g):
    k=int((1-min(c/0.85,1))*(len(RAMP)-1)); return RAMP[k], 0.55+0.45*min(c,1)
HEX='0123456789ABCDEF'
def st_hex(c,nb,i,j,g):
    e=edge_char(c)
    if e: return e,0.45
    return HEX[g.integers(16)], (1.0 if g.random()<0.06 else 0.55+0.25*g.random())
KANA=[chr(cp) for cp in range(0xFF66,0xFF9E)]+list('0123456789')
def st_kana(c,nb,i,j,g):
    e=edge_char(c)
    if e: return e,0.45
    return KANA[g.integers(len(KANA))], (1.0 if g.random()<0.05 else 0.5+0.3*g.random())
WORD='WEYLAND-YUTANI·'
def st_word(c,nb,i,j,g):
    e=edge_char(c)
    if e: return e,0.45
    return WORD[(i+j*4)%len(WORD)], 0.8
PAL3=(np.array([196,236,128],np.float32),np.array([92,196,218],np.float32))   # punchier warm/cool split
HILITE=np.array([214,255,226],np.float32)
def s_hybrid(pal=None,seed=9,base=0.85,bold=False,hi_rate=0.06,hi_white=False,sweep=None,glow=0,legacy=False):
    # legacy=True draws the random digit before the brightness roll, matching how 12m/12n were first rendered
    # original cell layout and edge punctuation, letter bodies swapped for hex digits
    g=np.random.default_rng(seed)
    img=Image.new('RGB',(W,H),(0,0,0)); d=ImageDraw.Draw(img)
    fnt=ImageFont.truetype(F+('consolab.ttf' if bold else 'consola.ttf'),44); fp=ImageFont.truetype(F+'consola.ttf',44)
    for c in LY['cells']:
        X,Y=to4k(c['x'],c['y']); k=sweep(X,Y) if sweep else 1.0
        if c['ch'] in PUNCT: d.text((X,Y),c['ch'],font=fp,fill=gcol(c['blue'],0.62*base*k,pal),anchor='mm'); continue
        digit=HEX[g.integers(16)] if legacy else None
        hot=g.random()<hi_rate; v=1.0 if hot else 0.6+0.22*g.random()
        if digit is None: digit=HEX[g.integers(16)]
        col=tuple(int(t*min(1,base*k*1.05)) for t in HILITE) if (hot and hi_white) else gcol(c['blue'],v*base*k,pal)
        d.text((X,Y),digit,font=fnt,fill=col,anchor='mm')
    a=np.asarray(img).astype(np.float32)
    if glow:   # tight phosphor bloom: hugs the glyphs, no wide haze
        b1=np.asarray(img.filter(ImageFilter.GaussianBlur(2.5))).astype(np.float32)
        b2=np.asarray(img.filter(ImageFilter.GaussianBlur(7))).astype(np.float32)
        a=np.clip(a+b1*0.45*glow+b2*0.18*glow,0,255)
    return a
def sweep_fn(X,Y):   # diagonal refresh band, brighter through the middle of the wings
    t=((X-W/2)*0.35+(Y-H/2))/260; return 0.78+0.4*np.exp(-t*t)
STYLES={
 '12n7-bold-soft':    lambda: s_hybrid(PAL2,base=0.85,bold=True),
 '12n1-pop-bright':   lambda: s_hybrid(PAL3,base=1.0,hi_rate=0.08),
 '12n2-pop-bold':     lambda: s_hybrid(PAL3,base=0.95,bold=True),
 '12n3-pop-glow':     lambda: s_hybrid(PAL3,base=0.9,glow=1.0),
 '12n4-pop-backlit':  (lambda: s_hybrid(PAL3,base=0.95,hi_rate=0.08,hi_white=True), 0.6),
 '12n5-pop-sweep':    lambda: s_hybrid(PAL3,base=0.9,sweep=sweep_fn,hi_white=True),
 '12n6-pop-combo':    (lambda: s_hybrid(PAL3,base=0.95,bold=True,hi_white=True,glow=0.7), 0.5),
 '12m-hybrid-hex-ascii':  lambda: s_hybrid(legacy=True),
 '12n-hybrid-two-tone':   lambda: s_hybrid(PAL2,legacy=True),
 '12o-hex-stream-two-tone': lambda: typeset(st_hex,dens=2,base=0.8,pal=PAL2),
 '12f-type-ascii':      lambda: s_ascii(),
 '12g-type-fine-ascii': lambda: typeset(st_ramp,dens=2,base=0.75),
 '12h-type-hex-stream': lambda: typeset(st_hex,dens=2,base=0.8),
 '12i-type-katakana':   lambda: typeset(st_kana,dens=2,size=24,fontfile='msgothic.ttc',base=0.8),
 '12j-type-wordmark':   lambda: typeset(st_word,dens=2,base=0.8),
}
def titles():
    img=Image.new('L',(W,H),0); d=ImageDraw.Draw(img); fnt=ImageFont.truetype(F+'consolab.ttf',40)
    for txt,y in [('WEYLAND-YUTANI CORP',LY['title_y']),('BUILDING BETTER WORLDS',LY['tag_y'])]:
        target={'W':36*CW0,'B':42*CW0}[txt[0]]; n=len(txt)
        adv=[fnt.getlength(ch) for ch in txt]; track=(target-sum(adv))/(n-1)
        x=W/2-target/2; Y=oy+y*SC
        for ch,a in zip(txt,adv): d.text((x,Y),ch,font=fnt,fill=255,anchor='lm'); x+=a+track
    return np.asarray(img).astype(np.float32)/255
TT=titles()
def scene(name,wings,backlit=0):
    logo=np.maximum(wings,TT[...,None]*GHI*0.85)
    m=Image.fromarray(((logo.max(2)>10)*255).astype(np.uint8)).resize((W//8,H//8),Image.BOX)
    m=m.point(lambda v:255 if v else 0).filter(ImageFilter.MaxFilter(7)).filter(ImageFilter.GaussianBlur(4)).resize((W,H),Image.BILINEAR)
    keep=1-np.asarray(m).astype(np.float32)/255*0.92
    dots=dot_lines()*(0.45+0.55*np.clip(1-r/1.5,0,1))
    bg=mix((20,34,32),(6,11,11),(r/1.25)**1.2)
    if backlit:   # darken a soft plate behind the logo so it lifts by contrast, not brightness
        pm=Image.fromarray(((logo.max(2)>10)*255).astype(np.uint8)).resize((W//8,H//8),Image.BOX).point(lambda v:255 if v else 0)
        pm=pm.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(10)).resize((W,H),Image.BILINEAR)
        bg=bg*(1-backlit*np.asarray(pm).astype(np.float32)[...,None]/255)
    h=HUD(); sp=48
    for k,gx in enumerate(np.arange(sp/2,W,sp*5)):
        if gx>W*0.35: h.text(gx,sp/2+14,f'{k*5:03d}',18,80,'ma',2)
    for k,gy in enumerate(np.arange(sp/2,H,sp*5)):
        if 0<k and gy<BOT-60: h.text(W-sp/2-14,gy-9,f'{k*5:03d}',18,80,'ra',2)
    R=W-170
    h.text(R,TOP+40,'WY-NET  SECURE WORKSTATION',34,170,'ra',6,True)
    h.text(R,TOP+92,'NODE 7F3A-0C  //  CLEARANCE LEVEL 2',26,115,'ra',4)
    y=BOT-60; h.rule(R-1500,R,y-30,55)
    h.text(R,y,'THIS TERMINAL IS PROPERTY OF WEYLAND-YUTANI CORP.  ALL ACTIVITY IS MONITORED AND RECORDED.',22,95,'ra',3)
    h.text(R,y+36,'(C) 2122 WEYLAND-YUTANI CORP.  BUILDING BETTER WORLDS',22,80,'ra',3)
    render(bg,[(dots*keep,(55,95,85)*np.array(0.85)),(h.arr(),(130,185,170))],name,h,logo)
if __name__=='__main__':
    for n in (sys.argv[1:] or list(STYLES)):
        v=STYLES[n]; fn,bl=(v if isinstance(v,tuple) else (v,0)); scene(n,fn(),bl)
